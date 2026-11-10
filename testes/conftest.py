"""Peças de teste: relógio parado, ids previsíveis e fábricas de entidades."""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

os.environ["ENJOY_REPOSITORIO"] = "memoria"
os.environ.pop("ANTHROPIC_API_KEY", None)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from enjoy.adaptadores.repositorios import memoria  # noqa: E402
from enjoy.casos_de_uso.portas import GeradorDeIds, Relogio  # noqa: E402
from enjoy.entidades import Aluno, Desempenho, Empresa, Escola, Vaga  # noqa: E402


class RelogioParado(Relogio):
    def agora(self) -> datetime:
        return datetime(2026, 11, 8, 10, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))


class IdsSequenciais(GeradorDeIds):
    def __init__(self) -> None:
        self.n = 0

    def novo_id(self) -> str:
        self.n += 1
        return f"id-{self.n}"


def desempenho(media=8.5, frequencia=95, atitude=5, regular=None) -> Desempenho:
    return Desempenho(media, media if regular is None else regular, frequencia,
                      atitude, atitude, atitude)


def aluno(id="a1", nome="Ana Souza", escola_id="e-centro", habilidades=("Python", "SQL"),
          turnos=("tarde",), modalidades=("presencial",), modulo=2, autorizado=True,
          desemp=None) -> Aluno:
    return Aluno(id=id, nome=nome, escola_id=escola_id, curso="Técnico em DS", modulo=modulo,
                 turnos=turnos, modalidades=modalidades, habilidades=habilidades,
                 desempenho=desemp or desempenho(), autorizado=autorizado)


def vaga(id="v1", empresa_id="emp1", modalidade="presencial", turno="tarde",
         obrigatorias=("Python", "SQL", "Git"), desejaveis=("Docker",)) -> Vaga:
    return Vaga(id=id, empresa_id=empresa_id, titulo="Estágio back-end",
                modalidade=modalidade, turno=turno, obrigatorias=obrigatorias, desejaveis=desejaveis)


@pytest.fixture
def repos():
    r = {
        "escolas": memoria.EscolasEmMemoria(),
        "alunos": memoria.AlunosEmMemoria(),
        "empresas": memoria.EmpresasEmMemoria(),
        "vagas": memoria.VagasEmMemoria(),
        "pedidos": memoria.PedidosEmMemoria(),
    }
    r["escolas"].salvar(Escola("e-centro", "EE Praça", "Centro"))
    r["escolas"].salvar(Escola("e-pimentas", "EE Pimentas", "Pimentas"))
    r["empresas"].salvar(Empresa("emp1", "Trilha Software", "Centro", "Software"))
    r["empresas"].salvar(Empresa("emp2", "Pista Azul", "Cumbica", "Logística"))
    return r
