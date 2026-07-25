from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.base import *  # noqa: F403
from app.modules.auth.router import router as auth_router
from app.modules.chat.router import router as chat_router
from app.modules.lost_found.router import router as lost_found_router
from app.modules.product.router import router as product_router


app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}


app.include_router(auth_router)
app.include_router(product_router)
app.include_router(lost_found_router)
app.include_router(chat_router)
