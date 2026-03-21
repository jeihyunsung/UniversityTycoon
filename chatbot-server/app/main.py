from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.kakao import router as kakao_router


app = FastAPI(
    title="University Tycoon Chatbot Server",
    version="0.1.0",
    description="Kakao chatbot skill server skeleton for University Tycoon.",
)

app.include_router(health_router)
app.include_router(kakao_router, prefix="/webhooks/kakao", tags=["kakao"])
