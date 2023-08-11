import RPi.GPIO as GPIO
import time
import threading
import I2C_LCD_driver as I2C_LCD_driver
import random
from picamera import PiCamera
import requests
import datetime
import csv

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

try_again = 1
bot_token = "6389868402:AAGoeCy-D8nOl7qi42k_9iJ-1eH15Ilm2I8"

camera = PiCamera()
camera.start_preview()

LCD = I2C_LCD_driver.lcd()
GPIO.setup(26, GPIO.OUT)
PWM = GPIO.PWM(26, 50)

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


def send_telegram_message(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }

    response = requests.post(url, json=payload)
    if response.ok:
        print("Message sent successfully!")
    else:
        print("Failed to send message.")


def send_telegram_image(token, chat_id, image_path):
    url = f'https://api.telegram.org/bot{token}/sendPhoto'
    payload = {
        "chat_id": chat_id,
    }
    with open(image_path, 'rb') as image_file:
        files = {'photo': image_file}
        response = requests.post(url, data=payload, files=files)

    if response.ok:
        print("Image sent successfully!")
    else:
        print("Failed to send image.")


def write_to_csv(phone_number, weight, success):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open('data.csv', 'a') as file:
        writer = csv.writer(file, delimiter = ',', lineterminator = '\n')
        writer.writerow([phone_number, weight, success, timestamp])


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


def take_picture(path):
    camera.capture(path)


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

        if "1" in title and len(pressed_keys) == 1:
            submit_pressed = True

        if submit_pressed:
            return pressed_keys


def play_buzzer():
    GPIO.setup(18, GPIO.OUT)
    GPIO.output(18, 1)
    time.sleep(1)
    GPIO.output(18, 0)


def main():
    global bot_token
    global try_again

    PWM.start(12)  # close the dispenser
    LCD.lcd_display_string("SmartPaws setup", 1)
    time.sleep(1)
    LCD.lcd_clear()

    LCD.lcd_display_string("Enter weight", 1)
    weight = int(get_keypad_input("(g): "))
    LCD.lcd_clear()
    LCD.lcd_display_string("Enter time", 1)
    feeding_time = get_keypad_input("(24hr): ")
    feeding_time = format_to_24_hour(feeding_time)
    LCD.lcd_clear()

    # Link phone number loop
    while True:
        LCD.lcd_display_string("Link Telegram?", 1)
        link_tele = int(get_keypad_input("0=No, 1=Yes:"))
        print(link_tele)

        if link_tele == 1:
            LCD.lcd_clear()
            LCD.lcd_display_string("Enter your Chat", 1)
            while try_again:
                chat_id = get_keypad_input("ID: ")
                if len(chat_id) == 10:
                    chat_id = int(chat_id)
                    otp = random.randint(1000, 9999)
                    send_telegram_message(bot_token, chat_id, "Your OTP is " + str(otp))

                    LCD.lcd_clear()
                    LCD.lcd_display_string("OTP sent to", 1)
                    time.sleep(2)

                    LCD.lcd_clear()
                    LCD.lcd_display_string("Enter OTP", 1)
                    otp_input = get_keypad_input("")

                    while otp_input != str(otp):
                        LCD.lcd_clear()
                        LCD.lcd_display_string("Invalid OPT", 1)
                        time.sleep(1)
                        LCD.lcd_display_string("Enter OPT", 1)
                        otp_input = get_keypad_input("")

                    LCD.lcd_clear()
                    LCD.lcd_display_string("Linked to ", 1)
                    LCD.lcd_display_string("Telegram", 2)
                    break
                else:
                    LCD.lcd_clear()
                    LCD.lcd_display_string("Invalid ID!", 1)
                    LCD.lcd_display_string("Try again?", 2)
                    time.sleep(2)
                    LCD.lcd_clear()
                    LCD.lcd_display_string("Press", 1)
                    try_again = int(get_keypad_input("0=No, 1=Yes:"))

    LCD.lcd_clear()
    LCD.lcd_display_string("Setup done!", 1)
    time.sleep(1)

    LCD.lcd_clear()
    time_thread = threading.Thread(target=update_time_display, args=(feeding_time,))
    time_thread.start()
    while True:
        current_time = get_current_time()
        print("current_time: " + current_time)
        print("feeding_time: " + feeding_time)
        print(current_time == feeding_time)
        if current_time == feeding_time:
            play_buzzer()
            PWM.start(3)
            time.sleep(2)
            PWM.start(12)

            if link_number == 1:
                path = '/home/pi/Desktop/ET0401-Pet-Feeding-System/project/pet.jpg'
                take_picture(path)
                send_telegram_message(bot_token, chat_id, "Your pet has been fed at {}".format(current_time))
                send_telegram_image(bot_token, chat_id, path)
                write_to_csv(phone_number_input, weight, "True")

        time.sleep(1)


main()