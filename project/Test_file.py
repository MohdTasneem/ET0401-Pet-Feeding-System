import RPi.GPIO as GPIO
import time
import threading
import random
import I2C_LCD_driver as I2C_LCD_driver
import requests

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

LCD = I2C_LCD_driver.lcd()
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


def format_to_24_hour(time_input):
    if len(time_input) >= 4:
        hours = time_input[:2]
        minutes = time_input[2:4]
        seconds = "00"
        formatted_time = f"{hours}:{minutes}:{seconds}"
        return formatted_time
    else:
        return "Invalid time format"

# def get_current_date():
    # local_time = time.localtime()
    # return time.strftime("%D", local_time)
def get_current_time():
    # local_time = time.localtime()
    # return time.strftime("%H:%M:%S", local_time)
    return time.strftime("%H:%M:%S")


def update_time_display(time_input):
    while True:
        LCD.lcd_display_string("To feed " + time_input, 1)
        current_time = get_current_time()
        LCD.lcd_display_string("Time " + current_time, 2)
        time.sleep(1)


def get_keypad_input(title):
    pressed_keys = ""

    while True:
        if "(24hr)" in title:
            formatted_time = pressed_keys[:2] + ":" + pressed_keys[2:]
            LCD.lcd_display_string(title + formatted_time, 2)

        elif "1" in title and len(pressed_keys) == 1:
            break

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
            return pressed_keys  #check whther the loop break or continue might affect functionality


def play_buzzer():
    GPIO.setup(18, GPIO.OUT)
    GPIO.output(18, 1)
    time.sleep(1)
    GPIO.output(18, 0)

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


def main():
    bot_token = "6389868402:AAGoeCy-D8nOl7qi42k_9iJ-1eH15Ilm2I8"
    try_again = 1
    LCD.lcd_display_string("Start of setup", 1)
    time.sleep(2)
    LCD.lcd_clear

    LCD.lcd_display_string("Enter frequency")
    frequency = int(get_keypad_input("(1-4): "))
    LCD.lcd_clear()

    LCD.lcd_display_string("Enter weight", 1)
    weight = int(get_keypad_input("(g): "))
    LCD.lcd_clear()

    LCD.lcd_display_string("Enter time", 1)
    feeding_time = get_keypad_input("(24hr): ")
    feeding_time = format_to_24_hour(feeding_time)
    LCD.lcd_clear()

    while True:
        LCD.lcd_display_string("Link Telegram?", 1)
        link_tele = int(get_keypad_input("0=No, 1=Yes:"))
        print(link_tele)

        if link_tele == 1:
            LCD.lcd_clear()
            LCD.lcd_display_string("Enter your Chat", 1)
            while try_again:
                chat_id = int(get_keypad_input("ID: "))
                if len(chat_id) == 10:
                    LCD.lcd_clear()
                    LCD.lcd_display_string("Linked to ", 1)
                    LCD.lcd_display_string("Telegram", 2)
                    time.sleep(2)
                    break
                else:
                    LCD.lcd_clear()
                    LCD.lcd_display_string("Invalid ID!", 1)
                    LCD.lcd_display_string("Try again?", 2)
                    time.sleep(2)
                    LCD.lcd_display_string("Press", 1)
                    try_again = int(get_keypad_input("0=No, 1=Yes:"))

        LCD.lcd_clear
        LCD.lcd_display_string("Setup complete!", 1)
        time.sleep(2)

        LCD.lcd_clear()
        time_thread = threading.Thread(target=update_time_display, args=(feeding_time,))
        time_thread.start()

        while True:
            current_time = get_current_time()
            print("current_time: " + current_time)
            print("feeding_time: " + feeding_time)
            print(current_time == feeding_time)
            if current_time == feeding_time:

                PWM.start(3)  # 3% duty cycle
                print('duty cycle:', 3)  # 3 o'clock position
                time.sleep(4)  # allow time for movement
                PWM.start(12)  # 13% duty cycle
                print('duty cycle:', 12)  # 9 o'clock position
                time.sleep(2)

                play_buzzer()
                if link_tele == 1:
                    send_telegram_message(bot_token, chat_id, "Your pet has been fed at {}".format(current_time))
# def main():
#     LCD.lcd_display_string("Start of setup", 1)
#     time.sleep(2)
#     LCD.lcd_clear
#
#     LCD.lcd_display_string("Enter weight", 1)
#     weight = int(get_keypad_input("(g): "))
#     LCD.lcd_clear()
#
#     LCD.lcd_display_string("Enter time", 1)
#     feeding_time = get_keypad_input("(24hr): ")
#     feeding_time = format_to_24_hour(feeding_time)
#     LCD.lcd_clear()
#
#     # Link phone number loop
#     while True:
#         LCD.lcd_display_string("Link phone no.?", 1)
#         link_number = int(get_keypad_input("0=no, 1=yes: "))
#         print(link_number)
#         if link_number == 1:  # If the user chooses to link the phone number, ask for opt to verify the phone number
#             LCD.lcd_clear()
#             LCD.lcd_display_string("Enter phone no.", 1)
#             phone_number_input = get_keypad_input("")
#             LCD.lcd_clear()
#             opt = random.randint(1000, 9999)
#             result = send_text_message("+65" + phone_number_input, "Your OPT is " + str(opt))
#             if result == 400:
#                 LCD.lcd_clear()
#                 LCD.lcd_display_string("Invalid phone no.", 1)
#                 time.sleep(1)
#                 LCD.lcd_clear()
#             else:
#                 LCD.lcd_display_string("OPT sent to", 1)
#                 LCD.lcd_display_string("+65" + phone_number_input, 2)
#                 time.sleep(2)
#                 LCD.lcd_clear()
#                 LCD.lcd_display_string("Enter OPT", 1)
#                 opt_input = get_keypad_input("")
#                 while opt_input != str(opt):
#                     LCD.lcd_clear()
#                     LCD.lcd_display_string("Invalid OPT", 1)
#                     LCD.lcd_display_string("Enter OPT", 2)
#                     opt_input = get_keypad_input("")
#                 LCD.lcd_clear()
#                 LCD.lcd_display_string("Phone no. linked!", 1)
#                 break  # Exit the loop if the phone number is valid
#         else:
# #             break  # Exit the loop if the user chooses not to link the phone number
#
#     LCD.lcd_clear()
#     LCD.lcd_display_string("Setup done!", 1)
#     time.sleep(1)
#     LCD.lcd_clear()
#     time_thread = threading.Thread(target=update_time_display, args=(feeding_time,))
#     time_thread.start()
#     while True:
#         current_time = get_current_time()
#         print("current_time: " + current_time)
#         print("feeding_time: " + feeding_time)
#         print(current_time == feeding_time)
#         if current_time == feeding_time:
#             play_buzzer()
#             if link_number == 1:
#                 result = send_text_message("+65" + phone_number_input, "Your pet has been fed at " + feeding_time + "!")
#         time.sleep(0.8)
#

main()
