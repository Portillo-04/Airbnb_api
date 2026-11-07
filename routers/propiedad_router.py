import os
import uuid
import json
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlmodel import select
from config.session_Dependencia import SessionDependencia
from config.permissions import RequireAutenticado
from models.propiedad import (
    Propiedad,
    PropiedadCreate,
    PropiedadUpdate,
    PropiedadResponse,
    EstadoPropiedad
)
from models.contrato import Contrato, EstadoContrato
from datetime import datetime, timezone

router = APIRouter(prefix="/propiedades", tags=["propiedades"])

UPLOAD_DIR = Path("uploads/propiedades")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def generate_filename(original_name: str) -> str:
    ext = original_name.split(".")[-1].lower() if original_name else "jpg"
    allowed_ext = ["jpg", "jpeg", "png", "webp"]
    if ext not in allowed_ext:
        raise HTTPException(
            status_code=400, detail="Extensión no permitida. Solo JPG, PNG o WebP")
    return f"{uuid.uuid4().hex}.{ext}"


async def save_image(file: UploadFile) -> str:
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, detail="Tipo de archivo no permitido. Solo JPEG, PNG o WebP")

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400, detail="La imagen no puede superar los 5MB")

    filename = generate_filename(file.filename or "image.jpg")
    filepath = UPLOAD_DIR / filename

    with open(filepath, "wb") as buffer:
        buffer.write(content)

    return f"/uploads/propiedades/{filename}"


def delete_old_image(image_url: Optional[str]):
    if image_url and "/uploads/propiedades/" in image_url:
        try:
            filename = image_url.split("/")[-1]
            filepath = UPLOAD_DIR / filename
            if filepath.exists():
                filepath.unlink()
        except Exception:
            pass


@router.get(
    "/disponibles",
    response_model=List[PropiedadResponse],
    summary="Ver propiedades disponibles"
)
def obtener_disponibles(session: SessionDependencia):
    statement = select(Propiedad).where(
        Propiedad.estado == EstadoPropiedad.DISPONIBLE)
    return session.exec(statement).all()


@router.post(
    "/",
    response_model=PropiedadResponse,
    status_code=201,
    summary="Crear Propiedad con Imagen"
)
async def crear_propiedad(
    datos_json: str = Form(..., alias="datos"),
    file: UploadFile | None = File(None),
    session: SessionDependencia,
    token: dict = Depends(RequireAutenticado)
):
    rol = token.get("rol")
    if rol == "inquilino":
        raise HTTPException(
            status_code=403, detail="Los inquilinos no pueden registrar propiedades")

    try:
        datos_dict = json.loads(datos_json)
        datos = PropiedadCreate(**datos_dict)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Datos inválidos: {str(e)}")

    imagen_url = None
    if file:
        imagen_url = await save_image(file)

    if rol == "propietario":
        nueva = Propiedad(
            **datos.model_dump(exclude={'propietario_id', 'imagen_url'}),
            propietario_id=token["id"],
            imagen_url=imagen_url
        )
    else:
        nueva = Propiedad(
            **datos.model_dump(exclude={'imagen_url'}),
            imagen_url=imagen_url
        )

    session.add(nueva)
    session.commit()
    session.refresh(nueva)
    return PropiedadResponse.model_validate(nueva)


@router.put(
    "/{propiedad_id}",
    response_model=PropiedadResponse,
    summary="Actualizar Propiedad e Imagen"
)
async def actualizar_propiedad(
    propiedad_id: int,
    datos_json: str = Form(..., alias="datos"),
    file: UploadFile | None = File(None),
    session: SessionDependencia,
    token: dict = Depends(RequireAutenticado)
):
    propiedad = session.get(Propiedad, propiedad_id)
    if not propiedad:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")

    rol = token.get("rol")
    mi_id = token.get("id")

    if rol == "propietario" and propiedad.propietario_id != mi_id:
        raise HTTPException(
            status_code=403, detail="No eres el dueño de esta propiedad")
    elif rol == "inquilino":
        raise HTTPException(
            status_code=403, detail="Los inquilinos no pueden modificar propiedades")

    try:
        datos_dict = json.loads(datos_json)
        datos = PropiedadUpdate(**datos_dict)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Datos inválidos: {str(e)}")

    if file:
        delete_old_image(propiedad.imagen_url)
        propiedad.imagen_url = await save_image(file)

    update_data = datos.model_dump(exclude_unset=True, exclude={'imagen_url'})
    for key, value in update_data.items():
        setattr(propiedad, key, value)

    propiedad.updated_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(propiedad)
    return PropiedadResponse.model_validate(propiedad)


