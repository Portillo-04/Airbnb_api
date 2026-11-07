from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from pydantic import EmailStr, ConfigDict
from enum import Enum as PyEnum
import sqlalchemy as sa


def validate_phone(value: str) -> str:
    if value and not re.match(r'^\d{4}-\d{4}$', value):
        raise ValueError("El teléfono debe tener formato XXXX-XXXX")
    return value


TelefonoPattern = str | None


class RolUsuario(str, PyEnum):
    PROPIETARIO = "propietario"
    INQUILINO = "inquilino"
    ADMINISTRADOR = "administrador"


class UsuarioBase(SQLModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True, use_enum_values=True)

    nombre: str = Field(max_length=100, min_length=3)
    email: EmailStr = Field(max_length=150)
    telefono: Optional[TelefonoPattern] = Field(default=None, max_length=9)

    rol: RolUsuario = Field(
        default=RolUsuario.INQUILINO,
        sa_column=sa.Column(
            sa.Enum("propietario", "inquilino",
                    "administrador", name="rolusuario"),
            nullable=False,
            server_default="inquilino"
        )
    )


class UsuarioCreate(UsuarioBase):
    password: str = Field(min_length=6, max_length=100,
                          description="Contraseña en texto plano")


class UsuarioUpdate(SQLModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True, use_enum_values=True)

    nombre: Optional[str] = Field(default=None, max_length=100, min_length=3)
    email: Optional[EmailStr] = Field(default=None, max_length=150)
    telefono: Optional[TelefonoPattern] = Field(default=None, max_length=9)
    rol: Optional[RolUsuario] = Field(default=None)
    activo: Optional[bool] = Field(default=None)

    password: Optional[str] = Field(
        default=None,
        min_length=6,
        max_length=100,
        description="Nueva contraseña (solo admins pueden cambiarla en otros usuarios)"
    )


class UsuarioLogin(SQLModel):
    username: str = Field(description="Email o nombre de usuario")
    password: str = Field(description="Contraseña")


class Usuario(UsuarioBase, table=True):
    __tablename__ = "usuarios"

    id: Optional[int] = Field(default=None, primary_key=True)

    password_hashed: str = Field(
        max_length=255,
        sa_column=sa.Column("password", sa.String(255), nullable=False)
    )

    activo: bool = Field(default=True)

    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=sa.Column(sa.DateTime(timezone=False),
                            server_default=sa.func.now())
    )

    propiedades: list["Propiedad"] = Relationship(back_populates="propietario")
    contratos: list["Contrato"] = Relationship(back_populates="inquilino")
    pagos: list["Pago"] = Relationship(back_populates="usuario")
    mantenimientos: list["SolicitudMantenimiento"] = Relationship(
        back_populates="solicitante")
    solicitudes_visita: list["SolicitudVisita"] = Relationship(
        back_populates="solicitante")
    solicitudes_alquiler: list["SolicitudAlquiler"] = Relationship(
        back_populates="solicitante")


class UsuarioResponse(UsuarioBase):
    id: int
    activo: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
