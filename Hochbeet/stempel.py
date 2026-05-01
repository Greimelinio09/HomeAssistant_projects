#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# GPIO-Pins definieren
GPIO_23 = 23  # GPIO 23 entspricht physischem Pin 16
GPIO_24 = 24  # GPIO 24 entspricht physischem Pin 18
GPIO_25 = 25
GPIO_26 = 26

zeit = 5  # Zeit in Sekunden

# Initialisiere die GPIO-Bibliothek
GPIO.setup(GPIO_23, GPIO.OUT)
GPIO.setup(GPIO_24, GPIO.OUT)
GPIO.setup(GPIO_25, GPIO.OUT)
GPIO.setup(GPIO_26, GPIO.OUT)

def set_pin_tristate(pin):
    GPIO.setup(pin, GPIO.IN)

def set_pin_output(pin):
    GPIO.setup(pin, GPIO.OUT)

set_pin_tristate(GPIO_23)
set_pin_tristate(GPIO_24)
set_pin_tristate(GPIO_25)
set_pin_tristate(GPIO_26)

try:
    while True:
        befehl = int(input("Befehl eingeben (1 Dach auf, 0 Dach zu): "))

        if befehl == 1:
            # GPIO 24 und 25 als Ausgangspins setzen
            set_pin_output(GPIO_24)
            set_pin_output(GPIO_25)
            # GPIO 24 und 25 auf HIGH setzen
            GPIO.output(GPIO_24, GPIO.HIGH)
            GPIO.output(GPIO_25, GPIO.HIGH)
            print("Dach geht auf")
            time.sleep(zeit)
            # GPIO 24 und 25 auf Tri-State setzen
            set_pin_tristate(GPIO_24)
            set_pin_tristate(GPIO_25)
        elif befehl == 0:
            # GPIO 23 und 26 als Ausgangspins setzen
            set_pin_output(GPIO_23)
            set_pin_output(GPIO_26)
            # GPIO 23 und 26 auf HIGH setzen
            GPIO.output(GPIO_23, GPIO.HIGH)
            GPIO.output(GPIO_26, GPIO.HIGH)
            print("Dach geht zu")
            time.sleep(zeit)
            # GPIO 23 und 26 auf Tri-State setzen
            set_pin_tristate(GPIO_23)
            set_pin_tristate(GPIO_26)
        else:
            print("Ungültiger Befehl. Bitte 1 oder 0 eingeben.")
except KeyboardInterrupt:
    print("Programm beendet.")
finally:
    GPIO.cleanup()
