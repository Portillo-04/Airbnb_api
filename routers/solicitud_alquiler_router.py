from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import select
from config.session_Dependencia import SessionDependencia
from config.security_Dependencia import Token_Dependencia
from models.solicitud_alquiler import SolicitudAlquiler, SolicitudAlquilerCreate, SolicitudAlquilerResponse, EstadoSolicitudAlquiler
from models.propiedad import Propiedad, EstadoVivienda
from models.usuario import Usuario
from datetime import datetime

router = APIRouter(prefix="/solicitudes-alquiler",
                   tags=["solicitudes-alquiler"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="usuarios/login")


@router.post(
    "/",
    response_model=SolicitudAlquilerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Solicitar Alquiler"
)
def solicitar_alquiler(
    datos: SolicitudAlquilerCreate,
    session: SessionDependencia,
    _: str = Depends(oauth2_scheme),
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


@router.get(
    "/",
    response_model=list[SolicitudAlquilerResponse],
    summary="Listar Solicitudes Alquiler"
)
def listar_solicitudes(
    session: Session = Depends(get_session),
    token: dict = Depends(get_current_user),
    limit: int = 100,
    offset: int = 0
):
    rol = token.get("rol")
    mi_id = token.get("id")

    statement = select(SolicitudAlquiler)

    if rol == "inquilino":
        statement = statement.where(SolicitudAlquiler.inquilino_id == mi_id)
    elif rol == "propietario":
        statement = statement.join(Propiedad).where(
            Propiedad.propietario_id == mi_id)

    statement = statement.offset(offset).limit(limit)

    solicitudes = session.exec(statement).all()

    if solicitudes:
        inquilino_ids = list(set(s.inquilino_id for s in solicitudes))
        usuarios = session.exec(select(Usuario).where(
            Usuario.id.in_(inquilino_ids))).all()
        mapa_nombres = {u.id: u.nombre for u in usuarios}

        for s in solicitudes:
            s.inquilino_nombre = mapa_nombres.get(
                s.inquilino_id, "Inquilino Desconocido")

    return solicitudes


@router.patch(
    "/{id}",
    response_model=SolicitudAlquilerResponse,
    summary="Responder Solicitud Alquiler"
)
def responder_solicitud_alquiler(
    id: int,
    datos: dict,
    session: SessionDependencia,
    _: str = Depends(oauth2_scheme),
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


@router.get("/test-limpio", summary="Prueba Sin Annotated")
def test_limpio(
    limit: int = 100,
    offset: int = 0
):
    return {"mensaje": "Si no ves args/kwargs aquí, Annotated es el culpable"}
