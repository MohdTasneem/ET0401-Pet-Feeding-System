import time

import RPi.GPIO as GPIO
from time import sleep
import I2C_LCD_driver as I2C_LCD_driver
from datetime import datetime
import schedule
from threading import Thread

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

LCD = I2C_LCD_driver.lcd()

MATRIX = [[1, 2, 3],
          [4, 5, 6],
          [7, 8, 9],
          ['*', 0, '#']]  # layout of keys on the keypad
ROW = [6, 20, 19, 13]  # row pins
COL = [12, 5, 16]  # column pins

# set column pins as outputs, and write the default value of 1 to each
for i in range(3):
    GPIO.setup(COL[i], GPIO.OUT)
    GPIO.output(COL[i], 1)

# set row pins as inputs, with pull-up
for j in range(4):
    GPIO.setup(ROW[j], GPIO.IN, pull_up_down=GPIO.PUD_UP)

def get_keys(type):
    pressed_keys = ""

    while True:
        LCD.lcd_display_string("Input " + type + ": ", 1)
        LCD.lcd_display_string(pressed_keys, 2)
        for i in range(3):  # loop thru’ all columns
            GPIO.output(COL[i], 0)  # pull one column pin low
            for j in range(4):  # check which row pin becomes low
                if GPIO.input(ROW[j]) == 0:  # if a key is pressed
                    key = MATRIX[j][i]
                    print(key)  # print the key pressed
        if key == "#":
            break
        elif key == "*":
            pressed_keys = pressed_keys[:-1]
        else:
            pressed_keys += str(MATRIX[j][i])
        while GPIO.input(ROW[j]) == 0:  # debounce
            sleep(0.1)
        GPIO.output(COL[i], 1)
        if type == "Time":
            if len(pressed_keys) == 2:
                pressed_keys += ":"
            elif len(pressed_keys) == 5:
                break
    return pressed_keys


def weight_and_time():
    weight = get_keys("Weight")
    time = get_keys("Time")
    if time and weight:
        LCD.lcd_clear()
        LCD.lcd_display_string("Weight: " + weight, 1)
        LCD.lcd_display_string("Time: " + time, 2)
    feeding_time = datetime.strptime(time, "%H:%M")
    print(feeding_time)


def main():
    local_time = time.localtime()
    current_time = time.strftime("%H:%M", local_time)
    print(current_time)
    weight_and_time()



main()
