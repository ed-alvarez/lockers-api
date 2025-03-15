from typing import Dict, List

import asyncer
from aioboto3 import Session
from config import get_settings
from fastapi import status
from fastapi.datastructures import UploadFile
from fastapi.exceptions import HTTPException

from .files import generate_file_name, is_image


class ImagesService:
    def __init__(self):
        self._aws_session: Session = Session()
        self._bucket: str = get_settings().images_bucket

    async def upload(self, directory: str, image: UploadFile) -> Dict[str, str]:
        if not is_image(image):
            raise HTTPException(
                detail="Only images are allowed",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        file_name = generate_file_name(directory, image)
        async with self._aws_session.client(
            "s3",
            aws_access_key_id=get_settings().aws_access_key_id,
            aws_secret_access_key=get_settings().aws_secret_access_key,
            region_name=get_settings().aws_region,
        ) as s3:
            try:
                await s3.upload_fileobj(
                    image.file,
                    self._bucket,
                    file_name,
                    ExtraArgs={
                        "ContentType": image.content_type,
                        "ACL": "public-read",
                    },
                )

            except Exception:
                raise HTTPException(
                    detail="Failed to upload image",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            url = f"https://{self._bucket}.s3.amazonaws.com/{file_name}"
        return {"url": url, "key": file_name}

    async def delete(self, key: str):
        async with self._aws_session.client(
            "s3",
            aws_access_key_id=get_settings().aws_access_key_id,
            aws_secret_access_key=get_settings().aws_secret_access_key,
            region_name=get_settings().aws_region,
        ) as s3:
            try:
                await s3.delete_object(Bucket=self._bucket, Key=key)
            except Exception as e:
                raise HTTPException(
                    detail=f"Failed to delete image: {e}",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

    async def batch_upload(self, directory: str, images: List[UploadFile]) -> List[str]:
        urls = []

        async with self._aws_session.client(
            "s3",
            aws_access_key_id=get_settings().aws_access_key_id,
            aws_secret_access_key=get_settings().aws_secret_access_key,
            region_name=get_settings().aws_region,
        ) as s3:
            for image in images:
                if not is_image(image):
                    raise HTTPException(
                        detail="Only images are allowed",
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )

                file_name = generate_file_name(directory, image)
                async with asyncer.create_task_group() as task_group:
                    try:
                        task_group.soonify(s3.upload_fileobj)(
                            image.file,
                            self._bucket,
                            file_name,
                            ExtraArgs={
                                "ContentType": image.content_type,
                                "ACL": "public-read",
                            },
                        )

                    except Exception:
                        raise HTTPException(
                            detail="Failed to upload image",
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        )

                urls.append(f"https://{self._bucket}.s3.amazonaws.com/{file_name}")

            return urls


async def images_service():
    return ImagesService()
