from pydantic import BaseModel, Field
from typing import Optional


class UserProfile(BaseModel):
    property_price: int = Field(
        ..., ge=1, le=5, description="Property price rating (1-5 stars)"
    )
    property_price_increase: int = Field(
        ..., ge=1, le=5, description="Property price increase potential (1-5 stars)"
    )
    proximity_amenities: int = Field(
        ..., ge=1, le=5, description="Proximity to amenities (1-5 stars)"
    )
    proximity_schools: int = Field(
        ..., ge=1, le=5, description="Proximity to reputable schools (1-5 stars)"
    )
    proximity_train_station: int = Field(
        ..., ge=1, le=5, description="Proximity to train station (1-5 stars)"
    )
    natural_hazard_risk: int = Field(
        ...,
        ge=1,
        le=5,
        description="Flood or bush fire risk (1-5 stars, 1 is low risk)",
    )

    def to_dict(self) -> dict:
        return self.model_dump()


class UserProfileInput:
    property_price: int
    property_price_increase: int
    proximity_amenities: int
    proximity_schools: int
    proximity_train_station: int
    natural_hazard_risk: int
