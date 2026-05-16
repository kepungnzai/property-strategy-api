from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Location(BaseModel):
    suburb: str
    state: str
    country: str


class Report(BaseModel):
    id: str
    location: Location
    property_type: str
    current_analysis: str
    user_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ReportCreate(BaseModel):
    location: Location
    property_type: str
    current_analysis: str
    user_id: Optional[str] = None


class UserReport(BaseModel):
    userId: str
    reportId: str
    creationTime: Optional[datetime] = None


class GoogleUser(BaseModel):
    google_id: str
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None
