"""Config flow for Hoymiles MQTT Battery."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_BASE_TOPIC,
    CONF_BATTERIES,
    CONF_CAPACITY_KWH,
    CONF_CREATE_GROUP_SENSORS,
    CONF_CREATE_INDIVIDUAL_SPLIT_POWER,
    CONF_DEVICE_NAME,
    CONF_ENABLE_DIAGNOSTICS,
    CONF_GROUP_NAME,
    CONF_INVERT_POWER,
    CONF_MODEL,
    CONF_SERIAL,
    DEFAULT_BASE_TOPIC,
    DEFAULT_CAPACITY_KWH,
    DEFAULT_CREATE_GROUP_SENSORS,
    DEFAULT_CREATE_INDIVIDUAL_SPLIT_POWER,
    DEFAULT_ENABLE_DIAGNOSTICS,
    DEFAULT_GROUP_NAME,
    DEFAULT_INVERT_POWER,
    DOMAIN,
    MODEL_MS_A2,
    MODELS,
)
from .hub import HoymilesMqttHub


class HoymilesMqttBatteryConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hoymiles MQTT Battery."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        self._data: dict[str, Any] = {
            CONF_BATTERIES: [],
        }

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Collect global settings."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            self._data.update(user_input)
            self._data[CONF_BASE_TOPIC] = self._clean_base_topic(
                self._data.get(CONF_BASE_TOPIC, DEFAULT_BASE_TOPIC)
            )
            return await self.async_step_battery()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_BASE_TOPIC, default=DEFAULT_BASE_TOPIC): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                    ),
                    vol.Required(CONF_GROUP_NAME, default=DEFAULT_GROUP_NAME): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                    ),
                    vol.Required(
                        CONF_CREATE_GROUP_SENSORS,
                        default=DEFAULT_CREATE_GROUP_SENSORS,
                    ): selector.BooleanSelector(),
                    vol.Required(
                        CONF_CREATE_INDIVIDUAL_SPLIT_POWER,
                        default=DEFAULT_CREATE_INDIVIDUAL_SPLIT_POWER,
                    ): selector.BooleanSelector(),
                    vol.Required(
                        CONF_ENABLE_DIAGNOSTICS,
                        default=DEFAULT_ENABLE_DIAGNOSTICS,
                    ): selector.BooleanSelector(),
                }
            ),
        )

    async def async_step_battery(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Collect one battery."""
        errors: dict[str, str] = {}

        if user_input is not None:
            battery = self._normalize_battery(user_input)
            serial = battery[CONF_SERIAL]
            existing = {
                item[CONF_SERIAL]
                for item in self._data.get(CONF_BATTERIES, [])
            }
            if serial in existing:
                errors[CONF_SERIAL] = "serial_already_added"
            else:
                self._data[CONF_BATTERIES].append(battery)
                return await self.async_step_add_more()

        return self.async_show_form(
            step_id="battery",
            data_schema=self._battery_schema(),
            errors=errors,
        )

    async def async_step_add_more(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Ask whether another battery should be added."""
        if user_input is not None:
            if user_input.get("add_another", False):
                return await self.async_step_battery()
            return self.async_create_entry(
                title="Hoymiles MQTT Battery",
                data=self._data,
            )

        return self.async_show_form(
            step_id="add_more",
            data_schema=vol.Schema(
                {
                    vol.Required("add_another", default=False): selector.BooleanSelector(),
                }
            ),
        )

    @staticmethod
    def _clean_base_topic(value: str) -> str:
        return str(value).strip().strip("/") or DEFAULT_BASE_TOPIC

    @staticmethod
    def _normalize_battery(data: dict[str, Any]) -> dict[str, Any]:
        serial = HoymilesMqttHub.normalize_serial(data[CONF_SERIAL])
        name = str(data.get(CONF_DEVICE_NAME) or "").strip() or f"MSA-{serial}"
        return {
            CONF_DEVICE_NAME: name,
            CONF_SERIAL: serial,
            CONF_MODEL: data.get(CONF_MODEL, MODEL_MS_A2),
            CONF_CAPACITY_KWH: float(data.get(CONF_CAPACITY_KWH, DEFAULT_CAPACITY_KWH)),
            CONF_INVERT_POWER: bool(data.get(CONF_INVERT_POWER, DEFAULT_INVERT_POWER)),
        }

    @staticmethod
    def _battery_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
        defaults = defaults or {}
        return vol.Schema(
            {
                vol.Required(
                    CONF_DEVICE_NAME,
                    default=defaults.get(CONF_DEVICE_NAME, ""),
                ): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                ),
                vol.Required(
                    CONF_SERIAL,
                    default=defaults.get(CONF_SERIAL, ""),
                ): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                ),
                vol.Required(
                    CONF_MODEL,
                    default=defaults.get(CONF_MODEL, MODEL_MS_A2),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=MODELS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    CONF_CAPACITY_KWH,
                    default=defaults.get(CONF_CAPACITY_KWH, DEFAULT_CAPACITY_KWH),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.1,
                        max=200,
                        step=0.01,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement="kWh",
                    )
                ),
                vol.Required(
                    CONF_INVERT_POWER,
                    default=defaults.get(CONF_INVERT_POWER, DEFAULT_INVERT_POWER),
                ): selector.BooleanSelector(),
            }
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return HoymilesMqttBatteryOptionsFlow(config_entry)


class HoymilesMqttBatteryOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Hoymiles MQTT Battery."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize the options flow."""
        self.config_entry = config_entry
        self._data: dict[str, Any] = {**config_entry.data, **config_entry.options}
        self._data.setdefault(CONF_BATTERIES, [])

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Show option actions."""
        if user_input is not None:
            action = user_input["action"]
            if action == "settings":
                return await self.async_step_settings()
            if action == "add_battery":
                return await self.async_step_add_battery()
            if action == "remove_battery":
                return await self.async_step_remove_battery()
            return self.async_create_entry(title="", data=self._data)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required("action", default="settings"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                "settings",
                                "add_battery",
                                "remove_battery",
                                "finish",
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
        )

    async def async_step_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Change global settings."""
        if user_input is not None:
            self._data.update(user_input)
            self._data[CONF_BASE_TOPIC] = HoymilesMqttBatteryConfigFlow._clean_base_topic(
                self._data.get(CONF_BASE_TOPIC, DEFAULT_BASE_TOPIC)
            )
            return self.async_create_entry(title="", data=self._data)

        return self.async_show_form(
            step_id="settings",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_BASE_TOPIC,
                        default=self._data.get(CONF_BASE_TOPIC, DEFAULT_BASE_TOPIC),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                    ),
                    vol.Required(
                        CONF_GROUP_NAME,
                        default=self._data.get(CONF_GROUP_NAME, DEFAULT_GROUP_NAME),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                    ),
                    vol.Required(
                        CONF_CREATE_GROUP_SENSORS,
                        default=self._data.get(
                            CONF_CREATE_GROUP_SENSORS, DEFAULT_CREATE_GROUP_SENSORS
                        ),
                    ): selector.BooleanSelector(),
                    vol.Required(
                        CONF_CREATE_INDIVIDUAL_SPLIT_POWER,
                        default=self._data.get(
                            CONF_CREATE_INDIVIDUAL_SPLIT_POWER,
                            DEFAULT_CREATE_INDIVIDUAL_SPLIT_POWER,
                        ),
                    ): selector.BooleanSelector(),
                    vol.Required(
                        CONF_ENABLE_DIAGNOSTICS,
                        default=self._data.get(
                            CONF_ENABLE_DIAGNOSTICS, DEFAULT_ENABLE_DIAGNOSTICS
                        ),
                    ): selector.BooleanSelector(),
                }
            ),
        )

    async def async_step_add_battery(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Add a battery from the options flow."""
        errors: dict[str, str] = {}
        if user_input is not None:
            battery = HoymilesMqttBatteryConfigFlow._normalize_battery(user_input)
            serial = battery[CONF_SERIAL]
            existing = {
                item[CONF_SERIAL]
                for item in self._data.get(CONF_BATTERIES, [])
            }
            if serial in existing:
                errors[CONF_SERIAL] = "serial_already_added"
            else:
                self._data[CONF_BATTERIES].append(battery)
                return self.async_create_entry(title="", data=self._data)

        return self.async_show_form(
            step_id="add_battery",
            data_schema=HoymilesMqttBatteryConfigFlow._battery_schema(),
            errors=errors,
        )

    async def async_step_remove_battery(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Remove one configured battery."""
        batteries = self._data.get(CONF_BATTERIES, [])
        if not batteries:
            return self.async_abort(reason="no_batteries_configured")

        options = [
            selector.SelectOptionDict(
                value=battery[CONF_SERIAL],
                label=f"{battery.get(CONF_DEVICE_NAME, battery[CONF_SERIAL])} ({battery[CONF_SERIAL]})",
            )
            for battery in batteries
        ]

        if user_input is not None:
            serial_to_remove = user_input[CONF_SERIAL]
            self._data[CONF_BATTERIES] = [
                battery
                for battery in batteries
                if battery[CONF_SERIAL] != serial_to_remove
            ]
            return self.async_create_entry(title="", data=self._data)

        return self.async_show_form(
            step_id="remove_battery",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SERIAL): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
        )
