"""Strict existing Lab control schema, shared by both HTTP adapters."""
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class Scenario(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    demand_percent: Annotated[int, Field(ge=0, le=200)] = 100
    lead_days: Annotated[int, Field(ge=1, le=14)] = 2
    review_days: Annotated[int, Field(ge=1, le=7)] = 3
    supplier_delay_days: Annotated[int, Field(ge=0, le=14)] = 0
    inbound_day: Annotated[int, Field(ge=0, le=27)] = 1
    reservation_qty: Annotated[int, Field(ge=0, le=100)] = 3
    safety_qty: Annotated[int, Field(ge=0, le=100)] = 2
    pack_size: Annotated[int, Field(ge=1, le=24)] = 6
    moq: Annotated[int, Field(ge=1, le=100)] = 10
    service_target_percent: Annotated[int, Field(ge=0, le=100)] = 90
    evidence_case: Literal['clean', 'incomplete_supply'] = 'clean'
