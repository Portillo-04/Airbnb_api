from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import select
from config.session_Dependencia import SessionDependencia
from config.security_Dependencia import Token_Dependencia
from models.solicitud_visita import SolicitudVisita, SolicitudVisitaCreate, SolicitudVisitaResponse, EstadoSolicitudVisita
from models.propiedad import Propiedad
from datetime import datetime

router = APIRouter()


@router.post("/solicitudes-visita", response_model=SolicitudVisitaResponse, status_code=status.HTTP_201_CREATED)
def solicitar_visita(
    datos: SolicitudVisitaCreate,
    session: SessionDependencia,
    token: dict = Depends(Token_Dependencia)
):
    rol = token.get("rol")

    if rol == "propietario":
        raise HTTPException(
            status_code=403, detail="Los propietarios no solicitan visitas a sus propias propiedades")

    if datos.fecha_solicitada <= datetime.now():
        raise HTTPException(
            status_code=400, detail="La fecha de visita debe ser futura")

    prop = session.get(Propiedad, datos.propiedad_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")

    nueva = SolicitudVisita(
        **datos.model_dump(),
        visitante_id=token.get("id"),
        estado=EstadoSolicitudVisita.PENDIENTE
    )
    session.add(nueva)
    session.commit()
    session.refresh(nueva)
    return SolicitudVisitaResponse.model_validate(nueva)


@router.get("/solicitudes-visita", response_model=list[SolicitudVisitaResponse])
def listar_solicitudes_visita(session: SessionDependencia, token: dict = Depends(Token_Dependencia)):
    rol = token.get("rol")
    mi_id = token.get("id")
    statement = select(SolicitudVisita)

    if rol == "propietario":
        from sqlmodel import col
        statement = statement.join(Propiedad).where(
            Propiedad.propietario_id == mi_id)
    else:
        statement = statement.where(SolicitudVisita.visitante_id == mi_id)

    return session.exec(statement).all()


@router.patch("/solicitudes-visita/{id}", response_model=SolicitudVisitaResponse)
def responder_visita(
    id: int,
    datos: dict,
    session: SessionDependencia,
    token: dict = Depends(Token_Dependencia)
):
    solicitud = session.get(SolicitudVisita, id)
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    rol = token.get("rol")
    mi_id = token.get("id")

    if rol != "propietario" and rol != "administrador":
        raise HTTPException(
            status_code=403, detail="No tienes permiso para responder visitas")

    if rol == "propietario":
        prop = session.get(Propiedad, solicitud.propiedad_id)
        if not prop or prop.propietario_id != mi_id:
            raise HTTPException(
                status_code=403, detail="No eres el dueño de esta propiedad")

    if "estado" in datos:
        solicitud.estado = datos["estado"]
    if "respuesta_propietario" in datos:
        solicitud.respuesta_propietario = datos["respuesta_propietario"]

    session.commit()
    session.refresh(solicitud)
    return SolicitudVisitaResponse.model_validate(solicitud)
