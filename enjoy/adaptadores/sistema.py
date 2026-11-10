from __future__ import annotations

import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from enjoy.casos_de_uso.portas import GeradorDeIds, Relogio


class RelogioDoSistema(Relogio):
    def __init__(self, fuso: str = "America/Sao_Paulo") -> None:
        self.fuso = ZoneInfo(fuso)

    def agora(self) -> datetime:
        return datetime.now(self.fuso)


class IdsAleatorios(GeradorDeIds):
    def novo_id(self) -> str:
        return uuid.uuid4().hex[:12]
