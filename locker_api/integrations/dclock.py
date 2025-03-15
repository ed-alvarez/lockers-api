import base64
import json
import time

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from fastapi import HTTPException

APP_ID = "df568d3b4616422caa0868b7b8876081"
PRIVATE_KEY = """
-----BEGIN RSA PRIVATE KEY-----
MIICdgIBADANBgkqhkiG9w0BAQEFAASCAmAwggJcAgEAAoGBAJtzpqJHCySAlNSHtltrDPYPPDw8BPu7IspSPbWR0blMhPTIIfGtYKy8jI0tcHP6+3/1zkm/XAi/5pXwXb+0NswF+vrmGw3TiC2YW6IdY6j5EDk6ZQxJNy+ChL9HfOWRGeRZRoPfdUf7hCcvnmDlhwHC/SMhIEDCHIYbJiz82sWzAgMBAAECgYBJxBCPsvyznpyBWcEMEnl9De+8eZK3za6NqYcE8SQ/NPNmoM2SvH5CmdpsZ+KT9sZ/iyoPztGiiUWnYv9pp9/UJZ8NBhC5v9t4VKygKKWXeBHE2FoWk05gnT1iLI3CxnaTnEnjYsWdZf3N9Ax5/HUBrEra2JRSv+DDA5IeKHGmOQJBAM02bRlK0CFjHl55kyrlHqMrnfCzmoFNOIPnGjdrsDqSeDWw9Wn7UKwhzqRDkEv+WNPboU9jk9PoYiUGdIbWvK0CQQDB7Iv62PwTWhyZ/2O7d4i/5EDaQpiQ1/7Z0d0fJfuOrM9/ZbdQ5Pgxst6bt0pS1Mcu9KrgNQNcyxqZYjX5eHffAkAZiD4GuZIvtT9gDcxLt/oZ3yFlg1Mj51Gyx5wxbQqeHv8p3vyJ1STyZbpqIaXgbqLqqRbm48LOyMj9RlJVPH55AkA+LjD8MBMzyVMedetusvdgQDojQfNVjkyjX019rVop93NZMC5FfAWxOd9zIqRsRtnPTphz58u6N03CHOGdqmkVAkEAmL5FCuVVyOHS8CaQZL9i7jKoV8u/wOTXAmiupVleh0Esdiy0nNyfmu3tKQS/j9MoWSRBQgPm4xhVjg5dPy9BFQ==
-----END RSA PRIVATE KEY-----
"""


def sign_dclock_json_data(data):
    # Deserialize the private key from a string
    private_key_bytes = PRIVATE_KEY.encode("utf-8")
    private_key = serialization.load_pem_private_key(private_key_bytes, password=None)

    # Milliseconds
    timestamp = int(round(time.time() * 1000))

    # Sign the data using the private key
    signature = private_key.sign(
        (APP_ID + data + str(timestamp)).encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )

    # Encode the signature in Base64
    signature_base64 = base64.b64encode(signature).decode("utf-8")

    return {
        "sign": signature_base64,
        "timestamp": timestamp,
    }


# Gets all locks in one box (locker wall)
async def query_box(terminal_no: str):
    # Example terminal number: DC21071701247878
    data_to_sign = json.dumps({"terminalNo": terminal_no})
    signature = sign_dclock_json_data(data_to_sign)

    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(
                url="https://account.dclockers.com/openplatform/v1/device/queryBox",
                headers={
                    "Content-Type": "application/json",
                },
                json={
                    "sign": signature["sign"],
                    "data": data_to_sign,
                    "appId": "df568d3b4616422caa0868b7b8876081",
                    "timestamp": signature["timestamp"],
                },
            )
        except Exception as e:
            print(e)
            raise HTTPException(
                status_code=400,
                detail=f"DClock API failed to query box {terminal_no}. Communication with box failed",
            )

        res_data = res.json()

        print(res_data)

        if res_data["code"] != 200:
            raise HTTPException(
                status_code=400,
                detail=f"DClock API failed to query box {terminal_no}. Error code {res.status_code}",
            )

        return res.json()["data"]


# Unlocks a single box (locker)
async def remote_open_box(terminal_no: str, box_no: str):
    # Example terminal number: DC21071701247878
    data_to_sign = json.dumps({"terminalNo": terminal_no, "boxNo": box_no})
    signature = sign_dclock_json_data(data_to_sign)

    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(
                url="https://account.dclockers.com/openplatform/v1/device/remoteOpenBox",
                headers={
                    "Content-Type": "application/json",
                },
                json={
                    "sign": signature["sign"],
                    "data": data_to_sign,
                    "appId": "df568d3b4616422caa0868b7b8876081",
                    "timestamp": signature["timestamp"],
                },
            )
        except Exception as e:
            print(e)
            raise HTTPException(
                status_code=400,
                detail=f"DClock API failed to unlock box {box_no} on terminal {terminal_no}. Communication with box failed",
            )

        res_data = res.json()

        print(res_data)

        if res_data["msg"] != "OK":
            raise HTTPException(
                status_code=400,
                detail=f"DClock API failed to unlock box {box_no} on terminal {terminal_no}. Error code {res_data['errorCode']}",
            )

        return res.json()
