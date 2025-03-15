import asyncio
import csv
from uuid import UUID

from config import get_settings
from fastapi import HTTPException, UploadFile
from pydantic import BaseModel


async def process_csv_upload(
    id_org: UUID,
    file: UploadFile,
    write_model: BaseModel,
    create_func: callable,
    update_func: callable,
):
    """CSV Upload Processor

    Args:
        id_org (UUID): id of the organization
        file (UploadFile): CSV file to be processed
        write_model (BaseModel): Model to be used for parsing the CSV rows
        create_func (callable): function to be used for creating the records
        update_func (callable): function to be used for updating the records

    the callback functions should have the following signature:
        async def create_func(id_org, model)
        async def update_func(id_org, model, id_resource)

    Raises:
        HTTPException: If the number of records in the CSV exceeds the limit

    Returns:
        list[dict]: results of the CSV processing
    """

    results = []

    # Read and decode the CSV contents
    contents = await file.read()
    csv_content = contents.decode()

    # Use DictReader as it allows to directly map CSV headers to dictionary keys
    csv_reader = csv.DictReader(csv_content.splitlines())

    # Check for limits on the number of records
    if sum(1 for _ in csv_reader) > get_settings().MAX_CSV_RECORDS:
        raise HTTPException(
            status_code=400,
            detail=f"Too many records. Limit is {get_settings().MAX_CSV_RECORDS} per upload.",
        )

    # Resetting the CSV reader cursor to the start after counting the rows
    csv_reader = csv.DictReader(csv_content.splitlines())

    for row in csv_reader:
        try:
            # Convert only the specified fields to boolean, or None
            data = {k: to_bool(v) if v != "" else None for k, v in row.items()}

            # Parsing each CSV row into Device.Write type
            model = write_model(**data)
            if row.get("id"):
                # If the row has an id, we assume it's an update
                id_resource = UUID(row.get("id"))
                # running the update function

                result = await asyncio.wait_for(
                    update_func(id_org, model, id_resource),
                    get_settings().TIMEOUT_SECONDS,
                )
                # getting the name from the result, and the error message if any
                results.append({"name": row.get("name"), "detail": result})
                continue

            # running the create function
            result = await asyncio.wait_for(
                create_func(id_org, model),
                get_settings().TIMEOUT_SECONDS,
            )
            # getting the name from the result, and the error message if any
            results.append({"name": row.get("name"), "detail": result})
        except asyncio.TimeoutError:
            results.append({"name": row.get("name"), "detail": "Timeout Error"})
        except Exception as e:
            # Append Any error message and None for the device.
            results.append({"name": row.get("name"), "detail": str(e)})

    return results


def to_bool(value: str) -> bool | str:
    """Converts a string to a boolean

    Args:
        value (str): value to be converted

    Returns:
        bool: True if the string is 'true', False if the string is 'false', otherwise the original value
    """
    true_values = ["true", "t", "yes", "y", "1"]
    false_values = ["false", "f", "no", "n", "0"]

    if isinstance(value, str):
        lower_value = value.lower()
        if lower_value in true_values:
            return True
        if lower_value in false_values:
            return False

    return value
