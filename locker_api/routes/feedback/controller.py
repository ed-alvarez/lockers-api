from typing import Optional
from uuid import UUID

from ..organization.controller import get_org
from fastapi import UploadFile
from util.images import ImagesService
from util import email

from .model import Feedback
from ..organization.controller import get_org_sendgrid_auth_sender, is_ups_org


async def create_feedback(
    feedback: Feedback.Write,
    images: Optional[list[UploadFile]],
    id_org: UUID,
    images_service: ImagesService,
):
    org = await get_org(id_org)
    images_urls = None

    if images and images_service:
        images_urls = await images_service.batch_upload(id_org, images)

    new_feedback = dict(
        location=feedback.location,
        device=feedback.device,
        member=feedback.member,
        department=feedback.department,
        description=feedback.description,
        notes=feedback.notes,
        pictures=images_urls if images_urls else None,
    )

    email_sender = await get_org_sendgrid_auth_sender(id_org)

    email.send(
        sender=email_sender,
        recipient="support@koloni.me",
        subject=f"New feedback received from {org.name}",
        html_content=(
            f"<strong>Location:</strong> {feedback.location}<br />"
            + f"<strong>Device:</strong> {feedback.device}<br />"
            + f"<strong>Member:</strong> {feedback.member}<br />"
            + f"<strong>Department:</strong> {feedback.department}<br />"
            + f"<strong>Description:</strong> {feedback.description}<br />"
            + "<strong>Notes:</strong><br /><br />"
            + feedback.notes
            + "<br/><br/>"
            + "<strong>Images:</strong><br /><br />"
            + ("<br />".join(images_urls) if images_urls else "No images attached.")
        ),
        is_ups_org=await is_ups_org(id_org),
    )

    return new_feedback
