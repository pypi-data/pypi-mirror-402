from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import app.core.database.models 
# from app.modules.user.routes import router as user_router -- Importar rotas


app = FastAPI(
    title="SmartAPI",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.include_router(modules_router.router) -- Incluir rotas


@app.get("/")
async def health():
    return {"status": "ok"}
