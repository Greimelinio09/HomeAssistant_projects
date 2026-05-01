import RPi.GPIO as GPIO
import time
import paho.mqtt.client as mqtt
from math import pi

MQTT_BROKER = "10.0.0.68"
MQTT_PORT = 1883
MQTT_DISTANCE = "zisterne/pi/outdoor/distance"
MQTT_WATERLEVEL = "zisterne/pi/outdoor/waterlevel"
MQTT_PERCENTAGE = "zisterne/pi/outdoor/percentage"
MQTT_USER = "mqtt"
MQTT_PASS = "mqtt"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(MQTT_USER, MQTT_PASS)
client.connect(MQTT_BROKER, MQTT_PORT)

Triggerpin = 18
Echopin = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(Triggerpin, GPIO.OUT)
GPIO.setup(Echopin, GPIO.IN)

# Zisterne definieren
ZISTERNE_DURCHMESSER = 2.5

# 2000mm bis zum Ablauf 2640mm ist der Sensor vom Boden entfernt
ZISTERNE_MAX_WATER_HIGHT = 2

# Sensor Hoehe ueber Boden
ZISTERNE_SENSOR_HIGHT = 2.64

# DEFINE AVERAGE Rounds for Distance measurement
AVERAGE_ROUNDS = 70



def distanz():
    # Trigger auf HIGH setzen
    GPIO.output(Triggerpin, True)
    time.sleep(0.00001)
    GPIO.output(Triggerpin, False)

    start_zeit = time.time()
    stop_zeit = time.time()

    # Startzeit speichern
    while GPIO.input(Echopin) == 0:
        start_zeit = time.time()

    # Stopzeit speichern
    while GPIO.input(Echopin) == 1:
        stop_zeit = time.time()

    # Zeitdifferenz
    zeit_differenz = stop_zeit - start_zeit

    # Schallgeschwindigkeit (34300 cm/s) * Zeit / 2
    entfernung = (zeit_differenz * 34300) / 2

    return entfernung

def getwater(distance):
    wassermenge_max = ZISTERNE_DURCHMESSER * ZISTERNE_DURCHMESSER * pi * ZISTERNE_MAX_WATER_HIGHT * 1000 / 4
    zisterne_inhalt = ZISTERNE_DURCHMESSER * ZISTERNE_DURCHMESSER * pi * (ZISTERNE_SENSOR_HIGHT - distance / 100) * 1000 / 4
    voll_in_prozent = zisterne_inhalt / wassermenge_max * 100

    # print ("MAX = %.1f Liter, Aktuell = %.1f Liter, Gefuellt = %.1f Prozent" % ( wassermenge_max, zisterne_inhalt, voll_in_prozent))

    if zisterne_inhalt > 200 and zisterne_inhalt < 11000:
        print("MAX = %.1f Liter" % wassermenge_max)
        print("Aktuell = %.1f Liter" % zisterne_inhalt)
        print("Gefuellt = %.1f Prozent" % voll_in_prozent)
        return zisterne_inhalt
    else:
        print("Wrong reading")
        return 0

def getpercentage(distance):
    wassermenge_max = ZISTERNE_DURCHMESSER * ZISTERNE_DURCHMESSER * pi * ZISTERNE_MAX_WATER_HIGHT * 1000 / 4
    zisterne_inhalt = ZISTERNE_DURCHMESSER * ZISTERNE_DURCHMESSER * pi * (ZISTERNE_SENSOR_HIGHT - distance / 100) * 1000 / 4
    voll_in_prozent = zisterne_inhalt / wassermenge_max * 100

    # print ("MAX = %.1f Liter, Aktuell = %.1f Liter, Gefuellt = %.1f Prozent" % ( wassermenge_max, zisterne_inhalt, voll_in_prozent))

    if zisterne_inhalt > 200 and zisterne_inhalt < 11000:
        print("MAX = %.1f Liter" % wassermenge_max)
        print("Aktuell = %.1f Liter" % zisterne_inhalt)
        print("Gefuellt = %.1f Prozent" % voll_in_prozent)
        return voll_in_prozent
    else:
        print("Wrong reading")
        return 0

def sendmqtt(distance, waterlevel, percentage):
    client.publish(MQTT_DISTANCE, distance, retain=True)
    client.publish(MQTT_WATERLEVEL, waterlevel, retain=True)
    client.publish(MQTT_PERCENTAGE, percentage, retain=True)

if __name__ == '__main__':
    try:
        while True:
            distance = distanz()
            waterlevel = getwater(distance)
            percentage = getpercentage(distance)

            print(f"Gemessene Entfernung: {distance:.1f} cm")

            if waterlevel != 0:
                sendmqtt(distance, waterlevel, percentage)

            time.sleep(5)

    except KeyboardInterrupt:
        print("Messung beendet")
        GPIO.cleanup()