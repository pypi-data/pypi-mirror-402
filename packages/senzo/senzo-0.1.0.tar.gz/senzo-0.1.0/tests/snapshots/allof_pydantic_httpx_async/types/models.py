from __future__ import annotations
from pydantic import BaseModel, Field
from typing import final


@final
class Animal(BaseModel):
    """Base animal type"""

    id: str
    name: str


@final
class Cat(BaseModel):
    """Base animal type"""

    id: str
    name: str
    indoor: bool | None = Field(default=None)


@final
class Dog(BaseModel):
    """Base animal type"""

    breed: str
    id: str
    name: str
    age: int | None = Field(default=None)


@final
class Labrador(BaseModel):
    """A labrador retriever"""

    breed: str
    color: str
    id: str
    name: str
    age: int | None = Field(default=None)
