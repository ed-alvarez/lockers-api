import csv
from apscheduler.jobstores.base import JobLookupError
from datetime import datetime, timedelta, timezone
from io import StringIO
from math import ceil
from typing import List, Optional
from uuid import UUID
from uuid import uuid4

from async_stripe import stripe
from fastapi.responses import StreamingResponse
from config import get_settings
from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from sqlalchemy import (
    and_,
    between,
    desc,
    distinct,
    func,
    or_,
    select,
    insert,
    delete,
    update,
)
from sqlalchemy.sql import extract


from ..device.model import Device, LockStatus, Status
from ..event.model import Event, EventStatus
from ..issue.model import Issue
from ..location.model import Location
from ..organization.controller import get_org, get_org_tree_bfs
from ..organization.model import LinkOrgUser, Org
from ..user.model import User
from ..member.controller import get_user
from .model import Location as LocationReport

from .model import (
    Report,
    PaginatedReports,
    EMAIL_BODY,
    Recurrence,
    TimeFrame,
    TopLocations,
)
from util.scheduler import scheduler
from util.email import send_csv_file
from ..organization.controller import get_org_sendgrid_auth_sender

stripe.api_key = get_settings().stripe_api_key


async def get_partner_reports(
    id_org: UUID,
    user_pool: str,
    page: int = 1,
    size: int = 50,
    id_report: Optional[UUID] = None,
    search: Optional[str] = None,
    target_org: Optional[UUID] = None,
):
    if target_org:
        query = select(Org).where(Org.id == target_org, Org.id_tenant == id_org)
        response = await db.session.execute(query)

        if not response.scalar_one_or_none():
            raise HTTPException(
                status_code=404,
                detail="Organization is not a sub-organization of the tenant or does not exist.",
            )
    if target_org:
        query = select(Report).where(Report.id_org == target_org)
    else:
        query = select(Report).where(Report.id_org == id_org)

    if id_report:
        query = query.where(Report.id == id_report)
        result = await db.session.execute(query)
        data = result.scalar_one()
        report = Report.Read.parse_obj(data)
        if report.assign_to:
            report.assignees = await get_report_assignees(report, user_pool)
        return report

    if search:
        query = query.where(Report.name.ilike(f"%{search}%"))

    count = query
    query = (
        query.limit(size).offset((page - 1) * size).order_by(Report.created_at.desc())
    )

    data = await db.session.execute(query)
    counter = await db.session.execute(count)

    total_count = len(counter.all())

    reports = data.scalars().all()

    response = []
    for report in reports:
        report = Report.Read.parse_obj(report)
        if report.assign_to:
            report.assignees = await get_report_assignees(report, user_pool)
        response.append(report)

    return PaginatedReports(
        items=response,
        total=total_count,
        pages=ceil(total_count / size),
    )


async def create_report(id_org: UUID, report: Report.Write):
    if (
        report.recurrence == Recurrence.weekly
        or report.recurrence == Recurrence.biweekly
    ) and report.weekday is None:
        raise HTTPException(
            status_code=400,
            detail="Weekly reports must have a weekday selected",
        )
    elif (
        report.recurrence == Recurrence.monthly
        or report.recurrence == Recurrence.bimonthly
    ) and not report.month:
        raise HTTPException(
            status_code=400,
            detail="Monthly reports must have a start month selected",
        )

    # create a version based on the current date and the name
    epoch = int(datetime.utcnow().timestamp())
    report_id = uuid4()
    db_report = Report(
        id=report_id,
        name=report.name,
        contents=report.contents,
        assign_to=report.assign_to,
        recurrence=report.recurrence.value,
        weekday=report.weekday,
        month=report.month,
        when=report.when.value,
        include_sub_orgs=report.include_sub_orgs,
        send_time=report.send_time,
        version=f"report_{str(report_id)}_{str(epoch)}",
        target_org=report.target_org or id_org,
        last_content=None,
        last_sent=None,
        id_org=id_org,
    )

    query = insert(Report).values(db_report.dict()).returning(Report)
    result = await db.session.execute(query)
    await db.session.commit()
    data = result.all()[0]

    schedule_report(report, data.id)

    return data


