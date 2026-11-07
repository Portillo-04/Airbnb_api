from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional
import sqlalchemy as sa


class PagoBase(SQLModel):
    monto: float = Field(nullable=False, ge=0)
    fecha_pago: datetime = Field(nullable=False)
    metodo_pago: str = Field(max_length=50, default="transferencia")
    descripcion: Optional[str] = Field(default=None, max_length=500)

    paypal_transaction_id: Optional[str] = Field(default=None, max_length=100)

    usuario_id: int = Field(foreign_key="usuarios.id", nullable=False)
    contrato_id: Optional[int] = Field(
        default=None, foreign_key="contratos.id")


class Pago(PagoBase, table=True):
    __tablename__ = "pagos"

    id: Optional[int] = Field(default=None, primary_key=True)

    created_at: datetime = Field(
        default=None,
        sa_column=sa.Column(sa.DateTime(timezone=False),
                            server_default=sa.func.now())
    )

    usuario: "Usuario" = Relationship(back_populates="pagos")


class PagoCreate(PagoBase):
    pass


class PagoResponse(PagoBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
