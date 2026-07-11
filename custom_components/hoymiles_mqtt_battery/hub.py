"""MQTT hub for Hoymiles MQTT Battery."""
from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
import json
import logging
from typing import Any

from homeassistant.components import mqtt
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    BATTERY_STATE_CHARGE,
    BATTERY_STATE_DISCHARGE,
    BATTERY_STATE_STANDBY,
    CONF_BASE_TOPIC,
    CONF_BATTERIES,
    CONF_CAPACITY_KWH,
    CONF_DEVICE_NAME,
    CONF_INVERT_POWER,
    CONF_MODEL,
    CONF_SERIAL,
    DEFAULT_BASE_TOPIC,
    DEVICE_TOPIC,
    EMS_MODE_COMMAND_SUFFIX,
    EMS_MODE_MQTT_CONTROL,
    GROUP_VALUE_BATTERY_STATE,
    GROUP_VALUE_CHARGE_TODAY,
    GROUP_VALUE_DISCHARGE_TODAY,
    GROUP_VALUE_POWER_FROM_BATTERY,
    GROUP_VALUE_POWER_RAW,
    GROUP_VALUE_POWER_TO_BATTERY,
    GROUP_VALUE_SOC,
    JSON_BATTERY_POWER,
    JSON_BATTERY_STATE,
    JSON_BATTERY_TEMP,
    JSON_CHARGE_TODAY,
    JSON_DISCHARGE_TODAY,
    JSON_EMS_MODE,
    JSON_RSSI,
    JSON_SOC,
    MQTT_DEVICE_PREFIX,
    POWER_CONTROL_SET_SUFFIX,
    QUICK_TOPIC,
    SYSTEM_TOPIC,
    VALUE_BATTERY_STATE,
    VALUE_BATTERY_TEMP,
    VALUE_CHARGE_TODAY,
    VALUE_DISCHARGE_TODAY,
    VALUE_EMS_MODE,
    VALUE_POWER_CONTROL,
    VALUE_POWER_RAW,
    VALUE_RSSI,
    VALUE_SOC,
)

_LOGGER = logging.getLogger(__name__)
CHARGE_TODAY_KEYS = (JSON_CHARGE_TODAY, "charge_e", "charge_energy", "charge_today", "today_chg_e", "daily_chg_e")
DISCHARGE_TODAY_KEYS = (JSON_DISCHARGE_TODAY, "discharge_e", "discharge_energy", "discharge_today", "today_dchg_e", "daily_dchg_e")
KEEPALIVE_INTERVAL = timedelta(seconds=50)


