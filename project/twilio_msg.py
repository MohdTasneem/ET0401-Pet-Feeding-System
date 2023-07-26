from twilio.rest import Client

def send_text_message(destination: str, message: str):
    account_sid = 'AC17f0a9ec890036265cba68687f70a297'
    auth_token = '024f45598be0c9c1e212d38f18451d4a'
    client = Client(account_sid, auth_token)

    message = client.messages.create(
        to=destination,
        body=message
    )
    
    return message.sid


