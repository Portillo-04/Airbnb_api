from fastapi import Depends, HTTPException, status
from config.security import oauth2_scheme, decode_access_token
from models.usuario import RolUsuario


def require_role(*allowed_roles: RolUsuario):
    def role_checker(token: str = Depends(oauth2_scheme)):
        try:
            payload = decode_access_token(token)
            user_role = payload.get("rol")

            if user_role not in [role.value for role in allowed_roles]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Acceso denegado. Roles permitidos: {[r.value for r in allowed_roles]}"
                )
            return payload
        except Exception:
            raise HTTPException(
                status_code=401, detail="Token inválido o expirado")

    return role_checker


RequireAdmin = require_role(RolUsuario.ADMINISTRADOR)
RequirePropietario = require_role(RolUsuario.PROPIETARIO)
RequireInquilino = require_role(RolUsuario.INQUILINO)
RequireAutenticado = require_role(
    RolUsuario.ADMINISTRADOR,
    RolUsuario.PROPIETARIO,
    RolUsuario.INQUILINO,
)
RequireAdminOPropietario = require_role(
    RolUsuario.ADMINISTRADOR, RolUsuario.PROPIETARIO)
