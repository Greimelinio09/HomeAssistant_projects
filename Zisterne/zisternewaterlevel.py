import RPi.GPIO as GPIO
import time
import paho.mqtt.client as mqtt
from math import pi

# ---------------- MQTT ----------------
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
client.loop_start()

# ---------------- GPIO ----------------
Triggerpin = 18
Echopin = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(Triggerpin, GPIO.OUT)
GPIO.setup(Echopin, GPIO.IN)

GPIO.output(Triggerpin, False)

# ---------------- Zisterne ----------------
ZISTERNE_DURCHMESSER = 2.5
ZISTERNE_MAX_WATER_HIGHT = 2
ZISTERNE_SENSOR_HIGHT = 2.64

# ---------------- CONFIG ----------------
TIMEOUT = 0.03  # 30ms
SAMPLES = 10    # weniger als 70 → stabiler!

# ---------------- DISTANZ ----------------
def distanz():
    GPIO.output(Triggerpin, False)
    time.sleep(0.0002)

    GPIO.output(Triggerpin, True)
    time.sleep(0.00001)
    GPIO.output(Triggerpin, False)

    timeout_start = time.time()

    # warten bis Echo HIGH wird
    while GPIO.input(Echopin) == 0:
        start = time.time()
        if time.time() - timeout_start > TIMEOUT:
            return -1

    timeout_start = time.time()

    # warten bis Echo LOW wird
    while GPIO.input(Echopin) == 1:
        stop = time.time()
        if time.time() - timeout_start > TIMEOUT:
            return -1

    duration = stop - start
    distance = (duration * 34300) / 2

    return distance

# ---------------- FILTERED DISTANCE ----------------
def get_distance_filtered():
    values = []

    for _ in range(SAMPLES):
        d = distanz()
        if d > 0 and d < 500:   # Filter für Zisterne
            values.append(d)
        time.sleep(0.05)

    if len(values) == 0:
        return -1

    return sum(values) / len(values)

# ---------------- VOLUME ----------------
def getwater(distance):
    if distance <= 0:
        return 0

    wassermenge_max = ZISTERNE_DURCHMESSER**2 * pi * ZISTERNE_MAX_WATER_HIGHT * 1000 / 4
    zisterne_inhalt = ZISTERNE_DURCHMESSER**2 * pi * (ZISTERNE_SENSOR_HIGHT - distance / 100) * 1000 / 4

    if zisterne_inhalt < 200 or zisterne_inhalt > 11000:
        print("Wrong reading")
        return 0

    return zisterne_inhalt

# ---------------- PERCENT ----------------
def getpercentage(distance):
    if distance <= 0:
        return 0

    wassermenge_max = ZISTERNE_DURCHMESSER**2 * pi * ZISTERNE_MAX_WATER_HIGHT * 1000 / 4
    zisterne_inhalt = ZISTERNE_DURCHMESSER**2 * pi * (ZISTERNE_SENSOR_HIGHT - distance / 100) * 1000 / 4

    return (zisterne_inhalt / wassermenge_max) * 100

# ---------------- MQTT ----------------
def sendmqtt(distance, waterlevel, percentage):
    client.publish(MQTT_DISTANCE, distance, retain=True)
    client.publish(MQTT_WATERLEVEL, waterlevel, retain=True)
    client.publish(MQTT_PERCENTAGE, percentage, retain=True)

# ---------------- MAIN ----------------
if __name__ == '__main__':
    try:
        while True:

            distance = get_distance_filtered()

            if distance == -1:
                print("No valid echo")
                time.sleep(2)
                continue

            waterlevel = getwater(distance)
            percentage = getpercentage(distance)

            print(f"Distanz: {distance:.1f} cm")

            if waterlevel > 0:
                sendmqtt(distance, waterlevel, percentage)

            time.sleep(5)

    except KeyboardInterrupt:
        print("Messung beendet")
        GPIO.cleanup()
        client.loop_stop()