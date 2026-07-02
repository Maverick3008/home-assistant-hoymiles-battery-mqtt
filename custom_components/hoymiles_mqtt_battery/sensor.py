"""Sensors for Hoymiles MQTT Battery."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfPower, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    BATTERY_STATES,
    CONF_BATTERIES,
    CONF_CREATE_GROUP_SENSORS,
    CONF_CREATE_INDIVIDUAL_SPLIT_POWER,
    CONF_DEVICE_NAME,
    CONF_ENABLE_DIAGNOSTICS,
    CONF_GROUP_NAME,
    CONF_SERIAL,
    DATA_HUB,
    DEFAULT_CREATE_GROUP_SENSORS,
    DEFAULT_CREATE_INDIVIDUAL_SPLIT_POWER,
    DEFAULT_ENABLE_DIAGNOSTICS,
    DEFAULT_GROUP_NAME,
    DOMAIN,
    GROUP_VALUE_BATTERY_STATE,
    GROUP_VALUE_CHARGE_TODAY,
    GROUP_VALUE_DISCHARGE_TODAY,
    GROUP_VALUE_POWER_FROM_BATTERY,
    GROUP_VALUE_POWER_TO_BATTERY,
    GROUP_VALUE_SOC,
    VALUE_BATTERY_STATE,
    VALUE_BATTERY_TEMP,
    VALUE_CHARGE_TODAY,
    VALUE_DISCHARGE_TODAY,
    VALUE_POWER_FROM_BATTERY,
    VALUE_POWER_RAW,
    VALUE_POWER_TO_BATTERY,
    VALUE_RSSI,
    VALUE_SOC,
)
from .hub import HoymilesMqttHub


@dataclass(frozen=True, kw_only=True)
class HoymilesSensorEntityDescription(SensorEntityDescription):
    """Description for a Hoymiles sensor."""

    value_fn: Callable[[HoymilesMqttHub, str | None], Any]
    entity_registry_enabled_default: bool = True
    options: list[str] | None = None


def _battery_value(key: str) -> Callable[[HoymilesMqttHub, str | None], Any]:
    def value_fn(hub: HoymilesMqttHub, serial: str | None) -> Any:
        if serial is None:
            return None
        return hub.battery_value(serial, key)

    return value_fn


def _battery_power_from(hub: HoymilesMqttHub, serial: str | None) -> float | None:
    if serial is None:
        return None
    return hub.battery_power_from(serial)


def _battery_power_to(hub: HoymilesMqttHub, serial: str | None) -> float | None:
    if serial is None:
        return None
    return hub.battery_power_to(serial)


def _group_value(key: str) -> Callable[[HoymilesMqttHub, str | None], Any]:
    def value_fn(hub: HoymilesMqttHub, serial: str | None) -> Any:
        return hub.group_value(key)

    return value_fn


BATTERY_SENSOR_DESCRIPTIONS: tuple[HoymilesSensorEntityDescription, ...] = (
    HoymilesSensorEntityDescription(
        key=VALUE_SOC,
        translation_key=VALUE_SOC,
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
        value_fn=_battery_value(VALUE_SOC),
    ),
    HoymilesSensorEntityDescription(
        key=VALUE_BATTERY_TEMP,
        translation_key=VALUE_BATTERY_TEMP,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
        value_fn=_battery_value(VALUE_BATTERY_TEMP),
    ),
    HoymilesSensorEntityDescription(
        key=VALUE_CHARGE_TODAY,
        translation_key=VALUE_CHARGE_TODAY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:battery-charging",
        value_fn=_battery_value(VALUE_CHARGE_TODAY),
    ),
    HoymilesSensorEntityDescription(
        key=VALUE_DISCHARGE_TODAY,
        translation_key=VALUE_DISCHARGE_TODAY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:battery-minus",
        value_fn=_battery_value(VALUE_DISCHARGE_TODAY),
    ),
    HoymilesSensorEntityDescription(
        key=VALUE_POWER_RAW,
        translation_key=VALUE_POWER_RAW,
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-sync",
        value_fn=_battery_value(VALUE_POWER_RAW),
    ),
    HoymilesSensorEntityDescription(
        key=VALUE_POWER_FROM_BATTERY,
        translation_key=VALUE_POWER_FROM_BATTERY,
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-arrow-down",
        value_fn=_battery_power_from,
    ),
    HoymilesSensorEntityDescription(
        key=VALUE_POWER_TO_BATTERY,
        translation_key=VALUE_POWER_TO_BATTERY,
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-arrow-up",
        value_fn=_battery_power_to,
    ),
    HoymilesSensorEntityDescription(
        key=VALUE_BATTERY_STATE,
        translation_key=VALUE_BATTERY_STATE,
        device_class=SensorDeviceClass.ENUM,
        icon="mdi:battery-clock",
        options=BATTERY_STATES,
        value_fn=_battery_value(VALUE_BATTERY_STATE),
    ),
    HoymilesSensorEntityDescription(
        key=VALUE_RSSI,
        translation_key=VALUE_RSSI,
        native_unit_of_measurement="dBm",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:wifi",
        entity_registry_enabled_default=False,
        value_fn=_battery_value(VALUE_RSSI),
    ),
)

GROUP_SENSOR_DESCRIPTIONS: tuple[HoymilesSensorEntityDescription, ...] = (
    HoymilesSensorEntityDescription(
        key=GROUP_VALUE_SOC,
        translation_key=GROUP_VALUE_SOC,
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
        value_fn=_group_value(GROUP_VALUE_SOC),
    ),
    HoymilesSensorEntityDescription(
        key=GROUP_VALUE_POWER_FROM_BATTERY,
        translation_key=GROUP_VALUE_POWER_FROM_BATTERY,
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-arrow-down",
        value_fn=_group_value(GROUP_VALUE_POWER_FROM_BATTERY),
    ),
    HoymilesSensorEntityDescription(
        key=GROUP_VALUE_POWER_TO_BATTERY,
        translation_key=GROUP_VALUE_POWER_TO_BATTERY,
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-arrow-up",
        value_fn=_group_value(GROUP_VALUE_POWER_TO_BATTERY),
    ),
    HoymilesSensorEntityDescription(
        key=GROUP_VALUE_CHARGE_TODAY,
        translation_key=GROUP_VALUE_CHARGE_TODAY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:battery-charging",
        value_fn=_group_value(GROUP_VALUE_CHARGE_TODAY),
    ),
    HoymilesSensorEntityDescription(
        key=GROUP_VALUE_DISCHARGE_TODAY,
        translation_key=GROUP_VALUE_DISCHARGE_TODAY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:battery-minus",
        value_fn=_group_value(GROUP_VALUE_DISCHARGE_TODAY),
    ),
    HoymilesSensorEntityDescription(
        key=GROUP_VALUE_BATTERY_STATE,
        translation_key=GROUP_VALUE_BATTERY_STATE,
        device_class=SensorDeviceClass.ENUM,
        icon="mdi:battery-clock",
        options=BATTERY_STATES,
        value_fn=_group_value(GROUP_VALUE_BATTERY_STATE),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Hoymiles MQTT Battery sensors."""
    hub: HoymilesMqttHub = hass.data[DOMAIN][entry.entry_id][DATA_HUB]
    config = hub.config

    create_split_power = config.get(
        CONF_CREATE_INDIVIDUAL_SPLIT_POWER,
        DEFAULT_CREATE_INDIVIDUAL_SPLIT_POWER,
    )
    enable_diagnostics = config.get(CONF_ENABLE_DIAGNOSTICS, DEFAULT_ENABLE_DIAGNOSTICS)
    create_group_sensors = config.get(
        CONF_CREATE_GROUP_SENSORS,
        DEFAULT_CREATE_GROUP_SENSORS,
    )

    entities: list[SensorEntity] = []

    for battery in config.get(CONF_BATTERIES, []):
        serial = battery[CONF_SERIAL]
        for description in BATTERY_SENSOR_DESCRIPTIONS:
            if description.key in (VALUE_POWER_FROM_BATTERY, VALUE_POWER_TO_BATTERY):
                if not create_split_power:
                    continue
            if description.key == VALUE_RSSI and not enable_diagnostics:
                continue
            entities.append(HoymilesBatterySensor(hub, entry, serial, description))

    if create_group_sensors:
        for description in GROUP_SENSOR_DESCRIPTIONS:
            entities.append(HoymilesGroupSensor(hub, entry, description))

    async_add_entities(entities)


