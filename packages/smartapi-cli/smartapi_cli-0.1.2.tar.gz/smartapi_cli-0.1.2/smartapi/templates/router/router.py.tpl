from fastapi import APIRouter

router = APIRouter(
    prefix="/{module_snake}",
    tags=["{module}"],
)
