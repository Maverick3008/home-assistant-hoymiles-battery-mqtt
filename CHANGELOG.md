# Changelog

## 0.1.4

- Added group sensor `Total Power from/to Battery` / `Gesamt-Power from/to Battery`.
- The new group sensor sums all raw battery power values and keeps the sign: positive means discharge, negative means charge.

## 0.1.3

- Removed software calculation of daily charge/discharge energy from `bat_p` again.
- `Charge Today` and `Discharge Today` now only use MQTT counters such as `chg_e` and `dchg_e`, including supported aliases.
- Daily energy sensors stay unavailable until the first MQTT payload containing those counters arrives.
- Group daily energy sensors continue to sum all available individual battery counters.

## 0.1.2

- Added software calculation for `Charge Today` and `Discharge Today` when MQTT payloads do not provide `chg_e` / `dchg_e`.
- Daily charge/discharge energy is now integrated from `bat_p`, persisted locally, reset at midnight and included in the group totals.
- Keeps firmware-provided MQTT energy counters as preferred source when they are available.

## 0.1.1

- Added group sensors for total daily charge energy and total daily discharge energy.
- Improved parsing of daily charge/discharge counters by accepting common JSON key aliases and by checking all incoming Hoymiles MQTT payloads.

## 0.1.0

- Initial release.
- UI setup via Config Flow.
- Supports multiple Hoymiles batteries by serial number.
- Creates individual battery sensors from MQTT JSON topics.
- Creates separated `Power from Battery` and `Power to Battery` sensors per battery.
- Creates shared group sensors for capacity-weighted state of charge, total charge power, total discharge power and group state.
- Includes local brand images for Home Assistant 2026.3 and newer.
