from datetime import datetime, timedelta, timezone
from math import ceil
from random import randint
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, UploadFile
from fastapi_async_sqlalchemy import db
from pydantic import conint
from sqlalchemy import VARCHAR, and_, cast, delete, insert, or_, select, update
from util.images import ImagesService

# from ..event.controller import partner_cancel_event
from ..webhook.controller import send_payload
from ..webhook.model import EventChange
from ..event.model import Event, EventStatus
from ..member.controller import get_user as get_cognito_member
from ..settings.controller import get_settings_org
from .helpers.email import email_issue_to_support, email_notify_team_member
from .model import Issue, IssueStatus, PaginatedIssues
from ..device.controller import set_device_maintenance
from ..organization.controller import get_org_name
from ..white_label.controller import partner_get_white_label


async def get_mobile_issues(
    id_user: UUID,
    id_org: UUID,
    page: conint(ge=1),
    size: conint(ge=1),
    id_issue: Optional[UUID] = None,
    search: Optional[str] = None,
):
    query = select(Issue).where(and_(Issue.id_user == id_user, Issue.id_org == id_org))

    if id_issue:
        # * Early return if id_issue is provided

        query = query.where(Issue.id == id_issue)

        result = await db.session.execute(query)
        issue = result.scalar_one()

        return issue

    if search:
        query = query.filter(
            or_(
                cast(Issue.description, VARCHAR).ilike(f"%{search}%"),
                cast(Issue.issue_id, VARCHAR).ilike(f"%{search}%"),
            )
        )

    count = select(Issue).where(and_(Issue.id_user == id_user, Issue.id_org == id_org))

    query = (
        query.limit(size).offset((page - 1) * size).order_by(Issue.created_at.desc())
    )

    data = await db.session.execute(query)
    total = await db.session.execute(count)

    total_count = len(total.unique().all())

    return PaginatedIssues(
        items=data.unique().scalars().all(),
        total=total_count,
        pages=ceil(total_count / size),
    )


async def get_partner_issues(
    id_org: UUID,
    page: conint(ge=1),
    size: conint(ge=1),
    id_issue: Optional[UUID] = None,
    search: Optional[str] = None,
    current_user_pool: Optional[str] = None,
):
    query = select(Issue).where(Issue.id_org == id_org)

    if id_issue:
        # * Early return if id_issue is provided

        query = query.where(Issue.id == id_issue)

        response = await db.session.execute(query)
        issue = response.unique().scalar_one()

        return issue

    if search:
        query = query.filter(
            or_(
                cast(Issue.description, VARCHAR).ilike(f"%{search}%"),
                cast(Issue.issue_id, VARCHAR).ilike(f"%{search}%"),
            )
        )

    query = (
        query.limit(size).offset((page - 1) * size).order_by(Issue.created_at.desc())
    )
    count = select(Issue).where(Issue.id_org == id_org)

    data = await db.session.execute(query)
    total = await db.session.execute(count)

    total_count = len(total.unique().all())

    issues = data.unique().scalars().all()

    # Mutate issues to include team member details from Cognito user pool, only
    # if the issue is assigned to a team member:
    mutated_issues: list[Issue.Read] = []

    for issue in issues:
        issue = Issue.Read.parse_obj(issue)

        if issue.team_member_id:
            try:
                cognito_member = await get_cognito_member(
                    current_user_pool, str(issue.team_member_id)
                )

                if cognito_member:
                    issue.team_member = cognito_member
            except Exception:
                pass

        mutated_issues.append(issue)

    return PaginatedIssues(
        items=mutated_issues,
        total=total_count,
        pages=ceil(total_count / size),
    )


