import RPi.GPIO as GPIO
import time
import threading
import I2C_LCD_driver as I2C_LCD_driver
from twilio_msg import send_text_message

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

LCD = I2C_LCD_driver.lcd()

MATRIX = [[1, 2, 3],
          [4, 5, 6],
          [7, 8, 9],
          ['*', 0, '#']]  # layout of keys on the keypad
ROW = [6, 20, 19, 13]  # row pins
COL = [12, 5, 16]  # column

# set column pins as outputs, and write the default value of 1 to each
for i in range(3):
    GPIO.setup(COL[i], GPIO.OUT)
    GPIO.output(COL[i], 1)

# set row pins as inputs, with pull-up
for j in range(4):
    GPIO.setup(ROW[j], GPIO.IN, pull_up_down=GPIO.PUD_UP)

def format_to_24_hour(time_input):
    if len(time_input) >= 4:
        hours = time_input[:2]
        minutes = time_input[2:4]
        seconds = "00"
        formatted_time = f"{hours}:{minutes}:{seconds}"
        return formatted_time
    else:
        return "Invalid time format"

def get_current_time():
    return time.strftime("%H:%M:%S")

def update_time_display(time_input):
    while True:
        LCD.lcd_display_string("To feed " + time_input, 1)
        current_time = get_current_time()
        LCD.lcd_display_string("Time " + current_time, 2)
        time.sleep(1)
        LCD.lcd_clear()

def get_keypad_input(title):
    pressed_keys = ""
    while True:
        if "(24hr)" in title:
            formatted_time = pressed_keys[:2] + ":" + pressed_keys[2:]
            LCD.lcd_display_string(title + formatted_time, 2)
        else:
            LCD.lcd_display_string(title + pressed_keys, 2)
        submit_pressed = False
        for i in range(3):  # loop through all columns
            GPIO.output(COL[i], 0)  # pull one column pin low
            for j in range(4):  # check which row pin becomes low
                if GPIO.input(ROW[j]) == 0:  # if a key is pressed
                    if MATRIX[j][i] == "*":
                        pressed_keys = pressed_keys[:-1]
                        print(pressed_keys)
                        LCD.lcd_display_string(title + "            " + pressed_keys, 2)
                    elif MATRIX[j][i] == "#":
                        submit_pressed = True
                    else:
                        print(MATRIX[j][i])  # print the key pressed
                        pressed_keys += str(MATRIX[j][i])
                        while GPIO.input(ROW[j]) == 0:  # debounce
                            time.sleep(0.1)
            GPIO.output(COL[i], 1)  # write back the default value of 1
        
        if submit_pressed:
            return pressed_keys


def play_buzzer():
    GPIO.output(18, 1)
    time.sleep(1)
    GPIO.output(18, 0)

def main():
    LCD.lcd_display_string("Enter weight", 1)
    weight = int(get_keypad_input("(g): "))
    LCD.lcd_clear()
    LCD.lcd_display_string("Enter time", 1)
    feeding_time = get_keypad_input("(24hr): ")
    feeding_time = format_to_24_hour(feeding_time)
    LCD.lcd_clear()
    LCD.lcd_display_string("Link phone no.?", 1)
    link_number = int(get_keypad_input("0=no, 1=yes: "))
    print(link_number)
    if link_number == 1:
        LCD.lcd_clear()
        LCD.lcd_display_string("Enter phone no.", 1)
        phone_number_input = get_keypad_input("")
    LCD.lcd_clear()
    LCD.lcd_display_string("Setup done!", 1)
    time.sleep(1)
    LCD.lcd_clear()
    time_thread = threading.Thread(target=update_time_display, args=(feeding_time,))
    time_thread.start()
    while True:
        current_time = get_current_time()
        if current_time == feeding_time:
            play_buzzer()

main()
