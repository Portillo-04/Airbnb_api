from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import select
from config.session_Dependencia import SessionDependencia
from config.security_Dependencia import Token_Dependencia
from models.mantenimiento import SolicitudMantenimiento, SolicitudCreate, SolicitudUpdate, SolicitudResponse, EstadoSolicitud
from models.propiedad import Propiedad
from models.usuario import Usuario, RolUsuario

router = APIRouter()


@router.post("/mantenimiento", response_model=SolicitudResponse, status_code=status.HTTP_201_CREATED)
def crear_solicitud_mantenimiento(
    datos: SolicitudCreate,
    session: SessionDependencia,
    token: dict = Depends(Token_Dependencia)
):
    rol = token.get("rol")

    if rol != "inquilino":
        raise HTTPException(
            status_code=403, detail="Solo los inquilinos pueden solicitar mantenimiento")

    prop = session.get(Propiedad, datos.propiedad_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")

    inquilino = session.get(Usuario, datos.inquilino_id)
    if not inquilino or inquilino.rol != RolUsuario.INQUILINO:
        raise HTTPException(
            status_code=400, detail="Debe ser un usuario con rol de inquilino")

    if inquilino.id != token.get("id"):
        raise HTTPException(
            status_code=403, detail="No puedes solicitar mantenimiento a nombre de otro usuario")

    nueva = SolicitudMantenimiento(**datos.model_dump())
    session.add(nueva)
    session.commit()
    session.refresh(nueva)
    return SolicitudResponse.model_validate(nueva)


@router.get("/mantenimiento", response_model=list[SolicitudResponse])
def listar_solicitudes(session: SessionDependencia, token: dict = Depends(Token_Dependencia)):
    rol = token.get("rol")
    mi_id = token.get("id")
    statement = select(SolicitudMantenimiento)

    if rol == "inquilino":
        statement = statement.where(
            SolicitudMantenimiento.inquilino_id == mi_id)
    elif rol == "propietario":

        from sqlmodel import col
        statement = statement.join(Propiedad).where(
            Propiedad.propietario_id == mi_id)

    return session.exec(statement).all()


@router.patch("/mantenimiento/{id}", response_model=SolicitudResponse)
def actualizar_estado_mantenimiento(
    id: int,
    datos: SolicitudUpdate,
    session: SessionDependencia,
    token: dict = Depends(Token_Dependencia)
):
    solicitud = session.get(SolicitudMantenimiento, id)
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    rol = token.get("rol")
    mi_id = token.get("id")

    if rol == "inquilino":

        raise HTTPException(
            status_code=403, detail="No tienes permiso para cambiar el estado de esta solicitud")

    if rol == "propietario":
        prop = session.get(Propiedad, solicitud.propiedad_id)
        if not prop or prop.propietario_id != mi_id:
            raise HTTPException(
                status_code=403, detail="No tienes permiso sobre esta solicitud")

    update_data = datos.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(solicitud, k, v)

    session.commit()
    session.refresh(solicitud)
    return SolicitudResponse.model_validate(solicitud)
