from fastapi import APIRouter
from app.api import analytics # Assicurati che punti al file giusto

api_router = APIRouter()

# Qui diciamo che tutto quello che c'è in analytics.py avrà il prefisso /analytics
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])