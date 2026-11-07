from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional
from enum import Enum
import sqlalchemy as sa


class EstadoSolicitud(str, Enum):
    PENDIENTE = "pendiente"
    EN_PROCESO = "en_proceso"
    RESUELTO = "resuelto"
    CANCELADO = "cancelado"


class SolicitudBase(SQLModel):
    titulo: str = Field(nullable=False, max_length=200, min_length=3)
    descripcion: str = Field(nullable=False, max_length=1000, min_length=10)
    estado: EstadoSolicitud = Field(default=EstadoSolicitud.PENDIENTE)

    propiedad_id: int = Field(foreign_key="propiedades.id", nullable=False)
    inquilino_id: int = Field(foreign_key="usuarios.id", nullable=False)


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
        sa_column=sa.Column(
            sa.DateTime(timezone=False),
            server_default=sa.func.now(),
            onupdate=sa.func.now()
        )
    )

    solicitante: "Usuario" = Relationship(back_populates="mantenimientos")


class SolicitudCreate(SolicitudBase):
    pass


class SolicitudUpdate(SQLModel):
    estado: Optional[EstadoSolicitud] = None
    descripcion: Optional[str] = Field(
        default=None, max_length=1000, min_length=10)


class SolicitudResponse(SolicitudBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
