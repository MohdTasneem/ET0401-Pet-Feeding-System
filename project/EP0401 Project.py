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

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

spi=spidev.SpiDev() #create SPI object
spi.open(0,0) #open SPI port 0, device (CS) 0

# Initialize the camera
camera = PiCamera()
camera.start_preview()

LCD = I2C_LCD_driver.lcd()
GPIO.setup(26,GPIO.OUT)
PWM = GPIO.PWM(26, 50)

# Keypad setup
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

# Function to read the value of potentiometer
def readadc(adcnum):
    #read SPI data from the MCP3008, 8 channels in total
    if adcnum>7 or adcnum<0:
        return -1
    spi.max_speed_hz = 1350000
    r=spi.xfer2([1,8+adcnum<<4,0]) #construct list of 3 items, before sending to ADC:
                                 #1(start), (single-ended+channel#) shifted left 4 bits, 0(stop)
                                 #see MCP3008 datasheet for details
    data=((r[1]&3)<<8)+r[2] # ADD first byte with 3 or 0b00000011 - masking operation
                            #shift result left by 8 bits
                            #OR result with second byte, to get 10-bit ADC result
    return data

# Function to write data to data.csv
def write_to_csv(phone_number, weight, success):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open('data.csv', 'a') as file:
        writer = csv.writer(file, delimiter = ',', lineterminator = '\n')
        writer.writerow([phone_number, weight, success, timestamp])

# Function to upload image to imgur and return the url
def upload_to_imgur(path):
    client_id = '150fcc365051925'
    client_secret = '4dd7a56dd94eaa89ed6925f0489d50bbec5fab38'

    client = ImgurClient(client_id, client_secret)
    response = client.upload_from_path(path, config=None, anon=True)
    return response['link']

# Function to send text message
def send_text_message(destination, message, image_url):
    try:
        account_sid = 'AC17f0a9ec890036265cba68687f70a297'
        auth_token = '75f2310a56e63c08a3738b16caf2d16d'
        client = Client(account_sid, auth_token) # Initialize Twilio client
        print(image_url)
        if (image_url == None): # If no image is provided, send a text message
            message = client.messages.create(
                to=destination,
                from_='+12185629896',
                body=message,
            )
        else: # If an image is provided, send a MMS
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

# Function to format time input to 24 hour format
def format_to_24_hour(time_input):
    if len(time_input) >= 4:
        hours = time_input[:2]
        minutes = time_input[2:4]
        seconds = "00"
        formatted_time = f"{hours}:{minutes}:{seconds}"
        return formatted_time
    else:
        return "Invalid time format"

# Function to get current time
def get_current_time():
    return time.strftime("%H:%M:%S")

# Function to update the time display on the LED
def update_time_display(time_input):
    while True:
        LCD.lcd_display_string("To feed " + time_input, 1)
        current_time = get_current_time()
        LCD.lcd_display_string("Time " + current_time, 2)
        time.sleep(1)

# Function to take a picture using the camera module
def take_picture(path):
        camera.capture(path)
        img = Image.open(path)

# Function to get input from the keypad
def get_keypad_input(title):
    pressed_keys = ""
    while True:
        if "(24hr)" in title: # If the title contains (24hr), format the time input
            formatted_time = pressed_keys[:2] + ":" + pressed_keys[2:]
            LCD.lcd_display_string(title + formatted_time, 2)
        else:
            LCD.lcd_display_string(title + pressed_keys, 2)
        submit_pressed = False
        for i in range(3):  # loop through all columns
            GPIO.output(COL[i], 0)  # pull one column pin low
            for j in range(4):  # check which row pin becomes low
                if GPIO.input(ROW[j]) == 0:  # if a key is pressed
                    if MATRIX[j][i] == "*": # If the * key is pressed, delete the last character
                        pressed_keys = pressed_keys[:-1]
                        print(pressed_keys)
                        LCD.lcd_display_string(title + "            " + pressed_keys, 2)
                    elif MATRIX[j][i] == "#": # If the # key is pressed, submit the input
                        submit_pressed = True
                    else:
                        print(MATRIX[j][i])  # print the key pressed
                        pressed_keys += str(MATRIX[j][i])
                        while GPIO.input(ROW[j]) == 0:  # debounce
                            time.sleep(0.1)
            GPIO.output(COL[i], 1)  # write back the default value of 1
        
        if submit_pressed:
            return pressed_keys


# Function to play the buzzer
def play_buzzer():
    GPIO.setup(18,GPIO.OUT)
    GPIO.output(18, 1)
    time.sleep(1)
    GPIO.output(18, 0)

