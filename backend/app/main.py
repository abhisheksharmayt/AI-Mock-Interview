from fastapi import FastAPI
from app.routers.routes import router
import os

app = FastAPI()

app.include_router(router, prefix=os.getenv("API_PREFIX", "/api/v1"))