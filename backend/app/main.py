import os
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
import time
import logging

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.routers import admin, dishes, health, members, menu, votes, periods
from app.services import store

logger = logging.getLogger(__name__)

_DEFAULT_LOG_FORMAT = "[%(asctime)s] %(levelname)s %(name)s: %(message)s"
_DEV_LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"


@asynccontextmanager
async def lifespan(application: FastAPI):
    store.seed_data()
    yield


app = FastAPI(title="Family Meal Planner MVP", lifespan=lifespan)

_default_origins = ["http://localhost:5173"]
_extra_origins = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
_allowed_origins = _default_origins + [o.strip() for o in _extra_origins if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def invalidate_store_cache_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Invalidate store cache on every request to ensure fresh data from DynamoDB.

    In a Lambda environment, different invocations may have independent global state.
    Always invalidating the cache on reads guarantees we reload from DynamoDB and
    see changes made by other Lambda containers.
    """
    store.invalidate_store_cache()
    return await call_next(request)


@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Log every request with method, path, query params, and response status/duration."""
    start = time.perf_counter()
    method = request.method
    path = request.url.path
    query = str(request.query_params) if request.query_params else ""
    req_desc = f"{method} {path}" + (f"?{query}" if query else "")

    logger.info("-> %s", req_desc)

    response = await call_next(request)

    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info("<- %s %d (%.0fms)", req_desc, response.status_code, elapsed_ms)

    return response


app.include_router(health.router, tags=["health"])
app.include_router(dishes.router, prefix="/dishes", tags=["dishes"])
app.include_router(votes.router, prefix="/votes", tags=["votes"])
app.include_router(menu.router, prefix="/weekly-menu", tags=["weekly-menu"])
app.include_router(periods.router, prefix="/weekly-menu", tags=["weekly-menu"])
app.include_router(members.router, prefix="/members", tags=["members"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