def schedule_report(report: Report.Write, report_id: UUID):
    match report.recurrence:
        case Recurrence.weekly:
            scheduler.add_job(
                send_report,
                "cron",
                day="*",
                month="*",
                day_of_week=report.weekday,
                hour=int(report.send_time.split(":")[0]),
                minute=int(report.send_time.split(":")[1]),
                second=0,
                args=[report_id],
                id=str(report_id),
            )
        case Recurrence.biweekly:
            scheduler.add_job(
                send_report,
                "cron",
                day="1-7,15-21",
                month="*",
                day_of_week=report.weekday,
                hour=int(report.send_time.split(":")[0]),
                minute=int(report.send_time.split(":")[1]),
                second=0,
                args=[report_id],
                id=str(report_id),
            )
        case Recurrence.monthly:
            start_date = datetime(
                datetime.utcnow().year, month=report.month, day=datetime.utcnow().day
            )
            scheduler.add_job(
                send_report,
                "cron",
                day="1" if report.when == TimeFrame.start else "28",
                month="*",
                day_of_week="*",
                hour=int(report.send_time.split(":")[0]),
                minute=int(report.send_time.split(":")[1]),
                second=0,
                start_date=start_date,
                args=[report_id],
                id=str(report_id),
            )
        case Recurrence.bimonthly:
            start_date = datetime(
                datetime.utcnow().year, month=report.month, day=datetime.utcnow().day
            )
            scheduler.add_job(
                send_report,
                "cron",
                day="1" if report.when == TimeFrame.start else "28",
                month="*/2",
                day_of_week="*",
                hour=int(report.send_time.split(":")[0]),
                minute=int(report.send_time.split(":")[1]),
                second=0,
                start_date=start_date,
                args=[report_id],
                id=str(report_id),
            )


async def update_report(id_report: UUID, id_org: UUID, report: Report.Write):
    if not any([report.recurrence, report.weekday, report.month]):
        raise HTTPException(
            status_code=400,
            detail="No recurring periods were selected, either a day and a month are selected or a recurring period (monthly, weekly, bimonthly, biweekly) is set",
        )

    epoch = int(datetime.utcnow().timestamp())
    query = (
        update(Report)
        .where(Report.id == id_report)
        .values(
            name=report.name,
            contents=report.contents,
            assign_to=report.assign_to,
            recurrence=report.recurrence.value if report.recurrence else None,
            weekday=report.weekday,
            month=report.month,
            when=report.when.value,
            include_sub_orgs=report.include_sub_orgs,
            send_time=report.send_time,
            version=f"report_{str(id_report)}_{str(epoch)}",
            target_org=report.target_org or id_org,
        )
        .returning(Report)
    )

    result = await db.session.execute(query)
    await db.session.commit()
    data = result.all()[0]

    try:
        scheduler.remove_job(job_id=str(id_report))  # type: ignore
    except JobLookupError:
        pass

    schedule_report(report, id_report)

    return data


async def delete_report(id_report: UUID, id_org: UUID):
    query = select(Report).where(Report.id == id_report, Report.id_org == id_org)
    result = await db.session.execute(query)
    report = result.scalar_one()

    query = delete(Report).where(Report.id == id_report, Report.id_org == id_org)
    await db.session.execute(query)
    await db.session.commit()

    try:
        scheduler.remove_job(str(id_report))
    except JobLookupError:
        pass

    return report


async def delete_reports(id_reports: List[UUID], id_org: UUID):
    for id_report in id_reports:
        await delete_report(id_report=id_report, id_org=id_org)

    return {"detail": "Reports deleted"}


async def send_report(id_report: UUID):
    query = select(Report).where(Report.id == id_report)
    result = await db.session.execute(query)
    report = result.scalar_one_or_none()

    if not report:
        return

    if not report.assign_to:
        return

    org = await get_org(report.id_org)
    report_data = await generate_all_reports(
        report.id_org, report.include_sub_orgs, report.contents
    )

    for user_id in report.assign_to:
        user = await get_user(org.user_pool, str(user_id))

        file = generate_csv(report_data)

        report_contents = ""

        for c in report.contents:
            report_contents += f"<li>{c.replace('_', ' ')}</li>"

        content = EMAIL_BODY.format(
            user_name=user.name,
            report_version=report.version,
            report_contents=report_contents,
        )

        email_sender = await get_org_sendgrid_auth_sender(org.id)

        send_csv_file(
            email_sender,
            user.email,
            f"Organization Report: {report.name}",
            content,
            file,
            report.version,
        )

    query = (
        update(Report)
        .where(Report.id == id_report)
        .values(
            last_sent=datetime.utcnow(),
        )
    )
    await db.session.execute(query)
    await db.session.commit()


async def get_reports(id_org: UUID, target_org: Optional[UUID] = None):
    reports = {
        "earnings": await get_earnings(id_org=id_org, target_org=target_org),
        "users": await get_users(id_org=id_org, target_org=target_org),
        "transactions": await get_events(id_org=id_org, target_org=target_org),
        "top_users": await get_top_users(id_org=id_org, target_org=target_org),
        "top_locations": await get_top_locations(id_org=id_org, target_org=target_org),
    }

    return reports


