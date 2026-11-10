from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer  # ✅ IMPORTAR ESTO
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

# ✅ DEFINIR EL ESQUEMA DE SEGURIDAD GLOBAL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="usuarios/login")


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
    openapi_tags=[],
    docs_url=None,
    redoc_url=None,
    # ✅ AGREGAR SEGURIDAD A NIVEL GLOBAL PARA SWAGGER
    swagger_ui_oauth2_redirect_url="/oauth2-redirect",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
    }
)

# ✅ REGISTRAR EL SCHEMA DE SEGURIDAD EN OPENAPI
app.add_api_route("/openapi.json", lambda: None, include_in_schema=False)


@app.get("/docs", response_class=HTMLResponse, include_in_schema=False)
async def custom_docs():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Alquileres AIRBNB - Documentación</title>
        <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
        <style>
            .topbar { display: none; }
            .logo-header { 
                padding: 30px 20px; 
                text-align: center; 
                background: #fff;
            }
            .logo-header img { 
                max-height: 100px; 
                width: auto;       
                display: block; 
                margin: 0 auto;    
            }
        </style>
    </head>
    <body>
        <div class="logo-header">
            <img src="/assets/logo.png" alt="Logo API Alquileres AIRBNB">
        </div>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
        <script>
            window.onload = function() {
                window.ui = SwaggerUIBundle({
                    url: "/openapi.json",
                    dom_id: '#swagger-ui',
                    presets: [SwaggerUIBundle.presets.apis],
                    layout: "BaseLayout"
                });
            };
        </script>
    </body>
    </html>
    """


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

ASSETS_DIR = "assets"
if os.path.exists(ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

app.include_router(usuario_router.router, tags=["usuarios"])
app.include_router(propiedad_router.router, tags=["propiedades"])
app.include_router(contrato_router.router, tags=["contratos"])
app.include_router(pago_router.router, tags=["pagos"])
app.include_router(mantenimiento_router.router, tags=["mantenimiento"])
app.include_router(solicitud_visita_router.router, tags=["solicitudes-visita"])
app.include_router(solicitud_alquiler_router.router,
                   tags=["solicitudes-alquiler"])
