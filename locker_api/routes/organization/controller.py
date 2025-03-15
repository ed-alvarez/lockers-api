import re
from math import ceil
from typing import Optional, List
from uuid import UUID

import aioboto3
from botocore.errorfactory import ClientError
from config import get_settings
from fastapi import HTTPException, UploadFile
from fastapi_async_sqlalchemy import db
from pydantic import conint
from sqlalchemy import and_, delete, desc, insert, or_, select, update, cast, VARCHAR
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import selectinload
from util.images import ImagesService


from ..developer.model import ApiKey
from ..device.model import Device
from ..event.model import Event
from ..location.model import Location
from ..member.controller import create_user
from ..member.model import MemberUpdate, Role, RoleType
from ..organization.model import LinkOrgUser
from ..price.model import Price
from ..settings.controller import create_settings
from ..settings.model import OrgSettings
from ..size.model import Size
from ..locker_wall.model import LockerWall
from ..memberships.model import Membership
from ..notifications.model import Notification
from ..reservations.model import Reservation

# from ..white_label.controller import partner_get_white_label
from ..white_label.model import WhiteLabel
from ..webhook.model import Webhook
from ..groups.model import Groups
from ..products.model import Product
from ..issue.model import Issue
from ..promo.model import Promo
from ..product_groups.model import ProductGroup
from ..product_tracking.product_tracking import ProductTracking
from ..conditions.model import Condition
from ..feedback.model import Feedback
from ..reports.model import Report
from ..filters.model import OrgFilters
from .model import Org, PaginatedOrgs, OrgFeatures


async def get_org_name(id_org: UUID):
    query = select(Org.name).where(Org.id == id_org)

    data = await db.session.execute(query)
    return data.scalar_one()  # raises NoResultFound


async def is_sub_org(target_org: UUID, parent_org: UUID) -> bool:
    """This function checks if the org is a sub-org of another org

    Args:
        id_org (UUID): the id of the org to check
        parent_org (UUID): the id of the parent org

    Returns:
        bool: True if the org is a sub-org, False otherwise
    """
    query = select(Org).where(Org.id == target_org)
    response = await db.session.execute(query)
    org: Optional[Org.Read] = response.scalar_one_or_none()
    if not org:
        return False

    if org.id_tenant is None:
        return False

    if str(org.id_tenant) == str(parent_org):
        return True

    # Recursively check if the org is a sub-org of the parent org
    return await is_sub_org(org.id_tenant, parent_org)


async def get_org_tree(id_org: UUID) -> list[UUID]:
    """Returns a list of orgs from the current org to the top most org"""
    orgs = []
    current_org = id_org
    while current_org:
        query = select(Org).where(Org.id == current_org)
        response = await db.session.execute(query)
        org: Optional[Org.Read] = response.scalar_one_or_none()
        if not org:
            break
        orgs.append(org.id)
        current_org = org.id_tenant
    return orgs


async def is_ojmar_org(id_org: UUID) -> bool:
    """
    Returns True if the `id_org` provided is Ojmar, or any sub-org of Ojmar

    This depends on the fact that Ojmar org's id is 68bdc743-2ae6-4c1a-87b2-98514e0f4487
    """
    ojmar_org_str = "68bdc743-2ae6-4c1a-87b2-98514e0f4487"
    # ojmar_org_str = "bc6647fb-90d8-4c79-87e9-9b6942383e4a"  #  testing
    if str(id_org) == ojmar_org_str:
        return True

    # Check if this is a child org of Ojmar
    return await is_sub_org(id_org, UUID(ojmar_org_str))


async def is_ups_org(id_org: UUID) -> bool:
    """
    Returns True if the `id_org` provided is UPS, or any sub-org of UPS just like
    function is_ojmar_org.

    This depends on the fact that UPS org's id is e4c6aef6-2a9a-46af-8611-ded972e661e8
    """
    ups_org_str = "e4c6aef6-2a9a-46af-8611-ded972e661e8"
    ups_test_org_str = "ca6235d5-3e61-49aa-94a5-feeb3eeb6a47"
    ups_testing_org_str = "0a128f61-50ec-427c-9ff7-b30905b98831"

    if (
        str(id_org) == ups_org_str
        or str(id_org) == ups_test_org_str
        or str(id_org) == ups_testing_org_str
    ):
        return True

    return False


