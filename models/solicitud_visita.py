from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional
from enum import Enum
import sqlalchemy as sa


class EstadoSolicitudVisita(str, Enum):
    PENDIENTE = "PENDIENTE"
    APROBADA = "APROBADA"
    RECHAZADA = "RECHAZADA"
    COMPLETADA = "COMPLETADA"


class SolicitudVisitaBase(SQLModel):
    propiedad_id: int = Field(foreign_key="propiedades.id", nullable=False)
    visitante_id: int = Field(foreign_key="usuarios.id", nullable=False)
    fecha_solicitada: datetime
    mensaje: Optional[str] = Field(default=None, max_length=500)
    estado: EstadoSolicitudVisita = Field(
        default=EstadoSolicitudVisita.PENDIENTE)
    respuesta_propietario: Optional[str] = Field(default=None, max_length=500)


class SolicitudVisita(SolicitudVisitaBase, table=True):
    __tablename__ = "solicitudvisita"

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

    solicitante: "Usuario" = Relationship(back_populates="solicitudes_visita")


class SolicitudVisitaCreate(SolicitudVisitaBase):
    pass


class SolicitudVisitaResponse(SolicitudVisitaBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