async def get_report(id_report: UUID, id_org: UUID) -> Report:
    query = select(Report).where(Report.id == id_report, Report.id_org == id_org)
    result = await db.session.execute(query)
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return report


async def get_events(
    id_org: UUID,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    target_org: Optional[UUID] = None,
):
    if target_org:
        query = select(Org).where(Org.id == target_org, Org.id_tenant == id_org)
        response = await db.session.execute(query)

        if not response.scalar_one_or_none():
            raise HTTPException(
                status_code=404,
                detail="Organization is not a sub-organization of the tenant or does not exist.",
            )

    if target_org:
        query_total = select(func.count(Event.id)).where(Event.id_org == target_org)
    else:
        query_total = select(func.count(Event.id)).where(Event.id_org == id_org)

    response_total = await db.session.execute(query_total)
    total = response_total.scalars().first()

    from_date = (
        from_date if from_date else datetime.now(timezone.utc) - timedelta(weeks=52)
    )
    to_date = to_date if to_date else datetime.now(timezone.utc)

    query = (
        select(
            func.count(Event.id),
            extract("month", Event.created_at).label("month"),
        )
        .where(
            between(
                Event.created_at,
                from_date,
                to_date,
            ),
        )
        .group_by(
            extract("month", Event.created_at),
        )
    )

    if target_org:
        query = query.where(Event.id_org == target_org)
    else:
        query = query.where(Event.id_org == id_org)

    response = await db.session.execute(query)

    return {"total": total, "data": response.all()}


async def get_earnings(id_org: UUID, target_org: Optional[UUID] = None):
    if target_org:
        query = select(Org).where(Org.id == target_org, Org.id_tenant == id_org)
        response = await db.session.execute(query)

        if not response.scalar_one_or_none():
            raise HTTPException(
                status_code=404,
                detail="Organization is not a sub-organization of the tenant or does not exist.",
            )

    query = select(func.sum(Event.total)).where(
        Event.event_status == EventStatus.finished,
        between(
            Event.created_at,
            datetime.now(timezone.utc) - timedelta(weeks=4),
            datetime.now(timezone.utc),
        ),
    )

    if target_org:
        query = query.where(Event.id_org == target_org)
    else:
        query = query.where(Event.id_org == id_org)

    response = await db.session.execute(query)

    org = await get_org(target_org if target_org else id_org)

    account = await stripe.Account.retrieve(org.stripe_account_id)
    earnings = response.scalars().first() or 0

    return {
        "earnings": earnings,
        "currency": account["default_currency"],
    }


async def get_users(
    id_org: UUID,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    target_org: Optional[UUID] = None,
):
    if target_org:
        query = select(Org).where(Org.id == target_org, Org.id_tenant == id_org)
        response = await db.session.execute(query)

        if not response.scalar_one_or_none():
            raise HTTPException(
                status_code=404,
                detail="Organization is not a sub-organization of the tenant or does not exist.",
            )

    if target_org:
        query_total = select(func.count(LinkOrgUser.id_user)).where(
            LinkOrgUser.id_org == target_org
        )
    else:
        query_total = select(func.count(LinkOrgUser.id_user)).where(
            LinkOrgUser.id_org == id_org
        )

    response_total = await db.session.execute(query_total)
    total = response_total.scalars().first()

    query = (
        select(
            func.count(LinkOrgUser.id_user),
            extract("month", LinkOrgUser.created_at).label("month"),
        )
        .where(
            between(
                LinkOrgUser.created_at,
                (
                    from_date
                    if from_date
                    else datetime.now(timezone.utc) - timedelta(weeks=26)
                ),
                to_date if to_date else datetime.now(timezone.utc),
            ),
        )
        .group_by(
            extract("month", LinkOrgUser.created_at),
        )
    )

    if target_org:
        query = query.where(LinkOrgUser.id_org == target_org)
    else:
        query = query.where(LinkOrgUser.id_org == id_org)

    response = await db.session.execute(query)

    return {"total": total, "data": response.all()}


async def get_top_users(id_org: UUID, target_org: Optional[UUID] = None):
    if target_org:
        query = select(Org).where(Org.id == target_org, Org.id_tenant == id_org)
        response = await db.session.execute(query)

        if not response.scalar_one_or_none():
            raise HTTPException(
                status_code=404,
                detail="Organization is not a sub-organization of the tenant or does not exist.",
            )

    query = (
        select(
            User,
            func.count(Event.id).label("count"),
            func.max(Location.name).label("location"),
            func.coalesce(func.sum(Event.total), 0).label("purchases"),
        )
        .join(Event)
        .join_from(Event, Device, Event.id_device == Device.id)
        .join_from(Device, Location, Device.id_location == Location.id)
        .group_by(User.id)
        .order_by(desc("count"))
        .limit(5)
    )

    if target_org:
        query = query.where(Event.id_org == target_org)
    else:
        query = query.where(Event.id_org == id_org)

    response = await db.session.execute(query)
    data = response.all()

    return data


