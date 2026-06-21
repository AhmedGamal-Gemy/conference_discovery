from fastapi import APIRouter
from pydantic import BaseModel
from .pipeline import router as pipeline_router

router = APIRouter()

router.include_router(pipeline_router)