async def get_org_messaging_service_sid(id_org: UUID):
    # Get Twilio Messaging Service SID by id_org. At the moment, this only
    # supports Ojmar and UPS orgs, for the rest, the default Twilio MS SID will
    # be returned
    if await is_ojmar_org(id_org):
        return get_settings().ojmar_messaging_service_sid
    if await is_ups_org(id_org):
        return get_settings().ups_messaging_service_sid

    return get_settings().twilio_messaging_service_sid


async def get_org_sendgrid_auth_sender(id_org: UUID):
    # Get Twilio SendGrid Mail sender by id_org. At the moment, this only
    # supports Ojmar and UPS orgs, for the rest, the default info@koloni.me
    # email will be used
    if await is_ojmar_org(id_org):
        return get_settings().twilio_sendgrid_ojmar_auth_sender
    if await is_ups_org(id_org):
        return get_settings().twilio_sendgrid_ups_auth_sender

    return get_settings().twilio_sendgrid_auth_sender


async def get_org_tree_bfs(id_org: UUID) -> list[UUID]:
    """Returns a list of orgs from the root org to all the sub orgs"""
    orgs = []
    queue = [id_org]

    while queue:
        current_org = queue.pop(0)
        orgs.append(current_org)

        query = select(Org.id).where(Org.id_tenant == current_org)
        response = await db.session.execute(query)
        sub_orgs = response.scalars().all()
        queue.extend(sub_orgs)

    return orgs


async def get_root_org(id_org: UUID) -> Optional[Org.Read]:
    query = select(Org).where(Org.id == id_org)
    response = await db.session.execute(query)

    org: Optional[Org.Read] = response.scalar_one_or_none()

    while org and org.id_tenant:
        query = select(Org).where(Org.id == org.id_tenant)
        response = await db.session.execute(query)
        org: Optional[Org.Read] = response.scalar_one_or_none()

    return org


async def public_get_org(name: str):
    query = select(Org).where(and_(Org.name == name.lower(), Org.active == True))  # noqa: E712

    data = await db.session.execute(query)

    org_dat = data.unique().scalar_one_or_none()  # raises NoResultFound
    if org_dat is None:
        # Handle the case where no event is found

        raise HTTPException(
            status_code=404,
            detail="No organization found with the provided name.",
        )

    # Select White label
    query = select(WhiteLabel).where(WhiteLabel.id_org == org_dat.id)
    data = await db.session.execute(query)
    org_wl = data.unique().scalar_one_or_none()

    org_st = await db.session.execute(
        select(OrgSettings).where(OrgSettings.id_org == org_dat.id)
    )
    org_settings = org_st.unique().scalar_one_or_none()

    root = await get_root_org(org_dat.id)

    return {
        "id": org_dat.id,
        "name": org_dat.name,
        "app_logo": org_wl.app_logo if org_wl else None,
        "client_id": org_dat.client_id,
        "user_pool": org_dat.user_pool,
        "white_label": org_wl,
        "created_at": org_dat.created_at,
        "rental_mode": org_dat.rental_mode,
        "storage_mode": org_dat.storage_mode,
        "delivery_mode": org_dat.delivery_mode,
        "service_mode": org_dat.service_mode,
        "vending_mode": org_dat.vending_mode,
        "support_email": org_settings.default_support_email if org_settings else None,
        "support_phone": org_settings.default_support_phone if org_settings else None,
        "stripe_enabled": True if org_dat.stripe_account_id else False,
        "super_tenant": org_dat.super_tenant,
        "oem_logo": root.white_label.app_logo,
    }


