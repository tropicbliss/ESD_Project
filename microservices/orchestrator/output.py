from pydantic import BaseModel
from input import PetType


class ReadUser(BaseModel):
    name: str
    contactNo: str
    email: str


class Groomer(BaseModel):
    acceptedPets: list[PetType]
    address: str
    capacity: int
    contactNo: str
    email: str
    name: str
    pictureUrl: str
    basic: int
    premium: int
    luxury: int


class FutureCapacity(BaseModel):
    date: str
    remainingCapacity: int


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


class CustomerAppointments(BaseModel):
    id: str
    userName: str
    startDate: str
    endDate: str
    pets: list[Pet]


class Error(BaseModel):
    detail: str


class Checkout(BaseModel):
    checkoutUrl: str
    appointmentId: str
