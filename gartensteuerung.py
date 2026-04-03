#!/usr/bin/env python3

import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
import time
import threading
import os
import Adafruit_DHT

# =========================
# GPIO PINS
# =========================
GPIO_23 = 23
GPIO_24 = 24
GPIO_25 = 25
GPIO_26 = 26

TempSensor = 5

# =========================
# MQTT CONFIG
# =========================
broker_address = "10.0.0.68"
broker_port = 1883

MQTT_TEMPERATURE = "home/garden/pi/temperature"
MQTT_CPU_TEMP = "home/garden/pi/cpu_temperature"

MQTT_STAMP1_SET = "home/garden/pi/stamp/1/set"
MQTT_STAMP1_STATE = "home/garden/pi/stamp/1/state"

MQTT_STAMP2_SET = "home/garden/pi/stamp/2/set"
MQTT_STAMP2_STATE = "home/garden/pi/stamp/2/state"

username = "mqtt"
password = "mqtt"

# =========================
# LIMITS
# =========================
STAMP1_MAX_TOTAL = 20   # Sekunden insgesamt
STAMP2_MAX_TIME = 25    # Sekunden pro Lauf

# =========================
# ZUSTÄNDE
# =========================
temperature = None
humidity = None

stamp1_active = False
stamp2_active = False

stamp1_total_time = 0.0
stamp1_start_time = 0.0
stamp2_start_time = 0.0

# =========================
# GPIO SETUP
# =========================
GPIO.setmode(GPIO.BCM)

def set_pin_tristate(pin):
    GPIO.setup(pin, GPIO.IN)

def set_pin_output(pin):
    GPIO.setup(pin, GPIO.OUT)

# alle Pins sicher AUS (Tristate!)
for pin in [GPIO_23, GPIO_24, GPIO_25, GPIO_26]:
    set_pin_tristate(pin)

# =========================
# MQTT CALLBACKS
# =========================
def on_connect(client, userdata, flags, rc):
    print("MQTT verbunden:", rc)
    client.subscribe(MQTT_STAMP1_SET)
    client.subscribe(MQTT_STAMP2_SET)

# =========================
# STAMPEL FUNKTIONEN
# =========================
def stop_stamp1():
    global stamp1_active, stamp1_total_time, stamp1_start_time

    if stamp1_active:
        duration = time.time() - stamp1_start_time
        stamp1_total_time += duration
        print(f"Stempel1 gesamt: {stamp1_total_time:.2f}s")

    set_pin_tristate(GPIO_24)
    set_pin_tristate(GPIO_25)

    stamp1_active = False
    client.publish(MQTT_STAMP1_STATE, "OFF", retain=True)


def stop_stamp2():
    global stamp2_active

    set_pin_tristate(GPIO_23)
    set_pin_tristate(GPIO_26)

    stamp2_active = False
    client.publish(MQTT_STAMP2_STATE, "OFF", retain=True)


def reset_stamp1():
    global stamp1_total_time
    stamp1_total_time = 0.0
    print("Stempel1 RESET")

# =========================
# MQTT MESSAGE HANDLING
# =========================
def on_message(client, userdata, msg):
    global stamp1_active, stamp2_active
    global stamp1_start_time, stamp2_start_time

    message = msg.payload.decode().strip()

    # 🔼 STAMPEL 1 (HOCH)
    if msg.topic == MQTT_STAMP1_SET:

        if message == "ON":

            if stamp1_total_time >= STAMP1_MAX_TOTAL:
                print("❌ Stempel1 LIMIT erreicht!")
                return

            # Sicherheit: nie beide gleichzeitig
            if stamp2_active:
                stop_stamp2()

            set_pin_output(GPIO_24)
            set_pin_output(GPIO_25)
            GPIO.output(GPIO_24, GPIO.HIGH)
            GPIO.output(GPIO_25, GPIO.HIGH)

            stamp1_active = True
            stamp1_start_time = time.time()

            client.publish(MQTT_STAMP1_STATE, "ON", retain=True)

        elif message == "OFF":
            stop_stamp1()

    # 🔽 STAMPEL 2 (RUNTER)
    elif msg.topic == MQTT_STAMP2_SET:

        if message == "ON":

            # Sicherheit: nie beide gleichzeitig
            if stamp1_active:
                stop_stamp1()

            set_pin_output(GPIO_23)
            set_pin_output(GPIO_26)
            GPIO.output(GPIO_23, GPIO.HIGH)
            GPIO.output(GPIO_26, GPIO.HIGH)

            stamp2_active = True
            stamp2_start_time = time.time()

            client.publish(MQTT_STAMP2_STATE, "ON", retain=True)

        elif message == "OFF":
            stop_stamp2()

# =========================
# CPU TEMP
# =========================
def get_cpu_temp():
    temp = os.popen("vcgencmd measure_temp").readline()
    return float(temp.replace("temp=", "").replace("'C\n", ""))

def cpu_loop():
    while True:
        cpu_temp = get_cpu_temp()
        print(f"CPU: {cpu_temp}°C")
        client.publish(MQTT_CPU_TEMP, cpu_temp, retain=True)
        time.sleep(60)

# =========================
# DHT11
# =========================
def dht_loop():
    global temperature, humidity

    while True:
        humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, TempSensor)

        if humidity is not None and temperature is not None:
            print(f"T:{temperature} H:{humidity}")
            client.publish(MQTT_TEMPERATURE, temperature, retain=True)

        time.sleep(2)

# =========================
# SAFETY LOOP
# =========================
def safety_loop():
    global stamp1_active, stamp2_active
    global stamp1_start_time, stamp2_start_time

    while True:

        # 🔼 Gesamtlimit 20s
        if stamp1_active:
            duration = time.time() - stamp1_start_time

            if duration + stamp1_total_time >= STAMP1_MAX_TOTAL:
                print("⛔ AUTO STOP Stempel1 (Limit)")
                stop_stamp1()

        # 🔽 max 25s
        if stamp2_active:
            duration = time.time() - stamp2_start_time

            if duration >= STAMP2_MAX_TIME:
                print("⛔ AUTO STOP Stempel2")
                stop_stamp2()
                reset_stamp1()

        time.sleep(0.1)

# =========================
# MQTT SETUP
# =========================
client = mqtt.Client()
client.username_pw_set(username, password)
client.on_connect = on_connect
client.on_message = on_message

client.connect(broker_address, broker_port, 60)

# =========================
# THREADS
# =========================
threading.Thread(target=cpu_loop, daemon=True).start()
threading.Thread(target=dht_loop, daemon=True).start()
threading.Thread(target=safety_loop, daemon=True).start()

# =========================
# LOOP
# =========================
client.loop_forever()