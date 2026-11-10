from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional
from enum import Enum
import sqlalchemy as sa


class EstadoSolicitudAlquiler(str, Enum):
    PENDIENTE = "PENDIENTE"
    APROBADA = "APROBADA"
    RECHAZADA = "RECHAZADA"
    POSPUESTA = "POSPUESTA"


class SolicitudAlquilerBase(SQLModel):
    propiedad_id: int = Field(foreign_key="propiedades.id", nullable=False)
    inquilino_id: int = Field(foreign_key="usuarios.id", nullable=False)
    fecha_inicio: datetime
    fecha_fin: datetime
    estado: EstadoSolicitudAlquiler = Field(
        default=EstadoSolicitudAlquiler.PENDIENTE)
    respuesta_propietario: Optional[str] = Field(default=None, max_length=500)


class SolicitudAlquiler(SolicitudAlquilerBase, table=True):
    __tablename__ = "solicitudalquiler"

    id: Optional[int] = Field(default=None, primary_key=True)

    created_at: datetime = Field(
        default=None,
        sa_column=sa.Column(sa.DateTime(timezone=False),
                            server_default=sa.func.now())
    )
    updated_at: datetime = Field(
        default=None,
        sa_column=sa.Column(
            sa.DateTime(timezone=False),
            server_default=sa.func.now(),
            onupdate=sa.func.now()
        )
    )

    solicitante: "Usuario" = Relationship(
        back_populates="solicitudes_alquiler")


class SolicitudAlquilerCreate(SolicitudAlquilerBase):
    pass


class SolicitudAlquilerResponse(SolicitudAlquilerBase):
    id: int
    created_at: datetime

    inquilino_nombre: Optional[str] = None

    class Config:
        from_attributes = True
