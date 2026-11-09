import os
import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from sqlmodel import select
from config.session_Dependencia import SessionDependencia
from config.security_Dependencia import Token_Dependencia
from models.contrato import Contrato, ContratoCreate, ContratoUpdate, ContratoResponse, EstadoContrato
from models.propiedad import Propiedad, EstadoVivienda
from models.usuario import Usuario, RolUsuario
from datetime import datetime, timezone

router = APIRouter(prefix="/contratos", tags=["contratos"])

UPLOAD_DIR_CONTRATOS = Path("uploads/contratos")
MAX_PDF_SIZE = 10 * 1024 * 1024  # 10MB


# ✅ SUBIR CONTRATO FIRMADO EN FÍSICO
@router.post(
    "/upload-pdf",
    summary="Subir Contrato Firmado (Físico)",
    dependencies=[Depends(Token_Dependencia)]
)
async def subir_contrato_firmado(
    file: UploadFile = File(...),
    contrato_id: int = Form(...),
    session: SessionDependencia,
    token: dict = Depends(Token_Dependencia)
):
    rol = token.get("rol")
    if rol == "inquilino":
        raise HTTPException(
            status_code=403, detail="Solo propietarios/admins pueden subir contratos firmados")

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

    # Actualizar contrato en BD
    contrato = session.get(Contrato, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    prop = session.get(Propiedad, contrato.propiedad_id)
    if rol == "propietario" and (not prop or prop.propietario_id != token.get("id")):
        raise HTTPException(
            status_code=403, detail="No eres el dueño de esta propiedad")

    contrato.pdf_url = f"/uploads/contratos/{unique_name}"
    contrato.estado = EstadoContrato.FIRMADO
    contrato.fecha_firma = datetime.now(timezone.utc)
    contrato.firmado_por = token.get("id")

    session.commit()

    return {"mensaje": "Contrato firmado físicamente subido exitosamente", "pdf_url": contrato.pdf_url}


# ✅ CREAR CONTRATO (BORRADOR)
@router.post(
    "/",
    response_model=ContratoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear Contrato",
    dependencies=[Depends(Token_Dependencia)]
)
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


# ✅ LISTAR CONTRATOS (SOLO ADMIN)
@router.get(
    "/",
    response_model=list[ContratoResponse],
    summary="Listar Contratos",
    dependencies=[Depends(Token_Dependencia)]
)
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


# ✅ VER/DESCARGAR DOCUMENTO (INQUILINO O DUEÑO)
@router.get(
    "/{id}/documento",
    summary="Ver/Descargar Contrato",
    dependencies=[Depends(Token_Dependencia)]
)
def ver_documento_contrato(
    id: int,
    session: SessionDependencia,
    token: dict = Depends(Token_Dependencia)
):
    contrato = session.get(Contrato, id)
    if not contrato or not contrato.pdf_url:
        raise HTTPException(
            status_code=404, detail="Contrato o documento no disponible")

    mi_id = token.get("id")
    rol = token.get("rol")

    if rol == "inquilino" and contrato.inquilino_id != mi_id:
        raise HTTPException(
            status_code=403, detail="No tienes acceso a este contrato")

    if rol == "propietario":
        prop = session.get(Propiedad, contrato.propiedad_id)
        if not prop or prop.propietario_id != mi_id:
            raise HTTPException(
                status_code=403, detail="No tienes permiso sobre este contrato")

    return {"pdf_url": contrato.pdf_url, "estado": contrato.estado}


# ✅ ACTUALIZAR ESTADO
@router.patch(
    "/{id}",
    response_model=ContratoResponse,
    summary="Actualizar Estado Contrato",
    dependencies=[Depends(Token_Dependencia)]
)
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