# Main function
def main():
    PWM.start(12) # close the dispenser
    LCD.lcd_display_string("Start of setup", 1) # Tells user that the setup is starting
    time.sleep(1)
    LCD.lcd_clear()

    LCD.lcd_display_string("Enter weight", 1) # Asks user to enter the weight of the food
    weight = int(get_keypad_input("(g): ")) # Gets the weight of the food from keypad input
    LCD.lcd_clear()
    LCD.lcd_display_string("Enter time", 1) # Asks user to enter the time of feeding in 24 hour format
    feeding_time = get_keypad_input("(24hr): ") # Gets the time of feeding from keypad input
    feeding_time = format_to_24_hour(feeding_time) # Formats the time of feeding to 24 hour format
    LCD.lcd_clear()
    
    # Loop to prompt the user if they would like to link their phone number
    while True:
        LCD.lcd_display_string("Link phone no.?", 1) # Asks user if they would like to link their phone number
        link_number = int(get_keypad_input("0=no, 1=yes: ")) # Gets the user's choice from keypad input
        print(link_number)
        if link_number == 1: # If the user chooses to link the phone number, ask for otp to verify the phone number
            LCD.lcd_clear()
            LCD.lcd_display_string("Enter phone no.", 1) # Asks user to enter their phone number
            phone_number_input = get_keypad_input("") # Gets the phone number from keypad input
            LCD.lcd_clear()
            otp = random.randint(1000, 9999) # Generates a random 4 digit OTP
            result = send_text_message("+65" + phone_number_input, "Your OTP is " + str(otp), None) # Sends the OTP to the user's phone number
            if result == 400: # If the phone number is invalid, prompt the user to enter a valid phone number
                LCD.lcd_clear()
                LCD.lcd_display_string("Invalid phone no.", 1)
                time.sleep(1)
                LCD.lcd_clear()
            else: # If the phone number is valid, prompt the user to enter the OTP
                LCD.lcd_display_string("OTP sent to", 1) # Tells the user that the OTP has been sent to their phone number
                LCD.lcd_display_string("+65" + phone_number_input, 2) # Displays the phone number that the OTP has been sent to
                time.sleep(2)
                LCD.lcd_clear()
                LCD.lcd_display_string("Enter OTP", 1) # Asks user to enter the OTP
                otp_input = get_keypad_input("") # Gets the OTP from keypad input
                while otp_input != str(otp): # If the OTP entered is incorrect, prompt the user to enter the OTP again
                    LCD.lcd_clear()
                    LCD.lcd_display_string("Invalid OTP", 1)
                    LCD.lcd_display_string("Enter OTP", 2)
                    otp_input = get_keypad_input("")
                LCD.lcd_clear()
                LCD.lcd_display_string("Phone no. linked!", 1) # Tells the user that the phone number has been linked
                break  # Exit the loop if the phone number is valid
        else:
            break  # Exit the loop if the user chooses not to link the phone number

    LCD.lcd_clear()
    LCD.lcd_display_string("Setup done!", 1) # Tells the user that the setup is done
    time.sleep(1)
    LCD.lcd_clear()
    time_thread = threading.Thread(target=update_time_display, args=(feeding_time,)) # Create a thread to update the time display in real time
    time_thread.start() # Start the thread
    while True: # Loop to check if the current time is the same as the feeding time
        current_time = get_current_time()
        print("current_time: " + current_time)
        print("feeding_time: " + feeding_time)
        print(current_time == feeding_time)
        if current_time == feeding_time: # If the current time is the same as the feeding time, start the pet feeding process
            play_buzzer() # Play the buzzer to simulate a speaker playing a sound to get the pet's attention
            PWM.start(3)
            while weight_dispensed < weight: # Loop to dispense the food until the weight dispensed is the same as the weight of the food
                weight_dispensed = readadc(1)
                print("weight dispensed" , weight_dispensed)
            
            if weight_dispensed >= weight: # If the weight dispensed is the same as the weight of the food, stop the pet feeding process
                PWM.start(12)
                if link_number == 1: # If the user has linked their phone number, send a text message to the user to notify them that their pet has been fed
                    path = '/home/pi/Desktop/ET0401-Pet-Feeding-System/project/pet.jpg'
                    take_picture(path)
                    image_url = upload_to_imgur(path)
                    write_to_csv(phone_number_input, weight, "True")
                    result = send_text_message("+65" + phone_number_input, "Your pet has been fed at " + feeding_time + "!", image_url)
            
        time.sleep(0.8)

main()