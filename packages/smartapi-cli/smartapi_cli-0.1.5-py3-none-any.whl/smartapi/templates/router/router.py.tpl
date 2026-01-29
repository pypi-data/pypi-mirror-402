from fastapi import APIRouter, Depends
from app.core.database.async_db import get_db

router = APIRouter(
    prefix="/{module_snake}",
    tags=["{module}"],
)
