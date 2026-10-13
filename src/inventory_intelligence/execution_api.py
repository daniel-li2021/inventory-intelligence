"""Read-only execution evidence plus an explicitly configured loopback synthetic journal."""
from typing import Annotated, Literal
import sqlite3

from fastapi import HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from . import execution
from .product import _wire

Control=Literal['clean','zero','cold-shortage','spike','missing','notified-delay','unannounced-delay']
Identity=Annotated[str,Field(min_length=1,max_length=200)]
Digest=Annotated[str,Field(pattern=r'^[0-9a-f]{64}$')]


class Admit(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    name: Control
    day: Annotated[int,Field(ge=0,le=6)]
    archive_digest: Digest


class Event(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    decision_id: Identity
    event_id: Identity
    kind: Literal['receipt','eta']
    known_day: Annotated[str,Field(pattern=r'^\d{4}-\d{2}-\d{2}$')]
    quantity: Annotated[int,Field(ge=1,le=1000000)]|None=None
    eta: Annotated[str,Field(pattern=r'^\d{4}-\d{2}-\d{2}$')]|None=None
    archive_digest: Digest


def install_execution_routes(application,journal_path=None):
    from .workflow import Journal
    journal=Journal(journal_path) if journal_path is not None else None
    application.state.journal_enabled=journal is not None

    def invoke(request,allowed,function,*args,archive_digest=None):
        if set(request.query_params)-allowed or any(len(request.query_params.getlist(k))!=1 for k in request.query_params):
            raise HTTPException(422,'Invalid execution query')
        try:
            loaded=execution.load_execution();_,digest=loaded
            if archive_digest is not None and archive_digest!=digest:raise HTTPException(409,'Execution evidence changed; reload explicitly')
        except (ValueError,OSError,KeyError,TypeError,IndexError,EOFError) as error:
            raise HTTPException(503,'Synthetic execution evidence unavailable') from error
        try:
            return JSONResponse(function(loaded,*args),headers={'Cache-Control':'no-store'})
        except (ValueError,KeyError,TypeError) as error:
            raise HTTPException(422,'Invalid synthetic execution selection or event') from error
        except (sqlite3.Error,OSError) as error:
            raise HTTPException(503,'Local synthetic journal unavailable; retained state unchanged') from error

    def local(request):
        if journal is None:raise HTTPException(404,'Local synthetic journal is disabled')
        origin=request.headers.get('origin')
        if (request.url.hostname not in ('127.0.0.1','localhost','::1')
            or (origin is not None and origin!=str(request.base_url).rstrip('/'))
            or request.headers.get('content-type','').split(';')[0]!='application/json'):
            raise HTTPException(403,'Journal writes require same-origin loopback JSON')

    @application.get('/api/execution')
    def overview(request:Request):
        return invoke(request,set(),lambda loaded:execution.overview(loaded)|dict(journal_enabled=journal is not None))

    @application.get('/api/execution/detail')
    def detail(request:Request,name:Control,archive_digest:str|None=Query(default=None,max_length=64)):
        return invoke(request,{'name','archive_digest'},lambda loaded,name:execution.selected(name,loaded),name,archive_digest=archive_digest)

    @application.get('/api/execution/evidence')
    def evidence(request:Request,name:Control,day:int=Query(ge=0,le=6),archive_digest:str|None=Query(default=None,max_length=64)):
        return invoke(request,{'name','day','archive_digest'},lambda loaded,name,day:execution.evidence(name,day,loaded),name,day,archive_digest=archive_digest)

    @application.get('/api/execution/journal')
    def snapshot(request:Request,as_of:str=Query(default='2026-03-20',max_length=10),archive_digest:str|None=Query(default=None,max_length=64)):
        if journal is None:return JSONResponse(dict(enabled=False,synthetic_only=True),headers={'Cache-Control':'no-store'})
        return invoke(request,{'as_of','archive_digest'},lambda loaded:_wire(journal.snapshot(as_of))|dict(enabled=True),archive_digest=archive_digest)

    @application.post('/api/execution/admit')
    def admit(request:Request,body:Admit):
        local(request)
        return invoke(request,set(),lambda loaded:_wire(journal.admit(loaded[0]['manual'][body.name],body.day)),
                      archive_digest=body.archive_digest)

    @application.post('/api/execution/event')
    def event(request:Request,body:Event):
        local(request)
        return invoke(request,set(),lambda loaded:_wire(journal.record(**body.model_dump(exclude={'archive_digest'}))),
                      archive_digest=body.archive_digest)