async def get_org(id_org: UUID) -> Org.Read:
    query = select(Org).where(Org.id == id_org)

    data = await db.session.execute(query)
    # Attempting to retrieve the organization data
    try:
        org_data = data.scalar_one()  # raises NoResultFound

    except NoResultFound:
        raise HTTPException(status_code=404, detail="Organization not found")

    org = Org.Read.parse_obj(org_data)
    org.stripe_enabled = True if org_data.stripe_account_id else False

    root = await get_root_org(org.id)
    if root and root.white_label:
        org.oem_logo = root.white_label.app_logo

    return org


async def get_user_pool_by_api_key(api_key: str):
    query = (
        select(Org.user_pool).join(ApiKey).where(ApiKey.key == api_key, ApiKey.active)
    )

    response = await db.session.execute(query)

    data = response.scalar_one_or_none()

    if not data:
        raise HTTPException(status_code=403, detail="API key not found or inactive")

    return data


async def get_org_id_by_api_key(api_key: str):
    query = select(ApiKey.id_org).where(ApiKey.key == api_key, ApiKey.active)

    response = await db.session.execute(query)

    data = response.scalar_one_or_none()

    if not data:
        raise HTTPException(status_code=403, detail="API key not found or inactive")

    return data


async def get_org_id_by_pin_code(
    id_org: str, pin_code: str, with_le_role: bool = False
):
    query = select(Role).where(
        and_(Role.id_org == str(id_org), Role.pin_code == pin_code)
    )

    response = await db.session.execute(query)

    data = response.scalars().first()

    if not data:
        raise HTTPException(status_code=403, detail="Invalid pin code")

    if with_le_role:
        return data.role

    return data.id_org


async def get_org_id_by_user_pool(user_pool: str):
    query = select(Org.id).where(Org.user_pool == user_pool)

    data = await db.session.execute(query)
    return data.scalar_one()  # raises NoResultFound


async def get_orgs(
    current_org: UUID,
    page: conint(gt=0),
    size: conint(gt=0),
    expand: Optional[bool] = False,
    search: Optional[str] = None,
    active: Optional[bool] = None,
):
    query = (
        select(Org)
        .where(
            or_(Org.id == current_org, Org.id_tenant == current_org),
        )
        .order_by(
            desc(Org.created_at)
        )  # New line: sort by 'created_at' in descending order
        .limit(size)
        .offset((page - 1) * size)
    )

    if search:
        query = query.filter(
            or_(
                cast(Org.name, VARCHAR).ilike(f"%{search}%"),
                cast(Org.user_pool, VARCHAR).ilike(f"%{search}%"),
                cast(Org.client_id, VARCHAR).ilike(f"%{search}%"),
                cast(Org.stripe_account_id, VARCHAR).ilike(f"%{search}%"),
            )
        )

    if active:
        query = query.where(Org.active == active)

    count = select(Org).where(or_(Org.id == current_org, Org.id_tenant == current_org))

    data = await db.session.execute(query)
    total = await db.session.execute(count)

    organizations = data.scalars().all()
    organizations = [Org.Read.parse_obj(org) for org in organizations]

    if expand:
        await include_tree(organizations)

    total_count = len(total.all())

    return PaginatedOrgs(
        items=organizations,
        total=total_count,
        pages=ceil(total_count / size),
    )


async def include_tree(orgs: List[Org.Read]):
    for org in orgs:
        query = select(Org).where(Org.id_tenant == org.id)
        data = await db.session.execute(query)
        rows = data.scalars().all()
        sub_orgs = [Org.Read.parse_obj(row) for row in rows]

        if len(sub_orgs) > 0:
            org.sub_orgs = sub_orgs
            await include_tree(sub_orgs)