async def get_top_locations(id_org: UUID, target_org: Optional[UUID] = None):
    if target_org:
        query = select(Org).where(Org.id == target_org, Org.id_tenant == id_org)
        response = await db.session.execute(query)

        if not response.scalar_one_or_none():
            raise HTTPException(
                status_code=404,
                detail="Organization is not a sub-organization of the tenant or does not exist.",
            )

    query = (
        select(
            func.count(Event.id).label("count"),
            Location.id,
            Location.name,
            Location.address,
        )
        .join_from(Event, Device, Device.id == Event.id_device)
        .join_from(Device, Location, Location.id == Device.id_location)
        .group_by(Location.id)
        .order_by(desc("count"))
        .limit(5)
    )

    if target_org:
        query = query.where(Event.id_org == target_org)
    else:
        query = query.where(Event.id_org == id_org)

    response = await db.session.execute(query)

    data = response.unique().all()

    # The order of the fields in the query is count, id, name, address
    # This is guaranteed by the query, so we can safely unpack the data
    return [
        TopLocations(
            count=i[0], Location=LocationReport(id=i[1], name=i[2], address=i[3])
        )
        for i in data
    ]


async def get_user_growth(id_org: UUID, interval: Optional[str] = "month"):
    match interval:
        case "day":
            interval = timedelta(hours=24)
        case "week":
            interval = timedelta(days=7)
        case "month":
            interval = timedelta(weeks=4)
        case "year":
            interval = timedelta(weeks=52)
        case _:
            raise HTTPException(
                status_code=400,
                detail="Interval must be one of: day, week, month, year.",
            )
    # This will return the number of users that have been created in this interval (e.g. this month)
    current = select(func.count(LinkOrgUser.id_user)).where(
        LinkOrgUser.id_org == id_org,
        between(
            LinkOrgUser.created_at,
            datetime.now(timezone.utc) - interval,
            datetime.now(timezone.utc),
        ),
    )
    # This will return the number of users that have been created in the last interval (e.g. last month)
    last = select(func.count(LinkOrgUser.id_user)).where(
        LinkOrgUser.id_org == id_org,
        between(
            LinkOrgUser.created_at,
            datetime.now(timezone.utc) - interval * 2,
            datetime.now(timezone.utc) - interval,
        ),
    )

    current_response = await db.session.execute(current)
    last_response = await db.session.execute(last)

    current_data = current_response.scalars().first()
    last_data = last_response.scalars().first()

    # If the last interval equates to 0, we return 100% growth
    if last_data == 0:
        return {
            "percentage": 100,
        }

    growth_percentage = (current_data - last_data) / last_data * 100

    return {"percentage": growth_percentage}


async def get_issue_rate(
    id_org: UUID,
    locations: Optional[List[UUID]] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
):
    # If no locations are specified, fetch all locations associated with the org's devices

    if not locations:
        query = select(Location.id).where(Location.id_org == id_org)
        response = await db.session.execute(query)
        locations = [*response.scalars().all()]

    grand_total_issues = 0
    grand_total_transactions = 0

    for location in locations:
        device_ids_subquery = select(Device.id).where(
            and_(Device.id_org == id_org, Device.id_location == location)
        )

        # Build the transaction query for this location
        query_total_transactions = select(func.count(Event.id)).where(
            Event.id_device.in_(device_ids_subquery)
        )

        # Issues query for this location
        events_subquery = select(Event.id).where(
            Event.id_device.in_(device_ids_subquery)
        )
        query_total_issues = select(func.count(Issue.id)).where(
            Issue.id_event.in_(events_subquery)
        )

        # Apply date filter if provided
        if from_date and to_date:
            date_condition = between(Issue.created_at, from_date, to_date)
            query_total_issues = query_total_issues.where(date_condition)
            query_total_transactions = query_total_transactions.where(date_condition)

        # Fetch results for this location
        total_transactions = await db.session.scalar(query_total_transactions)
        total_issues = await db.session.scalar(query_total_issues)

        grand_total_issues += total_issues
        grand_total_transactions += total_transactions

    grand_issue_rate = (
        (grand_total_issues / grand_total_transactions) * 100
        if grand_total_transactions
        else 0
    )

    return {
        "total_issues": grand_total_issues,
        "total_transactions": grand_total_transactions,
        "issue_rate": grand_issue_rate,
    }


