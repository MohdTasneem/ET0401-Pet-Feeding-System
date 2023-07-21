import RPi.GPIO as GPIO
from time import sleep
import project.I2C_LCD_driver as I2C_LCD_driver #import the library

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

LCD = I2C_LCD_driver.lcd() #instantiate an lcd object, call it LCD

def keypad():
    MATRIX = [[1, 2, 3],
            [4, 5, 6],
            [7, 8, 9],
            ['*', 0, '#']]  # layout of keys on keypad
    ROW = [6, 20, 19, 13]  # row pins
    COL = [12, 5, 16]  # column pins

    # set column pins as outputs, and write default value of 1 to each
    for i in range(3):
        GPIO.setup(COL[i], GPIO.OUT)
        GPIO.output(COL[i], 1)

    # set row pins as inputs, with pull up
    for j in range(4):
        GPIO.setup(ROW[j], GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # scan keypad
    while (True):
        for i in range(3):  # loop thru’ all columns
            GPIO.output(COL[i], 0)  # pull one column pin low
            for j in range(4):  # check which row pin becomes low
                if GPIO.input(ROW[j]) == 0:  # if a key is pressed
                    print(MATRIX[j][i])  # print the key pressed
                    while GPIO.input(ROW[j]) == 0:  # debounce
                        sleep(0.1)
            GPIO.output(COL[i], 1)  # write back default value of 1

def display_led(string_to_display):
    sleep(0.5)
    LCD.backlight(0) #turn backlight off
    sleep(0.5)
    LCD.backlight(1) #turn backlight on 
    LCD.lcd_display_string(string_to_display, 1) #write on line 1
    # LCD.lcd_display_string("Address = 0x27", 2, 2) #write on line 2
    #             #starting on 3rd column
    
def clear_led():
    LCD.lcd_clear()

def main():
    display_led("Test")

