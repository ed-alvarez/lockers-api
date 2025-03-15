from math import ceil
from typing import Generic, Sequence, TypeVar

from pydantic.generics import GenericModel

DataType = TypeVar("DataType")


class Page(GenericModel, Generic[DataType]):
    items: Sequence[DataType]

    total: int
    pages: int


def paginate(data: list[DataType], size: int, count: int):
    return Page(items=data, total=count, pages=ceil(count / size))
