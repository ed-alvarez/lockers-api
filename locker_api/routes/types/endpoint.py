from typing import Dict, List

from fastapi import APIRouter


from ..device.model import HardwareType, Mode
from ..event.model import EventStatus
from ..price.model import Currency
from ..notifications.model import NotificationType

router = APIRouter(tags=["types"])


@router.get("/types/device/mode", response_model=List[Dict[str, str]])
async def get_modes():
    """Get All Device modes"""

    result = []
    for data in Mode:
        result.append(
            {
                "value": data.name,
                "label": "Asset" if data.name == "rental" else data.value.capitalize(),
            }
        )

    return result


@router.get("/types/device/hardware", response_model=List[Dict[str, str]])
async def get_hardware():
    """Get All Device hardware types"""

    result = []
    for data in HardwareType:
        result.append({"value": data.name, "label": data.value.capitalize()})

    return result


@router.get("/types/notification/type", response_model=List[Dict[str, str]])
async def get_notification_type():
    """Get All Notification types"""

    result = []
    for data in NotificationType:
        result.append({"value": data.name, "label": data.value.capitalize()})

    return result


@router.get("/types/event/status", response_model=List[Dict[str, str]])
async def get_event_status():
    """Get All Event statuses"""

    result = []
    for data in EventStatus:
        result.append({"value": data.name, "label": data.value.capitalize()})

    return result


@router.get("/types/event/currencies", response_model=List[Dict[str, str]])
async def get_currencies():
    """Get All Event statuses"""

    result = []
    for data in Currency:
        result.append({"value": data.name, "label": data.value.upper()})

    return result
