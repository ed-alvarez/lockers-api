from config import get_settings
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from fastapi import HTTPException


def lookup_phone(phone: str):
    try:
        client = Client(get_settings().twilio_sid, get_settings().twilio_secret)
        client.lookups.v1.phone_numbers(phone).fetch()
    except TwilioRestException:
        raise HTTPException(status_code=400, detail="Invalid phone number")
