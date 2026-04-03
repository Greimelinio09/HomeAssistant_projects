# 🌱 Smart Hochbeet System

Ein smartes Hochbeet-Projekt basierend auf Raspberry Pi, MQTT und Home Assistant.
Ziel ist die Überwachung und Steuerung von Umweltbedingungen sowie mechanischen Komponenten (z. B. Stempel für Öffnen/Schließen).

---

## 🚀 Features

* 📡 MQTT Kommunikation
* 🏠 Integration in Home Assistant
* 🌡️ Temperaturmessung (DHT11)
* 💻 CPU-Temperatur Monitoring
* 🔧 Steuerung von Aktoren (Stempel)
* 🔒 Sicherheitslogik (Zeitlimits & Tristate)
* ⚡ Echtzeitsteuerung über Dashboard

---

## 🧰 Hardware

* Raspberry Pi 3
* DHT11 Temperatur-/Feuchtigkeitssensor
* 4x GPIO gesteuerte Aktoren (Stempel)
* Netzteil + Verkabelung

---

## 🧠 Software

* Python 3
* MQTT (z. B. Mosquitto)
* Home Assistant
* RPi.GPIO
* Adafruit_DHT
* paho-mqtt

---

## 🔌 GPIO Belegung

| Funktion       | GPIO   |
| -------------- | ------ |
| Stempel 1 HIGH | 24, 25 |
| Stempel 2 HIGH | 23, 26 |
| DHT11 Sensor   | 5      |

👉 Pins werden im **Tristate-Modus (INPUT)** deaktiviert, um Hardware zu schützen.

---

## 📡 MQTT Topics

### Steuerung

* `home/garden/pi/stamp/1/set`
* `home/garden/pi/stamp/2/set`

Payload:

* `ON`
* `OFF`

### Status

* `home/garden/pi/stamp/1/state`
* `home/garden/pi/stamp/2/state`

### Sensoren

* `home/garden/pi/temperature`
* `home/garden/pi/cpu_temperature`

---

## ⚙️ Installation

```bash
sudo apt update
sudo apt install python3-pip
pip3 install paho-mqtt RPi.GPIO Adafruit_DHT
```

Script starten:

```bash
python3 main.py
```

---

## 🏠 Home Assistant Integration

### MQTT Switches

```yaml
mqtt:
  switch:
    - name: "Stempel 1"
      command_topic: "home/garden/pi/stamp/1/set"
      state_topic: "home/garden/pi/stamp/1/state"

    - name: "Stempel 2"
      command_topic: "home/garden/pi/stamp/2/set"
      state_topic: "home/garden/pi/stamp/2/state"
```

---

## 🔒 Sicherheitsfunktionen

* ⏱️ Stempel 1: max. **20 Sekunden gesamt**
* ⏱️ Stempel 2: max. **25 Sekunden pro Lauf**
* 🔄 Reset durch Gegenbewegung
* ⚡ Kein LOW-Signal → nur HIGH oder Tristate

---

## 📸 Projektidee

Das System ermöglicht:

* automatisiertes Öffnen/Schließen eines Hochbeets
* Überwachung von Temperatur
* Integration in Smart Home Systeme
* spätere Erweiterung mit KI oder Sprachsteuerung

---

## 🔮 ToDo / Ideen

* [ ] Bodenfeuchtigkeitssensor
* [ ] Automatische Bewässerung
* [ ] KI-Integration (Ollama + Home Assistant)
* [ ] Dashboard Visualisierung
* [ ] Positionssteuerung statt Zeit

---

## 👨‍💻 Autor

Felix Greimel-Längauer

---

## 🪪 Lizenz

MIT License
