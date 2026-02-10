"""
API routers for the Sage House Review Dashboard.
"""
from routers.reviews import router as reviews_router
from routers.platforms import router as platforms_router
from routers.alerts import router as alerts_router
from routers.sync import router as sync_router
from routers.health import router as health_router
from routers.templates import router as templates_router

__all__ = [
    "reviews_router",
    "platforms_router",
    "alerts_router",
    "sync_router",
    "health_router",
    "templates_router",
]