async def get_new_transaction_percentage(
    id_org: UUID,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
):
    # If no date range is provided, the default is the last one month

    if not from_date or not to_date:
        to_date = datetime.now(timezone.utc)
        from_date = to_date - timedelta(days=30)

    # Query to count total transactions in the date range

    query_total = select(func.count(Event.id)).where(
        Event.id_org == id_org, Event.created_at.between(from_date, to_date)
    )
    response_total = await db.session.execute(query_total)
    total_transactions = response_total.scalar()

    # Query to count total transactions before the date range

    query_previous_total = select(func.count(Event.id)).where(
        Event.id_org == id_org, Event.created_at < from_date
    )
    response_previous_total = await db.session.execute(query_previous_total)
    previous_total_transactions = response_previous_total.scalar()

    # Calculate the new transaction percentage

    if previous_total_transactions > 0:
        new_transaction_percentage = (
            (total_transactions - previous_total_transactions)
            / previous_total_transactions
        ) * 100
    elif total_transactions > 0:
        new_transaction_percentage = 100
    else:
        new_transaction_percentage = 0

    return {
        "new_transactions": total_transactions - previous_total_transactions,
        "new_transaction_percentage": new_transaction_percentage,
    }


async def get_system_health(id_org: UUID):
    # Query to get all location ids within the organization

    query_locations = (
        select(Device.id_location).where(Device.id_org == id_org).distinct()
    )
    response_locations = await db.session.execute(query_locations)
    location_ids = response_locations.scalars().all()

    health_data = []

    for location_id in location_ids:
        # Query to count total devices at the location

        query_total_devices = select(func.count(Device.id)).where(
            Device.id_org == id_org, Device.id_location == location_id
        )
        response_total_devices = await db.session.execute(query_total_devices)
        total_devices = response_total_devices.scalar()

        # Query to count devices in maintenance or offline at the location

        query_unhealthy_devices = select(func.count(Device.id)).where(
            Device.id_org == id_org,
            Device.id_location == location_id,
            (Device.status == Status.maintenance)
            | (Device.lock_status == LockStatus.offline),
            # checking for maintenance status or offline lock status
        )
        response_unhealthy_devices = await db.session.execute(query_unhealthy_devices)
        unhealthy_devices = response_unhealthy_devices.scalar()

        # Calculate the health percentage
        health_percentage = (
            ((total_devices - unhealthy_devices) / total_devices) * 100
            if total_devices
            else 0
        )

        health_data.append(
            {
                "location_id": location_id,
                "total_devices": total_devices,
                "unhealthy_devices": unhealthy_devices,
                "health_percentage": health_percentage,
            }
        )

    return health_data


async def get_occupancy_rate(
    id_org: UUID,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
):
    from_date = (
        from_date if from_date else datetime.now(timezone.utc) - timedelta(hours=24)
    )
    to_date = to_date if to_date else datetime.now(timezone.utc)

    query = (
        select(Location.id, Location.name, Location.address, func.count(Device.id))
        .where(Location.id_org == id_org)
        .join(Device)
        .group_by(Location.id)
    )
    response = await db.session.execute(query)

    locations = response.all()

    query = (
        select(
            Location.id,
            Location.name,
            Location.address,
            func.count(distinct(Event.id_device)),
        )
        .where(Location.id_org == id_org)
        .join_from(Device, Location, Device.id_location == Location.id)
        .join_from(Device, Event, Device.id == Event.id_device)
        .where(
            between(
                Event.created_at,
                from_date,
                to_date,
            ),
        )
        .group_by(Location.id)
    )
    response = await db.session.execute(query)

    events = response.all()

    response = [
        {
            "id": location.id,
            "name": location.name,
            "address": location.address,
            # * Occupancy rate is calculated by dividing the number of events by the number of devices,
            # and multiplying by 100
            "occupancy_rate": next(
                (
                    event[3] / location[3] * 100
                    for event in events
                    if event[0] == location.id and location[3] != 0
                ),
                0,
            ),
        }
        for location in locations
    ]

    return response


