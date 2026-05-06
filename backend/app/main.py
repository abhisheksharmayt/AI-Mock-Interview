from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.routes import router
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=os.getenv("API_PREFIX", "/api/v1"))