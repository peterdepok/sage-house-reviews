from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import models, database
from .routers import reviews, platforms, alerts
from .services import scheduler

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Sage House Reviews API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    scheduler.start_scheduler()

app.include_router(reviews.router, prefix="/api/reviews", tags=["reviews"])
app.include_router(platforms.router, prefix="/api/platforms", tags=["platforms"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])

@app.get("/api/health")
def health_check():
    return {"status": "healthy"}
