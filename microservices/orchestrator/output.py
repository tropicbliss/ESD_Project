from pydantic import BaseModel
from enum import Enum


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


class ReadUser(BaseModel):
    name: str
    contactNo: str
    email: str


class Groomer(BaseModel):
    acceptedPets: list[PetType]
    address: str
    contactNo: str
    email: str
    name: str
    pictureUrl: str
    basic: int
    premium: int
    luxury: int


class GroomerRead(BaseModel):
    result: list[Groomer]


class Comment(BaseModel):
    id: str
    userName: str
    title: str
    message: str
    rating: int


class CensoredComment(BaseModel):
    id: str
    title: str
    message: str


class Appointment(BaseModel):
    id: str
    groomerName: str
    startDate: str
    endDate: str
    groomerPictureUrl: str
    petNames: list[str]


class Pet(BaseModel):
    petType: PetType
    name: str
    gender: str
    age: int
    medicalInfo: str

    class Config:
        use_enum_values = True


class PriceTier(str, Enum):
    basic = "basic"
    premium = "premium"
    luxury = "luxury"


class CustomerAppointments(BaseModel):
    id: str
    userName: str
    startDate: str
    endDate: str
    pets: list[Pet]
    priceTier: PriceTier
    totalPrice: float

    class Config:
        use_enum_values = True


class Error(BaseModel):
    detail: str


class Checkout(BaseModel):
    redirectUrl: str
