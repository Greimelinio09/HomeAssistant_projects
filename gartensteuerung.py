#!/usr/bin/env python3

import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
import time
import threading
import os
import Adafruit_DHT

# GPIO-Pins
GPIO_23 = 23
GPIO_24 = 24
GPIO_25 = 25
GPIO_26 = 26

TempSensor = 5

temperature = None
humidity = None
merker = 0

# MQTT
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

zeitup = 20
zeitdown = 10

# GPIO Setup
GPIO.setmode(GPIO.BCM)

def set_pin_tristate(pin):
    GPIO.setup(pin, GPIO.IN)

def set_pin_output(pin):
    GPIO.setup(pin, GPIO.OUT)

# Initial alles aus (Tristate!)
set_pin_tristate(GPIO_23)
set_pin_tristate(GPIO_24)
set_pin_tristate(GPIO_25)
set_pin_tristate(GPIO_26)

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    print("Connected:", rc)
    client.subscribe(MQTT_STAMP1_SET)
    client.subscribe(MQTT_STAMP2_SET)

def on_message(client, userdata, msg):
    message = msg.payload.decode()

    # 🔹 STAMPEL 1 (GPIO 24 + 25)
    if msg.topic == MQTT_STAMP1_SET:
        if message == "ON":
            set_pin_output(GPIO_24)
            set_pin_output(GPIO_25)
            GPIO.output(GPIO_24, GPIO.HIGH)
            GPIO.output(GPIO_25, GPIO.HIGH)

            client.publish(MQTT_STAMP1_STATE, "ON", retain=True)

        elif message == "OFF":
            set_pin_tristate(GPIO_24)
            set_pin_tristate(GPIO_25)

            client.publish(MQTT_STAMP1_STATE, "OFF", retain=True)

    # 🔹 STAMPEL 2 (GPIO 23 + 26)
    elif msg.topic == MQTT_STAMP2_SET:
        if message == "ON":
            set_pin_output(GPIO_23)
            set_pin_output(GPIO_26)
            GPIO.output(GPIO_23, GPIO.HIGH)
            GPIO.output(GPIO_26, GPIO.HIGH)

            client.publish(MQTT_STAMP2_STATE, "ON", retain=True)

        elif message == "OFF":
            set_pin_tristate(GPIO_23)
            set_pin_tristate(GPIO_26)

            client.publish(MQTT_STAMP2_STATE, "OFF", retain=True)

# CPU Temperatur
def get_cpu_temp():
    temp = os.popen("vcgencmd measure_temp").readline()
    return float(temp.replace("temp=", "").replace("'C\n", ""))

def cpu_loop():
    while True:
        cpu_temp = get_cpu_temp()
        print(f"CPU: {cpu_temp}°C")
        client.publish(MQTT_CPU_TEMP, cpu_temp, retain=True)
        time.sleep(60)

# DHT11
def dht_loop():
    global temperature, humidity

    while True:
        humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, TempSensor)

        if humidity is not None and temperature is not None:
            print(f"T:{temperature} H:{humidity}")
            client.publish(MQTT_TEMPERATURE, temperature, retain=True)

        time.sleep(2)

# Automatik
def auto_loop():
    global temperature, merker

    while True:
        if temperature is not None:

            if temperature <= 15 and merker != 1:
                set_pin_output(GPIO_23)
                set_pin_output(GPIO_26)
                GPIO.output(GPIO_23, GPIO.HIGH)
                GPIO.output(GPIO_26, GPIO.HIGH)

                client.publish(MQTT_STAMP2_STATE, "ON", retain=True)

                time.sleep(zeitdown)

                set_pin_tristate(GPIO_23)
                set_pin_tristate(GPIO_26)

                client.publish(MQTT_STAMP2_STATE, "OFF", retain=True)

                merker = 1

            elif temperature >= 22 and merker != 0:
                set_pin_output(GPIO_24)
                set_pin_output(GPIO_25)
                GPIO.output(GPIO_24, GPIO.HIGH)
                GPIO.output(GPIO_25, GPIO.HIGH)

                client.publish(MQTT_STAMP1_STATE, "ON", retain=True)

                time.sleep(zeitup)

                set_pin_tristate(GPIO_24)
                set_pin_tristate(GPIO_25)

                client.publish(MQTT_STAMP1_STATE, "OFF", retain=True)

                merker = 0

        time.sleep(1)

# MQTT Setup
client = mqtt.Client()
client.username_pw_set(username, password)
client.on_connect = on_connect
client.on_message = on_message

client.connect(broker_address, broker_port, 60)

# Threads starten
threading.Thread(target=cpu_loop, daemon=True).start()
threading.Thread(target=dht_loop, daemon=True).start()
threading.Thread(target=auto_loop, daemon=True).start()

# Loop
client.loop_forever()