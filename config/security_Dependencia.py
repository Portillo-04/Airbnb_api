from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends
from config.security import get_current_user

OAuth2FormDependencia = Annotated[OAuth2PasswordRequestForm, Depends()]
Token_Dependencia = Annotated[dict, Depends(get_current_user)]
