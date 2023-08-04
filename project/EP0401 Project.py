import RPi.GPIO as GPIO
import time
import threading
import random
import I2C_LCD_driver as I2C_LCD_driver
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import random
from PIL import Image
from picamera import PiCamera
from os import path
from imgurpython import ImgurClient
import datetime
import csv

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

camera = PiCamera()
camera.start_preview()

LCD = I2C_LCD_driver.lcd()
GPIO.setup(26,GPIO.OUT)
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

def write_to_csv(phone_number, weight, success):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open('data.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([phone_number, weight, success, timestamp])

def upload_to_imgur(path):
    client_id = '150fcc365051925'
    client_secret = '4dd7a56dd94eaa89ed6925f0489d50bbec5fab38'

    client = ImgurClient(client_id, client_secret)
    response = client.upload_from_path(path, config=None, anon=True)
    return response['link']

def send_text_message(destination, message, image_url):
    try:
        account_sid = 'AC17f0a9ec890036265cba68687f70a297'
        auth_token = '5a49c7578256dc9af3d30d96ddf9bf95'
        client = Client(account_sid, auth_token)
        print(image_url)
        if (image_url == None):
            message = client.messages.create(
                to=destination,
                from_='+12185629896',
                body=message,
            )
        else:
            message = client.messages.create(
                from_='+12185629896',
                to=destination,
                body=message,
                media_url=image_url,
            )
        print(message.sid)
        return message.sid
    except TwilioRestException as err:
        print(err)
        return err.status

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
        img = Image.open(path)

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
    GPIO.setup(18,GPIO.OUT)
    GPIO.output(18, 1)
    time.sleep(1)
    GPIO.output(18, 0)

def main():
    PWM.start(12) # close the dispenser
    LCD.lcd_display_string("Start of setup", 1)
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
        LCD.lcd_display_string("Link phone no.?", 1)
        link_number = int(get_keypad_input("0=no, 1=yes: "))
        print(link_number)
        if link_number == 1: # If the user chooses to link the phone number, ask for opt to verify the phone number
            LCD.lcd_clear()
            LCD.lcd_display_string("Enter phone no.", 1)
            phone_number_input = get_keypad_input("")
            LCD.lcd_clear()
            opt = random.randint(1000, 9999)
            result = send_text_message("+65" + phone_number_input, "Your OTP is " + str(opt), None)
            if result == 400:
                LCD.lcd_clear()
                LCD.lcd_display_string("Invalid phone no.", 1)
                time.sleep(1)
                LCD.lcd_clear()
            else:
                LCD.lcd_display_string("OTP sent to", 1)
                LCD.lcd_display_string("+65" + phone_number_input, 2)
                time.sleep(2)
                LCD.lcd_clear()
                LCD.lcd_display_string("Enter OTP", 1)
                opt_input = get_keypad_input("")
                while opt_input != str(opt):
                    LCD.lcd_clear()
                    LCD.lcd_display_string("Invalid OTP", 1)
                    LCD.lcd_display_string("Enter OTP", 2)
                    opt_input = get_keypad_input("")
                LCD.lcd_clear()
                LCD.lcd_display_string("Phone no. linked!", 1)
                break  # Exit the loop if the phone number is valid
        else:
            break  # Exit the loop if the user chooses not to link the phone number

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
                image_url = upload_to_imgur(path)
                write_to_csv(phone_number_input, weight, "True")
                result = send_text_message("+65" + phone_number_input, "Your pet has been fed at " + feeding_time + "!", image_url)
            
        time.sleep(0.8)

main()