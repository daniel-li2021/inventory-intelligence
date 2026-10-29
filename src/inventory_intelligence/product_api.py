"""Bounded, read-only product routes over the packaged synthetic catalog."""
from copy import deepcopy
from pathlib import Path
from threading import Lock
import sqlite3
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


class DemandAdjustment(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    kind: Literal['percent', 'pieces']
    value: Annotated[int, Field(ge=-1000, le=1000)]
    start_day: Annotated[str, Field(min_length=10, max_length=10)]
    end_day: Annotated[str, Field(min_length=10, max_length=10)]


class DemandScenario(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    cutoff: Selector
    sku_id: Selector
    warehouse_id: Selector
    archive_digest: Annotated[str, Field(pattern=r'^[0-9a-f]{64}$')]
    horizon: Annotated[int, Field(ge=7, le=28)] = 28
    method: Literal['mean', 'naive', 'seasonal_naive'] = 'mean'
    adjustment: DemandAdjustment | None = None


class DecisionRequest(ProductScenario):
    quantity: Annotated[int, Field(ge=0, le=2000)] | None = None
    order_minute: Annotated[int, Field(ge=0, le=1439)] = 540
    supplier: dict | None = None
    deliveries: dict | None = None


class TransferRequest(ProductScenario):
    donor_id: Selector
    quantity: Annotated[int, Field(ge=0, le=2000)]
    transport: dict
    supplier: dict | None = None


class TransferEvent(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    archive_digest: Annotated[str, Field(pattern=r'^[0-9a-f]{64}$')]
    transfer_id: Selector
    event_id: Annotated[str, Field(min_length=1, max_length=200)]
    kind: Literal['dispatch', 'receipt', 'eta']
    eta: Annotated[str, Field(max_length=10)] | None = None
    known_day: Annotated[str, Field(max_length=10)]
    quantity: Annotated[int, Field(ge=1, le=2000)] | None = None


class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    cutoff: Selector
    finding_id: Annotated[str, Field(min_length=1, max_length=200)]
    event_id: Annotated[str, Field(min_length=1, max_length=200)]
    status: Literal['acknowledged', 'investigating', 'resolved']
    note: Annotated[str, Field(min_length=1, max_length=1000)]
    reviewed_at: Annotated[str, Field(max_length=40)]
    calculation_digest: Annotated[str, Field(pattern=r'^[0-9a-f]{64}$')]
    archive_digest: Annotated[str, Field(pattern=r'^[0-9a-f]{64}$')]


class PurchaseEvent(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    archive_digest: Annotated[str, Field(pattern=r'^[0-9a-f]{64}$')]
    decision_id: Annotated[str, Field(min_length=1, max_length=200)]
    event_id: Annotated[str, Field(min_length=1, max_length=200)]
    kind: Literal['receipt', 'eta']
    known_day: Annotated[str, Field(max_length=10)]
    quantity: Annotated[int, Field(ge=1, le=2000)] | None = None
    eta: Annotated[str, Field(max_length=10)] | None = None


def install_product_routes(application, supplied=None, catalog_path=None, journal_path=None):
    # Imports remain inside setup to preserve the legacy module boundary.
    from . import product
    from .transfers import TransferJournal
    from .workflow import Journal
    from .exception_review import ReviewJournal
    transfer_journal = TransferJournal(journal_path) if journal_path is not None else None
    purchase_journal = Journal(journal_path) if journal_path is not None else None
    reviews = ReviewJournal(journal_path) if journal_path is not None else None
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
        from .demand_planning import DemandPlanningError
        if set(request.query_params) - allowed:
            raise HTTPException(422, 'Unknown product query field')
        if any(len(request.query_params.getlist(name)) != 1 for name in request.query_params):
            raise HTTPException(422, 'Repeated product query field')
        data = catalog()
        if archive_digest is not None and archive_digest != data['digest']:
            raise HTTPException(409, 'Saved view uses different evidence; reset to this archive explicitly')
        try:
            result = function(data, *args, **kwargs)
        except DemandPlanningError as error:
            raise HTTPException(422, str(error)) from error
        except (ValueError, KeyError, TypeError) as error:
            raise HTTPException(422, 'Invalid product selection or scenario') from error
        return JSONResponse(result, headers={'Cache-Control': 'no-store'})

    def local(request):
        origin = request.headers.get('origin')
        if journal_path is None: raise HTTPException(404, 'Synthetic journal disabled')
        if (request.url.hostname not in ('127.0.0.1','localhost','::1') or
            (origin is not None and origin != str(request.base_url).rstrip('/')) or
            request.headers.get('content-type','').split(';')[0] != 'application/json'):
            raise HTTPException(403, 'Synthetic writes require same-origin loopback JSON')

    def storage(function):
        try: return function()
        except (sqlite3.Error, OSError) as error:
            raise HTTPException(503, 'Synthetic journal unavailable; retained state unchanged') from error

    @application.get('/api/product/decision-context')
    def decision_context(request: Request, cutoff: Selector, sku_id: Selector, warehouse_id: Selector,
                         archive_digest: str | None = Query(default=None, max_length=64)):
        from .supplier_feasibility import example_profile
        def context(data):
            product._key(data, cutoff, sku_id, warehouse_id)
            return dict(supplier=example_profile(cutoff, sku_id, warehouse_id),
                        transport=dict(version_id='declared-demo-transit-v1-'+cutoff, known_day=cutoff,
                                       transit_days=1, capacity=24, setup_cost=4, per_piece_cost=1),
                        locations=data['dimensions']['warehouses'], journal_enabled=journal_path is not None,
                        assumption_label='Explicit synthetic demonstration terms; separate from saved source evidence')
        return invoke(request, {'cutoff','sku_id','warehouse_id','archive_digest'}, context, archive_digest=archive_digest)

    @application.post('/api/product/supplier-contrast')
    def supplier_contrast(request: Request, body: DecisionRequest):
        from .decision_contrast import compare
        if body.overrides or body.supplier is None: raise HTTPException(422, 'Explicit supplier profile required; overrides unsupported')
        return invoke(request, set(), compare, body.cutoff, body.sku_id, body.warehouse_id,
                      body.quantity, supplier=body.supplier, order_minute=body.order_minute,
                      deliveries=body.deliveries, archive_digest=body.archive_digest)

    @application.post('/api/product/supplier-admit')
    def supplier_admit(request: Request, body: DecisionRequest):
        local(request)
        if body.overrides or body.deliveries: raise HTTPException(422, 'Admission cannot use hypothetical outcomes')
        return invoke(request, set(), lambda data: storage(lambda: product._wire(purchase_journal.admit_supplier(data,
                      cutoff=body.cutoff, sku_id=body.sku_id, warehouse_id=body.warehouse_id, supplier=body.supplier,
                      quantity=body.quantity, order_minute=body.order_minute,
                      arm='alternative' if body.quantity is not None else 'actual_proposal'))), archive_digest=body.archive_digest)

    @application.post('/api/product/transfer-contrast')
    def transfer_contrast(request: Request, body: TransferRequest):
        from .transfers import compare
        if body.overrides: raise HTTPException(422, 'Unsupported transfer overrides')
        return invoke(request, set(), compare, body.cutoff, body.sku_id, body.donor_id, body.warehouse_id,
                      body.quantity, body.transport, body.supplier, archive_digest=body.archive_digest)

    @application.post('/api/product/transfer-reserve')
    def transfer_reserve(request: Request, body: TransferRequest):
        from .transfers import compare
        local(request)
        if body.overrides: raise HTTPException(422, 'Unsupported transfer overrides')
        def reserve(data):
            return storage(lambda: product._wire(transfer_journal.reserve(data, body.cutoff, body.sku_id,
                body.donor_id, body.warehouse_id, body.quantity, body.transport, body.supplier)))
        return invoke(request, set(), reserve, archive_digest=body.archive_digest)

    @application.post('/api/product/transfer-event')
    def transfer_event(request: Request, body: TransferEvent):
        local(request)
        return invoke(request, set(), lambda data: storage(lambda: product._wire(transfer_journal.record(
                      **body.model_dump(exclude={'archive_digest'})))), archive_digest=body.archive_digest)

    @application.get('/api/product/transfer-history')
    def transfer_history(request: Request, as_of: str = Query(max_length=10),
                         archive_digest: str | None = Query(default=None, max_length=64)):
        return invoke(request, {'as_of','archive_digest'}, lambda data: storage(lambda: transfer_journal.snapshot(as_of))
                      if transfer_journal else dict(enabled=False, synthetic_only=True), archive_digest=archive_digest)


    @application.get('/api/product/feedback-example')
    def feedback_example(request: Request):
        if request.query_params: raise HTTPException(422, 'Saved feedback example has no selection fields')
        from .evaluation_summary import load_feedback
        try: return JSONResponse(load_feedback(), headers={'Cache-Control':'no-store'})
        except (ValueError, OSError) as error:
            raise HTTPException(503, 'Saved feedback unavailable') from error

    @application.get('/api/product/evaluation')
    def evaluation(request: Request):
        if request.query_params: raise HTTPException(422, 'Evaluation has no selection fields')
        from .evaluation_summary import load_summary
        try: return JSONResponse(load_summary(), headers={'Cache-Control':'no-store'})
        except (ValueError, OSError) as error:
            raise HTTPException(503, 'Saved evaluation unavailable') from error

    @application.get('/api/product/reviews')
    def review_history(request: Request, cutoff: str | None = Query(default=None, max_length=10),
                       archive_digest: str | None = Query(default=None, max_length=64)):
        from .insights import discover
        from .exception_review import finding_binding
        def history(data):
            discovery = discover(data, cutoff)
            return dict(journal_enabled=reviews is not None,
                        bindings=[dict(finding_id=f['id'], calculation_digest=product.archive_digest(f, False), known_at=f['known_at']) for f in discovery['findings']],
                        history=storage(lambda: reviews.snapshot(data, cutoff)) if reviews else None)
        return invoke(request, {'cutoff','archive_digest'}, history, archive_digest=archive_digest)

    @application.post('/api/product/review')
    def review(request: Request, body: ReviewRequest):
        local(request)
        return invoke(request, set(), lambda data: storage(lambda: reviews.append(data,
                      **body.model_dump(exclude={'archive_digest'}))), archive_digest=body.archive_digest)

    @application.get('/api/product/purchase-history')
    def purchase_history(request: Request, as_of: str = Query(max_length=10),
                         archive_digest: str | None = Query(default=None, max_length=64)):
        return invoke(request, {'as_of','archive_digest'}, lambda data: storage(lambda: product._wire(purchase_journal.snapshot(as_of)))
                      if purchase_journal else dict(enabled=False, synthetic_only=True), archive_digest=archive_digest)

    @application.post('/api/product/purchase-event')
    def purchase_event(request: Request, body: PurchaseEvent):
        local(request)
        return invoke(request, set(), lambda data: storage(lambda: product._wire(purchase_journal.record(
                      **body.model_dump(exclude={'archive_digest'})))), archive_digest=body.archive_digest)

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

    @application.get('/api/product/demand')
    def demand(request: Request, cutoff: Selector, sku_id: Selector, warehouse_id: Selector,
               horizon: int = Query(default=28, ge=7, le=28),
               method: Literal['mean', 'naive', 'seasonal_naive'] = 'mean',
               archive_digest: str | None = Query(default=None, max_length=64)):
        from .demand_planning import calculate
        return invoke(request, {'cutoff', 'sku_id', 'warehouse_id', 'horizon', 'method', 'archive_digest'},
                      calculate, cutoff, sku_id, warehouse_id, horizon=horizon, method=method,
                      archive_digest=archive_digest)

    @application.post('/api/product/demand-scenario')
    def demand_scenario(request: Request, body: DemandScenario):
        from .demand_planning import calculate
        return invoke(request, set(), calculate, body.cutoff, body.sku_id, body.warehouse_id,
                      horizon=body.horizon, method=body.method,
                      adjustment=body.adjustment.model_dump() if body.adjustment else None,
                      archive_digest=body.archive_digest)

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
