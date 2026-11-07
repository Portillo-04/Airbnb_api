from typing import Annotated
from sqlmodel import Session
from fastapi import Depends
from config.db import engine


def get_session():
    with Session(engine) as session:
        yield session


SessionDependencia = Annotated[Session, Depends(get_session)]
