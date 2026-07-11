"""Sensors for Hoymiles MQTT Battery."""
from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfPower, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import *
from .hub import HoymilesMqttHub

@dataclass(frozen=True, kw_only=True)
class Desc(SensorEntityDescription):
    value_fn: Callable[[HoymilesMqttHub, str | None], Any]
    entity_registry_enabled_default: bool = True
    options: list[str] | None = None

def battery_value(key):
    return lambda hub, serial: None if serial is None else hub.battery_value(serial, key)
def group_value(key):
    return lambda hub, serial: hub.group_value(key)

BATTERY_DESCS = (
    Desc(key=VALUE_SOC, translation_key=VALUE_SOC, native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, icon="mdi:battery", value_fn=battery_value(VALUE_SOC)),
    Desc(key=VALUE_BATTERY_TEMP, translation_key=VALUE_BATTERY_TEMP, native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, icon="mdi:thermometer", value_fn=battery_value(VALUE_BATTERY_TEMP)),
    Desc(key=VALUE_CHARGE_TODAY, translation_key=VALUE_CHARGE_TODAY, native_unit_of_measurement=UnitOfEnergy.WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, icon="mdi:battery-charging", value_fn=battery_value(VALUE_CHARGE_TODAY)),
    Desc(key=VALUE_DISCHARGE_TODAY, translation_key=VALUE_DISCHARGE_TODAY, native_unit_of_measurement=UnitOfEnergy.WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, icon="mdi:battery-minus", value_fn=battery_value(VALUE_DISCHARGE_TODAY)),
    Desc(key=VALUE_POWER_RAW, translation_key=VALUE_POWER_RAW, native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, icon="mdi:battery-sync", value_fn=battery_value(VALUE_POWER_RAW)),
    Desc(key=VALUE_POWER_FROM_BATTERY, translation_key=VALUE_POWER_FROM_BATTERY, native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, icon="mdi:battery-arrow-down", value_fn=lambda h,s: h.battery_power_from(s) if s else None),
    Desc(key=VALUE_POWER_TO_BATTERY, translation_key=VALUE_POWER_TO_BATTERY, native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, icon="mdi:battery-arrow-up", value_fn=lambda h,s: h.battery_power_to(s) if s else None),
    Desc(key=VALUE_BATTERY_STATE, translation_key=VALUE_BATTERY_STATE, device_class=SensorDeviceClass.ENUM, icon="mdi:battery-clock", options=BATTERY_STATES, value_fn=battery_value(VALUE_BATTERY_STATE)),
    Desc(key=VALUE_RSSI, translation_key=VALUE_RSSI, native_unit_of_measurement="dBm", device_class=SensorDeviceClass.SIGNAL_STRENGTH, state_class=SensorStateClass.MEASUREMENT, icon="mdi:wifi", entity_registry_enabled_default=False, value_fn=battery_value(VALUE_RSSI)),
)
GROUP_DESCS = (
    Desc(key=GROUP_VALUE_SOC, translation_key=GROUP_VALUE_SOC, native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, icon="mdi:battery", value_fn=group_value(GROUP_VALUE_SOC)),
    Desc(key=GROUP_VALUE_POWER_RAW, translation_key=GROUP_VALUE_POWER_RAW, native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, icon="mdi:battery-sync", value_fn=group_value(GROUP_VALUE_POWER_RAW)),
    Desc(key=GROUP_VALUE_POWER_FROM_BATTERY, translation_key=GROUP_VALUE_POWER_FROM_BATTERY, native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, icon="mdi:battery-arrow-down", value_fn=group_value(GROUP_VALUE_POWER_FROM_BATTERY)),
    Desc(key=GROUP_VALUE_POWER_TO_BATTERY, translation_key=GROUP_VALUE_POWER_TO_BATTERY, native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, icon="mdi:battery-arrow-up", value_fn=group_value(GROUP_VALUE_POWER_TO_BATTERY)),
    Desc(key=GROUP_VALUE_CHARGE_TODAY, translation_key=GROUP_VALUE_CHARGE_TODAY, native_unit_of_measurement=UnitOfEnergy.WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, icon="mdi:battery-charging", value_fn=group_value(GROUP_VALUE_CHARGE_TODAY)),
    Desc(key=GROUP_VALUE_DISCHARGE_TODAY, translation_key=GROUP_VALUE_DISCHARGE_TODAY, native_unit_of_measurement=UnitOfEnergy.WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, icon="mdi:battery-minus", value_fn=group_value(GROUP_VALUE_DISCHARGE_TODAY)),
    Desc(key=GROUP_VALUE_BATTERY_STATE, translation_key=GROUP_VALUE_BATTERY_STATE, device_class=SensorDeviceClass.ENUM, icon="mdi:battery-clock", options=BATTERY_STATES, value_fn=group_value(GROUP_VALUE_BATTERY_STATE)),
)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    hub = hass.data[DOMAIN][entry.entry_id][DATA_HUB]
    config = hub.config
    entities = []
    for battery in hub.batteries:
        for desc in BATTERY_DESCS:
            if desc.key in (VALUE_POWER_FROM_BATTERY, VALUE_POWER_TO_BATTERY) and not config.get(CONF_CREATE_INDIVIDUAL_SPLIT_POWER, DEFAULT_CREATE_INDIVIDUAL_SPLIT_POWER): continue
            if desc.key == VALUE_RSSI and not config.get(CONF_ENABLE_DIAGNOSTICS, DEFAULT_ENABLE_DIAGNOSTICS): continue
            entities.append(BatterySensor(hub, entry, battery[CONF_SERIAL], desc))
    if config.get(CONF_CREATE_GROUP_SENSORS, DEFAULT_CREATE_GROUP_SENSORS):
        entities.extend(GroupSensor(hub, entry, desc) for desc in GROUP_DESCS)
    async_add_entities(entities)

class BaseSensor(SensorEntity):
    _attr_has_entity_name = True
    def __init__(self, hub, entry, desc):
        self.hub, self.entry, self.entity_description = hub, entry, desc
        self._attr_entity_registry_enabled_default = desc.entity_registry_enabled_default
        if desc.options is not None: self._attr_options = desc.options
    async def async_added_to_hass(self): self.async_on_remove(self.hub.async_add_listener(self._update))
    @callback
    def _update(self): self.async_write_ha_state()
    @property
    def available(self): return self.native_value is not None

class BatterySensor(BaseSensor):
    def __init__(self, hub, entry, serial, desc):
        super().__init__(hub, entry, desc); self.serial = hub.normalize_serial(serial)
        self._attr_unique_id = f"{DOMAIN}_{self.serial}_{desc.key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN,self.serial)}, manufacturer="Hoymiles", model=hub.battery_model(self.serial), name=hub.battery_name(self.serial))
    @property
    def native_value(self): return self.entity_description.value_fn(self.hub, self.serial)

class GroupSensor(BaseSensor):
    def __init__(self, hub, entry, desc):
        super().__init__(hub, entry, desc)
        self._attr_unique_id = f"{DOMAIN}_group_{desc.key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN,"group")}, manufacturer="Hoymiles", model="MQTT Battery Group", name=hub.config.get(CONF_GROUP_NAME,DEFAULT_GROUP_NAME))
    @property
    def native_value(self): return self.entity_description.value_fn(self.hub, None)
