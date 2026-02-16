"""Aggregate router for all backend API modules."""

from fastapi import APIRouter

from .routes.policy import router as policy_router
from .routes.simulation import router as simulation_router
from .routes.telemetry import dashboard_router, rocket_router

api_router = APIRouter()
api_router.include_router(policy_router)
api_router.include_router(simulation_router)
api_router.include_router(rocket_router)
api_router.include_router(dashboard_router)

