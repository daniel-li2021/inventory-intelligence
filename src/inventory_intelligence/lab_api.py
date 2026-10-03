"""Optional local same-origin API and static UI for the synthetic Decision Lab."""
from copy import deepcopy
from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from .lab import evaluate, load_evidence, validate_evidence


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


def create_app(evidence=None):
    """Keep injected evidence immutable; requests fail closed on archive problems."""
    application = FastAPI(title='Inventory Decision Lab', version='1')
    supplied = deepcopy(evidence)

    def archive():
        try:
            return load_evidence() if supplied is None else validate_evidence(deepcopy(supplied))
        except (ValueError, OSError) as error:
            raise HTTPException(status_code=503, detail='Synthetic replay evidence is unavailable or invalid') from error

    @application.get('/api/lab')
    def lab():
        return evaluate(evidence=archive())

    @application.get('/api/evidence')
    @application.get('/api/lab/evidence', include_in_schema=False)
    def evidence_archive():
        return archive()

    @application.post('/api/scenarios')
    def scenarios(scenario: Scenario):
        return evaluate(scenario.model_dump(), evidence=archive())

    static = Path(__file__).with_name('lab_static')

    @application.get('/', include_in_schema=False)
    def index():
        path = static/'index.html'
        if not path.is_file():
            raise HTTPException(status_code=503, detail='Decision Lab UI assets are unavailable')
        return FileResponse(path)

    # check_dir=False permits API-only tests before packaged frontend integration.
    application.mount('/static', StaticFiles(directory=static, check_dir=False), name='static')
    return application


app = create_app()
