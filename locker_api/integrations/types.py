from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel

# Spintly


class SpintlyTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    issued_token_type: str


class _Sites(BaseModel):
    id: int
    name: str
    location: str
    timezone: str
    address: str


class _SitesMessage(BaseModel):
    sites: Optional[List[_Sites]]


class _AccessPoints(BaseModel):
    id: int
    name: str
    hasInternetAcess: bool


class _AccessPointMessage(BaseModel):
    accessPoints: Optional[List[_AccessPoints]]


class SpintlyResponse(BaseModel):
    type: str
    message: Union[_SitesMessage, _AccessPointMessage, str]


# Linka


class LinkaTokenResponse(BaseModel):
    name: str
    access_token: str
    access_token_expireAt: datetime


class _LinkaSettings(BaseModel):
    lockedSleep: Optional[int]
    unlockedSleep: Optional[int]
    audio: Optional[int]
    theftInterval: Optional[int]
    theftDuration: Optional[int]
    lockedInterval: Optional[int]
    unlockedInterval: Optional[int]
    statePing: Optional[int]
    gnssMode: Optional[int]
    loopControl: Optional[int]
    fullGps: Optional[int]
    lockBattery: Optional[int]
    ipAddress: Optional[int]
    remoteCommands: Optional[int]
    fullGps: Optional[int]
    gpsOffBatterPercent: Optional[int]
    periodAInterval: Optional[int]
    periodBInterval: Optional[int]
    periodAStart: Optional[int]
    periodAStart: Optional[int]
    remoteCommands: Optional[int]
    disconnectedLock: Optional[int]


class _LinkaGPSData(BaseModel):
    date: datetime
    mac_addr: str
    lock_state: str
    battery: int


class LinkaMessage(BaseModel):
    status: str
    message: Optional[str]
    data: Optional[Union[_LinkaSettings, _LinkaGPSData, LinkaTokenResponse]]


class LinkaCommandStatus(BaseModel):
    command_id: str
    status: int
    status_desc: str
    date: datetime
    mac_addr: str
    command: str
