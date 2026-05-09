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
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ReportCreate(BaseModel):
    location: Location
    property_type: str
    current_analysis: str
