from pydantic import BaseModel, EmailStr, Field, validator
from datetime import date, datetime
from decimal import Decimal
from typing import Optional


class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str  # Must be one of 'admin','frontdesk','manager'

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True  # Pydantic V2 replacement for orm_mode

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    user_id: int
    name: str
    email: str
    role: str

class CreateReservation(BaseModel):
    first_name: str = Field(..., max_length=50)
    last_name: str = Field(..., max_length=50)
    email: EmailStr
    phone_number: str = Field(..., max_length=15)
    check_in: date
    check_out: date
    total_amount: Decimal = Field(..., gt=0)
    address: str = Field(..., max_length=200)
    credit_card_number: str = Field(..., max_length=20)
    cc_expiry: str # MM/YY format
    status: str = Field("booked")
    room_number: Optional[str] = None
    room_type: str = Field(..., max_length=20)  # Must be one of 'Single','Double'
    created_by: int

    @validator("status")
    def validate_status(cls, v):
        allowed = ["booked", "checked_in", "checked_out", "cancelled"]
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v

    @validator("check_out")
    def check_dates(cls, v, values):
        if "check_in" in values and v <= values["check_in"]:
            raise ValueError("check_out must be after check_in")
        return v

    @validator("credit_card_number")
    def validate_cc_number(cls, v):
        if not v.isdigit():
            raise ValueError("credit_card_number must contain only digits")
        return v

class ReservationResponse(BaseModel):
    reservation_id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    check_in: date
    check_out: date
    total_amount: Decimal
    address: str
    credit_card_number: str
    cc_expiry: str
    status: str
    room_type: str
    room_number: Optional[str] = None
    created_by: int
    updated_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ReservationUpdate(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[EmailStr]
    phone_number: Optional[str]
    check_in: Optional[str]
    check_out: Optional[str]
    total_amount: Optional[float]
    address: Optional[str]
    credit_card_number: Optional[str]
    cc_expiry: Optional[str]
    status: Optional[str]
    room_type: Optional[str]
    

class ArrivalResponse(BaseModel):
    first_name: str
    last_name: str
    check_in: date
    check_out: date
    days: int
    room_number: Optional[str] = None,
    room_type: str
    reservation_id: int

    class Config:
        from_attributes = True

class CheckinResponse(BaseModel):
    first_name: str
    last_name: str
    check_in: date
    check_out: date
    reservation_id: int
    class Config:
        from_attributes = True


class DepartureResponse(BaseModel):
    first_name: str
    last_name: str
    reservation_id: int
    room_number: Optional[str] = None
    room_type: str

    class Config:
        from_attributes = True

class ReservationUpdate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    check_in: date
    check_out: date
    total_amount: Decimal
    address: str
    credit_card_number: str
    cc_expiry: str
    status: str
    room_type: str
    room_number: Optional[str] = None
    created_by: int
    updated_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class RoomBase(BaseModel):
    room_number: str
    room_type: str  # Must be one of 'Single','Double'
    status: str  # Must be one of 'vacant','occupied','maintenance','housekeeping'
    room_condition: str  # Must be one of 'clean','dirty','under_maintenance'

    class Config:
        from_attributes = True

class RoomUpdate(BaseModel):
    room_type: Optional[str]
    room_condition: Optional[str]
    status: Optional[str]