class HoymilesMqttHub:
    """Subscribe to Hoymiles MQTT topics and cache current values."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        self.hass = hass
        self.config = config
        self._listeners: list[Callable[[], None]] = []
        self._unsubscribers: list[Callable[[], None]] = []
        self._battery_config_by_serial: dict[str, dict[str, Any]] = {}
        self._values: dict[str, dict[str, Any]] = {}

        for battery in config.get(CONF_BATTERIES, []):
            serial = self.normalize_serial(battery[CONF_SERIAL])
            normalized = dict(battery)
            normalized[CONF_SERIAL] = serial
            self._battery_config_by_serial[serial] = normalized
            self._values.setdefault(serial, {})

    @staticmethod
    def normalize_serial(serial: str) -> str:
        normalized = str(serial).strip()
        if normalized.upper().startswith(MQTT_DEVICE_PREFIX):
            normalized = normalized[len(MQTT_DEVICE_PREFIX):]
        return normalized

    @property
    def batteries(self) -> list[dict[str, Any]]:
        return list(self._battery_config_by_serial.values())

    def battery_config(self, serial: str) -> dict[str, Any]:
        return self._battery_config_by_serial[self.normalize_serial(serial)]

    def battery_name(self, serial: str) -> str:
        config = self.battery_config(serial)
        return config.get(CONF_DEVICE_NAME) or f"MSA-{self.normalize_serial(serial)}"

    def battery_model(self, serial: str) -> str | None:
        return self.battery_config(serial).get(CONF_MODEL)

    def battery_capacity_kwh(self, serial: str) -> float:
        try:
            return float(self.battery_config(serial).get(CONF_CAPACITY_KWH, 0))
        except (TypeError, ValueError):
            return 0.0

    def battery_value(self, serial: str, key: str) -> Any:
        return self._values.get(self.normalize_serial(serial), {}).get(key)

    def battery_power_from(self, serial: str) -> float | None:
        power = self.battery_value(serial, VALUE_POWER_RAW)
        return None if power is None else round(abs(min(float(power), 0.0)), 1)

    def battery_power_to(self, serial: str) -> float | None:
        power = self.battery_value(serial, VALUE_POWER_RAW)
        return None if power is None else round(max(float(power), 0.0), 1)

    def group_value(self, key: str) -> Any:
        if key == GROUP_VALUE_SOC:
            weighted_sum = total_capacity = 0.0
            for battery in self.batteries:
                serial = battery[CONF_SERIAL]
                soc = self.battery_value(serial, VALUE_SOC)
                capacity = self.battery_capacity_kwh(serial)
                if soc is not None and capacity > 0:
                    weighted_sum += float(soc) * capacity
                    total_capacity += capacity
            return round(weighted_sum / total_capacity, 1) if total_capacity else None
        if key == GROUP_VALUE_POWER_RAW:
            return self._sum_values(VALUE_POWER_RAW)
        if key == GROUP_VALUE_POWER_FROM_BATTERY:
            values = [self.battery_power_from(b[CONF_SERIAL]) for b in self.batteries]
            return self._sum_known(values)
        if key == GROUP_VALUE_POWER_TO_BATTERY:
            values = [self.battery_power_to(b[CONF_SERIAL]) for b in self.batteries]
            return self._sum_known(values)
        if key == GROUP_VALUE_CHARGE_TODAY:
            return self._sum_values(VALUE_CHARGE_TODAY)
        if key == GROUP_VALUE_DISCHARGE_TODAY:
            return self._sum_values(VALUE_DISCHARGE_TODAY)
        if key == GROUP_VALUE_BATTERY_STATE:
            power_from = self.group_value(GROUP_VALUE_POWER_FROM_BATTERY)
            power_to = self.group_value(GROUP_VALUE_POWER_TO_BATTERY)
            if power_from is None and power_to is None:
                return None
            if power_from and power_from > 0:
                return BATTERY_STATE_DISCHARGE
            if power_to and power_to > 0:
                return BATTERY_STATE_CHARGE
            return BATTERY_STATE_STANDBY
        return None

    def _sum_values(self, key: str) -> float | None:
        return self._sum_known([self.battery_value(b[CONF_SERIAL], key) for b in self.batteries])

    @staticmethod
    def _sum_known(values: list[Any]) -> float | None:
        known = [float(value) for value in values if value is not None]
        return round(sum(known), 1) if known else None

    def topic(self, serial: str, suffix: str) -> str:
        base_topic = str(self.config.get(CONF_BASE_TOPIC, DEFAULT_BASE_TOPIC)).strip("/")
        return f"{base_topic}/{MQTT_DEVICE_PREFIX}{self.normalize_serial(serial)}/{suffix}"

    def command_topic(self, serial: str, component: str, suffix: str) -> str:
        """Build an official Hoymiles command topic from the configured sensor base."""
        base = str(self.config.get(CONF_BASE_TOPIC, DEFAULT_BASE_TOPIC)).strip("/")
        root = base.rsplit("/", 1)[0] if base.endswith("/sensor") else base
        return f"{root}/{component}/{MQTT_DEVICE_PREFIX}{self.normalize_serial(serial)}/{suffix}"

    async def async_start(self) -> None:
        for battery in self.batteries:
            serial = battery[CONF_SERIAL]
            await self._subscribe(serial, QUICK_TOPIC)
            await self._subscribe(serial, DEVICE_TOPIC)
            await self._subscribe(serial, SYSTEM_TOPIC)
        self._unsubscribers.append(async_track_time_interval(self.hass, self._async_keepalive, KEEPALIVE_INTERVAL))

    async def async_stop(self) -> None:
        for unsubscribe in self._unsubscribers:
            unsubscribe()
        self._unsubscribers.clear()
        self._listeners.clear()

    async def _subscribe(self, serial: str, suffix: str) -> None:
        topic = self.topic(serial, suffix)

        @callback
        def message_received(message: Any) -> None:
            self._handle_message(serial, suffix, message.payload)

        unsubscribe = await mqtt.async_subscribe(self.hass, topic, message_received, qos=0)
        self._unsubscribers.append(unsubscribe)

    async def async_set_ems_mode(self, serial: str, mode: str) -> None:
        serial = self.normalize_serial(serial)
        await mqtt.async_publish(
            self.hass,
            self.command_topic(serial, "select", EMS_MODE_COMMAND_SUFFIX),
            mode,
            qos=1,
            retain=False,
        )
        self._values.setdefault(serial, {})[VALUE_EMS_MODE] = mode
        self._notify_listeners()

    async def async_set_power_control(self, serial: str, value: float) -> None:
        """Set battery power. Positive discharges; negative charges, per Hoymiles."""
        serial = self.normalize_serial(serial)
        value = round(max(-2000.0, min(2000.0, float(value))), 1)
        await mqtt.async_publish(
            self.hass,
            self.command_topic(serial, "number", POWER_CONTROL_SET_SUFFIX),
            str(value),
            qos=1,
            retain=False,
        )
        self._values.setdefault(serial, {})[VALUE_POWER_CONTROL] = value
        self._notify_listeners()

    async def _async_keepalive(self, _now: Any) -> None:
        """Repeat the power command before Hoymiles' one-minute timeout."""
        for battery in self.batteries:
            serial = battery[CONF_SERIAL]
            values = self._values.get(serial, {})
            if values.get(VALUE_EMS_MODE) != EMS_MODE_MQTT_CONTROL:
                continue
            value = values.get(VALUE_POWER_CONTROL)
            if value is not None:
                await self.async_set_power_control(serial, float(value))

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(listener)

        @callback
        def remove_listener() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return remove_listener

    @callback
    def _notify_listeners(self) -> None:
        for listener in list(self._listeners):
            listener()

    @callback
    def _handle_message(self, serial: str, suffix: str, payload: str | bytes) -> None:
        serial = self.normalize_serial(serial)
        try:
            if isinstance(payload, bytes):
                payload = payload.decode()
            data = json.loads(payload)
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError):
            return
        if not isinstance(data, dict):
            return

        values = self._values.setdefault(serial, {})
        if suffix == QUICK_TOPIC:
            self._set_float(values, VALUE_SOC, data.get(JSON_SOC))
            power = self._as_float(data.get(JSON_BATTERY_POWER))
            if power is not None:
                physical_power = -power if self.battery_config(serial).get(CONF_INVERT_POWER, False) else power
                values[VALUE_POWER_RAW] = round(-physical_power, 1)
            if data.get(JSON_BATTERY_STATE) is not None:
                values[VALUE_BATTERY_STATE] = str(data[JSON_BATTERY_STATE])
        elif suffix == DEVICE_TOPIC:
            self._set_float(values, VALUE_BATTERY_TEMP, data.get(JSON_BATTERY_TEMP))
            self._set_float(values, VALUE_RSSI, data.get(JSON_RSSI))
        elif suffix == SYSTEM_TOPIC:
            mode = data.get(JSON_EMS_MODE)
            if mode is not None:
                values[VALUE_EMS_MODE] = str(mode)

        self._set_first_float(values, VALUE_CHARGE_TODAY, data, CHARGE_TODAY_KEYS)
        self._set_first_float(values, VALUE_DISCHARGE_TODAY, data, DISCHARGE_TODAY_KEYS)
        self._notify_listeners()

    @staticmethod
    def _as_float(value: Any) -> float | None:
        if value in (None, "", "unknown", "unavailable"):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _set_float(cls, values: dict[str, Any], key: str, value: Any) -> None:
        number = cls._as_float(value)
        if number is not None:
            values[key] = round(number, 1)

    @classmethod
    def _set_first_float(cls, values: dict[str, Any], key: str, data: dict[str, Any], keys: tuple[str, ...]) -> bool:
        for candidate in keys:
            number = cls._as_float(data.get(candidate))
            if number is not None:
                values[key] = round(number, 1)
                return True
        return False
