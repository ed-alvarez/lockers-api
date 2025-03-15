from pydantic import BaseModel
from typing import Optional
from enum import Enum
from util.form import as_form


class Department(Enum):
    sales = "Sales"
    customer_support = "Customer Support"
    finance = "Finance"


class Feedback:
    location: Optional[str]
    device: Optional[str]

    member: Optional[str]

    department: Optional[str]

    pictures: Optional[list[str]]

    description: str
    notes: str

    @as_form
    class Write(BaseModel):
        location: Optional[str]
        device: Optional[str]
        member: Optional[str]

        department: Optional[str]

        description: str
        notes: str

    class Read(BaseModel):
        location: Optional[str]
        device: Optional[str]

        member: Optional[str]

        department: str

        pictures: Optional[list[str]]
        description: str
        notes: str