async def get_transactions_per_locker_per_range(
    id_org: UUID,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    locations: Optional[List[UUID]] = None,
) -> dict:
    # Fetch org creation date

    org = await db.session.get(Org, id_org)
    org_creation_date = org.created_at.date()

    # If no date strings are provided, default to transactions from org creation date to now
    if not start_date:
        start_date_obj = org_creation_date
    else:
        # Convert the ISO UTC string to a datetime.date object
        start_date_obj = datetime.fromisoformat(start_date).date()

    if not end_date:
        end_date_obj = datetime.now(timezone.utc).date()
    else:
        # Convert the ISO UTC string to a datetime.date object
        end_date_obj = datetime.fromisoformat(end_date).date()

    # If locations are not provided, get all locations for the given org
    if not locations:
        query = select(Location.id).where(Location.id_org == id_org)
        response = await db.session.execute(query)
        locations = [*response.scalars().all()]

    location_results = []

    total_transactions = 0
    total_locker_doors = 0

    for location in locations:
        # Count transactions for the current location

        transaction_query = select(func.count(Event.id)).where(
            and_(
                Event.created_at >= start_date_obj,
                Event.created_at <= end_date_obj,
                Event.id_org == id_org,
                Event.id_device.in_(
                    select(Device.id).where(Device.id_location == location)
                ),
            )
        )
        location_transactions = await db.session.scalar(transaction_query)

        # Count locker doors for the current location
        locker_query = select(func.count(Device.id)).where(
            and_(Device.id_org == id_org, Device.id_location == location)
        )
        location_locker_doors = await db.session.scalar(locker_query)

        # Calculate average transactions per locker for the current location
        avg_transactions_per_locker = (
            location_transactions / location_locker_doors
            if location_locker_doors
            else 0
        )

        location_results.append(
            {
                "location_id": location,
                "total_transactions": location_transactions,
                "total_locker_doors": location_locker_doors,
                "avg_transactions_per_locker": avg_transactions_per_locker,
            }
        )

        total_transactions += location_transactions
        total_locker_doors += location_locker_doors

    avg_transactions_per_locker_total = (
        total_transactions / total_locker_doors if total_locker_doors else 0
    )

    return {
        "start_date": start_date,
        "end_date": end_date,
        "locations_breakdown": location_results,
        "total_transactions": total_transactions,
        "total_locker_doors": total_locker_doors,
        "avg_transactions_per_locker": avg_transactions_per_locker_total,
    }


async def generate_all_reports(
    id_org: UUID,
    include_sub_orgs: bool,
    contents: Optional[List[str]] = None,
) -> dict | list:
    report_map = {
        "earnings": get_earnings,
        "user_growth": get_user_growth,
        "system_health": get_system_health,
        "issue_rate": get_issue_rate,
        "occupancy_rate": get_occupancy_rate,
        "transaction_rate": get_new_transaction_percentage,
        "top_users": get_top_users,
        "top_locations": get_top_locations,
        "active_locks": get_active_locks_report,
    }

    if not include_sub_orgs:
        reports = {}
        for report in contents:
            if report in report_map:
                reports[report] = await report_map[report](id_org)

        return reports

    orgs = await get_org_tree_bfs(id_org)
    total_reports = []
    for target_org in orgs:
        org = await get_org(target_org)

        reports = {}
        for report in contents:
            if report in report_map:
                reports[report] = await report_map[report](id_org)

        total_reports.append(
            {
                "id": org.id,
                "name": org.name,
                "parent": org.id_tenant,
                "reports": reports,
            }
        )
    return total_reports


async def get_total_transactions_for_location(
    id_org: UUID, locations: Optional[List[UUID]] = None, date: Optional[str] = None
) -> dict:
    # Fetch org creation date

    org = await db.session.get(Org, id_org)
    org_creation_date = org.created_at.date()

    # If no date string is provided, default to transactions from org creation date to now
    if not date:
        start_date = org_creation_date
        end_date = datetime.now(timezone.utc).date()

    else:
        # Convert the ISO UTC string to a datetime.date object
        start_date = datetime.fromisoformat(date).date()
        end_date = start_date + timedelta(days=1)

    # Prepare a dictionary to store results and a variable for total transactions
    transactions_breakdown = {}
    grand_total_transactions = 0

    if locations:
        # For each location, compute total transactions

        for location in locations:
            location_query = select(func.count(Event.id)).where(
                and_(
                    Event.created_at >= start_date,
                    Event.created_at < end_date,
                    Event.id_org == id_org,
                    Event.id_device.in_(
                        select(Device.id).where(Device.id_location == location)
                    ),
                )
            )
            location_transactions = await db.session.scalar(location_query)
            transactions_breakdown[str(location)] = location_transactions
            grand_total_transactions += location_transactions

    else:
        # If no specific locations are provided, aggregate transactions for the entire organization

        org_query = select(func.count(Event.id)).where(
            and_(
                Event.created_at >= start_date,
                Event.created_at < end_date,
                Event.id_org == id_org,
            )
        )
        total_transactions = await db.session.scalar(org_query)
        transactions_breakdown["organization_total"] = total_transactions
        grand_total_transactions = total_transactions

    # Return results with breakdown and grand total

    return {
        "breakdown": transactions_breakdown,
        "grand_total": grand_total_transactions,
    }


