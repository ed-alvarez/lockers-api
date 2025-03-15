import base64
import requests
import json

from fastapi import UploadFile

from config import get_settings


async def packagex_scan_request(label_image: UploadFile):
    # Read file contents
    file_contents = await label_image.read()

    # Convert content to base64
    encoded_string = base64.b64encode(file_contents).decode("utf-8")

    # Construct the base64 image URL
    encoded_image = f"data:image/jpeg;base64,{encoded_string}"

    # PackageX Scan API configuration:
    headers = {
        "PX-API-KEY": get_settings().packagex_api_key,
        "Content-Type": "application/json",
    }

    scan_body = json.dumps(
        {
            "image_url": encoded_image,
            "type": "shipping_label",
            "barcode_values": [],
            "location_id": None,
            "metadata": {},
            "options": {
                "parse_addresses": True,
                "match_contacts": True,
            },
        }
    )

    # Making the POST request
    response = requests.post(
        f"{get_settings().packagex_api_url}/v1/scans", headers=headers, data=scan_body
    )

    return response.json()
