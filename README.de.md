# Hoymiles MQTT Battery

Custom Integration für Home Assistant für Hoymiles MS-A2 und HiBattery AC Akkus, die ihre Daten bereits per MQTT veröffentlichen.

Die Integration ersetzt lange manuelle MQTT-Sensor-YAML-Blöcke durch eine Einrichtung per Home-Assistant-GUI. Du fügst einen oder mehrere Akkus per Seriennummer hinzu, und die Integration erstellt automatisch einzelne Akku-Sensoren und gemeinsame Gruppensensoren.

## Funktionen

- Einrichtung per Home-Assistant-Config-Flow.
- Mehrere Hoymiles-Akkus in einem Integrationseintrag.
- Funktioniert mit MQTT-Topics wie `homeassistant/sensor/MSA-280024351071/quick/state`.
- Erstellt einzelne Sensoren pro Akku.
- Erstellt getrennte `Power from Battery` und `Power to Battery` Sensoren pro Akku.
- Erstellt gemeinsame Gruppensensoren über alle hinterlegten Akkus, inklusive vorzeichenbehafteter `Gesamt-Power from/to Battery`.
- Berechnet den gemeinsamen Ladezustand kapazitätsgewichtet anhand der eingetragenen Akku-Kapazitäten.
- Summiert die tägliche Ladung und Entladung in zusätzlichen Gruppensensoren.
- Liest die Tagesenergie aus `system/state` und akzeptiert alternative JSON-Schlüssel. Wenn diese Werte etwas später als `quick/state` kommen, bleiben die Energie-Sensoren bis zum ersten passenden Payload kurzzeitig nicht verfügbar.
- Optionales Invertieren des eingehenden MQTT-Power-Vorzeichens pro Akku, falls deine MQTT-Bridge andersherum sendet.
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

Die Tagesenergie wird primär aus `chg_e` und `dchg_e` gelesen. Zusätzlich prüft die Integration alle eingehenden Payloads auf gängige Alternativen wie `charge_e`, `charge_today`, `discharge_e` und `discharge_today`. Das hilft, wenn eine Hoymiles-MQTT-Bridge die Werte in einem kombinierten Payload oder mit leicht anderen Schlüsseln veröffentlicht.

Wenn der erste `quick/state`-Payload nur Werte wie `bat_p`, `soc` und `bat_sts` enthält, können **Ladung heute** und **Entladung heute** kurzzeitig als nicht verfügbar erscheinen. Sie aktualisieren sich, sobald der spätere MQTT-Payload mit `chg_e` / `dchg_e` oder einem unterstützten Alias eintrifft.

## Erstellte Sensoren pro Akku

Jeder konfigurierte Akku bekommt diese Sensoren:

| Sensor | Einheit | Beschreibung |
|---|---:|---|
| Ladezustand | % | Akkustand aus `soc` |
| Batterietemperatur | °C | Batterietemperatur aus `bat_temp` |
| Ladung heute | Wh | Tagesladung aus MQTT-Zähler |
| Entladung heute | Wh | Tagesentladung aus MQTT-Zähler |
| Power from/to Battery | W | Vorzeichenbehaftete Akkuleistung; Entladung negativ, Ladung positiv |
| Entladeleistung | W | Nur positive Entladeleistung |
| Ladeleistung | W | Nur positive Ladeleistung |
| Batteriestatus | enum | Batteriestatus aus `bat_sts` |
| RSSI | dBm | WLAN-Signalstärke, in der Entitätsregistrierung standardmäßig deaktiviert |

## Gruppensensoren

Die Integration erstellt ein virtuelles Gesamt-Gerät mit diesen Sensoren:

| Sensor | Einheit | Beschreibung |
|---|---:|---|
| Gesamt-Ladezustand | % | Kapazitätsgewichteter Ladezustand aller Akkus |
| Gesamt-Power from/to Battery | W | Vorzeichenbehaftete Summe aller einzelnen `Power from/to Battery` Sensoren; negativ = Entladung, positiv = Ladung |
| Gesamt-Entladeleistung | W | Summe aller einzelnen Entladeleistungs-Sensoren |
| Gesamt-Ladeleistung | W | Summe aller einzelnen Ladeleistungs-Sensoren |
| Gesamt-Ladung heute | Wh | Summe aller einzelnen `Ladung heute` Sensoren |
| Gesamt-Entladung heute | Wh | Summe aller einzelnen `Entladung heute` Sensoren |
| Gesamt-Batteriestatus | enum | `discharge`, `charge` oder `standby`, abgeleitet aus der Gruppenleistung |

Der vorzeichenbehaftete Sensor **Gesamt-Power from/to Battery** ist praktisch, wenn ein einzelner Wert Laden und Entladen darstellen soll. Da diese Integration für Setups gedacht ist, bei denen alle Akkus gleichzeitig laden oder gleichzeitig entladen, wird kein zusätzlicher separater Nettoleistungs-Sensor erstellt.

## Verzögerte Tagesenergie-Zähler

Manche MQTT-Bridges veröffentlichen zuerst `quick/state` und etwas später die Tagesenergie-Zähler. Ein erster Payload kann zum Beispiel so aussehen:

```json
{
  "bat_sts": "discharge",
  "bat_p": 20.7,
  "soc": 56.8
}
```

In diesem Payload gibt es noch keine Felder wie `chg_e` oder `dchg_e`. Deshalb bleiben **Ladung heute** und **Entladung heute** zunächst nicht verfügbar. Die Integration hört weiter auf alle abonnierten Topics und aktualisiert die Tagesenergie-Sensoren, sobald ein späterer Payload `chg_e`, `dchg_e` oder einen unterstützten Alias enthält.

Die Gruppensensoren **Gesamt-Ladung heute** und **Gesamt-Entladung heute** summieren alle Einzelwerte, die bereits verfügbar sind.

## Power-Vorzeichen

Standardmäßig nimmt die Integration für den eingehenden MQTT-Wert `bat_p` an:

```text
bat_p > 0  = Entladung / Leistung aus Akku
bat_p < 0  = Ladung / Leistung in Akku
bat_p = 0  = Standby
```

Der sichtbare Sensor **Power from/to Battery** wird bewusst andersherum ausgegeben:

```text
Power from/to Battery < 0  = Entladung / Leistung aus Akku
Power from/to Battery > 0  = Ladung / Leistung in Akku
Power from/to Battery = 0  = Standby
```

Dadurch bedeutet Entladung negativ und Ladung positiv. Die getrennten Sensoren **Entladeleistung** und **Ladeleistung** bleiben weiterhin immer positive Werte.

Wenn deine MQTT-Bridge `bat_p` selbst genau andersherum sendet, aktiviere beim jeweiligen Akku **MQTT-Power-Vorzeichen invertieren**.

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