async def create_org(
    member: MemberUpdate,
    settings: OrgSettings.Write,
    email: str,
    white_label: WhiteLabel.Write,
    features: OrgFeatures,
    id_tenant: UUID,
    images_service: ImagesService,
    image: Optional[UploadFile] = None,
):
    check_email = re.match(
        r"([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+",
        email,
    )

    if not check_email:
        raise HTTPException(
            status_code=400,
            detail="Invalid email",
        )

    # check if the org is a tenant
    data = await db.session.execute(select(Org).where(Org.id == id_tenant))

    if not data.scalars().first().super_tenant:
        raise HTTPException(
            status_code=403,
            detail=f"Org with id {id_tenant} is not a super-tenant",
        )

    """Creates a new user pool for the org"""
    app_name = " ".join(white_label.app_name.split())  # remove duplicate spaces
    org_name = app_name.lower().replace(" ", "-")  # replace spaces with dashes

    """Creates a new org in the database"""
    new_org = Org(
        name=org_name,
        active=True,
        id_tenant=id_tenant,
        rental_mode=features.rental_mode,
        storage_mode=features.storage_mode,
        delivery_mode=features.delivery_mode,
        service_mode=features.service_mode,
        vending_mode=features.vending_mode,
        linka_hardware=features.linka_hardware,
        ojmar_hardware=features.ojmar_hardware,
        gantner_hardware=features.gantner_hardware,
        harbor_hardware=features.harbor_hardware,
        dclock_hardware=features.dclock_hardware,
        spintly_hardware=features.spintly_hardware,
        super_tenant=features.super_tenant,
        lite_app_enabled=features.lite_app_enabled,
        pricing=features.pricing,
        product=features.product,
        notifications=features.notifications,
        multi_tenant=features.multi_tenant,
        toolbox=features.toolbox,
    )
    query = insert(Org).values(**new_org.dict()).returning(Org)

    response = await db.session.execute(query)
    await db.session.commit()

    new_org = response.all().pop()
    new_id_org = new_org[0]

    """Creates a new white label for the org"""
    white_label.organization_owner = email
    try:
        new_org_wl = await create_white_label(
            image, images_service, white_label, new_id_org
        )
    except Exception as e:
        query = delete(Org).where(Org.id == new_id_org)
        await db.session.execute(query)
        await db.session.commit()

        raise HTTPException(
            status_code=400,
            detail=f"Failed to create white label: {e}",
        )

    """Updates the org with Cognito user pool and client id"""
    try:
        user_pool = await create_user_pool(
            org_name=org_name,
            white_label=new_org_wl,
        )
    except ClientError as e:
        query_wl = delete(WhiteLabel).where(WhiteLabel.id == new_org_wl.id)
        query = delete(Org).where(Org.id == new_id_org)

        await delete_white_label(new_org_wl.id, images_service)
        await db.session.execute(query_wl)
        await db.session.execute(query)
        await db.session.commit()

        raise HTTPException(
            status_code=400,
            detail=f"Failed to create organization user pool: {e}",
        )

    user_pool_client = await create_user_pool_client(
        user_pool_id=user_pool["UserPool"]["Id"]
    )

    update_query = (
        update(Org)
        .where(Org.id == new_id_org)
        .values(
            user_pool=user_pool["UserPool"]["Id"],
            client_id=user_pool_client["UserPoolClient"]["ClientId"],
        )
        .returning(Org)
    )

    await db.session.execute(update_query)
    await db.session.commit()

    org_name = await get_org_name(new_id_org)
    invoice_pre = re.sub(r"[aeiouAEIOU]", "", org_name).replace("-", "")[:3].upper()
    settings.invoice_prefix = invoice_pre

    await create_settings(id_org=new_id_org, settings=settings)

    member.role = RoleType.admin
    new_member = await create_user(
        user_pool_id=user_pool["UserPool"]["Id"],
        id_org=new_id_org,
        email=email,
        member=member,
    )

    await add_helpdesk_account(user_pool_id=user_pool["UserPool"]["Id"])

    """Creates subdomain login in Route53"""
    await create_record(org_name=org_name)

    # Add this block of code to fetch the newly created Org with its associated white_label
    org_with_wl_query = (
        select(Org).where(Org.id == new_id_org).options(selectinload(Org.white_label))
    )
    result = await db.session.execute(org_with_wl_query)
    updated_org_with_wl = result.scalars().first()

    return {
        "org_data": updated_org_with_wl,
        "first_name": new_member.first_name,
        "last_name": new_member.last_name,
    }


