"""Constants for the Hoymiles MQTT Battery integration."""
from __future__ import annotations

DOMAIN = "hoymiles_mqtt_battery"
PLATFORMS = ["sensor", "select", "number"]

CONF_BASE_TOPIC = "base_topic"
CONF_BATTERIES = "batteries"
CONF_DEVICE_NAME = "device_name"
CONF_SERIAL = "serial"
CONF_MODEL = "model"
CONF_CAPACITY_KWH = "capacity_kwh"
CONF_INVERT_POWER = "invert_power"
CONF_GROUP_NAME = "group_name"
CONF_CREATE_GROUP_SENSORS = "create_group_sensors"
CONF_CREATE_INDIVIDUAL_SPLIT_POWER = "create_individual_split_power"
CONF_ENABLE_DIAGNOSTICS = "enable_diagnostics"

DEFAULT_BASE_TOPIC = "homeassistant/sensor"
DEFAULT_GROUP_NAME = "Hoymiles Gesamt"
DEFAULT_CAPACITY_KWH = 2.24
DEFAULT_CREATE_GROUP_SENSORS = True
DEFAULT_CREATE_INDIVIDUAL_SPLIT_POWER = True
DEFAULT_ENABLE_DIAGNOSTICS = True
DEFAULT_INVERT_POWER = False

MODEL_MS_A2 = "MS-A2"
MODEL_HIBATTERY_AC = "HiBattery AC"
MODEL_CUSTOM = "Custom"
MODELS = [MODEL_MS_A2, MODEL_HIBATTERY_AC, MODEL_CUSTOM]

MQTT_DEVICE_PREFIX = "MSA-"
QUICK_TOPIC = "quick/state"
DEVICE_TOPIC = "device/state"
SYSTEM_TOPIC = "system/state"
EMS_MODE_COMMAND_SUFFIX = "ems_mode/command"
POWER_CONTROL_SET_SUFFIX = "power_ctrl/set"

DATA_HUB = "hub"

BATTERY_STATE_CHARGE = "charge"
BATTERY_STATE_DISCHARGE = "discharge"
BATTERY_STATE_STANDBY = "standby"
BATTERY_STATES = [BATTERY_STATE_DISCHARGE, BATTERY_STATE_CHARGE, BATTERY_STATE_STANDBY]

EMS_MODE_GENERAL = "general"
EMS_MODE_MQTT_CONTROL = "mqtt_ctrl"
EMS_MODE_TOU_PLAN = "tou_plan"
EMS_MODES = [EMS_MODE_GENERAL, EMS_MODE_MQTT_CONTROL, EMS_MODE_TOU_PLAN]

JSON_SOC = "soc"
JSON_BATTERY_TEMP = "bat_temp"
JSON_CHARGE_TODAY = "chg_e"
JSON_DISCHARGE_TODAY = "dchg_e"
JSON_BATTERY_POWER = "bat_p"
JSON_RSSI = "rssi"
JSON_BATTERY_STATE = "bat_sts"
JSON_EMS_MODE = "ems_mode"

VALUE_SOC = "soc"
VALUE_BATTERY_TEMP = "battery_temperature"
VALUE_CHARGE_TODAY = "charge_today"
VALUE_DISCHARGE_TODAY = "discharge_today"
VALUE_POWER_RAW = "power_raw"
VALUE_POWER_FROM_BATTERY = "power_from_battery"
VALUE_POWER_TO_BATTERY = "power_to_battery"
VALUE_BATTERY_STATE = "battery_state"
VALUE_RSSI = "rssi"
VALUE_EMS_MODE = "ems_mode"
VALUE_POWER_CONTROL = "power_control"

GROUP_VALUE_SOC = "group_soc"
GROUP_VALUE_POWER_RAW = "group_power_raw"
GROUP_VALUE_POWER_FROM_BATTERY = "group_power_from_battery"
GROUP_VALUE_POWER_TO_BATTERY = "group_power_to_battery"
GROUP_VALUE_CHARGE_TODAY = "group_charge_today"
GROUP_VALUE_DISCHARGE_TODAY = "group_discharge_today"
GROUP_VALUE_BATTERY_STATE = "group_battery_state"
