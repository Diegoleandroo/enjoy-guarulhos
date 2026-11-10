"""Aplicação web. Rodar:  uvicorn enjoy.frameworks_drivers.app:app --reload"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from enjoy.adaptadores.api.controladores import criar_rotas
from enjoy.adaptadores.api.erros_http import registrar_tratadores

from .config import Config
from .container import Container
from .seguranca import ProtecoesDaDemonstracao

WEB = Path(__file__).parent / "web"
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def criar_app(config: Config | None = None, container: Container | None = None) -> FastAPI:
    container = container or Container(config or Config.do_ambiente())

    @asynccontextmanager
    async def ciclo(_: FastAPI):
        container.inicializar()
        yield

    app = FastAPI(
        title="Enjoy API",
        description="Conecta alunos de curso técnico a empresas. Arquitetura Limpa.",
        version="1.0.0",
        lifespan=ciclo,
    )
    app.state.container = container
    app.add_middleware(ProtecoesDaDemonstracao)
    registrar_tratadores(app)
    app.include_router(criar_rotas(container))
    app.mount("/", StaticFiles(directory=WEB, html=True), name="web")
    return app


app = criar_app()
