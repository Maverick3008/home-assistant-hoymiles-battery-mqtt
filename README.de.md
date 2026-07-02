# Hoymiles MQTT Battery

Custom Integration für Home Assistant für Hoymiles MS-A2 und HiBattery AC Akkus, die ihre Daten bereits per MQTT veröffentlichen.

Die Integration ersetzt lange manuelle MQTT-Sensor-YAML-Blöcke durch eine Einrichtung per Home-Assistant-GUI. Du fügst einen oder mehrere Akkus per Seriennummer hinzu, und die Integration erstellt automatisch einzelne Akku-Sensoren und gemeinsame Gruppensensoren.

## Funktionen

- Einrichtung per Home-Assistant-Config-Flow.
- Mehrere Hoymiles-Akkus in einem Integrationseintrag.
- Funktioniert mit MQTT-Topics wie `homeassistant/sensor/MSA-280024351071/quick/state`.
- Erstellt einzelne Sensoren pro Akku.
- Erstellt getrennte `Power from Battery` und `Power to Battery` Sensoren pro Akku.
- Erstellt gemeinsame Gruppensensoren über alle hinterlegten Akkus.
- Berechnet den gemeinsamen Ladezustand kapazitätsgewichtet anhand der eingetragenen Akku-Kapazitäten.
- Optionales Invertieren des Power-Vorzeichens pro Akku.
- Optionale Diagnose-Sensoren wie RSSI.
- Enthält lokale Home-Assistant-Brand-Bilder unter `custom_components/hoymiles_mqtt_battery/brand/`.

## Erwartete MQTT-Topics

Für jede konfigurierte Seriennummer abonniert die Integration diese Topics:

```text
<base_topic>/MSA-<serial>/quick/state
<base_topic>/MSA-<serial>/device/state
<base_topic>/MSA-<serial>/system/state
```

Standard-Basis-Topic:

```text
homeassistant/sensor
```

Beispiel:

```text
homeassistant/sensor/MSA-280024351071/quick/state
```

## Erwartete JSON-Felder

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

## Erstellte Sensoren pro Akku

Jeder konfigurierte Akku bekommt diese Sensoren:

| Sensor | Einheit | Beschreibung |
|---|---:|---|
| Ladezustand | % | Akkustand aus `soc` |
| Batterietemperatur | °C | Batterietemperatur aus `bat_temp` |
| Ladung heute | Wh | Tagesladung aus `chg_e` |
| Entladung heute | Wh | Tagesentladung aus `dchg_e` |
| Power from/to Battery | W | Vorzeichenbehaftete Akkuleistung aus `bat_p` |
| Entladeleistung | W | Nur positive Entladeleistung |
| Ladeleistung | W | Nur positive Ladeleistung |
| Batteriestatus | enum | Batteriestatus aus `bat_sts` |
| RSSI | dBm | WLAN-Signalstärke, in der Entitätsregistrierung standardmäßig deaktiviert |

## Gruppensensoren

Die Integration erstellt ein virtuelles Gesamt-Gerät mit diesen Sensoren:

| Sensor | Einheit | Beschreibung |
|---|---:|---|
| Gesamt-Ladezustand | % | Kapazitätsgewichteter Ladezustand aller Akkus |
| Gesamt-Entladeleistung | W | Summe aller einzelnen Entladeleistungs-Sensoren |
| Gesamt-Ladeleistung | W | Summe aller einzelnen Ladeleistungs-Sensoren |
| Gesamt-Batteriestatus | enum | `discharge`, `charge` oder `standby`, abgeleitet aus der Gruppenleistung |

Es gibt bewusst keinen Nettoleistungs-Sensor, weil diese Integration für Setups gedacht ist, bei denen alle Akkus gleichzeitig laden oder gleichzeitig entladen.

## Power-Vorzeichen

Standardmäßig nimmt die Integration an:

```text
bat_p > 0  = Entladung / Leistung aus Akku
bat_p < 0  = Ladung / Leistung in Akku
bat_p = 0  = Standby
```

Wenn deine MQTT-Werte genau andersherum sind, aktiviere beim jeweiligen Akku **Power-Vorzeichen invertieren**.

## Berechnung des gemeinsamen Ladezustands

Der gemeinsame Ladezustand wird kapazitätsgewichtet berechnet:

```text
Gesamt-SOC = Summe(SOC × Kapazität_kWh) / Summe(Kapazität_kWh)
```

Wenn alle Akkus dieselbe Kapazität haben, entspricht das dem normalen Durchschnitt.

## Installation per HACS Custom Repository

1. Dieses Repository zu GitHub hochladen.
2. In Home Assistant **HACS** öffnen.
3. Oben rechts das Drei-Punkte-Menü öffnen und **Custom repositories** wählen.
4. Die GitHub-Repository-URL eintragen.
5. Kategorie **Integration** auswählen.
6. Integration herunterladen.
7. Home Assistant neu starten.
8. Zu **Einstellungen → Geräte & Dienste → Integration hinzufügen** gehen.
9. Nach **Hoymiles MQTT Battery** suchen.

## Manuelle Installation

1. Diesen Ordner kopieren:

```text
custom_components/hoymiles_mqtt_battery
```

in deinen Home-Assistant-Konfigurationsordner:

```text
/config/custom_components/hoymiles_mqtt_battery
```

2. Home Assistant neu starten.
3. Zu **Einstellungen → Geräte & Dienste → Integration hinzufügen** gehen.
4. Nach **Hoymiles MQTT Battery** suchen.

## Einrichtung

Bei der Einrichtung gibst du ein:

- MQTT-Basis-Topic, zum Beispiel `homeassistant/sensor`
- Name des Gesamt-Geräts, zum Beispiel `Hoymiles Gesamt`
- ob Gruppensensoren erstellt werden sollen
- ob getrennte Lade-/Entladeleistungs-Sensoren pro Akku erstellt werden sollen
- ob Diagnose-Sensoren erstellt werden sollen

Pro Akku gibst du ein:

- Akku-Name
- Seriennummer, mit oder ohne `MSA-`
- Modell
- Kapazität in kWh
- ob das Power-Vorzeichen invertiert werden soll

## Später Akkus hinzufügen oder entfernen

Öffne **Einstellungen → Geräte & Dienste → Hoymiles MQTT Battery → Konfigurieren**.

Dort kannst du:

- globale Einstellungen ändern
- einen Akku hinzufügen
- einen Akku entfernen

Home Assistant lädt die Integration nach dem Speichern der Optionen neu.

## Repository-Beschreibung für GitHub

```text
Home Assistant custom integration for Hoymiles MS-A2 and HiBattery AC MQTT battery sensors with multi-battery group state of charge and separated charge/discharge power.
```

## Hinweis

Dies ist eine inoffizielle Community-Integration und steht nicht mit Hoymiles in Verbindung.
