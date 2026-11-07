from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
from contextlib import asynccontextmanager
import os

from config.settings import get_settings
from config.db import crear_db_y_tablas

from models import usuario, propiedad, contrato, pago, mantenimiento, solicitud_alquiler, solicitud_visita

from routers import (
    usuario_router,
    propiedad_router,
    contrato_router,
    pago_router,
    mantenimiento_router,
    solicitud_visita_router,
    solicitud_alquiler_router
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        print("Creando/verificando tablas...")
        crear_db_y_tablas()
        print("Base de datos lista")
    except Exception as e:
        print(f"Error inicializando BD (la API seguirá corriendo): {e}")
    yield


app = FastAPI(
    title="API Alquileres AIRBNB",
    version="0.4.0",
    lifespan=lifespan,
    openapi_tags=[]
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    return response


ALLOWED_ORIGINS = [
    "http://68.211.113.156:3000",
    "http://68.211.113.156:5173",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

UPLOAD_DIR = "uploads"
os.makedirs(os.path.join(UPLOAD_DIR, "propiedades"), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "contratos"), exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(usuario_router.router, tags=["usuarios"])
app.include_router(propiedad_router.router, tags=["propiedades"])
app.include_router(contrato_router.router, tags=["contratos"])
app.include_router(pago_router.router, tags=["pagos"])
app.include_router(mantenimiento_router.router, tags=["mantenimiento"])
app.include_router(solicitud_visita_router.router, tags=["solicitudes-visita"])
app.include_router(solicitud_alquiler_router.router,
                   tags=["solicitudes-alquiler"])
