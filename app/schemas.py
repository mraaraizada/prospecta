from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.utils.validators import validate_query


class ProspectDiscoveryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="A natural-language prospect discovery query, e.g. 'Football lovers in Washington DC in USA'.")

    @field_validator("query")
    @classmethod
    def _validate_query(cls, value: str) -> str:
        return validate_query(value)


class QueryLocation(BaseModel):
    city: str | None = None
    state: str | None = None
    country: str | None = None


class QueryIntent(BaseModel):
    interest: str
    audience: str
    location: QueryLocation
    target_type: str  # "individual" | "business"


class SocialLink(BaseModel):
    platform: str
    link: str


class Prospect(BaseModel):
    name: str
    location: str | None = None
    social_link: list[SocialLink] = Field(default_factory=list)


class ProspectDiscoveryResponse(BaseModel):
    success: bool
    query: str
    total_prospects: int
    prospects: list[Prospect] = Field(default_factory=list)
    error: str | None = None
