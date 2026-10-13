"""Optional local same-origin API and static UI for the synthetic Decision Lab."""
from copy import deepcopy
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .lab import evaluate, load_evidence, validate_evidence
from .lab_api_types import Scenario



def create_app(evidence=None, product_evidence=None):
    """Keep injected evidence immutable; requests fail closed on archive problems."""
    application = FastAPI(title='Inventory Decision Intelligence', version='2')
    from .product_api import install_product_routes
    install_product_routes(application, product_evidence)
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

    @application.get('/lab', include_in_schema=False)
    def legacy_index():
        path = static/'index.html'
        if not path.is_file():
            raise HTTPException(status_code=503, detail='Decision Lab UI assets are unavailable')
        return FileResponse(path)

    product_static = Path(__file__).with_name('product_static')

    @application.get('/', include_in_schema=False)
    def index():
        path = product_static/'index.html'
        if not path.is_file():
            raise HTTPException(status_code=503, detail='Product UI assets are unavailable')
        return FileResponse(path)

    application.mount('/product-static', StaticFiles(directory=product_static, check_dir=False), name='product-static')

    # check_dir=False permits API-only tests before packaged frontend integration.
    application.mount('/static', StaticFiles(directory=static, check_dir=False), name='static')
    return application


app = create_app()
