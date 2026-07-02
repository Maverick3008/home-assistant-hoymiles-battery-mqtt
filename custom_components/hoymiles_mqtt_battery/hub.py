"""MQTT hub for Hoymiles MQTT Battery."""

from __future__ import annotations

from collections.abc import Callable
import json
import logging
from typing import Any

from homeassistant.components import mqtt
from homeassistant.core import HomeAssistant, callback

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
    GROUP_VALUE_BATTERY_STATE,
    GROUP_VALUE_POWER_FROM_BATTERY,
    GROUP_VALUE_POWER_TO_BATTERY,
    GROUP_VALUE_SOC,
    JSON_BATTERY_POWER,
    JSON_BATTERY_STATE,
    JSON_BATTERY_TEMP,
    JSON_CHARGE_TODAY,
    JSON_DISCHARGE_TODAY,
    JSON_RSSI,
    JSON_SOC,
    MQTT_DEVICE_PREFIX,
    QUICK_TOPIC,
    SYSTEM_TOPIC,
    VALUE_BATTERY_STATE,
    VALUE_BATTERY_TEMP,
    VALUE_CHARGE_TODAY,
    VALUE_DISCHARGE_TODAY,
    VALUE_POWER_RAW,
    VALUE_RSSI,
    VALUE_SOC,
)

_LOGGER = logging.getLogger(__name__)


class HoymilesMqttHub:
    """Subscribe to Hoymiles MQTT topics and cache current values."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize the hub."""
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
        """Normalize user-entered serial numbers for MQTT topics."""
        normalized = str(serial).strip()
        if normalized.upper().startswith(MQTT_DEVICE_PREFIX):
            normalized = normalized[len(MQTT_DEVICE_PREFIX) :]
        return normalized

    @property
    def batteries(self) -> list[dict[str, Any]]:
        """Return configured batteries."""
        return list(self._battery_config_by_serial.values())

    def battery_config(self, serial: str) -> dict[str, Any]:
        """Return config for one battery."""
        return self._battery_config_by_serial[self.normalize_serial(serial)]

    def battery_name(self, serial: str) -> str:
        """Return display name for one battery."""
        config = self.battery_config(serial)
        return config.get(CONF_DEVICE_NAME) or f"MSA-{self.normalize_serial(serial)}"

    def battery_model(self, serial: str) -> str | None:
        """Return model for one battery."""
        return self.battery_config(serial).get(CONF_MODEL)

    def battery_capacity_kwh(self, serial: str) -> float:
        """Return configured capacity for one battery."""
        try:
            return float(self.battery_config(serial).get(CONF_CAPACITY_KWH, 0))
        except (TypeError, ValueError):
            return 0.0

    def battery_value(self, serial: str, key: str) -> Any:
        """Return a cached value for one battery."""
        return self._values.get(self.normalize_serial(serial), {}).get(key)

    def battery_power_from(self, serial: str) -> float | None:
        """Return positive discharge power for one battery."""
        power = self.battery_value(serial, VALUE_POWER_RAW)
        if power is None:
            return None
        return round(max(float(power), 0.0), 1)

    def battery_power_to(self, serial: str) -> float | None:
        """Return positive charge power for one battery."""
        power = self.battery_value(serial, VALUE_POWER_RAW)
        if power is None:
            return None
        return round(abs(min(float(power), 0.0)), 1)

    def group_value(self, key: str) -> Any:
        """Return one calculated group value."""
        if key == GROUP_VALUE_SOC:
            return self._calculate_group_soc()
        if key == GROUP_VALUE_POWER_FROM_BATTERY:
            return self._calculate_group_power_from()
        if key == GROUP_VALUE_POWER_TO_BATTERY:
            return self._calculate_group_power_to()
        if key == GROUP_VALUE_BATTERY_STATE:
            return self._calculate_group_state()
        return None

    def _calculate_group_soc(self) -> float | None:
        weighted_sum = 0.0
        total_capacity = 0.0

        for battery in self.batteries:
            serial = battery[CONF_SERIAL]
            soc = self.battery_value(serial, VALUE_SOC)
            capacity = self.battery_capacity_kwh(serial)
            if soc is None or capacity <= 0:
                continue
            weighted_sum += float(soc) * capacity
            total_capacity += capacity

        if total_capacity <= 0:
            return None
        return round(weighted_sum / total_capacity, 1)

    def _calculate_group_power_from(self) -> float | None:
        values = [
            self.battery_power_from(battery[CONF_SERIAL])
            for battery in self.batteries
        ]
        known = [value for value in values if value is not None]
        if not known:
            return None
        return round(sum(known), 1)

    def _calculate_group_power_to(self) -> float | None:
        values = [
            self.battery_power_to(battery[CONF_SERIAL])
            for battery in self.batteries
        ]
        known = [value for value in values if value is not None]
        if not known:
            return None
        return round(sum(known), 1)

    def _calculate_group_state(self) -> str | None:
        power_from = self._calculate_group_power_from()
        power_to = self._calculate_group_power_to()
        if power_from is None and power_to is None:
            return None
        if power_from and power_from > 0:
            return BATTERY_STATE_DISCHARGE
        if power_to and power_to > 0:
            return BATTERY_STATE_CHARGE
        return BATTERY_STATE_STANDBY

    def topic(self, serial: str, suffix: str) -> str:
        """Build the MQTT topic for a battery and suffix."""
        base_topic = str(self.config.get(CONF_BASE_TOPIC, DEFAULT_BASE_TOPIC)).strip("/")
        return f"{base_topic}/{MQTT_DEVICE_PREFIX}{self.normalize_serial(serial)}/{suffix}"

    async def async_start(self) -> None:
        """Start MQTT subscriptions."""
        for battery in self.batteries:
            serial = battery[CONF_SERIAL]
            await self._subscribe(serial, QUICK_TOPIC)
            await self._subscribe(serial, DEVICE_TOPIC)
            await self._subscribe(serial, SYSTEM_TOPIC)

    async def async_stop(self) -> None:
        """Stop MQTT subscriptions."""
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
        _LOGGER.debug("Subscribed to Hoymiles MQTT topic %s", topic)

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Add a listener and return a function to remove it."""
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
        """Parse an MQTT message and update cached values."""
        serial = self.normalize_serial(serial)
        try:
            if isinstance(payload, bytes):
                payload = payload.decode()
            data = json.loads(payload)
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as err:
            _LOGGER.debug("Ignoring invalid Hoymiles MQTT payload for %s: %s", serial, err)
            return

        values = self._values.setdefault(serial, {})

        if suffix == QUICK_TOPIC:
            self._set_float(values, VALUE_SOC, data.get(JSON_SOC))
            power = self._as_float(data.get(JSON_BATTERY_POWER))
            if power is not None:
                if self.battery_config(serial).get(CONF_INVERT_POWER, False):
                    power *= -1
                values[VALUE_POWER_RAW] = round(power, 1)
            state = data.get(JSON_BATTERY_STATE)
            if state is not None:
                values[VALUE_BATTERY_STATE] = str(state)

        elif suffix == DEVICE_TOPIC:
            self._set_float(values, VALUE_BATTERY_TEMP, data.get(JSON_BATTERY_TEMP))
            self._set_float(values, VALUE_RSSI, data.get(JSON_RSSI))

        elif suffix == SYSTEM_TOPIC:
            self._set_float(values, VALUE_CHARGE_TODAY, data.get(JSON_CHARGE_TODAY))
            self._set_float(values, VALUE_DISCHARGE_TODAY, data.get(JSON_DISCHARGE_TODAY))

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
