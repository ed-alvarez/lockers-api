from uuid import UUID

from auth.cognito import get_current_org
from fastapi import APIRouter, Depends, File, UploadFile
from util.images import ImagesService
from util.response import BasicResponse

router = APIRouter(tags=["images"])


@router.post("/partner/images", status_code=201, response_model=BasicResponse)
async def upload_image(
    image: UploadFile = File(...),
    current_org: UUID = Depends(get_current_org),
    images_service: ImagesService = Depends(ImagesService),
):
    image_url = await images_service.upload(str(current_org), image)

    return {"detail": image_url["url"]}
