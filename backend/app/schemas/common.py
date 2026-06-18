"""Shared schema utilities."""
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = {"from_attributes": True}


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int


class Message(BaseModel):
    detail: str
