import json
from uuid import UUID

from fastapi_async_sqlalchemy import db
from sqlalchemy import insert, select, update


from .model import FilterType, OrgFilters


async def create_default_filters(
    id_org: UUID,
):
    filters = {}

    query = select(OrgFilters).where(OrgFilters.id_org == id_org)
    response = await db.session.execute(query)
    data = response.scalars().first()

    # If filters are not set in the database, create them automatically
    # with default values
    if not data:
        print("Creating filters")
        query = insert(OrgFilters).values(id_org=id_org).returning(OrgFilters)
        response = await db.session.execute(query)
        filters = response.all().pop()
    else:
        filters = data

    return filters


async def get_filter(
    id_org: UUID,
    filter_type: FilterType,
):
    filters = await create_default_filters(id_org)

    match filter_type:
        case FilterType.reporting:
            return filters.reporting
        case FilterType.pay_per:
            return filters.pay_per
        case FilterType.subscriptions:
            return filters.subscriptions
        case FilterType.promo_codes:
            return filters.promo_codes
        case FilterType.locations:
            return filters.locations
        case FilterType.devices:
            return filters.devices
        case FilterType.sizes:
            return filters.sizes
        case FilterType.transactions:
            return filters.transactions
        case FilterType.users:
            return filters.users
        case FilterType.members:
            return filters.members
        case FilterType.groups:
            return filters.groups
        case FilterType.issues:
            return filters.issues
        case FilterType.notifications:
            return filters.notifications
        case FilterType.inventory:
            return filters.inventory
        case FilterType.product_groups:
            return filters.product_groups
        case FilterType.conditions:
            return filters.conditions
        case FilterType.reservations:
            return filters.reservations
        case FilterType.subscribers:
            return filters.subscribers
        case _:
            return None


async def update_filter(
    id_org: UUID,
    filter_type: FilterType,
    payload: dict,
):
    await create_default_filters(id_org)

    proc_filter_type = filter_type.value.replace("-", "_")

    query = (
        update(OrgFilters)
        .where(OrgFilters.id_org == id_org)
        .values(
            {
                proc_filter_type: json.dumps(payload),
            }
        )
        .returning(OrgFilters)
    )

    response = await db.session.execute(query)
    await db.session.commit()

    updated_filter = response.first()[proc_filter_type]

    return updated_filter
