"""Number entities for Hoymiles MQTT Battery."""
from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_HUB, DOMAIN, VALUE_POWER_CONTROL
from .hub import HoymilesMqttHub


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up one power-control number per configured battery."""
    hub: HoymilesMqttHub = hass.data[DOMAIN][entry.entry_id][DATA_HUB]
    async_add_entities(HoymilesPowerControlNumber(hub, battery["serial"]) for battery in hub.batteries)


class HoymilesPowerControlNumber(NumberEntity):
    """Control charge/discharge power for an individual battery."""

    _attr_has_entity_name = True
    _attr_translation_key = "power_control"
    _attr_icon = "mdi:transmission-tower-import"
    _attr_device_class = NumberDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_native_min_value = -2000.0
    _attr_native_max_value = 2000.0
    _attr_native_step = 1.0
    _attr_mode = NumberMode.BOX

    def __init__(self, hub: HoymilesMqttHub, serial: str) -> None:
        self.hub = hub
        self.serial = hub.normalize_serial(serial)
        self._attr_unique_id = f"{DOMAIN}_{self.serial}_power_control"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.serial)},
            manufacturer="Hoymiles",
            model=hub.battery_model(self.serial),
            name=hub.battery_name(self.serial),
        )
        self._attr_extra_state_attributes = {
            "positive_value": "discharge",
            "negative_value": "charge",
            "zero_value": "standby",
            "requires_mode": "mqtt_ctrl",
        }

    @property
    def native_value(self) -> float:
        value = self.hub.battery_value(self.serial, VALUE_POWER_CONTROL)
        return float(value) if value is not None else 0.0

    async def async_set_native_value(self, value: float) -> None:
        await self.hub.async_set_power_control(self.serial, value)

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self.hub.async_add_listener(self._handle_update))

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()