async def patch_org_features(
    id_org: UUID,
    features: OrgFeatures,
    current_org: UUID,
) -> OrgFeatures:
    query = (
        update(Org)
        .where(
            or_(
                and_(Org.id == id_org, Org.id_tenant == current_org),
                Org.id == id_org,
            )
        )
        .values(
            **features.dict(exclude_unset=True),
        )
        .returning(Org)
    )

    response = await db.session.execute(query)
    await db.session.commit()  # raises IntegrityError

    data = response.all().pop()

    return OrgFeatures.parse_obj(data)


async def create_white_label(
    image: Optional[UploadFile],
    images_service: ImagesService,
    white_label: WhiteLabel.Write,
    id_org: UUID,
):
    try:
        image_data = await images_service.upload(id_org, image) if image else None
    except Exception as e:
        raise Exception(f"Failed to upload image: {e}")

    image_url = image_data["url"] if image_data else None
    image_key = image_data["key"] if image_data else None

    default_logo = "https://assets.website-files.com/61f7e37730d06c4a05d2c4f3/62c640ed55a520a3d21d9b61_koloni-logo-black%207-p-500.png"

    insert_query = (
        insert(WhiteLabel)
        .values(
            **white_label.dict(),
            app_logo=image_url if image else default_logo,
            image_key=image_key,
            id_org=id_org,
        )
        .returning(WhiteLabel)
    )

    response = await db.session.execute(insert_query)
    await db.session.commit()  # raises IntegrityError

    return response.all().pop()


async def delete_white_label(
    id_: UUID,
    images_service: ImagesService,
):
    # Find the white label to delete
    data = await db.session.execute(select(WhiteLabel).where(WhiteLabel.id == id_))
    white_label = data.scalars().first()

    if white_label is None:
        raise HTTPException(
            status_code=404,
            detail="WhiteLabel not found",
        )

    image_key = white_label.image_key

    # Delete the white label from the database
    delete_query = delete(WhiteLabel).where(WhiteLabel.id == id_)
    await db.session.execute(delete_query)
    await db.session.commit()

    # Delete the image from S3
    if image_key:
        try:
            await images_service.delete(image_key)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete image from S3: {e}",
            )

    return {"message": f"WhiteLabel {id_} deleted successfully"}


async def delete_org_settings(id_org: UUID):
    query = delete(OrgSettings).where(OrgSettings.id_org == id_org)
    await db.session.execute(query)
    await db.session.commit()


async def restore_org(id_org: UUID, current_org: UUID):
    # check if org exists
    data_org = await db.session.execute(
        select(Org).where(Org.id == id_org, Org.id_tenant == current_org)
    )
    org = data_org.scalars().first()

    if not org:
        raise HTTPException(
            status_code=404,
            detail=f"Org with id {id_org} was not found",
        )

    # Revert archived
    query = (
        update(Org)
        .where(Org.id == id_org, Org.id_tenant == current_org)
        .values(active=True)
    )
    await db.session.execute(query)
    await db.session.commit()

    return {"detail": "Organization restored successfully"}


async def archive_org(id_org: UUID, current_org: UUID):
    # check if the org to be deleted exists
    data_org = await db.session.execute(
        select(Org).where(Org.id == id_org, Org.id_tenant == current_org)
    )
    org = data_org.scalars().first()

    if not org:
        raise HTTPException(
            status_code=404,
            detail=f"Org with id {id_org} was not found",
        )

    # Conserving the user pool and route
    # Delete org's user pool
    # await delete_user_pool(user_pool_id=org.user_pool)
    # Delete Route53 record
    # await delete_record(org_name=org.name)

    # Archive org:
    query = update(Org).where(Org.id == id_org).values(active=False)

    await db.session.execute(query)
    await db.session.commit()

    return {"detail": "Organization archived successfully"}


