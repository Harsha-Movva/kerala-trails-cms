from pydantic import BaseModel, Field
from typing import Any, Literal

class LoginIn(BaseModel):
    email: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str

class SeasonIn(BaseModel):
    season: str = Field(min_length=2, max_length=80)
    start_month: int = Field(ge=1, le=12)
    end_month: int = Field(ge=1, le=12)
    price_per_person: float = Field(gt=0)

class PackageIn(BaseModel):
    code: str = Field(min_length=3, max_length=40, pattern=r"^[A-Za-z0-9-]+$")
    slug: str = Field(min_length=3, max_length=180, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title: str = Field(min_length=3, max_length=220)
    destination: str = Field(min_length=2, max_length=120)
    duration_days: int = Field(ge=1, le=60)
    summary: str = Field(min_length=10, max_length=3000)
    hero_image: str = Field(default="", max_length=500)
    itinerary: list[dict[str, Any]] = Field(default_factory=list, max_length=60)
    inclusions: list[str] = Field(default_factory=list, max_length=40)
    hotel_category: str = "4 star"
    status: Literal["draft", "published"] = "draft"
    seasons: list[SeasonIn] = Field(min_length=1, max_length=8)

class EnquiryIn(BaseModel):
    package_id: int | None = None
    name: str = Field(min_length=2, max_length=160)
    email: str = Field(min_length=5, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    phone: str = Field(default="", max_length=40, pattern=r"^[+0-9() .-]*$")
    message: str = Field(min_length=10, max_length=5000)
    whatsapp_consent: bool = False

class EnquiryStatusIn(BaseModel):
    status: Literal["new", "reviewing", "replied", "qualified", "closed"]
    assigned_to: int | None = None
    extracted: dict[str, Any] | None = None
