import RPi.GPIO as GPIO
from time import sleep
import I2C_LCD_driver as I2C_LCD_driver

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

def get_key(title):
    pressed_keys = ""
    break_loop = False
    # scan keypad
    while not break_loop:
        LCD.lcd_display_string(title + pressed_keys, 2)
        for i in range(3):  # loop through all columns
            GPIO.output(COL[i], 0)  # pull one column pin low
            for j in range(4):  # check which row pin becomes low
                if GPIO.input(ROW[j]) == 0:  # if a key is pressed
                    if MATRIX[j][i] == "#":
                        break_loop = True
                    elif MATRIX[j][i] == "*":
                        if len(pressed_keys) > 0:
                            pressed_keys = pressed_keys[:-1]  # Remove the last character
                    else:
                        print(MATRIX[j][i])  # print the key pressed
                        pressed_keys += str(MATRIX[j][i])
                        while GPIO.input(ROW[j]) == 0:  # debounce
                            sleep(0.1)
            GPIO.output(COL[i], 1)  # write back the default value of 1
    return pressed_keys

def main():
    LCD.lcd_display_string("Input weight", 1)
    weight_input_value = get_key("Weight: ")
    if weight_input_value:
        LCD.lcd_clear()
        LCD.lcd_display_string("Input time", 1)
        time_input_value = get_key("Time in 24hr: ")
        if time_input_value:
            LCD.lcd_clear()
            LCD.lcd_display_string("Weight: " + weight_input_value, 1)
            LCD.lcd_display_string("Time: " + time_input_value, 2)

main()
