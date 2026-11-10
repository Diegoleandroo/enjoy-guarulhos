"""Configuração vinda do ambiente ou do arquivo .env.

ENJOY_REPOSITORIO = sqlite | memoria   (padrão: sqlite)
ENJOY_DB          = caminho do banco   (padrão: dados/enjoy.db)
ENJOY_EXEMPLO     = 1 | 0              (carrega dados fictícios no banco vazio; padrão: 1)
ANTHROPIC_API_KEY = liga o assistente com IA (opcional; sem ela usa regras locais)
ENJOY_IA_MODELO   = modelo do Claude  (padrão: claude-haiku-5-5)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def ler_env(arquivo: Path) -> None:
    if not arquivo.exists():
        return
    for linha in arquivo.read_text(encoding="utf-8-sig").splitlines():
        chave, sep, valor = linha.strip().partition("=")
        if sep and chave and not chave.startswith("#"):
            valor = valor.strip().strip("\"'")
            if valor:
                os.environ.setdefault(chave.strip(), valor)


@dataclass(frozen=True)
class Config:
    repositorio: str = "sqlite"
    caminho_banco: str = str(RAIZ / "dados" / "enjoy.db")
    carregar_exemplo: bool = True
    arquivo_exemplo: str = str(RAIZ / "dados" / "exemplo.json")
    chave_ia: str | None = None
    modelo_ia: str = "claude-haiku-5-5"
    fuso: str = "America/Sao_Paulo"

    @classmethod
    def do_ambiente(cls, arquivo_env: Path | None = RAIZ / ".env") -> "Config":
        if arquivo_env is not None:
            ler_env(arquivo_env)
        env = os.environ.get
        return cls(
            repositorio=env("ENJOY_REPOSITORIO", cls.repositorio),
            caminho_banco=env("ENJOY_DB", cls.caminho_banco),
            carregar_exemplo=env("ENJOY_EXEMPLO", "1") != "0",
            chave_ia=env("ANTHROPIC_API_KEY") or None,
            modelo_ia=env("ENJOY_IA_MODELO", cls.modelo_ia),
            fuso=env("ENJOY_FUSO", cls.fuso),
        )
