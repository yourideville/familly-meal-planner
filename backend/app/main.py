import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import admin, dishes, health, members, menu, votes
from app.services import store


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

app.include_router(health.router, tags=["health"])
app.include_router(dishes.router, prefix="/dishes", tags=["dishes"])
app.include_router(votes.router, prefix="/votes", tags=["votes"])
app.include_router(menu.router, prefix="/weekly-menu", tags=["weekly-menu"])
app.include_router(members.router, prefix="/members", tags=["members"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
