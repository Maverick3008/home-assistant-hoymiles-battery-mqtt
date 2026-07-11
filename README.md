# Hoymiles MQTT Battery

Home Assistant custom integration for Hoymiles MS-A2 and HiBattery AC batteries via MQTT.

## Version 0.2.0

This release adds writable entities for each individual battery:

- `select`: EMS mode (`general`, `mqtt_ctrl`, `tou_plan`)
- `number`: charge/discharge power from `-2000 W` to `+2000 W`
- automatic MQTT power-command refresh every 50 seconds while `mqtt_ctrl` is active
- no control entities on the combined group device

### MQTT command topics

```text
homeassistant/select/MSA-<serial>/ems_mode/command
homeassistant/number/MSA-<serial>/power_ctrl/set
```

Positive values discharge the battery; negative values charge it. Power control requires `mqtt_ctrl`. Hoymiles only supports control on standalone units and the master unit.

## Installation

Install through HACS as a custom repository or copy `custom_components/hoymiles_mqtt_battery` to Home Assistant. Restart Home Assistant after updating.

## Existing features

Individual and group sensors for SOC, battery power, charge/discharge power, daily energy, temperature, state and RSSI. Group control is intentionally not created.

This is an unofficial community integration and is not affiliated with Hoymiles.
