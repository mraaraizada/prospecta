from __future__ import annotations

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas import ProspectDiscoveryRequest, ProspectDiscoveryResponse
from app.services.prospect_service import discover_prospects

app = FastAPI(
    title="Prospecta — AI-Powered Multi-Platform Prospect Discovery",
    description=(
        "Accepts a natural-language prospect discovery query, understands the "
        "interest/audience/location with an LLM, discovers real public profiles "
        "through authorized search APIs, and returns a consolidated, relevance-"
        "filtered list of prospects with their publicly available contact info."
    ),
    version="1.0.0",
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError) -> JSONResponse:
    errors = [{"field": ".".join(str(p) for p in err["loc"][1:]), "message": err["msg"]} for err in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": "Validation failed", "errors": errors})


@app.post("/prospect-discovery", response_model=ProspectDiscoveryResponse, summary="Discover real prospects matching a natural-language query")
async def create_prospect_discovery(payload: ProspectDiscoveryRequest) -> ProspectDiscoveryResponse:
    return await discover_prospects(payload.query)


@app.get("/", include_in_schema=False)
async def root():
    return {"service": "Prospecta", "docs": "/docs", "endpoint": "POST /prospect-discovery"}