def load_email_template(white_label: WhiteLabel.Read, org_name: str):
    from pathlib import Path

    ROOT_DIR = Path(__file__).parent
    psub_file = ROOT_DIR / "email_message.html"

    with open(psub_file) as f:
        contents = f.read()
        default_logo = "https://assets.website-files.com/61f7e37730d06c4a05d2c4f3/62c640ed55a520a3d21d9b61_koloni-logo-black%207-p-500.png"

        return (
            contents.replace("{{org_name}}", white_label.app_name)
            .replace(
                "{{org_logo}}",
                white_label.app_logo if white_label.app_logo else default_logo,
            )
            .replace("{{org_url}}", f"https://{org_name}.koloni.io")
            .replace("{{app_name}}", white_label.app_name)
        )


async def create_user_pool(org_name: str, white_label: WhiteLabel.Read):
    client = aioboto3.Session()
    async with client.client(
        "cognito-idp",
        aws_access_key_id=get_settings().aws_access_key_id,
        aws_secret_access_key=get_settings().aws_secret_access_key,
        region_name=get_settings().aws_region,
    ) as cognito:
        user_pool = await cognito.create_user_pool(
            PoolName=org_name,
            AutoVerifiedAttributes=["email"],
            MfaConfiguration="OFF",
            UsernameAttributes=["email"],
            AdminCreateUserConfig={
                "AllowAdminCreateUserOnly": True,
                "InviteMessageTemplate": {
                    "EmailMessage": load_email_template(white_label, org_name)
                },
            },
            AccountRecoverySetting={
                "RecoveryMechanisms": [
                    {"Priority": 1, "Name": "verified_email"},
                ]
            },
        )

    return user_pool


async def create_record(org_name: str):
    client = aioboto3.Session()
    async with client.client(
        "route53",
        aws_access_key_id=get_settings().aws_access_key_id,
        aws_secret_access_key=get_settings().aws_secret_access_key,
        region_name=get_settings().aws_region,
    ) as route53:
        await route53.change_resource_record_sets(
            HostedZoneId="Z0869207DWO6918O72X6",  # koloni.io
            ChangeBatch={
                "Comment": "Create Organization",
                "Changes": [
                    {
                        "Action": "CREATE",
                        "ResourceRecordSet": {
                            "Name": f"{org_name}.koloni.io",
                            "Type": "CNAME",
                            "TTL": 300,
                            "ResourceRecords": [
                                {"Value": f"{get_settings().cluster_url}"},
                            ],
                        },
                    },
                ],
            },
        )

        return f"{org_name}.koloni.io"


async def delete_record(org_name: str):
    client = aioboto3.Session()
    async with client.client(
        "route53",
        aws_access_key_id=get_settings().aws_access_key_id,
        aws_secret_access_key=get_settings().aws_secret_access_key,
        region_name=get_settings().aws_region,
    ) as route53:
        try:
            await route53.change_resource_record_sets(
                HostedZoneId="Z0869207DWO6918O72X6",  # koloni.io
                ChangeBatch={
                    "Comment": "Delete Organization",
                    "Changes": [
                        {
                            "Action": "DELETE",
                            "ResourceRecordSet": {
                                "Name": f"{org_name}.koloni.io",
                                "Type": "CNAME",
                                "TTL": 300,
                                "ResourceRecords": [
                                    {"Value": f"{get_settings().cluster_url}"},
                                ],
                            },
                        },
                    ],
                },
            )
        except Exception as e:
            print(f"Failed to delete CNAME records for org: {e}. Ignoring...")
            pass

        return f"{org_name}.koloni.io"


