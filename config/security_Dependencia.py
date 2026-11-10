from fastapi import Depends
from config.security import get_current_user

# ✅ FORMA SIMPLE Y DIRECTA (Sin Annotated)


def Token_Dependencia(token_data: dict = Depends(get_current_user)):
    return token_data
