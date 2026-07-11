"""Hoymiles MQTT Battery integration."""
from __future__ import annotations

from typing import Any
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DATA_HUB, DOMAIN, PLATFORMS
from .hub import HoymilesMqttHub


def entry_config(entry: ConfigEntry) -> dict[str, Any]:
    """Return the active config for a config entry."""
    return {**entry.data, **entry.options}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Hoymiles MQTT Battery from a config entry."""
    hub = HoymilesMqttHub(hass, entry_config(entry))
    await hub.async_start()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {DATA_HUB: hub}
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        await data[DATA_HUB].async_stop()
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload a config entry after options changed."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
