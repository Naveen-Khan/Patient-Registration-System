from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
import re
from datetime import datetime
from app.config import US_STATE_ABBR


class PatientCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    date_of_birth: str = Field(..., pattern=r"^\d{2}/\d{2}/\d{4}$")
    sex: str = Field(..., pattern=r"^(Male|Female|Other|Decline to Answer)$")
    phone_number: str = Field(..., min_length=10, max_length=15)
    address_line_1: str = Field(..., min_length=1, max_length=200)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=2, max_length=2)
    zip_code: str = Field(..., min_length=5, max_length=10)
    email: Optional[str] = Field(None, max_length=255)
    address_line_2: Optional[str] = Field(None, max_length=200)
    insurance_provider: Optional[str] = Field(None, max_length=200)
    insurance_member_id: Optional[str] = Field(None, max_length=100)
    preferred_language: str = "English"
    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(None, max_length=15)

    model_config = ConfigDict(extra="ignore")

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_names(cls, v: str) -> str:
        if not re.match(r"^[A-Za-z\-']{1,50}$", v):
            raise ValueError("Name must be 1-50 characters, alphabetic with hyphens/apostrophes only")
        return v

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: str) -> str:
        if v not in US_STATE_ABBR:
            raise ValueError("State must be a valid 2-letter US state abbreviation")
        return v

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v: str) -> str:
        if not re.match(r"^\d{5}(-\d{4})?$", v):
            raise ValueError("ZIP code must be 5-digit or ZIP+4 format")
        return v

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if len(re.sub(r"[^\d]", "", v)) != 10:
            raise ValueError("Phone number must be a valid 10-digit US phone number")
        return v

    @field_validator("emergency_contact_phone")
    @classmethod
    def validate_emergency_phone(cls, v: Optional[str]) -> Optional[str]:
        if v and len(re.sub(r"[^\d]", "", v)) != 10:
            raise ValueError("Emergency contact phone must be a valid 10-digit US phone number")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: str) -> str:
        try:
            dob = datetime.strptime(v, "%m/%d/%Y")
            if dob > datetime.now():
                raise ValueError("Date of birth cannot be in the future")
        except ValueError:
            raise ValueError("Date of birth must be a valid date in MM/DD/YYYY format and not in the future")
        return v


class PatientUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    date_of_birth: Optional[str] = Field(None, pattern=r"^\d{2}/\d{2}/\d{4}$")
    sex: Optional[str] = Field(None, pattern=r"^(Male|Female|Other|Decline to Answer)$")
    phone_number: Optional[str] = Field(None, min_length=10, max_length=15)
    address_line_1: Optional[str] = Field(None, min_length=1, max_length=200)
    address_line_2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    state: Optional[str] = Field(None, min_length=2, max_length=2)
    zip_code: Optional[str] = Field(None, min_length=5, max_length=10)
    email: Optional[str] = Field(None, max_length=255)
    insurance_provider: Optional[str] = Field(None, max_length=200)
    insurance_member_id: Optional[str] = Field(None, max_length=100)
    preferred_language: Optional[str] = None
    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(None, max_length=15)

    model_config = ConfigDict(extra="ignore")

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_names(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r"^[A-Za-z\-']{1,50}$", v):
            raise ValueError("Name must be 1-50 characters, alphabetic with hyphens/apostrophes only")
        return v

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: Optional[str]) -> Optional[str]:
        if v and v not in US_STATE_ABBR:
            raise ValueError("State must be a valid 2-letter US state abbreviation")
        return v

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r"^\d{5}(-\d{4})?$", v):
            raise ValueError("ZIP code must be 5-digit or ZIP+4 format")
        return v

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v and len(re.sub(r"[^\d]", "", v)) != 10:
            raise ValueError("Phone number must be a valid 10-digit US phone number")
        return v

    @field_validator("emergency_contact_phone")
    @classmethod
    def validate_emergency_phone(cls, v: Optional[str]) -> Optional[str]:
        if v and len(re.sub(r"[^\d]", "", v)) != 10:
            raise ValueError("Emergency contact phone must be a valid 10-digit US phone number")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: Optional[str]) -> Optional[str]:
        if v:
            try:
                dob = datetime.strptime(v, "%m/%d/%Y")
                if dob > datetime.now():
                    raise ValueError("Date of birth cannot be in the future")
            except ValueError:
                raise ValueError("Date of birth must be a valid date in MM/DD/YYYY format and not in the future")
        return v


class PhoneCheck(BaseModel):
    phone_number: str