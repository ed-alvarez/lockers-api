from enum import Enum

from pydantic import BaseModel


class Channel(Enum):
    sms = "sms"
    email = "email"


class VerificationMessage(BaseModel):
    # The twilio verification object
    sid: str
    to: str
    channel: str
    status: str
