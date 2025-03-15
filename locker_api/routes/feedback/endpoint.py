from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile
from auth.cognito import get_current_org
from util.images import ImagesService

from .model import Feedback
from .controller import create_feedback

router = APIRouter(tags=["feedback"])


@router.post("/partner/feedback", response_model=Feedback.Read)
async def partner_create_feedback(
    current_org: UUID = Depends(get_current_org),
    feedback: Feedback.Write = Depends(Feedback.Write.as_form),
    images: Optional[list[UploadFile]] = None,
    images_service: ImagesService = Depends(ImagesService),
):
    feedback_response = await create_feedback(
        id_org=current_org,
        feedback=feedback,
        images=images,
        images_service=images_service,
    )

    return feedback_response
