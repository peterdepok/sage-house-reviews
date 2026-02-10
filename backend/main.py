from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, database, config
from .routers import reviews, platforms, alerts

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Sage House Reviews API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reviews.router, prefix="/api/reviews", tags=["reviews"])
app.include_router(platforms.router, prefix="/api/platforms", tags=["platforms"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])

@app.get("/api/health")
def health_check():
    return {"status": "healthy"}
