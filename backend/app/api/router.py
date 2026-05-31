"""Aggregate API routers."""

from fastapi import APIRouter

from app.api.routes import bracket, data, predict, root, teams

api_router = APIRouter()
api_router.include_router(root.router)
api_router.include_router(bracket.router)
api_router.include_router(data.router)
api_router.include_router(predict.router)
api_router.include_router(teams.router)
