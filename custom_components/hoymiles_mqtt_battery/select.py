"""Select entities for Hoymiles MQTT Battery."""
from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_HUB, DOMAIN, EMS_MODES, VALUE_EMS_MODE
from .hub import HoymilesMqttHub


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up one EMS mode select per configured battery."""
    hub: HoymilesMqttHub = hass.data[DOMAIN][entry.entry_id][DATA_HUB]
    async_add_entities(HoymilesEmsModeSelect(hub, battery["serial"]) for battery in hub.batteries)


class HoymilesEmsModeSelect(SelectEntity):
    """Select the EMS operating mode of an individual battery."""

    _attr_has_entity_name = True
    _attr_translation_key = "ems_mode"
    _attr_icon = "mdi:battery-cog"
    _attr_options = EMS_MODES

    def __init__(self, hub: HoymilesMqttHub, serial: str) -> None:
        self.hub = hub
        self.serial = hub.normalize_serial(serial)
        self._attr_unique_id = f"{DOMAIN}_{self.serial}_ems_mode"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.serial)},
            manufacturer="Hoymiles",
            model=hub.battery_model(self.serial),
            name=hub.battery_name(self.serial),
        )

    @property
    def current_option(self) -> str | None:
        value: Any = self.hub.battery_value(self.serial, VALUE_EMS_MODE)
        return str(value) if value in EMS_MODES else None

    async def async_select_option(self, option: str) -> None:
        if option not in EMS_MODES:
            raise ValueError(f"Unsupported Hoymiles EMS mode: {option}")
        await self.hub.async_set_ems_mode(self.serial, option)

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self.hub.async_add_listener(self._handle_update))

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()
