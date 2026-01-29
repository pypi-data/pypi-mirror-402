from fastapi import APIRouter, Depends
from app.modules.{module_snake}.controller.{module_snake}_controller import {module}Controller
from app.core.database.async_db import get_db

router = APIRouter(
    prefix="/{module_snake}",
    tags=["{module}"]
)

controller = {module}Controller()


@router.get("/")
async def index():
    return await controller.index()
