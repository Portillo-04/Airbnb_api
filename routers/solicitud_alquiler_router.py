from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import select
from config.session_Dependencia import SessionDependencia
from config.security_Dependencia import Token_Dependencia
from models.solicitud_alquiler import SolicitudAlquiler, SolicitudAlquilerCreate, SolicitudAlquilerResponse, EstadoSolicitudAlquiler
from models.propiedad import Propiedad, EstadoVivienda
from models.usuario import Usuario, RolUsuario
from datetime import datetime

router = APIRouter()


@router.post("/solicitudes-alquiler", response_model=SolicitudAlquilerResponse, status_code=status.HTTP_201_CREATED)
def solicitar_alquiler(
    datos: SolicitudAlquilerCreate,
    session: SessionDependencia,
    token: dict = Depends(Token_Dependencia)
):
    rol = token.get("rol")

    if rol != "inquilino":
        raise HTTPException(
            status_code=403, detail="Solo los inquilinos pueden solicitar alquiler")

    if datos.fecha_fin <= datos.fecha_inicio:
        raise HTTPException(
            status_code=400, detail="La fecha de fin debe ser posterior a la de inicio")

    prop = session.get(Propiedad, datos.propiedad_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")
    if prop.estado != EstadoVivienda.DISPONIBLE:
        raise HTTPException(
            status_code=400, detail="La propiedad no está disponible")

    nueva = SolicitudAlquiler(
        **datos.model_dump(),
        inquilino_id=token.get("id"),
        estado=EstadoSolicitudAlquiler.PENDIENTE
    )
    session.add(nueva)
    session.commit()
    session.refresh(nueva)
    return SolicitudAlquilerResponse.model_validate(nueva)


@router.get("/solicitudes-alquiler", response_model=list[SolicitudAlquilerResponse])
def listar_solicitudes_alquiler(session: SessionDependencia, token: dict = Depends(Token_Dependencia)):
    rol = token.get("rol")
    mi_id = token.get("id")
    statement = select(SolicitudAlquiler)

    if rol == "inquilino":
        statement = statement.where(SolicitudAlquiler.inquilino_id == mi_id)
    elif rol == "propietario":
        from sqlmodel import col
        statement = statement.join(Propiedad).where(
            Propiedad.propietario_id == mi_id)

    return session.exec(statement).all()


@router.patch("/solicitudes-alquiler/{id}", response_model=SolicitudAlquilerResponse)
def responder_solicitud_alquiler(
    id: int,
    datos: dict,
    session: SessionDependencia,
    token: dict = Depends(Token_Dependencia)
):
    solicitud = session.get(SolicitudAlquiler, id)
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    rol = token.get("rol")
    mi_id = token.get("id")

    if rol == "inquilino":
        raise HTTPException(
            status_code=403, detail="No puedes responder solicitudes de alquiler")

    if rol == "propietario":
        prop = session.get(Propiedad, solicitud.propiedad_id)
        if not prop or prop.propietario_id != mi_id:
            raise HTTPException(
                status_code=403, detail="No tienes permiso sobre esta solicitud")

    if "estado" in datos:
        solicitud.estado = datos["estado"]
    if "respuesta_propietario" in datos:
        solicitud.respuesta_propietario = datos["respuesta_propietario"]

    session.commit()
    session.refresh(solicitud)
    return SolicitudAlquilerResponse.model_validate(solicitud)
