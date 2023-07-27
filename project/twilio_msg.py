from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

def send_text_message(destination, message):
    try:
        account_sid = 'AC17f0a9ec890036265cba68687f70a297'
        auth_token = '1ede8019c422c2562405c11df88a26c4'
        client = Client(account_sid, auth_token)

        message = client.messages.create(
            to=destination,
            from_='+12185629896',
            body=message,
        )
        return message.sid
    except TwilioRestException as err:
        return err.status