async def create_issue(
    id_event: Optional[UUID],
    issue: Issue.Write,
    images: Optional[list[UploadFile]],
    id_user: Optional[UUID],
    id_org: UUID,
    images_service: Optional[ImagesService],
    user_pool_id: Optional[str] = None,
):
    images_urls = None

    if images and images_service:
        images_urls = await images_service.batch_upload(id_org, images)

    # Example: ISS340502
    issue_id = await generate_issue_id(id_org)

    issue.id_user = id_user or issue.id_user
    new_issue = Issue(
        **issue.dict(),
        id_org=id_org,
        id_event=id_event if id_event else None,
        pictures=images_urls if images_urls else None,
        issue_id=issue_id,
    )

    query = insert(Issue).values(new_issue.dict()).returning(Issue)

    response = await db.session.execute(query)
    await db.session.commit()
    issue_response = response.all().pop()

    white_label = await partner_get_white_label(id_org)

    org_name = await get_org_name(id_org)

    # If issue has been assigned to a team member, send an email to the
    # team member's email address.
    if issue_response.team_member_id and user_pool_id:
        cognito_member = await get_cognito_member(
            user_pool_id, str(issue_response.team_member_id)
        )

        if cognito_member:
            await email_notify_team_member(
                org_name=org_name,
                team_member_email=cognito_member.email,
                issue=issue_response,
                white_label=white_label,
                id_org=id_org,
            )

    # After adding an issue to the database, send an email to the
    # location's support email address, if the location doesn't have one,
    # default to the org's main support email address.
    #
    # If none of the above are set, simply ignore the email and log a warning.
    event_object = None
    org_settings_object = await get_settings_org(id_org)
    if id_event:
        query = select(Event).where(Event.id == id_event, Event.id_org == id_org)
        resp = await db.session.execute(query)
        event_object = resp.unique().scalar_one()
        event_object = Event.Read.parse_obj(event_object)

        try:
            location_email = event_object.device.location.contact_email
        except AttributeError:
            location_email = None

        org_default_support_email = org_settings_object.default_support_email

        await email_issue_to_support(
            org_default_support_email, location_email, issue_response, id_org
        )

    # Select to return the issue with the event and device details
    query = select(Issue).where(Issue.id == issue_response.id, Issue.id_org == id_org)
    response = await db.session.execute(query)
    issue_response = response.unique().scalar_one()

    # Set device to maintenance & cancel event
    if event_object:
        if org_settings_object.maintenance_on_issue:
            await set_device_maintenance(event_object.device.id, id_org, True)
        total_time: timedelta = datetime.now(timezone.utc) - event_object.started_at
        formatted_time = (
            f"{int(total_time.total_seconds() // 3600):02d}:{int(total_time.total_seconds() % 3600 // 60):02d}:"
            f"{int(total_time.total_seconds() % 3600 % 60):02d}"
        )
        query = (
            update(Event)
            .where(Event.id == event_object.id, Event.id_org == id_org)
            .values(
                event_status=EventStatus.canceled,
                ended_at=datetime.utcnow(),
                total_time=formatted_time,
                code=None,
            )
        )
        response = await db.session.execute(query)
        await db.session.commit()  # raises IntegrityError

        await send_payload(
            id_org,
            EventChange(
                id_org=id_org,
                id_event=event_object.id,
                event_status=event_object.event_status,
                event_obj=event_object,
            ),
        )

    return issue_response


async def generate_issue_id(id_org: UUID, depth: int = 1, max_depth: int = 25):
    if depth > max_depth:
        raise HTTPException(
            status_code=400, detail="Max depth reached, try again later"
        )

    # Generate a random number between 1 and 999999
    random_number = randint(1, 999999)
    issue_id = f"ISS{str(random_number).zfill(6)}"

    # Check if the generated issue_id already exists
    query = select(Issue).where(Issue.issue_id == issue_id, Issue.id_org == id_org)
    response = await db.session.execute(query)

    if response.unique().scalar_one_or_none():
        # If it exists, try again
        return await generate_issue_id(id_org, depth + 1)

    return issue_id


async def get_issue(id_issue: UUID, id_org: UUID) -> Issue:
    query = select(Issue).where(Issue.id == id_issue, Issue.id_org == id_org)

    response = await db.session.execute(query)
    return response.unique().scalar_one()


async def update_issue(
    id_issue: UUID,
    id_org: UUID,
    updated_issue: Issue,
    images_service: ImagesService,
    images: Optional[list[UploadFile]],
    user_pool_id: UUID,
):
    # Start the query without the pictures field
    print("HERE>", updated_issue.dict())
    query = (
        update(Issue)
        .where(Issue.id == id_issue, Issue.id_org == id_org)
        .values(**updated_issue.dict())
    )

    # Only update `pictures` if new images are provided
    if images:
        images_urls = await images_service.batch_upload(id_org, images)
        query = query.values(pictures=images_urls)  # update picture with new urls

    await db.session.execute(query)
    await db.session.commit()

    updated_issue_details = await get_issue(id_issue, id_org)

    if updated_issue_details.team_member_id:
        cognito_member = await get_cognito_member(
            user_pool_id, str(updated_issue_details.team_member_id)
        )
        white_label = await partner_get_white_label(id_org)
        org_name = await get_org_name(id_org)

        if cognito_member:
            await email_notify_team_member(
                org_name,
                cognito_member.email,
                white_label,
                updated_issue_details,
                id_org,
            )

    return updated_issue_details


async def delete_issue(id_issue: UUID, id_org: UUID) -> Issue:
    query = (
        delete(Issue)
        .where(Issue.id == id_issue, Issue.id_org == id_org)
        .returning(Issue)
    )

    response = await db.session.execute(query)
    await db.session.commit()

    try:
        return response.all().pop()
    except IndexError:
        raise HTTPException(status_code=404, detail="Issue not found")


async def delete_issues(id_issues: list[UUID], id_org: UUID):
    query = (
        delete(Issue)
        .where(Issue.id.in_(id_issues), Issue.id_org == id_org)
        .returning(Issue)
    )

    await db.session.execute(query)
    await db.session.commit()

    return {"detail": "Issues deleted"}


async def switch_issue_status(
    id_issue: UUID,
    status: IssueStatus,
    id_org: UUID,
):
    query = (
        update(Issue)
        .where(Issue.id == id_issue, Issue.id_org == id_org)
        .values(status=status)
        .returning(Issue)
    )

    response = await db.session.execute(query)
    await db.session.commit()

    try:
        updated_issue = response.all().pop()

        return updated_issue
    except IndexError:
        error_detail = "Issue not found"

        raise HTTPException(status_code=404, detail=error_detail)