async def add_helpdesk_account(user_pool_id: str):
    client = aioboto3.Session()

    h_email = "helpdesk@koloni.me"
    h_password = "c3kUt9d@upWBraT97n2jc"

    async with client.client(
        "cognito-idp",
        aws_access_key_id=get_settings().aws_access_key_id,
        aws_secret_access_key=get_settings().aws_secret_access_key,
        region_name=get_settings().aws_region,
    ) as cognito:
        await cognito.admin_create_user(
            UserPoolId=user_pool_id,
            Username=h_email,
            TemporaryPassword=h_password,
            UserAttributes=[
                {"Name": "email", "Value": h_email},
                {"Name": "email_verified", "Value": "true"},
            ],
        )

        await cognito.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=h_email,
            Password=h_password,
            Permanent=True,
        )


async def add_user(user_pool_id: str, email: str):
    client = aioboto3.Session()
    async with client.client(
        "cognito-idp",
        aws_access_key_id=get_settings().aws_access_key_id,
        aws_secret_access_key=get_settings().aws_secret_access_key,
        region_name=get_settings().aws_region,
    ) as cognito:
        try:
            await cognito.admin_create_user(
                UserPoolId=user_pool_id,
                Username=email,
                UserAttributes=[
                    {"Name": "email", "Value": email},
                ],
            )
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to add self to user pool, {e}",
            )


async def create_user_pool_client(user_pool_id: str):
    client = aioboto3.Session()
    async with client.client(
        "cognito-idp",
        aws_access_key_id=get_settings().aws_access_key_id,
        aws_secret_access_key=get_settings().aws_secret_access_key,
        region_name=get_settings().aws_region,
    ) as cognito:
        try:
            user_pool_client = await cognito.create_user_pool_client(
                UserPoolId=user_pool_id,
                ClientName="koloni-react",
                GenerateSecret=False,
                RefreshTokenValidity=30,
                AccessTokenValidity=60,
                IdTokenValidity=60,
                TokenValidityUnits={
                    "AccessToken": "minutes",
                    "IdToken": "minutes",
                    "RefreshToken": "days",
                },
                ExplicitAuthFlows=[
                    "ALLOW_ADMIN_USER_PASSWORD_AUTH",
                    "ALLOW_REFRESH_TOKEN_AUTH",
                    "ALLOW_CUSTOM_AUTH",
                    "ALLOW_USER_SRP_AUTH",
                    "ALLOW_USER_PASSWORD_AUTH",
                ],
                SupportedIdentityProviders=[
                    "COGNITO",
                ],
                CallbackURLs=[
                    "http://localhost",
                ],
                PreventUserExistenceErrors="ENABLED",
                AllowedOAuthFlows=["implicit", "code"],
                AllowedOAuthScopes=[
                    "openid",
                    "email",
                    "aws.cognito.signin.user.admin",
                ],
            )
        except Exception as e:
            await cognito.delete_user_pool(UserPoolId=user_pool_id)
            raise HTTPException(
                status_code=400,
                detail=f"Failed to create user pool client for org, {e}",
            )

    return user_pool_client


