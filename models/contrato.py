from sqlmodel import SQLModel, Field, Relationship
from datetime import date, datetime
from typing import Optional
from enum import Enum
import sqlalchemy as sa


class EstadoContrato(str, Enum):
    ACTIVO = "activo"
    FINALIZADO = "finalizado"
    CANCELADO = "cancelado"


class ContratoBase(SQLModel):
    fecha_inicio: date
    fecha_fin: date
    precio_mensual: float = Field(ge=0)
    estado: EstadoContrato = Field(default=EstadoContrato.ACTIVO)

    propiedad_id: int = Field(foreign_key="propiedades.id")
    inquilino_id: int = Field(foreign_key="usuarios.id")

    pdf_url: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Ruta relativa al archivo PDF del contrato firmado"
    )


class ContratoCreate(ContratoBase):
    pass


class ContratoUpdate(SQLModel):
    estado: Optional[EstadoContrato] = None
    pdf_url: Optional[str] = None


class Contrato(ContratoBase, table=True):
    __tablename__ = "contratos"

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

    propiedad: "Propiedad" = Relationship(back_populates="contratos")
    inquilino: "Usuario" = Relationship(back_populates="contratos")


class ContratoResponse(ContratoBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
