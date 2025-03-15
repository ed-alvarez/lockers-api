from pydantic import BaseModel
from typing import Optional


class BasicResponse(BaseModel):
    detail: str


class BasicResponseErr(BaseModel):
    detail: str
    err: Optional[list]


class Message(BaseModel):
    msg: str
