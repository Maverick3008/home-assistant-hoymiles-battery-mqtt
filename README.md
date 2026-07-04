# Hoymiles MQTT Battery

Custom Home Assistant integration for Hoymiles MS-A2 and HiBattery AC batteries that already publish their data to MQTT.

The integration replaces long manual MQTT sensor YAML blocks with a UI-based Config Flow. You add one or more batteries by serial number, and the integration automatically creates individual battery sensors plus shared group sensors.

> German documentation: [README.de.md](README.de.md)

## Features

- UI setup via Home Assistant Config Flow.
- Supports multiple Hoymiles batteries in one integration entry.
- Works with MQTT topics like `homeassistant/sensor/MSA-280024351071/quick/state`.
- Creates individual sensors per battery.
- Creates separated `Power from Battery` and `Power to Battery` sensors per battery.
- Creates group sensors across all configured batteries, including signed total `Power from/to Battery`.
- Calculates group state of charge capacity-weighted by the configured battery capacity.
- Sums daily charge and discharge energy into group sensors.
- Reads daily energy counters from `system/state` and accepts alternative JSON keys. If these values arrive later than `quick/state`, the energy sensors stay unavailable until the first counter payload is received.
- Optional inversion of the incoming MQTT power sign per battery if your MQTT bridge reports the opposite convention.
- Optional diagnostics such as RSSI.
- Includes local Home Assistant brand images in `custom_components/hoymiles_mqtt_battery/brand/`.

## Expected MQTT topics

For each configured serial number, the integration subscribes to these topics:

```text
<base_topic>/MSA-<serial>/quick/state
<base_topic>/MSA-<serial>/device/state
<base_topic>/MSA-<serial>/system/state
```

Default base topic:

```text
homeassistant/sensor
```

Example:

```text
homeassistant/sensor/MSA-280024351071/quick/state
```

## Expected JSON fields

### quick/state

```json
{
  "soc": 72.5,
  "bat_p": -380,
  "bat_sts": "charge"
}
```

### device/state

```json
{
  "bat_temp": 24.0,
  "rssi": -58
}
```

### system/state

```json
{
  "chg_e": 1250,
  "dchg_e": 980
}
```

The daily energy fields are primarily read from `chg_e` and `dchg_e`. The integration also checks all incoming payloads for common aliases such as `charge_e`, `charge_today`, `discharge_e`, and `discharge_today`. This helps when a Hoymiles MQTT bridge publishes the counters in a combined payload or uses slightly different key names.

If the first `quick/state` payload only contains values such as `bat_p`, `soc`, and `bat_sts`, **Charge Today** and **Discharge Today** may briefly show as unavailable. They update as soon as the later MQTT payload containing `chg_e` / `dchg_e` or one of the supported aliases arrives.

## Created sensors per battery

Each configured battery gets these sensors:

| Sensor | Unit | Description |
|---|---:|---|
| State of Charge | % | Battery state of charge from `soc` |
| Battery Temperature | °C | Battery temperature from `bat_temp` |
| Charge Today | Wh | Daily charge energy from MQTT counter |
| Discharge Today | Wh | Daily discharge energy from MQTT counter |
| Power from/to Battery | W | Signed battery power; negative = discharge, positive = charge |
| Power from Battery | W | Positive discharge power only |
| Power to Battery | W | Positive charge power only |
| Battery State | enum | Battery state from `bat_sts` |
| RSSI | dBm | Wi-Fi signal strength, disabled by default in the entity registry |

## Group sensors

The integration creates one virtual group device with these sensors:

| Sensor | Unit | Description |
|---|---:|---|
| Total State of Charge | % | Capacity-weighted state of charge across all batteries |
| Total Power from/to Battery | W | Signed sum of all individual `Power from/to Battery` sensors; negative = discharge, positive = charge |
| Total Power from Battery | W | Sum of all individual `Power from Battery` sensors |
| Total Power to Battery | W | Sum of all individual `Power to Battery` sensors |
| Total Charge Today | Wh | Sum of all individual `Charge Today` sensors |
| Total Discharge Today | Wh | Sum of all individual `Discharge Today` sensors |
| Total Battery State | enum | `discharge`, `charge`, or `standby` derived from group power |

The signed **Total Power from/to Battery** sensor is useful when one entity should show charging and discharging in a single value. Because the intended setup assumes all batteries charge or discharge at the same time, no additional separate net-power sensor is created.

## Delayed daily energy counters

Some MQTT bridges publish `quick/state` first and the daily energy counters a little later. A first payload may look like this:

```json
{
  "bat_sts": "discharge",
  "bat_p": 20.7,
  "soc": 56.8
}
```

In this payload there are no fields such as `chg_e` or `dchg_e`, so **Charge Today** and **Discharge Today** stay unavailable at first. The integration keeps listening to all subscribed topics and updates the daily energy sensors as soon as a later payload contains `chg_e`, `dchg_e`, or one of the supported aliases.

The group sensors **Total Charge Today** and **Total Discharge Today** sum all individual battery counters that are already available.

## Power sign convention

By default, the integration assumes this convention for the incoming MQTT value `bat_p`:

```text
bat_p > 0  = discharging / power from battery
bat_p < 0  = charging / power to battery
bat_p = 0  = standby
```

The visible **Power from/to Battery** sensor is intentionally exposed with the opposite sign:

```text
Power from/to Battery < 0  = discharging / power from battery
Power from/to Battery > 0  = charging / power to battery
Power from/to Battery = 0  = standby
```

This means discharge is negative and charge is positive. The separated **Power from Battery** and **Power to Battery** sensors remain positive-only values.

If your MQTT bridge already reports `bat_p` with the opposite convention, enable **Invert MQTT power sign** for that battery.

## Group state of charge calculation

The group state of charge is capacity-weighted:

```text
Group SOC = sum(SOC × capacity_kWh) / sum(capacity_kWh)
```

If all batteries have the same capacity, this is the same as the average SOC.

## Installation with HACS custom repository

1. Copy or upload this repository to GitHub.
2. In Home Assistant, open **HACS**.
3. Open the three-dot menu and select **Custom repositories**.
4. Add your GitHub repository URL.
5. Select category **Integration**.
6. Download the integration.
7. Restart Home Assistant.
8. Go to **Settings → Devices & services → Add integration**.
9. Search for **Hoymiles MQTT Battery**.

## Manual installation

1. Copy this folder:

```text
custom_components/hoymiles_mqtt_battery
```

into your Home Assistant config folder:

```text
/config/custom_components/hoymiles_mqtt_battery
```

2. Restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration**.
4. Search for **Hoymiles MQTT Battery**.

## Configuration

During setup you enter:

- MQTT base topic, for example `homeassistant/sensor`
- Group device name, for example `Hoymiles Total`
- Whether group sensors should be created
- Whether separated power sensors should be created per battery
- Whether diagnostic sensors should be created

For each battery you enter:

- Battery name
- Serial number, with or without `MSA-`
- Model
- Capacity in kWh
- Whether the power sign should be inverted

## Adding or removing batteries later

Open **Settings → Devices & services → Hoymiles MQTT Battery → Configure**.

From there you can:

- Change global settings
- Add a battery
- Remove a battery

Home Assistant reloads the integration after the options are saved.

## Repository description for GitHub

```text
Home Assistant custom integration for Hoymiles MS-A2 and HiBattery AC MQTT battery sensors with multi-battery group state of charge and separated charge/discharge power.
```

## Disclaimer

This is an unofficial community integration and is not affiliated with Hoymiles.