@router.get(
    "/mis-propiedades",
    response_model=List[PropiedadResponse],
    summary="Obtener Mis Propiedades"
)
def obtener_mis_propiedades(
    session: SessionDependencia,
    token: dict = Depends(RequireAutenticado)
):
    rol = token.get("rol")
    if rol == "inquilino":
        raise HTTPException(
            status_code=403, detail="Usa /disponibles para ver propiedades")

    if rol == "propietario":
        statement = select(Propiedad).where(
            Propiedad.propietario_id == token["id"])
    else:
        statement = select(Propiedad)
    return session.exec(statement).all()


@router.get(
    "/mis-propiedades-alquiladas",
    response_model=List[PropiedadResponse],
    summary="Propiedades que tengo alquiladas"
)
def obtener_propiedades_alquiladas(
    session: SessionDependencia,
    token: dict = Depends(RequireAutenticado)
):
    mi_id = token.get("id")

    contratos = session.exec(
        select(Contrato).where(
            Contrato.inquilino_id == mi_id,
            Contrato.estado == EstadoContrato.ACTIVO
        )
    ).all()

    if not contratos:
        return []

    propiedad_ids = [c.propiedad_id for c in contratos]

    propiedades = session.exec(
        select(Propiedad).where(Propiedad.id.in_(propiedad_ids))
    ).all()

    return propiedades


@router.get(
    "/{propiedad_id}",
    response_model=PropiedadResponse,
    summary="Obtener Detalle de Propiedad"
)
def obtener_propiedad(
    propiedad_id: int,
    session: SessionDependencia,
    token: dict = Depends(RequireAutenticado)
):
    propiedad = session.get(Propiedad, propiedad_id)
    if not propiedad:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")

    rol = token.get("rol")
    mi_id = token.get("id")

    if rol == "inquilino":
        contrato_activo = session.exec(
            select(Contrato).where(
                Contrato.inquilino_id == mi_id,
                Contrato.propiedad_id == propiedad_id,
                Contrato.estado == EstadoContrato.ACTIVO
            )
        ).first()
        if not contrato_activo:
            raise HTTPException(
                status_code=403, detail="No tienes permiso para ver esta propiedad")
    elif rol == "propietario" and propiedad.propietario_id != mi_id:
        raise HTTPException(
            status_code=403, detail="No eres el dueño de esta propiedad")

    return PropiedadResponse.model_validate(propiedad)


@router.delete(
    "/{propiedad_id}",
    status_code=204,
    summary="Eliminar Propiedad"
)
def eliminar_propiedad(
    propiedad_id: int,
    session: SessionDependencia,
    token: dict = Depends(RequireAutenticado)
):
    propiedad = session.get(Propiedad, propiedad_id)
    if not propiedad:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")

    rol = token.get("rol")
    mi_id = token.get("id")

    if rol == "propietario" and propiedad.propietario_id != mi_id:
        raise HTTPException(
            status_code=403, detail="No eres el dueño de esta propiedad")
    elif rol == "inquilino":
        raise HTTPException(
            status_code=403, detail="Los inquilinos no pueden eliminar propiedades")

    contratos_activos = session.exec(
        select(Contrato).where(
            Contrato.propiedad_id == propiedad_id,
            Contrato.estado == EstadoContrato.ACTIVO
        )
    ).all()

    if contratos_activos:
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar: tiene contratos activos."
        )

    delete_old_image(propiedad.imagen_url)

    session.delete(propiedad)
    session.commit()