async def get_avg_transaction_time_controller(id_org: UUID) -> float:
    end_date = datetime.now().replace(day=1)
    start_date = end_date - timedelta(days=1)
    start_date = start_date.replace(day=1)

    transaction_query = select(func.avg(Event.ended_at - Event.started_at)).where(
        and_(
            Event.id_org == id_org,
            Event.started_at >= start_date,
            Event.ended_at <= end_date,
        )
    )

    avg_transaction_time = await db.session.scalar(transaction_query)

    # Convert the result (a timedelta) to your preferred format. For simplicity, let's return the average in seconds.
    avg_seconds = avg_transaction_time.total_seconds() if avg_transaction_time else 0

    return avg_seconds


async def get_total_users_for_org(id_org: UUID) -> int:
    # Subquery to get distinct user IDs associated with events of the organization

    subquery = select(Event.id_user).where(Event.id_org == id_org).distinct()

    # Now count the distinct user IDs

    user_query = select(func.count()).select_from(subquery.alias())

    total_users = await db.session.scalar(user_query)

    return total_users


async def get_total_locations_controller(id_org: UUID) -> dict:
    # Fetch the org to check if it's a super tenant

    org = await db.session.get(Org, id_org)

    # Fetch locations for the main organization

    main_org_locations_query = select(func.count(Location.id)).where(
        Location.id_org == id_org
    )
    main_org_total_locations = await db.session.scalar(main_org_locations_query)

    # If the organization is a super tenant, get locations for its tenants
    if org.super_tenant:
        tenant_ids_query = select(Org.id).where(Org.id_tenant == id_org)
        tenant_ids = [id[0] for id in await db.session.execute(tenant_ids_query)]

        tenant_locations_query = select(func.count(Location.id)).where(
            Location.id_org.in_(tenant_ids)
        )
        tenant_total_locations = await db.session.scalar(tenant_locations_query)

    else:
        tenant_total_locations = 0

    # Total locations (sum of main org and tenants)
    total_locations = main_org_total_locations + tenant_total_locations

    return {
        "org_id": id_org,
        "main_org_total_locations": main_org_total_locations,
        "tenant_total_locations": tenant_total_locations,
        "total_locations": total_locations,
    }


async def get_avg_revenue_per_transaction_controller(id_org: UUID) -> dict:
    # Query to get the average total from the Event table for the specified organization

    avg_revenue_query = select(func.avg(Event.total)).where(
        and_(
            Event.id_org == id_org,
            Event.total.isnot(
                None
            ),  # Ensure we're only calculating for transactions with a specified total
        )
    )

    avg_revenue = await db.session.scalar(avg_revenue_query)

    # If the result is None (i.e., there were no transactions for the org), we default to 0
    avg_revenue = avg_revenue or 0

    return {
        "org_id": id_org,
        "avg_revenue_per_transaction": float(
            avg_revenue
        ),  # Convert Decimal to float for JSON serialization
    }


async def get_door_counts(
    id_org: UUID, locations_list: Optional[List[UUID]] = None
) -> dict:
    # Base query to count devices for the organization and its tenants

    base_query = (
        select(Org.id, Device.id_location, func.count(Device.id))
        .group_by(Org.id, Device.id_location)
        .join(Device, Org.id == Device.id_org)
    )

    # If locations are specified, we'll add them to the filter
    if locations_list:
        base_query = base_query.where(Device.id_location.in_(locations_list))

    # Get counts for the main organization and its tenant organizations, grouped by location

    org_counts_by_location = await db.session.execute(
        base_query.where(or_(Org.id == id_org, Org.id_tenant == id_org))
    )
    org_counts_by_location = org_counts_by_location.fetchall()

    main_org_counts = {}
    tenant_counts = {}
    grand_total = 0

    for org_id, loc_id, count in org_counts_by_location:
        grand_total += count

        if org_id == id_org:
            main_org_counts[str(loc_id)] = count
        else:
            if str(org_id) not in tenant_counts:
                tenant_counts[str(org_id)] = {}
            tenant_counts[str(org_id)][str(loc_id)] = count

    return {
        "main_org": {
            "id": str(id_org),
            "door_counts_by_location": main_org_counts,
        },
        "tenants": tenant_counts,
        "grand_total_doors": grand_total,
    }


def generate_csv(reports: dict | list) -> str:
    """
    Generate a CSV file from a dictionary of reports.

    :param reports: Dictionary containing multiple reports.
    """
    output = gen_csv(reports)

    data = output.getvalue()
    output.close()
    return data


def stream_csv(reports: dict | list) -> StreamingResponse:
    """
    Stream a CSV file from a dictionary of reports.

    :param reports: Dictionary containing multiple reports.
    """
    output = gen_csv(reports)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
    )


