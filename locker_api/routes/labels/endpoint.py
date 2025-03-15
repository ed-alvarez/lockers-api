from uuid import UUID

from auth.cognito import get_current_org
from fastapi import APIRouter, Depends, File, UploadFile


from .controller import packagex_scan_request


router = APIRouter(tags=["labels"])


@router.post("/labels/scan", status_code=201)
async def scan_label(
    label_image: UploadFile = File(...),
    current_org: UUID = Depends(get_current_org),
):
    scan_result = await packagex_scan_request(label_image)

    return scan_result
