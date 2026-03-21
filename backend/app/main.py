from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import dishes, health, menu, votes

app = FastAPI(title="Family Meal Planner MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(dishes.router, prefix="/dishes", tags=["dishes"])
app.include_router(votes.router, prefix="/votes", tags=["votes"])
app.include_router(menu.router, prefix="/weekly-menu", tags=["weekly-menu"])
