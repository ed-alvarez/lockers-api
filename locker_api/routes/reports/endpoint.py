from datetime import datetime
from typing import List, Optional
from uuid import UUID
from fastapi.responses import StreamingResponse
from pydantic import conint

from auth.cognito import get_current_org, get_current_user_pool
from config import get_settings
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_cache.decorator import cache
from ..organization.controller import is_sub_org
from util.response import BasicResponse


from . import controller
from .model import (
    Earnings,
    Graph,
    IssueRate,
    NewTransactionPercentageResponse,
    Occupancy,
    Percentage,
    SystemHealthResponse,
    TopLocations,
    TopUsers,
    Report,
    PaginatedReports,
    Summary,
)

router = APIRouter(tags=["reports"])


cache_seconds = get_settings().cache_seconds


@router.get("/partner/reports/all", response_model=PaginatedReports | Report.Read)
async def get_partner_reports(
    page: conint(gt=0) = 1,
    size: conint(gt=0) = 50,
    id_report: Optional[UUID] = None,
    search: Optional[str] = None,
    user_pool: str = Depends(get_current_user_pool),
    id_org: UUID = Depends(get_current_org),
    target_org: Optional[UUID] = None,
):
    res = await controller.get_partner_reports(
        id_org, user_pool, page, size, id_report, search, target_org
    )
    return res


@router.post("/partner/reports", response_model=Report.Read)
async def create_report(
    report: Report.Write,
    id_org: UUID = Depends(get_current_org),
):
    report = await controller.create_report(
        id_org=id_org,
        report=report,
    )
    return report


@router.delete("/partner/reports/{id_report}", response_model=Report.Read)
async def delete_report(
    id_report: UUID,
    id_org: UUID = Depends(get_current_org),
):
    report = await controller.delete_report(
        id_report=id_report,
        id_org=id_org,
    )
    return report


@router.delete("/partner/reports", response_model=BasicResponse)
async def delete_reports(
    id_reports: List[UUID],
    id_org: UUID = Depends(get_current_org),
):
    return await controller.delete_reports(
        id_reports=id_reports,
        id_org=id_org,
    )


@router.put("/partner/reports/{id_report}", response_model=Report.Read)
async def update_report(
    report: Report.Write,
    id_report: UUID,
    id_org: UUID = Depends(get_current_org),
):
    report = await controller.update_report(
        id_report=id_report, id_org=id_org, report=report
    )
    return report


@router.get("/partner/reports/download/{id_report}", response_class=StreamingResponse)
async def download_report(
    id_report: UUID,
    id_org: UUID = Depends(get_current_org),
):
    report = await controller.get_report(id_report, id_org)
    data = await controller.generate_all_reports(
        id_org, report.include_sub_orgs, report.contents
    )
    csv = controller.stream_csv(data)

    return csv


@router.get("/partner/reports", response_model=Summary)
@cache(600)
async def get_reports(
    id_org: UUID = Depends(get_current_org),
    target_org: Optional[UUID] = None,
):
    """Returns all reports for the current organization."""
    # Logging at the start
    # Logging input objects

    result = await controller.get_reports(id_org, target_org)
    # Logging result
    # Logging at the end

    return result


@router.get("/partner/reports/transactions", response_model=Graph)
@cache(600)
async def get_transactions(
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    id_org: UUID = Depends(get_current_org),
    target_org: Optional[UUID] = None,
):
    """Returns a list of transactions, optionally filtered by date range.
    If no date range is provided, the last 52 weeks are returned.
    Interval can be one of: day, week, month, year. Month is the default.
    """
    # Logging at the start

    result = await controller.get_events(id_org, from_date, to_date, target_org)
    # Logging result
    # Logging at the end

    return result


@router.get("/partner/reports/earnings", response_model=Earnings)
@cache(600)
async def get_earnings(
    id_org: UUID = Depends(get_current_org),
    target_org: Optional[UUID] = None,
):
    """Returns the earnings of this month."""
    # Logging at the start
    # Logging input parameters

    result = await controller.get_earnings(id_org, target_org)
    # Logging result
    # Logging at the end

    return result


