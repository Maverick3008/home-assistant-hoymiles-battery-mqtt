# Changelog

## 0.1.0

- Initial release.
- UI setup via Config Flow.
- Supports multiple Hoymiles batteries by serial number.
- Creates individual battery sensors from MQTT JSON topics.
- Creates separated `Power from Battery` and `Power to Battery` sensors per battery.
- Creates shared group sensors for capacity-weighted state of charge, total charge power, total discharge power and group state.
- Includes local brand images for Home Assistant 2026.3 and newer.
