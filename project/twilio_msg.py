from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import random

def send_text_message(destination, message):
    try:
        account_sid = 'AC17f0a9ec890036265cba68687f70a297'
        auth_token = '5a49c7578256dc9af3d30d96ddf9bf95'
        client = Client(account_sid, auth_token)

        message = client.messages.create(
            to=destination,
            from_='+12185629896',
            body=message,
        )
        print(message.sid)
        return message.sid
    except TwilioRestException as err:
        print(err)
        return err.status