def gen_csv(reports: dict | list) -> StringIO:
    output = StringIO()
    writer = csv.writer(output)
    if isinstance(reports, dict):
        for report_name, report_data in reports.items():
            writer.writerow([report_name.upper()])  # Write the report name

            # If data is a dictionary
            if isinstance(report_data, dict):
                if "data" in report_data and isinstance(report_data["data"], list):
                    # Write other keys first
                    for key, value in report_data.items():
                        if key != "data":
                            writer.writerow([key, value])

                    # Write the data tuples
                    writer.writerow(["Count", "Month"])
                    for count, month in report_data["data"]:
                        writer.writerow([count, month])
                else:
                    headers = report_data.keys()
                    writer.writerow(headers)
                    writer.writerow(report_data.values())

            # If data is a list
            elif isinstance(report_data, list) and report_data:
                first_item = report_data[0]

                if isinstance(first_item, dict):
                    headers = first_item.keys()
                    writer.writerow(headers)
                    for row in report_data:
                        writer.writerow(row.values())
                elif isinstance(first_item, (list, tuple)):
                    for row in report_data:
                        writer.writerow(row)
                else:
                    writer.writerow(report_data)

            writer.writerow([])  # Add an empty line between reports

    elif isinstance(reports, list):
        for entry in reports:
            writer.writerow(
                [f"{entry['name'].upper()} ORGANIZATION REPORT"]
            )  # add space
            writer.writerow(["id_org", "org_name", "id_parent"])  # add space
            writer.writerow(
                [entry["id"], entry["name"], entry["parent"]]
            )  # Write the org id
            writer.writerow([])  # add space

            for report_name, report_data in entry["reports"].items():
                writer.writerow([report_name.upper()])  # Write the report name

                # If data is a dictionary
                if isinstance(report_data, dict):
                    if "data" in report_data and isinstance(report_data["data"], list):
                        # Write other keys first
                        for key, value in report_data.items():
                            if key != "data":
                                writer.writerow([key, value])

                        # Write the data tuples
                        writer.writerow(["Count", "Month"])
                        for count, month in report_data["data"]:
                            writer.writerow([count, month])
                    else:
                        headers = report_data.keys()
                        writer.writerow(headers)
                        writer.writerow(report_data.values())

                # If data is a list
                elif isinstance(report_data, list) and report_data:
                    first_item = report_data[0]

                    if isinstance(first_item, dict):
                        headers = first_item.keys()
                        writer.writerow(headers)
                        for row in report_data:
                            writer.writerow(row.values())
                    elif isinstance(first_item, (list, tuple)):
                        for row in report_data:
                            writer.writerow(row)
                    else:
                        writer.writerow(report_data)

                writer.writerow([])  # Add an empty line between reports
            writer.writerow([])  # Add an empty line between reports

    return output


async def get_active_locks_report(id_org: UUID):
    """
    Fetches and calculates the active locks report for the previous month.
    """
    end_date = datetime.now().replace(day=1)
    start_date = end_date - timedelta(days=1)
    start_date = start_date.replace(day=1)

    # Query for active locks
    active_locks_query = (
        select(func.count())
        .select_from(Device)
        .where(
            and_(
                Device.id_org == id_org,
                Device.created_at.between(start_date, end_date),
                or_(Device.status == "available", Device.status == "reserved"),
            )
        )
        .group_by(Device.id)
    )

    # Query for maintenance locks
    maintenance_locks_query = (
        select(func.count())
        .select_from(Device)
        .where(
            and_(
                Device.id_org == id_org,
                Device.created_at.between(start_date, end_date),
                Device.status == "maintenance",
            )
        )
        .group_by(Device.id)
        .having(func.count(Device.id) == func.date_part("day", end_date - start_date))
    )

    # Execute queries
    active_locks_result = await db.session.execute(active_locks_query)
    maintenance_locks_result = await db.session.execute(maintenance_locks_query)

    active_locks_count = len(active_locks_result.scalars().all())
    maintenance_locks_count = len(maintenance_locks_result.scalars().all())

    # Calculate the final number of active locks excluding maintenance locks
    active_locks_excluding_maintenance = active_locks_count - maintenance_locks_count

    # New report format
    report = {
        "total_active_locks": active_locks_count,
        "total_locks_considered": active_locks_count + maintenance_locks_count,
        "active_locks_excluding_maintenance": active_locks_excluding_maintenance,
    }

    return report


async def get_report_assignees(report: Report.Read, user_pool: str):
    # Cache existing user IDs to avoid duplicate queries
    assignees = {}
    response = []
    for id_assignee in report.assign_to:
        if id_assignee not in assignees:
            try:
                user = await get_user(user_pool, str(id_assignee))
                assignees[id_assignee] = user
            except Exception:
                assignees[id_assignee] = None
        if assignees[id_assignee]:
            response.append(assignees[id_assignee])

    return response