@router.get("/partner/reports/users", response_model=Graph)
@cache(600)
async def get_users(
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    id_org: UUID = Depends(get_current_org),
    target_org: Optional[UUID] = None,
):
    """Returns a list of users, optionally filtered by date range.
    If no date range is provided, the last 26 weeks are returned.
    Interval can be one of: day, week, month, year. Month is the default.
    """
    # Logging at the start

    result = await controller.get_users(id_org, from_date, to_date, target_org)
    # Logging result
    # Logging at the end

    return result


@router.get("/partner/reports/top_users", response_model=list[TopUsers])
@cache(600)
async def get_top_users(
    id_org: UUID = Depends(get_current_org),
    target_org: Optional[UUID] = None,
):
    """Returns the top 5 users, ordered by the number of transactions"""
    # Logging at the start
    # Logging input parameters

    result = await controller.get_top_users(id_org, target_org)
    # Logging result
    # Logging at the end

    return result


@router.get("/partner/reports/locations", response_model=list[TopLocations])
@cache(600)
async def get_top_locations(
    id_org: UUID = Depends(get_current_org),
    target_org: Optional[UUID] = None,
):
    """Returns the top 5 locations, ordered by the number of transactions"""
    # Logging at the start
    # Logging input parameters

    result = await controller.get_top_locations(id_org, target_org)
    # Logging result
    # Logging at the end

    return result


@router.get("/partner/reports/user_growth", response_model=Percentage)
@cache(600)
async def get_user_growth(
    id_org: UUID = Depends(get_current_org),
    interval: str = "month",
    target_org: Optional[UUID] = None,
):
    """Returns the user growth given a time interval."""
    # Logging at the start
    # Logging input parameters
    if target_org:
        if not await is_sub_org(target_org, id_org):
            raise HTTPException(
                status_code=400,
                detail="Cannot access events from a non-sub organization",
            )
        id_org = target_org
    result = await controller.get_user_growth(id_org, interval)
    # Logging result
    # Logging at the end

    return result


@router.get("/partner/reports/issue_rate", response_model=IssueRate)
@cache(600)
async def get_issue_rate(
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    locations: Optional[str] = None,
    id_org: UUID = Depends(get_current_org),
    target_org: Optional[UUID] = None,
):
    """Returns the issue rate globally or for specific locations."""

    # Convert the comma-separated string into a list of UUIDs.
    # Logging at the start

    if target_org:
        if not await is_sub_org(target_org, id_org):
            raise HTTPException(
                status_code=400,
                detail="Cannot access events from a non-sub organization",
            )
        id_org = target_org
    locations_list = [UUID(loc) for loc in locations.split(",")] if locations else None

    result = await controller.get_issue_rate(id_org, locations_list, from_date, to_date)
    # Logging result
    # Logging at the end

    return result


@router.get(
    "/partner/reports/transaction_rate", response_model=NewTransactionPercentageResponse
)
@cache(600)
async def get_transaction_percentage(
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    id_org: UUID = Depends(get_current_org),
    target_org: Optional[UUID] = None,
):
    """Returns the percentage of new transactions added during a certain filtered time period."""
    # Logging at the start

    if target_org:
        if not await is_sub_org(target_org, id_org):
            raise HTTPException(
                status_code=400,
                detail="Cannot access events from a non-sub organization",
            )
        id_org = target_org
    result = await controller.get_new_transaction_percentage(id_org, from_date, to_date)
    # Logging result
    # Logging at the end

    return result


@router.get("/partner/reports/door_health", response_model=List[SystemHealthResponse])
@cache(600)
async def get_system_health(
    id_org: UUID = Depends(get_current_org), target_org: Optional[UUID] = None
):
    """Returns the health of each location."""

    if target_org:
        if not await is_sub_org(target_org, id_org):
            raise HTTPException(
                status_code=400,
                detail="Cannot access events from a non-sub organization",
            )
        id_org = target_org
    health_data = await controller.get_system_health(id_org)

    return health_data


