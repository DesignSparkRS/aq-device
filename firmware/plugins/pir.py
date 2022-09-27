import RPi.GPIO as GPIO
from DesignSpark.ESDK import AppLogger

GPIO1 = 20

class PIR:
        def __init__(self):
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(GPIO1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        def readSensors(self):
                pirState = GPIO.input(GPIO1)
                return {"pir": {"motion": int(pirState), "sensor": "pirplugin0.1"}}