import os
import uuid
import hashlib
import secrets
from pathlib import Path
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from pydantic import BaseModel
from sqlmodel import select
from config.session_Dependencia import SessionDependencia
from config.security_Dependencia import Token_Dependencia
from models.contrato import Contrato, ContratoCreate, ContratoUpdate, ContratoResponse, EstadoContrato
from models.propiedad import Propiedad, EstadoVivienda
from models.usuario import Usuario, RolUsuario
from datetime import datetime, timezone

router = APIRouter(prefix="/contratos", tags=["contratos"])

UPLOAD_DIR_CONTRATOS = Path("uploads/contratos")
MAX_PDF_SIZE = 10 * 1024 * 1024


# Modelo auxiliar para recibir la contraseña de forma segura
class FirmaRequest(BaseModel):
    password_firma: str


@router.post("/upload-pdf", summary="Subir PDF de Contrato")
async def subir_pdf_contrato(
    file: UploadFile = File(...),
    token: dict = Depends(Token_Dependencia)
):
    rol = token.get("rol")
    if rol == "inquilino":
        raise HTTPException(
            status_code=403, detail="Solo administradores y propietarios pueden subir contratos")

    if file.content_type != "application/pdf" or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400, detail="Solo se permiten archivos PDF válidos")

    content = await file.read()
    if len(content) > MAX_PDF_SIZE:
        raise HTTPException(
            status_code=413, detail=f"El PDF excede el límite de {MAX_PDF_SIZE // (1024*1024)}MB")

    UPLOAD_DIR_CONTRATOS.mkdir(parents=True, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}.pdf"
    file_path = UPLOAD_DIR_CONTRATOS / unique_name

    with open(file_path, "wb") as buffer:
        buffer.write(content)

    return {"pdf_url": f"/uploads/contratos/{unique_name}", "filename": unique_name}


@router.post("/", response_model=ContratoResponse, status_code=status.HTTP_201_CREATED)
def crear_contrato(
    datos: ContratoCreate,
    session: SessionDependencia,
    token: dict = Depends(Token_Dependencia)
):
    rol = token.get("rol")
    if rol == "inquilino":
        raise HTTPException(
            status_code=403, detail="Solo propietarios o admins pueden registrar contratos")

    if datos.fecha_fin <= datos.fecha_inicio:
        raise HTTPException(
            status_code=400, detail="La fecha de fin debe ser posterior a la fecha de inicio")

    prop = session.get(Propiedad, datos.propiedad_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")
    if prop.estado != EstadoVivienda.DISPONIBLE:
        raise HTTPException(
            status_code=400, detail="La propiedad no está disponible")

    if rol == "propietario" and prop.propietario_id != token.get("id"):
        raise HTTPException(
            status_code=403, detail="No puedes alquilar una propiedad que no te pertenece")

    inquilino = session.get(Usuario, datos.inquilino_id)
    if not inquilino:
        raise HTTPException(status_code=404, detail="Inquilino no encontrado")
    if inquilino.rol != RolUsuario.INQUILINO:
        raise HTTPException(
            status_code=400, detail="El usuario seleccionado no tiene rol de inquilino")

    nuevo_contrato = Contrato(**datos.model_dump())
    session.add(nuevo_contrato)

    prop.estado = EstadoVivienda.ALQUILADA
    prop.updated_at = datetime.now(timezone.utc)

    session.commit()
    session.refresh(nuevo_contrato)
    return ContratoResponse.model_validate(nuevo_contrato)


@router.get("/", response_model=list[ContratoResponse])
def listar_contratos(
    session: SessionDependencia,
    token: dict = Depends(Token_Dependencia)
):
    rol = token.get("rol")
    if rol != "administrador":
        raise HTTPException(
            status_code=403, detail="Acceso denegado. Solo el administrador puede listar todos los contratos")

    statement = select(Contrato)
    return session.exec(statement).all()


@router.patch("/{id}", response_model=ContratoResponse)
def actualizar_estado_contrato(
    id: int,
    datos: ContratoUpdate,
    session: SessionDependencia,
    token: dict = Depends(Token_Dependencia)
):
    contrato = session.get(Contrato, id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    rol = token.get("rol")
    mi_id = token.get("id")

    if rol == "propietario":
        prop = session.get(Propiedad, contrato.propiedad_id)
        if not prop or prop.propietario_id != mi_id:
            raise HTTPException(
                status_code=403, detail="No tienes permiso sobre este contrato")
    elif rol == "inquilino" and contrato.inquilino_id != mi_id:
        raise HTTPException(
            status_code=403, detail="No puedes modificar contratos ajenos")

    update_data = datos.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(contrato, key, value)

    contrato.updated_at = datetime.now(timezone.utc)

    if datos.estado in [EstadoContrato.FINALIZADO, EstadoContrato.CANCELADO]:
        prop = session.get(Propiedad, contrato.propiedad_id)
        if prop:
            prop.estado = EstadoVivienda.DISPONIBLE
            prop.updated_at = datetime.now(timezone.utc)

    session.commit()
    session.refresh(contrato)
    return ContratoResponse.model_validate(contrato)


@router.post("/{id}/generar-password-firma", response_model=dict)
def generar_password_firma(
    id: int,
    session: SessionDependencia,
    token: dict = Depends(Token_Dependencia)
):
    contrato = session.get(Contrato, id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    rol = token.get("rol")
    user_id = token.get("id")
    prop = session.get(Propiedad, contrato.propiedad_id)

    if rol != "administrador" and (not prop or prop.propietario_id != user_id):
        raise HTTPException(
            status_code=403, detail="No tienes permiso para generar contraseña")

    password_generada = secrets.token_urlsafe(9)

    password_hash = hashlib.sha256(
        password_generada.encode('utf-8')).hexdigest()

    contrato.password_firma_hash = password_hash
    session.commit()

    return {
        "contrato_id": id,
        "password_firma": password_generada,
        "mensaje": "⚠️ Guarda esta contraseña. No se volverá a mostrar."
    }


@router.post("/{id}/firmar", response_model=ContratoResponse)
def firmar_contrato(
    id: int,
    firma_data: FirmaRequest,
    session: SessionDependencia,
    token: dict = Depends(Token_Dependencia)
):
    contrato = session.get(Contrato, id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    if not contrato.password_firma_hash:
        raise HTTPException(
            status_code=400, detail="Este contrato aún no tiene contraseña de firma asignada")

    input_hash = hashlib.sha256(
        firma_data.password_firma.encode('utf-8')).hexdigest()
    if input_hash != contrato.password_firma_hash:
        raise HTTPException(
            status_code=403, detail="Contraseña de firma incorrecta")

    user_id = token.get("id")
    rol = token.get("rol")
    prop = session.get(Propiedad, contrato.propiedad_id)

    if not prop:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")
    if rol != "administrador" and prop.propietario_id != user_id:
        raise HTTPException(
            status_code=403, detail="No tienes permiso para firmar")

    contrato.firmado_por = user_id
    contrato.fecha_firma = datetime.now(timezone.utc)
    contrato.estado = EstadoContrato.FIRMADO

    session.commit()
    session.refresh(contrato)
    return ContratoResponse.model_validate(contrato)
