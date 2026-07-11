"""Config flow for Hoymiles MQTT Battery."""
from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from .const import *

def battery_schema(defaults=None):
    d=defaults or {}
    return vol.Schema({
        vol.Required(CONF_DEVICE_NAME, default=d.get(CONF_DEVICE_NAME,"Hoymiles Akku")): str,
        vol.Required(CONF_SERIAL, default=d.get(CONF_SERIAL,"")): str,
        vol.Required(CONF_MODEL, default=d.get(CONF_MODEL,MODEL_MS_A2)): selector.SelectSelector(selector.SelectSelectorConfig(options=MODELS, mode=selector.SelectSelectorMode.DROPDOWN)),
        vol.Required(CONF_CAPACITY_KWH, default=d.get(CONF_CAPACITY_KWH,DEFAULT_CAPACITY_KWH)): vol.Coerce(float),
        vol.Optional(CONF_INVERT_POWER, default=d.get(CONF_INVERT_POWER,DEFAULT_INVERT_POWER)): bool,
    })

def global_schema(defaults=None):
    d=defaults or {}
    return vol.Schema({
        vol.Required(CONF_BASE_TOPIC, default=d.get(CONF_BASE_TOPIC,DEFAULT_BASE_TOPIC)): str,
        vol.Required(CONF_GROUP_NAME, default=d.get(CONF_GROUP_NAME,DEFAULT_GROUP_NAME)): str,
        vol.Optional(CONF_CREATE_GROUP_SENSORS, default=d.get(CONF_CREATE_GROUP_SENSORS,True)): bool,
        vol.Optional(CONF_CREATE_INDIVIDUAL_SPLIT_POWER, default=d.get(CONF_CREATE_INDIVIDUAL_SPLIT_POWER,True)): bool,
        vol.Optional(CONF_ENABLE_DIAGNOSTICS, default=d.get(CONF_ENABLE_DIAGNOSTICS,True)): bool,
    })

class Flow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION=1
    def __init__(self): self.data={}; self.batteries=[]
    async def async_step_user(self,user_input=None):
        if user_input is not None: self.data.update(user_input); return await self.async_step_battery()
        return self.async_show_form(step_id="user",data_schema=global_schema())
    async def async_step_battery(self,user_input=None):
        if user_input is not None:
            serial=str(user_input[CONF_SERIAL]).replace("MSA-","").strip()
            await self.async_set_unique_id(f"hoymiles_mqtt_battery_{serial}"); self._abort_if_unique_id_configured()
            user_input[CONF_SERIAL]=serial; self.batteries.append(user_input); self.data[CONF_BATTERIES]=self.batteries
            return self.async_create_entry(title=self.data.get(CONF_GROUP_NAME,DEFAULT_GROUP_NAME),data=self.data)
        return self.async_show_form(step_id="battery",data_schema=battery_schema())
    @staticmethod
    @callback
    def async_get_options_flow(config_entry): return OptionsFlow(config_entry)

class OptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry): self.entry=entry; self.config={**entry.data,**entry.options}; self.batteries=list(self.config.get(CONF_BATTERIES,[]))
    async def async_step_init(self,user_input=None):
        if user_input is not None: self.config.update(user_input); return await self.async_step_menu()
        return self.async_show_form(step_id="init",data_schema=global_schema(self.config))
    async def async_step_menu(self,user_input=None):
        if user_input is not None:
            action=user_input["action"]
            if action=="add": return await self.async_step_add()
            if action=="remove": return await self.async_step_remove()
            self.config[CONF_BATTERIES]=self.batteries; return self.async_create_entry(title="",data=self.config)
        return self.async_show_form(step_id="menu",data_schema=vol.Schema({vol.Required("action"): selector.SelectSelector(selector.SelectSelectorConfig(options=["add","remove","finish"]))}))
    async def async_step_add(self,user_input=None):
        if user_input is not None: user_input[CONF_SERIAL]=str(user_input[CONF_SERIAL]).replace("MSA-","").strip(); self.batteries.append(user_input); return await self.async_step_menu()
        return self.async_show_form(step_id="add",data_schema=battery_schema())
    async def async_step_remove(self,user_input=None):
        if not self.batteries: return await self.async_step_menu()
        if user_input is not None: self.batteries=[b for b in self.batteries if b[CONF_SERIAL]!=user_input[CONF_SERIAL]]; return await self.async_step_menu()
        opts={b[CONF_SERIAL]:f"{b.get(CONF_DEVICE_NAME,b[CONF_SERIAL])} ({b[CONF_SERIAL]})" for b in self.batteries}
        return self.async_show_form(step_id="remove",data_schema=vol.Schema({vol.Required(CONF_SERIAL): selector.SelectSelector(selector.SelectSelectorConfig(options=[{"value":k,"label":v} for k,v in opts.items()]))}))
