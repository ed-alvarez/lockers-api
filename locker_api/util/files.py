import uuid

from fastapi.datastructures import UploadFile


def generate_file_name(directory: str, image: UploadFile) -> str:
    extension = image.filename.split(".")[-1]
    new_file = f"{uuid.uuid4().hex}{'.'}{extension}"
    return _escape_path(f"{directory}/{new_file}")


def is_image(file: UploadFile) -> bool:
    return file.content_type.startswith("image/")


def _escape_path(path: str) -> str:
    return "".join([character for character in path if character not in "|"])