async def delete_org_resources(id_org: UUID):
    query = delete(Issue).where(Issue.id_org == id_org)
    await db.session.execute(query)
    await db.session.commit()

    query = delete(OrgSettings).where(OrgSettings.id_org == id_org)
    await db.session.execute(query)

    query = delete(OrgFilters).where(OrgFilters.id_org == id_org)
    await db.session.execute(query)
    await db.session.commit()

    query = delete(Event).where(Event.id_org == id_org)
    await db.session.execute(query)
    await db.session.commit()

    query = delete(Reservation).where(Reservation.id_org == id_org)
    await db.session.execute(query)
    await db.session.commit()

    query = delete(Notification).where(Notification.id_org == id_org)
    await db.session.execute(query)
    await db.session.commit()

    query = delete(ProductTracking).where(ProductTracking.id_org == id_org)
    await db.session.execute(query)
    await db.session.commit()

    query = delete(Device).where(Device.id_org == id_org)
    await db.session.execute(query)
    await db.session.commit()

    query = delete(LockerWall).where(LockerWall.id_org == id_org)
    await db.session.execute(query)
    await db.session.commit()

    query = delete(Price).where(Price.id_org == id_org)
    await db.session.execute(query)
    await db.session.commit()

    query = delete(Promo).where(Promo.id_org == id_org)
    await db.session.execute(query)
    await db.session.commit()

    query = delete(Size).where(Size.id_org == id_org)
    await db.session.execute(query)
    await db.session.commit()

    query = delete(LinkOrgUser).where(LinkOrgUser.id_org == id_org)
    await db.session.execute(query)
    await db.session.commit()

    query = delete(Location).where(Location.id_org == id_org)
    await db.session.execute(query)
    await db.session.commit()

    query = delete(Membership).where(Membership.id_org == id_org)
    await db.session.execute(query)
    await db.session.commit()

    query = delete(Role).where(Role.id_org == id_org)
    await db.session.execute(query)
    await db.session.commit()

    query = delete(ApiKey).where(ApiKey.id_org == id_org)
    await db.session.execute(query)
    await db.session.commit()

    query = delete(Webhook).where(Webhook.id_org == id_org)
    await db.session.execute(query)
    await db.session.commit()

    query = delete(Groups).where(Groups.id_org == id_org)
    await db.session.execute(query)
    await db.session.commit()

    query = delete(Product).where(Product.id_org == id_org)
    await db.session.execute(query)
    await db.session.commit()

    query = delete(ProductGroup).where(ProductGroup.id_org == id_org)
    await db.session.execute(query)
    await db.session.commit()

    query = delete(Condition).where(Condition.id_org == id_org)
    await db.session.execute(query)
    await db.session.commit()

    query = delete(Feedback).where(Feedback.id_org == id_org)
    await db.session.execute(query)
    await db.session.commit()

    query = delete(Report).where(Report.id_org == id_org)
    await db.session.execute(query)
    await db.session.commit()

    query = delete(WhiteLabel).where(WhiteLabel.id_org == id_org)
    await db.session.execute(query)
    await db.session.commit()


async def delete_user_pool(user_pool_id: str):
    client = aioboto3.Session()
    async with client.client(
        "cognito-idp",
        aws_access_key_id=get_settings().aws_access_key_id,
        aws_secret_access_key=get_settings().aws_secret_access_key,
        region_name=get_settings().aws_region,
    ) as cognito:
        try:
            await cognito.delete_user_pool(UserPoolId=user_pool_id)
        except Exception as e:
            # raise HTTPException(
            #     status_code=400,
            #     detail=f"Failed to delete user pool for org, {e}",
            # )
            # Ignore the error since this could mean
            # that the user pool was already deleted
            print(f"Failed to delete user pool for org, {e}. Ignoring...")
            pass

    return True


async def get_org_by_user_pool(user_pool: str) -> Org.Read:
    query = select(Org).where(Org.user_pool == user_pool)

    data = await db.session.execute(query)
    return data.scalar_one()  # raises NoResultFound


async def mobile_get_org(id_org: UUID):
    query = select(Org).where(Org.id == id_org)

    data = await db.session.execute(query)
    try:
        org_data = data.scalar_one()  # raises NoResultFound

        return org_data
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Organization not found")


async def mobile_get_orgs(
    user_pool: str,
    page: conint(gt=0),
    size: conint(gt=0),
):
    query_tenant = select(Org.id).where(Org.user_pool == user_pool)
    data_tenant = await db.session.execute(query_tenant)

    try:
        id_tenant = data_tenant.scalar_one()
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail=f"Org with user pool {user_pool} was not found",
        )

    query = (
        select(Org)
        .where(or_(Org.id == id_tenant, Org.id_tenant == id_tenant))
        .offset((page - 1) * size)
        .limit(size)
    )

    count = select(Org).where(or_(Org.id == id_tenant, Org.id_tenant == id_tenant))

    data = await db.session.execute(query)
    total = await db.session.execute(count)

    total_count = len(total.all())

    return PaginatedOrgs(
        items=data.scalars().all(),
        total=total_count,
        pages=ceil(total_count / size),
    )
