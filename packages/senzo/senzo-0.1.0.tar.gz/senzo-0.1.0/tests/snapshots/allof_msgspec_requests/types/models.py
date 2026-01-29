from __future__ import annotations
import msgspec
from typing import final


@final
class Animal(msgspec.Struct, frozen=True, rename="camel"):
    """Base animal type"""

    id: str
    name: str


@final
class Cat(msgspec.Struct, frozen=True, rename="camel"):
    """Base animal type"""

    id: str
    name: str
    indoor: bool | None = None


@final
class Dog(msgspec.Struct, frozen=True, rename="camel"):
    """Base animal type"""

    breed: str
    id: str
    name: str
    age: int | None = None


@final
class Labrador(msgspec.Struct, frozen=True, rename="camel"):
    """A labrador retriever"""

    breed: str
    color: str
    id: str
    name: str
    age: int | None = None
