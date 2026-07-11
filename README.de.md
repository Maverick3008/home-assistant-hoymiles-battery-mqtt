# Hoymiles MQTT Battery

Home-Assistant-Custom-Integration für Hoymiles MS-A2 und HiBattery AC per MQTT.

## Version 0.2.0

Neu pro einzelnem Akku:

- `Select` für den EMS-Modus: `general`, `mqtt_ctrl`, `tou_plan`
- `Number` zur Steuerung der Lade-/Entladeleistung von `-2000 W` bis `+2000 W`
- automatische Wiederholung des Leistungsbefehls alle 50 Sekunden im Modus `mqtt_ctrl`
- bewusst keine Steuerungsentitäten beim Gesamtgerät

### MQTT-Befehlstopics

```text
homeassistant/select/MSA-<Seriennummer>/ems_mode/command
homeassistant/number/MSA-<Seriennummer>/power_ctrl/set
```

Positive Werte entladen, negative Werte laden. Die Leistungssteuerung benötigt den Modus `mqtt_ctrl`. Laut Hoymiles ist die Steuerung nur für Standalone-Geräte und das Mastergerät vorgesehen.

## Installation

Über HACS als benutzerdefiniertes Repository installieren oder den Ordner `custom_components/hoymiles_mqtt_battery` nach Home Assistant kopieren. Danach Home Assistant neu starten.

Das Projekt ist eine inoffizielle Community-Integration und steht nicht in Verbindung mit Hoymiles.
