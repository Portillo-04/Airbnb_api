from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional
from enum import Enum
import sqlalchemy as sa
from pydantic import field_serializer


class EstadoPropiedad(str, Enum):
    DISPONIBLE = "DISPONIBLE"
    ALQUILADA = "ALQUILADA"
    MANTENIMIENTO = "MANTENIMIENTO"


EstadoVivienda = EstadoPropiedad


class PropiedadBase(SQLModel):
    direccion: str = Field(nullable=False, max_length=255)
    departamento: str = Field(nullable=False, max_length=100)
    distrito: str = Field(nullable=False, max_length=100)
    descripcion: str = Field(nullable=False, max_length=1000)
    precio_mensual: float = Field(nullable=False)
    estado: EstadoPropiedad = Field(default=EstadoPropiedad.DISPONIBLE)
    imagen_url: Optional[str] = Field(default=None, max_length=500)
    propietario_id: int = Field(foreign_key="usuarios.id", nullable=False)


class Propiedad(PropiedadBase, table=True):
    __tablename__ = "propiedades"

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

    propietario: "Usuario" = Relationship(back_populates="propiedades")
    contratos: list["Contrato"] = Relationship(back_populates="propiedad")


class PropiedadCreate(PropiedadBase):
    pass


class PropiedadUpdate(SQLModel):
    direccion: Optional[str] = Field(default=None, max_length=255)
    departamento: Optional[str] = Field(default=None, max_length=100)
    distrito: Optional[str] = Field(default=None, max_length=100)
    descripcion: Optional[str] = Field(default=None, max_length=1000)
    precio_mensual: Optional[float] = None
    estado: Optional[EstadoPropiedad] = None
    imagen_url: Optional[str] = Field(default=None, max_length=500)
    propietario_id: Optional[int] = None


class PropiedadResponse(PropiedadBase):
    id: int
    created_at: datetime
    updated_at: datetime

    @field_serializer("precio_mensual")
    def serialize_precio(self, value: float) -> str:
        return f"${value:.2f}"

    class Config:
        from_attributes = True
