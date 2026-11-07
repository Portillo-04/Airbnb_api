from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select
from config.session_Dependencia import SessionDependencia
from config.permissions import RequireAdmin, RequireAutenticado
from lib.pwd import get_password_hash, verify_password
from models.usuario import Usuario, UsuarioCreate, UsuarioUpdate, UsuarioResponse, RolUsuario
from config.security import create_access_token

router = APIRouter()


def validar_email_unico(session, email: str, exclude_id: int = None):
    """Verifica que el email no exista, excepto para el propio usuario en updates"""
    stmt = select(Usuario).where(Usuario.email == email)
    if exclude_id:
        stmt = stmt.where(Usuario.id != exclude_id)
    if session.exec(stmt).first():
        raise HTTPException(
            status_code=400, detail="El email ya está registrado")


@router.post(
    "/usuarios/register",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar Usuario"
)
def register_usuario(datos: UsuarioCreate, session: SessionDependencia):

    if session.exec(select(Usuario).where(Usuario.nombre == datos.nombre)).first():
        raise HTTPException(
            status_code=400, detail="El nombre de usuario ya está en uso")

    validar_email_unico(session, datos.email)

    if datos.rol == RolUsuario.ADMINISTRADOR:
        raise HTTPException(
            status_code=403, detail="No puedes registrarte como administrador")

    rol_seguro = datos.rol if datos.rol in [
        RolUsuario.INQUILINO, RolUsuario.PROPIETARIO] else RolUsuario.INQUILINO

    nuevo = Usuario(
        **datos.model_dump(exclude={'password', 'rol'}),
        password_hashed=get_password_hash(datos.password),
        rol=rol_seguro,
        activo=True
    )
    session.add(nuevo)
    session.commit()
    session.refresh(nuevo)
    return UsuarioResponse.model_validate(nuevo)


@router.post(
    "/usuarios/admin",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequireAdmin)],
    summary="Crear Usuario Admin"
)
def create_usuario_admin(datos: UsuarioCreate, session: SessionDependencia):
    if session.exec(select(Usuario).where(Usuario.nombre == datos.nombre)).first():
        raise HTTPException(
            status_code=400, detail="El nombre de usuario ya está en uso")

    validar_email_unico(session, datos.email)

    nuevo = Usuario(
        **datos.model_dump(exclude={'password'}),
        password_hashed=get_password_hash(datos.password),
        activo=True
    )
    session.add(nuevo)
    session.commit()
    session.refresh(nuevo)
    return UsuarioResponse.model_validate(nuevo)


@router.get(
    "/usuarios/{id}",
    response_model=UsuarioResponse,
    dependencies=[Depends(RequireAutenticado)],
    summary="Obtener Usuario por ID"
)
def get_usuario(id: int, session: SessionDependencia, token: dict = Depends(RequireAutenticado)):
    soy_admin = token.get("rol") == "administrador"
    mi_id = token.get("id")

    if not soy_admin and mi_id != id:
        raise HTTPException(
            status_code=403, detail="No tienes permiso para ver este perfil")

    usuario = session.get(Usuario, id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return UsuarioResponse.model_validate(usuario)


@router.put(
    "/usuarios/{id}",
    response_model=UsuarioResponse,
    dependencies=[Depends(RequireAutenticado)],
    summary="Actualizar Usuario"
)
def update_usuario(id: int, datos: UsuarioUpdate, session: SessionDependencia, token: dict = Depends(RequireAutenticado)):
    soy_admin = token.get("rol") == "administrador"
    mi_id = token.get("id")

    if not soy_admin and mi_id != id:
        raise HTTPException(
            status_code=403, detail="Sin autorización para editar este perfil")

    usuario = session.get(Usuario, id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    data = datos.model_dump(exclude_unset=True)

    if "password" in data and data["password"]:
        if not soy_admin:
            raise HTTPException(
                status_code=403,
                detail="Solo el administrador tiene privilegios para cambiar contraseñas"
            )

        data["password_hashed"] = get_password_hash(data.pop("password"))

    if "rol" in data:
        if not soy_admin:
            raise HTTPException(
                status_code=403, detail="No tienes permiso para cambiar roles de usuario")

        nuevo_rol = data["rol"]
        if nuevo_rol == RolUsuario.ADMINISTRADOR and not soy_admin:
            raise HTTPException(
                status_code=403, detail="Solo administradores pueden asignar este rol")
        if not soy_admin and nuevo_rol not in [RolUsuario.INQUILINO, RolUsuario.PROPIETARIO]:
            raise HTTPException(
                status_code=403, detail="Transición de rol no permitida")

    if "email" in data and data["email"] != usuario.email:
        validar_email_unico(session, data["email"], exclude_id=id)

    for k, v in data.items():
        setattr(usuario, k, v)

    session.commit()
    session.refresh(usuario)
    return UsuarioResponse.model_validate(usuario)


@router.patch(
    "/usuarios/{id}",
    response_model=UsuarioResponse,
    dependencies=[Depends(RequireAutenticado)],
    summary="Actualizar Parcialmente"
)
def patch_usuario(id: int, datos: UsuarioUpdate, session: SessionDependencia, token: dict = Depends(RequireAutenticado)):
    soy_admin = token.get("rol") == "administrador"
    mi_id = token.get("id")

    if not soy_admin and mi_id != id:
        raise HTTPException(status_code=403, detail="Sin autorización")

    usuario = session.get(Usuario, id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    data = datos.model_dump(exclude_unset=True)

    if "password" in data and data["password"]:
        if not soy_admin:
            raise HTTPException(
                status_code=403,
                detail="Solo el administrador tiene privilegios para cambiar contraseñas"
            )
        data["password_hashed"] = get_password_hash(data.pop("password"))

    if "rol" in data:
        if not soy_admin:
            raise HTTPException(
                status_code=403, detail="No tienes permiso para cambiar roles de usuario")

        nuevo_rol = data["rol"]
        if nuevo_rol == RolUsuario.ADMINISTRADOR and not soy_admin:
            raise HTTPException(
                status_code=403, detail="Solo administradores pueden asignar este rol")
        if not soy_admin and nuevo_rol not in [RolUsuario.INQUILINO, RolUsuario.PROPIETARIO]:
            raise HTTPException(
                status_code=403, detail="Transición de rol no permitida")

    if "email" in data and data["email"] != usuario.email:
        validar_email_unico(session, data["email"], exclude_id=id)

    for k, v in data.items():
        setattr(usuario, k, v)

    session.commit()
    session.refresh(usuario)
    return UsuarioResponse.model_validate(usuario)


@router.delete(
    "/usuarios/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(RequireAdmin)],
    summary="Eliminar Usuario"
)
def delete_usuario(id: int, session: SessionDependencia):

    if id == 1:
        raise HTTPException(
            status_code=403, detail="No se puede eliminar la cuenta del administrador principal")

    usuario = session.get(Usuario, id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    session.delete(usuario)
    session.commit()


@router.post(
    "/usuarios/login",
    summary="Iniciar Sesión"
)
def login(session: SessionDependencia, form_data: OAuth2PasswordRequestForm = Depends()):
    usuario = session.exec(select(Usuario).where(
        Usuario.email == form_data.username)).first()

    if not usuario or not verify_password(form_data.password, usuario.password_hashed):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    if not usuario.activo:
        raise HTTPException(status_code=403, detail="Usuario inactivo")

    token = create_access_token(
        data={"sub": usuario.email, "id": usuario.id, "rol": usuario.rol}
    )
    return {"access_token": token, "token_type": "bearer"}
