from typing import Optional
from uuid import UUID

from auth.cognito import get_current_org, get_permission
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import conint
from util.csv import process_csv_upload

from ..member.model import RoleType
from . import controller
from .model import PaginatedReservation, Reservation, ReservationSettings
from util.response import BasicResponse

router = APIRouter(tags=["reservations"])


@router.get(
    "/partner/reservations",
    response_model=PaginatedReservation | Reservation.Read,
    response_model_exclude_none=True,
)
async def get_reservations(
    page: conint(gt=0) = 1,
    size: conint(gt=0) = 50,
    id_reservation: Optional[UUID] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    search: Optional[str] = None,
    id_org: UUID = Depends(get_current_org),
):
    """
    # Usage:
    ### * Get all reservations: `/partner/reservations?page=1&size=50`
    ### * Search reservations: `/partner/reservations?search=Locker`
    ### * Get a single reservation: `/partner/reservations?id_reservation=UUID`
    ### * Get a single reservation by key: `/partner/reservations?key=from_time&value=13:00`

    | param | type | description | return type
    | --- | --- | --- | --- |
    | id_reservation | UUID | The unique ID of a reservation | Single |
    | key | str | Parameter to look for a single reservation | Single |
    | value | str | Value of the "key" parameter | Single |
    | search | str | Search | List |
    """

    return await controller.get_reservations(
        page, size, id_org, id_reservation, key, value, search
    )


@router.post("/partner/reservations", response_model=Reservation.Read)
async def create_reservation(
    reservation: Reservation.Write,
    id_org: UUID = Depends(get_current_org),
    role: RoleType = Depends(get_permission),
):
    """
    # Usage:
    ### * Create a reservation: `/partner/reservations`
    """

    if role not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to create a reservation",
        )

    return await controller.create_reservation(reservation, id_org)


@router.post("/partner/reservations/csv")
async def upload_reservations_csv(
    file: UploadFile = File(...),
    permission: RoleType = Depends(get_permission),
    id_org: UUID = Depends(get_current_org),
):
    """
    Endpoint to upload and process CSV files containing reservation data.
    """

    # Logging at the start
    # Logging input objects

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    if file.filename.split(".")[-1].lower() != "csv":
        # Logging of ERROR
        raise HTTPException(status_code=400, detail="File type must be CSV")

    result = await process_csv_upload(
        id_org,
        file,
        Reservation.WriteCSV,
        controller.create_reservations_csv,
        controller.update_reservations_csv,
    )

    return result


@router.post("/partner/reservations/batch", response_model=BasicResponse)
async def create_reservations_batch(
    reservation: Reservation.Batch,
    id_org: UUID = Depends(get_current_org),
    role: RoleType = Depends(get_permission),
):
    """
    # Usage:
    ### * Create multiple reservations: `/partner/reservations/batch`
    """

    if role not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to create a reservation",
        )

    return await controller.create_reservations_batch(reservation, id_org)


@router.put("/partner/reservations/{id_reservation}", response_model=Reservation.Read)
async def update_reservation(
    id_reservation: UUID,
    reservation: Reservation.Write,
    id_org: UUID = Depends(get_current_org),
    role: RoleType = Depends(get_permission),
):
    """
    # Usage:
    ### * Update a reservation: `/partner/reservations/:id_reservation`
    """

    if role not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to update a reservation",
        )

    return await controller.update_reservation(id_reservation, reservation, id_org)


@router.delete(
    "/partner/reservations/{id_reservation}", response_model=Reservation.Read
)
async def delete_reservation(
    id_reservation: UUID,
    id_org: UUID = Depends(get_current_org),
    role: RoleType = Depends(get_permission),
):
    """
    # Usage:
    ### * Delete a reservation: `/partner/reservations/:id_reservation`
    """

    if role not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to delete a reservation",
        )

    return await controller.delete_reservation(id_reservation, id_org)


@router.delete("/partner/reservations", response_model=BasicResponse)
async def delete_reservations(
    id_reservations: list[UUID],
    id_org: UUID = Depends(get_current_org),
    role: RoleType = Depends(get_permission),
):
    """
    # Usage:
    ### * Delete multiple reservations: `/partner/reservations`
    """

    if role not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to delete reservations",
        )

    return await controller.delete_reservations(id_reservations, id_org)


@router.get("/partner/reservation-settings", response_model=ReservationSettings.Read)
async def get_reservation_settings(
    id_org: UUID = Depends(get_current_org), role: RoleType = Depends(get_permission)
):
    if role not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to delete reservations",
        )

    return await controller.get_reservation_settings(id_org)


@router.post("/partner/reservation-settings", response_model=ReservationSettings.Read)
async def create_reservation_settings(
    reservation_settings: ReservationSettings.Write,
    id_org: UUID = Depends(get_current_org),
    role: RoleType = Depends(get_permission),
):
    if role not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to delete reservations",
        )

    return await controller.create_reservation_settings(id_org, reservation_settings)


@router.put("/partner/reservation-settings", response_model=ReservationSettings.Read)
async def update_reservation_settings(
    reservation_settings: ReservationSettings.Write,
    id_org: UUID = Depends(get_current_org),
    role: RoleType = Depends(get_permission),
):
    if role not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to delete reservations",
        )

    return await controller.update_reservation_settings(id_org, reservation_settings)
