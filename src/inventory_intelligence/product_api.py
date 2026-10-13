"""Bounded, read-only product routes over the packaged synthetic catalog."""
from copy import deepcopy
from pathlib import Path
from threading import Lock
from typing import Annotated, Literal

from fastapi import HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from .lab_api_types import Scenario

Selector = Annotated[str, Field(min_length=1, max_length=100)]


def _package_identity(stat):
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns


class ProductScenario(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    cutoff: Selector
    sku_id: Selector
    warehouse_id: Selector
    archive_digest: Annotated[str, Field(pattern=r'^[0-9a-f]{64}$')]
    overrides: dict = Field(default_factory=dict)


def install_product_routes(application, supplied=None, catalog_path=None):
    # Imports remain inside setup to preserve the legacy module boundary.
    from . import product
    injected = deepcopy(supplied)
    cached = None
    identity = None
    lock = Lock()

    def catalog():
        nonlocal cached, identity
        try:
            # Only fully validated immutable packages are published to readers.
            # Replacement, including same-size edits, invalidates the receipt.
            # No trust/cache is shared with live operational database transactions.
            with lock:
                path = Path(catalog_path) if catalog_path else Path(product.__file__).with_name('product_evidence.json.gz')
                stat = path.stat() if injected is None else None
                current = _package_identity(stat) if stat is not None else 'injected'
                if cached is None or current != identity:
                    validated = product.load_catalog(path) if injected is None else product.validate_catalog(injected)
                    if injected is None and _package_identity(path.stat()) != current:
                        raise ValueError('Product archive changed during validation')
                    cached, identity = validated, current
                return cached
        except (ValueError, OSError, KeyError, TypeError) as error:
            raise HTTPException(503, 'Synthetic product evidence is unavailable or invalid') from error

    def invoke(request, allowed, function, *args, archive_digest=None, **kwargs):
        if set(request.query_params) - allowed:
            raise HTTPException(422, 'Unknown product query field')
        if any(len(request.query_params.getlist(name)) != 1 for name in request.query_params):
            raise HTTPException(422, 'Repeated product query field')
        data = catalog()
        if archive_digest is not None and archive_digest != data['digest']:
            raise HTTPException(409, 'Saved view uses different evidence; reset to this archive explicitly')
        try:
            result = function(data, *args, **kwargs)
        except (ValueError, KeyError) as error:
            raise HTTPException(422, 'Invalid product selection or scenario') from error
        return JSONResponse(result, headers={'Cache-Control': 'no-store'})

    @application.get('/api/product')
    @application.get('/api/product/overview')
    def overview(request: Request, cutoff: str | None = Query(default=None, max_length=100),
                 archive_digest: str | None = Query(default=None, max_length=64)):
        return invoke(request, {'cutoff', 'archive_digest'}, product.overview,
                      cutoff, archive_digest=archive_digest)

    @application.get('/api/product/explore')
    def explore(request: Request, cutoff: str | None = Query(default=None, max_length=100),
                style_id: str | None = Query(default=None, max_length=100),
                color: str | None = Query(default=None, max_length=100),
                size: str | None = Query(default=None, max_length=100),
                warehouse_id: str | None = Query(default=None, max_length=100),
                category: Literal['risk', 'opportunity', 'evidence', 'none'] | None = None,
                status: Literal['assessable', 'not_assessable'] | None = None,
                search: str | None = Query(default=None, max_length=100),
                page: int = Query(default=1, ge=1, le=100),
                page_size: int = Query(default=20, ge=1, le=100),
                sort: Literal['priority', 'sku', 'stock'] = 'priority',
                archive_digest: str | None = Query(default=None, max_length=64)):
        filters = {name: value for name, value in dict(style_id=style_id, color=color, size=size,
                   warehouse_id=warehouse_id, category=category, status=status, search=search).items()
                   if value is not None}
        return invoke(request, {'cutoff', 'style_id', 'color', 'size', 'warehouse_id', 'category',
                      'status', 'search', 'page', 'page_size', 'sort', 'archive_digest'},
                      product.explore, cutoff, filters, page=page, page_size=page_size,
                      sort=sort, archive_digest=archive_digest)

    @application.get('/api/product/detail')
    def detail(request: Request, cutoff: Selector, sku_id: Selector, warehouse_id: Selector,
               archive_digest: str | None = Query(default=None, max_length=64)):
        return invoke(request, {'cutoff', 'sku_id', 'warehouse_id', 'archive_digest'},
                      product.detail, cutoff, sku_id, warehouse_id, archive_digest=archive_digest)

    @application.get('/api/product/history')
    def history(request: Request, sku_id: Selector, warehouse_id: Selector,
                archive_digest: str | None = Query(default=None, max_length=64)):
        return invoke(request, {'sku_id', 'warehouse_id', 'archive_digest'},
                      product.history, sku_id, warehouse_id, archive_digest=archive_digest)

    @application.get('/api/product/insights')
    def insights(request: Request, cutoff: str | None = Query(default=None, max_length=100),
                 archive_digest: str | None = Query(default=None, max_length=64)):
        from .insights import discover
        return invoke(request, {'cutoff','archive_digest'}, discover, cutoff, archive_digest=archive_digest)

    @application.get('/api/product/contrast')
    def contrast(request: Request, cutoff: Selector, sku_id: Selector, warehouse_id: Selector,
                 quantity: int | None = Query(default=None,ge=0,le=2000),
                 delay_days: int = Query(default=0,ge=0,le=3),
                 archive_digest: str | None = Query(default=None,max_length=64)):
        from .decision_contrast import compare
        return invoke(request, {'cutoff','sku_id','warehouse_id','quantity','delay_days','archive_digest'},
                      compare,cutoff,sku_id,warehouse_id,quantity,delay_days,archive_digest=archive_digest)

    @application.get('/api/product/control')
    def control(request: Request, name: Literal['duplicate_inventory'],
                archive_digest: str | None = Query(default=None, max_length=64)):
        return invoke(request, {'name', 'archive_digest'}, product.control,
                      name, archive_digest=archive_digest)

    @application.get('/api/product/evidence')
    def evidence(request: Request, cutoff: Selector, sku_id: Selector, warehouse_id: Selector,
                 section: str = Query(default='plan', max_length=32),
                 page: int = Query(default=1, ge=1, le=100),
                 page_size: int = Query(default=20, ge=1, le=100),
                 archive_digest: str | None = Query(default=None, max_length=64)):
        return invoke(request, {'cutoff', 'sku_id', 'warehouse_id', 'section', 'page', 'page_size', 'archive_digest'},
                      product.evidence, cutoff, sku_id, warehouse_id, section,
                      page=page, page_size=page_size, archive_digest=archive_digest)

    @application.post('/api/product/scenario')
    @application.post('/api/product/scenarios', include_in_schema=False)
    def scenario(request: Request, body: ProductScenario):
        # Validate partial overrides without filling legacy defaults: each key has
        # its own saved policy/obligations, especially the zero-demand control.
        try:
            Scenario.model_validate(body.overrides)
        except ValueError as error:
            raise HTTPException(422, 'Invalid product scenario controls') from error
        return invoke(request, set(), product.scenario, body.cutoff, body.sku_id,
                      body.warehouse_id, body.overrides, archive_digest=body.archive_digest)

    @application.get('/health/live', include_in_schema=False)
    def live():
        return {'status': 'live'}

    @application.get('/health/ready', include_in_schema=False)
    def ready():
        data = catalog()
        from .execution import load_execution
        try:
            _, execution_digest = load_execution()
        except (ValueError,OSError,KeyError,TypeError,IndexError,EOFError) as error:
            raise HTTPException(503,'Synthetic execution evidence is unavailable or invalid') from error
        return JSONResponse({'status': 'ready', 'synthetic': True, 'archive_digest': data['digest'],
                             'execution_archive_digest':execution_digest},
                            headers={'Cache-Control': 'no-store'})
