from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional
from enum import Enum
import sqlalchemy as sa


class EstadoSolicitud(str, Enum):
    PENDIENTE = "PENDIENTE"
    EN_PROCESO = "EN_PROCESO"
    RESUELTO = "RESUELTO"
    RECHAZADO = "RECHAZADO"


class SolicitudBase(SQLModel):
    propiedad_id: int = Field(foreign_key="propiedades.id", nullable=False)
    inquilino_id: int = Field(foreign_key="usuarios.id", nullable=False)
    descripcion: str = Field(max_length=1000)
    estado: EstadoSolicitud = Field(default=EstadoSolicitud.PENDIENTE)
    respuesta_propietario: Optional[str] = Field(default=None, max_length=500)


class SolicitudMantenimiento(SolicitudBase, table=True):
    __tablename__ = "solicitudes_mantenimiento"

    id: Optional[int] = Field(default=None, primary_key=True)

    created_at: datetime = Field(
        default=None,
        sa_column=sa.Column(sa.DateTime(timezone=False),
                            server_default=sa.func.now())
    )
    updated_at: datetime = Field(
        default=None,
        sa_column=sa.Column(sa.DateTime(timezone=False),
                            server_default=sa.func.now(), onupdate=sa.func.now())
    )

    solicitante: "Usuario" = Relationship(back_populates="mantenimientos")


class SolicitudCreate(SolicitudBase):
    pass


class SolicitudUpdate(SQLModel):
    estado: Optional[EstadoSolicitud] = None
    respuesta_propietario: Optional[str] = None


class SolicitudResponse(SolicitudBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