@router.get("/partner/reports/occupancy_rate", response_model=List[Occupancy])
@cache(600)
async def get_occupancy_rate(
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    id_org: UUID = Depends(get_current_org),
    target_org: Optional[UUID] = None,
):
    """
    # Description
    Returns the occupancy rate of each location given a time interval. Default is the last 24 hours.
    # Explanation
    The occupancy rate is calculated as follows:
    - Get the number of devices of each location
    - Get the number of devices that have been used per location in the given time interval
    - Divide the second number by the first number and multiply by 100
    - The result is the occupancy rate of each location, in percentage
    """
    # Logging at the start
    # Logging input objects
    if target_org:
        if not await is_sub_org(target_org, id_org):
            raise HTTPException(
                status_code=400,
                detail="Cannot access events from a non-sub organization",
            )
        id_org = target_org
    occupancy_data = await controller.get_occupancy_rate(id_org, from_date, to_date)
    # Logging result (not displaying data for brevity)
    # Logging at the end

    return occupancy_data


@router.get("/partner/reports/transactions_per_locker", response_model=dict)
@cache(600)
async def get_transactions_per_locker_per_range(
    start_date: Optional[str] = None,  # Date in ISO UTC format
    end_date: Optional[str] = None,  # Date in ISO UTC format
    locations: Optional[str] = None,
    id_org: UUID = Depends(get_current_org),
    target_org: Optional[UUID] = None,
):
    """
    # Description Returns the average transactions per locker for a given date range and locations. If start_date and
    end_date are provided, they should be in the ISO UTC international format, e.g., "2023-04-15T14:56:00Z". If no
    dates are provided, we calculate transactions from the org_creation_date to the current date.
    """

    # Convert the comma-separated string into a list of UUIDs.
    # Logging at the start

    if target_org:
        if not await is_sub_org(target_org, id_org):
            raise HTTPException(
                status_code=400,
                detail="Cannot access events from a non-sub organization",
            )
        id_org = target_org
    # Convert the comma-separated string into a list of UUIDs if locations are provided.
    locations_list = None
    if locations:
        locations_list = [UUID(loc) for loc in locations.split(",")]

    result = await controller.get_transactions_per_locker_per_range(
        id_org, start_date, end_date, locations_list
    )
    # Logging result
    # Logging at the end

    return result


@router.get("/partner/reports/total_transactions", response_model=dict)
@cache(600)
async def get_total_transactions(
    locations: Optional[str] = None,
    date: Optional[str] = None,
    id_org: UUID = Depends(get_current_org),
    target_org: Optional[UUID] = None,
):
    """
    # Description
    Returns the total transactions for a given organization and location. If no date is provided,
    the total transactions from the day the org was created are returned.

    # Parameters - **id_org**: UUID of the organization. - **location**: UUID of the locations (optional) - separate
    with a comma like this '7cdfd8cd-842d-4682-b634-965ab7f4ed44,235952ea-2af0-4ce9-91a0-0164f5857e13,
    2d573dc0-c92c-4007-82e4-28d8e7422686'. - **date**: Date of the transactions in ISO UTC international format (
    optional). E.g., "2023-04-15T14:56:00Z". If no date is provided, the transactions for the previous day are
    returned.

    # Explanation
    The total transactions are calculated in the controller function based on the provided parameters.
    """
    # Convert the comma-separated string into a list of UUIDs
    # Logging at the start
    # Logging input objects
    if target_org:
        if not await is_sub_org(target_org, id_org):
            raise HTTPException(
                status_code=400,
                detail="Cannot access events from a non-sub organization",
            )
        id_org = target_org
    # Convert the comma-separated string into a list of UUIDs if locations are provided
    locations_list = None
    if locations:
        locations_list = [UUID(loc) for loc in locations.split(",")]

    transaction_data = await controller.get_total_transactions_for_location(
        id_org, locations_list, date
    )
    # Logging result
    # Logging at the end

    return transaction_data


