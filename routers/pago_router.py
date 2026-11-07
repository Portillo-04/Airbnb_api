from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import select
from config.session_Dependencia import SessionDependencia
from config.security_Dependencia import Token_Dependencia
from models.pago import Pago, PagoCreate, PagoResponse
from models.contrato import Contrato, EstadoContrato

router = APIRouter()


@router.post("/pagos", response_model=PagoResponse, status_code=status.HTTP_201_CREATED)
def registrar_pago(
    datos: PagoCreate,
    session: SessionDependencia,
    token: dict = Depends(Token_Dependencia)
):
    rol = token.get("rol")
    mi_id = token.get("id")

    contrato = session.get(Contrato, datos.contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    if contrato.estado != EstadoContrato.ACTIVO:
        raise HTTPException(
            status_code=400, detail="Solo se pueden registrar pagos en contratos activos")

    if rol == "propietario":
        raise HTTPException(
            status_code=403, detail="Los propietarios no registran pagos de inquilinos")

    if rol == "inquilino" and contrato.inquilino_id != mi_id:
        raise HTTPException(
            status_code=403, detail="No puedes pagar un contrato que no es tuyo")

    if datos.paypal_transaction_id:
        pago_existente = session.exec(
            select(Pago).where(Pago.paypal_transaction_id ==
                               datos.paypal_transaction_id)
        ).first()

        if pago_existente:
            raise HTTPException(
                status_code=409, detail="Este pago de PayPal ya fue registrado")

    data_dict = datos.model_dump()
    data_dict["usuario_id"] = mi_id

    nuevo_pago = Pago(**data_dict)
    session.add(nuevo_pago)
    session.commit()
    session.refresh(nuevo_pago)

    return PagoResponse.model_validate(nuevo_pago)


@router.get("/pagos/contrato/{contrato_id}", response_model=list[PagoResponse])
def historial_pagos(
    contrato_id: int,
    session: SessionDependencia,
    token: dict = Depends(Token_Dependencia)
):
    rol = token.get("rol")
    mi_id = token.get("id")

    contrato = session.get(Contrato, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    if rol == "inquilino" and contrato.inquilino_id != mi_id:
        raise HTTPException(
            status_code=403, detail="No puedes ver pagos de otros contratos")

    if rol == "propietario":

        from models.propiedad import Propiedad
        prop = session.get(Propiedad, contrato.propiedad_id)
        if not prop or prop.propietario_id != mi_id:
            raise HTTPException(
                status_code=403, detail="No tienes acceso a este contrato")

    statement = select(Pago).where(Pago.contrato_id == contrato_id)
    return session.exec(statement).all()
