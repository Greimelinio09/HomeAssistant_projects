import RPi.GPIO as GPIO
import time
import paho.mqtt.client as mqtt
from math import pi

# MQTT Konfiguration
MQTT_BROKER = "10.0.0.68"
MQTT_PORT = 1883
MQTT_DISTANCE = "zisterne/pi/outdoor/distance"
MQTT_WATERLEVEL = "zisterne/pi/outdoor/waterlevel"
MQTT_PERCENTAGE = "zisterne/pi/outdoor/percentage"
MQTT_USER = "mqtt"
MQTT_PASS = "mqtt"

# Zeit-Konfiguration
MEASURE_INTERVAL = 5        # Alle 5 Sekunden messen
SEND_INTERVAL = 15 * 60     # Alle 15 Minuten senden (900 Sekunden)

# Hardware-Setup
Triggerpin = 18
Echopin = 24
GPIO.setmode(GPIO.BCM)
GPIO.setup(Triggerpin, GPIO.OUT)
GPIO.setup(Echopin, GPIO.IN)

# Zisterne Definition
ZISTERNE_DURCHMESSER = 2.5
ZISTERNE_MAX_WATER_HIGHT = 2
ZISTERNE_SENSOR_HIGHT = 2.64

# MQTT Client Setup
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(MQTT_USER, MQTT_PASS)

def distanz():
    GPIO.output(Triggerpin, True)
    time.sleep(0.00001)
    GPIO.output(Triggerpin, False)

    start_zeit = time.time()
    stop_zeit = time.time()

    while GPIO.input(Echopin) == 0:
        start_zeit = time.time()
    while GPIO.input(Echopin) == 1:
        stop_zeit = time.time()

    zeit_differenz = stop_zeit - start_zeit
    entfernung = (zeit_differenz * 34300) / 2
    return entfernung

def calculate_values(avg_distance):
    # Berechnung der Liter und Prozent basierend auf dem Mittelwert
    wassermenge_max = ZISTERNE_DURCHMESSER * ZISTERNE_DURCHMESSER * pi * ZISTERNE_MAX_WATER_HIGHT * 1000 / 4
    zisterne_inhalt = ZISTERNE_DURCHMESSER * ZISTERNE_DURCHMESSER * pi * (ZISTERNE_SENSOR_HIGHT - avg_distance / 100) * 1000 / 4
    voll_in_prozent = (zisterne_inhalt / wassermenge_max) * 100
    
    return zisterne_inhalt, voll_in_prozent, wassermenge_max

def sendmqtt(distance, waterlevel, percentage):
    try:
        client.connect(MQTT_BROKER, MQTT_PORT)
        client.publish(MQTT_DISTANCE, round(distance, 2), retain=True)
        client.publish(MQTT_WATERLEVEL, round(waterlevel, 1), retain=True)
        client.publish(MQTT_PERCENTAGE, round(percentage, 1), retain=True)
        client.disconnect()
        print("--- Daten erfolgreich gesendet ---")
    except Exception as e:
        print(f"MQTT Fehler: {e}")

if __name__ == '__main__':
    messwerte = []
    letzter_send_zeitpunkt = time.time()
    
    print("Messung gestartet. Sammle Daten für 15 Minuten...")

    try:
        while True:
            # 1. Einzelmessung durchführen
            aktuelle_distanz = distanz()
            
            # Optional: Extrem falsche Sensorwerte (z.B. < 0) direkt ignorieren
            if aktuelle_distanz > 0:
                messwerte.append(aktuelle_distanz)
            
            # 2. Prüfen, ob 15 Minuten vergangen sind
            jetzt = time.time()
            if jetzt - letzter_send_zeitpunkt >= SEND_INTERVAL:
                if messwerte:
                    # Mittelwert der Distanz berechnen
                    avg_dist = sum(messwerte) / len(messwerte)
                    
                    # Berechnungen durchführen
                    liter, prozent, max_liter = calculate_values(avg_dist)
                    
                    # Validierung wie im Originalsketch
                    if 200 < liter < 11000:
                        print(f"Mittelwert Distanz (n={len(messwerte)}): {avg_dist:.2f} cm")
                        print(f"Aktuell: {liter:.1f} L ({prozent:.1f}%)")
                        sendmqtt(avg_dist, liter, prozent)
                    else:
                        print(f"Mittelwert ungültig ({liter:.1f} L). Sende nichts.")
                
                # Liste leeren und Timer zurücksetzen
                messwerte = []
                letzter_send_zeitpunkt = jetzt

            # 3. 5 Sekunden warten bis zur nächsten Messung
            time.sleep(MEASURE_INTERVAL)

    except KeyboardInterrupt:
        print("Messung beendet")
        GPIO.cleanup()