@router.get("/partner/reports/avg_transaction_time")
@cache(600)
async def get_average_transaction_time(
    start_date: Optional[str] = Query(
        None, description="Start date of the range in the format 'YYYY-MM-DDTHH:MM:SSZ'"
    ),
    end_date: Optional[str] = Query(
        None, description="End date of the range in the format 'YYYY-MM-DDTHH:MM:SSZ'"
    ),
    id_org: UUID = Depends(get_current_org),
    target_org: Optional[UUID] = None,
):
    """
    # Description
    Returns the average transaction time for transactions within the specified date range.

    # Explanation
    The average transaction time is calculated based on the difference between
    the transaction's started_at and ended_at times. The result is averaged for all transactions
    within the given date range.
    """
    if target_org:
        if not await is_sub_org(target_org, id_org):
            raise HTTPException(
                status_code=400,
                detail="Cannot access events from a non-sub organization",
            )
        id_org = target_org
    avg_transaction_time = await controller.get_avg_transaction_time_controller(id_org)

    return avg_transaction_time


@router.get("/partner/reports/total_users", response_model=int)
@cache(600)
async def get_total_users(
    id_org: UUID = Depends(get_current_org), target_org: Optional[UUID] = None
):
    """
    # Description
    Returns the total number of unique users for a given organization.

    # Explanation
    The total users are calculated in the controller function.
    """
    # Logging at the start
    # Logging input objects
    if target_org:
        if not await is_sub_org(target_org, id_org):
            raise HTTPException(
                status_code=400,
                detail="Cannot access events from a non-sub organization",
            )
        id_org = target_org
    total_users = await controller.get_total_users_for_org(id_org)
    # Logging result
    # Logging at the end

    return total_users


@router.get("/partner/reports/total_locations")
@cache(600)
async def get_total_locations_for_org_and_tenants(
    id_org: UUID = Depends(get_current_org),
    target_org: Optional[UUID] = None,
) -> dict:
    """
    # Description
    Returns the total locations for the organization and its tenant organizations.
    """
    # Logging at the start
    # Logging input objects
    if target_org:
        if not await is_sub_org(target_org, id_org):
            raise HTTPException(
                status_code=400,
                detail="Cannot access events from a non-sub organization",
            )
        id_org = target_org
    total_locations = await controller.get_total_locations_controller(id_org)
    # Logging result
    # Logging at the end

    return total_locations


@router.get("/partner/reports/avg_revenue_per_transaction")
@cache(600)
async def get_average_revenue_per_transaction(
    id_org: UUID = Depends(get_current_org),
    target_org: Optional[UUID] = None,
) -> dict:
    """
    # Description
    Returns the average revenue per transaction for the organization.
    """
    # Logging at the start
    # Logging input objects
    if target_org:
        if not await is_sub_org(target_org, id_org):
            raise HTTPException(
                status_code=400,
                detail="Cannot access events from a non-sub organization",
            )
        id_org = target_org
    average_revenue = await controller.get_avg_revenue_per_transaction_controller(
        id_org
    )
    # Logging result
    # Logging at the end

    return average_revenue


@router.get("/partner/reports/door_counts")
@cache(600)
async def get_door_counts_by_org(
    locations: Optional[str] = None,
    id_org: UUID = Depends(get_current_org),
    target_org: Optional[UUID] = None,
) -> dict:
    """
    # Description Returns the number of doors (devices) for the main organization and its tenant organizations,
    optionally filtered by multiple locations.
    """
    # Convert the comma-separated string into a list of UUIDs
    # Logging at the start
    if target_org:
        if not await is_sub_org(target_org, id_org):
            raise HTTPException(
                status_code=400,
                detail="Cannot access events from a non-sub organization",
            )
        id_org = target_org
    locations_list = None
    if locations:
        locations_list = [UUID(loc) for loc in locations.split(",")]

    # Logging input objects

    door_counts = await controller.get_door_counts(id_org, locations_list)
    # Logging result
    # Logging at the end

    return door_counts


@router.get("/partner/reports/active_locks", response_model=dict)
async def get_active_locks_report(
    id_org: UUID = Depends(get_current_org), target_org: Optional[UUID] = None
):
    """
    Endpoint to get a report of active locks for the previous month.
    """
    # Logging at the start
    if target_org:
        if not await is_sub_org(target_org, id_org):
            raise HTTPException(
                status_code=400,
                detail="Cannot access events from a non-sub organization",
            )
        id_org = target_org
    report = await controller.get_active_locks_report(id_org)
    # Logging result
    # Logging at the end

    return report
