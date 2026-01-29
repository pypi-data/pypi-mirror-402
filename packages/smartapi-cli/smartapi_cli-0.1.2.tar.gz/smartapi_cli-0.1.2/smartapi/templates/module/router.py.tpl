from fastapi import APIRouter
from app.modules.{module_snake}.controller.{module_snake}_controller import {module}Controller

router = APIRouter(
    prefix="/{module_snake}",
    tags=["{module}"]
)

controller = {module}Controller()


@router.get("/")
async def index():
    return await controller.index()