class HoymilesBaseSensor(SensorEntity):
    """Base class for Hoymiles sensors."""

    entity_description: HoymilesSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        hub: HoymilesMqttHub,
        entry: ConfigEntry,
        description: HoymilesSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        self.hub = hub
        self.entry = entry
        self.entity_description = description
        self._attr_entity_registry_enabled_default = (
            description.entity_registry_enabled_default
        )
        if description.options is not None:
            self._attr_options = description.options

    async def async_added_to_hass(self) -> None:
        """Register update listener."""
        self.async_on_remove(
            self.hub.async_add_listener(self._handle_coordinator_update)
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Write state on MQTT updates."""
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.native_value is not None


class HoymilesBatterySensor(HoymilesBaseSensor):
    """Sensor for one Hoymiles battery."""

    def __init__(
        self,
        hub: HoymilesMqttHub,
        entry: ConfigEntry,
        serial: str,
        description: HoymilesSensorEntityDescription,
    ) -> None:
        """Initialize the battery sensor."""
        super().__init__(hub, entry, description)
        self.serial = hub.normalize_serial(serial)
        self._attr_unique_id = f"{DOMAIN}_{self.serial}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.serial)},
            manufacturer="Hoymiles",
            model=hub.battery_model(self.serial),
            name=hub.battery_name(self.serial),
        )
        self._attr_extra_state_attributes = {
            "serial": self.serial,
            "quick_topic": hub.topic(self.serial, "quick/state"),
            "device_topic": hub.topic(self.serial, "device/state"),
            "system_topic": hub.topic(self.serial, "system/state"),
        }

    @property
    def native_value(self) -> Any:
        """Return the native value."""
        return self.entity_description.value_fn(self.hub, self.serial)


class HoymilesGroupSensor(HoymilesBaseSensor):
    """Calculated sensor for the battery group."""

    def __init__(
        self,
        hub: HoymilesMqttHub,
        entry: ConfigEntry,
        description: HoymilesSensorEntityDescription,
    ) -> None:
        """Initialize the group sensor."""
        super().__init__(hub, entry, description)
        group_name = hub.config.get(CONF_GROUP_NAME, DEFAULT_GROUP_NAME)
        self._attr_unique_id = f"{DOMAIN}_group_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "group")},
            manufacturer="Hoymiles",
            model="MQTT Battery Group",
            name=group_name,
        )
        self._attr_extra_state_attributes = {
            "battery_count": len(hub.batteries),
            "serials": [battery[CONF_SERIAL] for battery in hub.batteries],
            "calculation": "capacity_weighted_soc_and_separated_charge_discharge_power",
        }

    @property
    def native_value(self) -> Any:
        """Return the native value."""
        return self.entity_description.value_fn(self.hub, None)
