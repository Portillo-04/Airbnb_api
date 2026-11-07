import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine

# ✅ Importar todos los modelos para que SQLModel los registre
from models.usuario import Usuario
from models.propiedad import Propiedad
from models.contrato import Contrato
from models.pago import Pago
from models.mantenimiento import SolicitudMantenimiento
from models.solicitud_visita import SolicitudVisita
from models.solicitud_alquiler import SolicitudAlquiler

load_dotenv()

DATABASE_NAME = os.getenv("DATABASE_NAME", "airbnb")
DATABASE_USER = os.getenv("DATABASE_USER", "root")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "")
DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABASE_PORT = os.getenv("DATABASE_PORT", "3306")

DATABASE_URL = f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

engine = create_engine(DATABASE_URL, echo=True)

def crear_db_y_tablas():
    SQLModel.metadata.create_all(engine)