from pydantic import BaseModel
from enum import Enum


class CreateUser(BaseModel):
    name: str
    contactNo: str
    email: str


class UpdateUser(BaseModel):
    contactNo: str | None = None
    email: str | None = None


class CreateGroomer(BaseModel):
    name: str
    pictureUrl: str
    capacity: int
    address: str
    contactNo: str
    email: str
    petType: str
    basic: int
    premium: int
    luxury: int


class GroomerAccepts(BaseModel):
    petTypes: list[str]


class UpdateGroomer(BaseModel):
    pictureUrl: str | None = None
    capacity: int | None = None
    address: str | None = None
    contactNo: str | None = None
    email: str | None = None
    petType: str | None = None
    basic: int | None = None
    premium: int | None = None
    luxury: int | None = None


class PetType(str, Enum):
    birds = "Birds"
    hamsters = "Hamsters"
    cats = "Cats"
    dogs = "Dogs"
    rabbits = "Rabbits"
    guinea_pigs = "GuineaPigs"
    chinchillas = "Chinchillas"
    mice = "Mice"
    fishes = "Fishes"


class ReadGroomer(BaseModel):
    petType: PetType | None = None

    class Config:
        use_enum_values = True


class StatusType(str, Enum):
    awaiting = "awaiting"
    staying = "staying"
    left = "left"


class Status(BaseModel):
    status: StatusType

    class Config:
        use_enum_values = True
