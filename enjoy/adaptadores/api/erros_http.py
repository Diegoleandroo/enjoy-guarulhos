"""Traduz erros de negócio em respostas HTTP."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from enjoy.entidades import Conflito, DadosInvalidos, ErroDeNegocio, NaoEncontrado

CODIGOS = {NaoEncontrado: 404, Conflito: 409, DadosInvalidos: 422}


def registrar_tratadores(app: FastAPI) -> None:
    @app.exception_handler(ErroDeNegocio)
    async def tratar(_: Request, erro: ErroDeNegocio):
        codigo = next((v for k, v in CODIGOS.items() if isinstance(erro, k)), 400)
        return JSONResponse(status_code=codigo, content={"erro": str(erro)})
