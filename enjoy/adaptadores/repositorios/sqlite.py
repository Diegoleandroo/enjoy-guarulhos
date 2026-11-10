"""Repositórios em SQLite: os dados sobrevivem ao reiniciar.

Cada tabela guarda colunas para o que é filtrado e um JSON com o restante.
Os casos de uso não sabem que isso existe: só conhecem as portas.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from enjoy.casos_de_uso.portas import (
    AlunoRepository,
    EmpresaRepository,
    EscolaRepository,
    PedidoRepository,
    VagaRepository,
)
from enjoy.entidades import Aluno, Desempenho, Empresa, Escola, Pedido, Projeto, StatusPedido, Vaga

TABELAS = ("escolas", "alunos", "empresas", "vagas", "pedidos")


class BancoSqlite:
    def __init__(self, caminho: str) -> None:
        if caminho != ":memory:":
            Path(caminho).parent.mkdir(parents=True, exist_ok=True)
        self.conexao = sqlite3.connect(caminho, check_same_thread=False)
        self.trava = threading.Lock()
        with self.trava, self.conexao:
            for tabela in TABELAS:
                self.conexao.execute(
                    f"CREATE TABLE IF NOT EXISTS {tabela} (id TEXT PRIMARY KEY, dados TEXT NOT NULL)"
                )

    def gravar(self, tabela: str, item_id: str, dados: dict) -> None:
        with self.trava, self.conexao:
            self.conexao.execute(
                f"INSERT INTO {tabela} (id, dados) VALUES (?, ?) "
                "ON CONFLICT(id) DO UPDATE SET dados = excluded.dados",
                (item_id, json.dumps(dados, ensure_ascii=False)),
            )

    def ler(self, tabela: str, item_id: str) -> dict | None:
        with self.trava:
            linha = self.conexao.execute(
                f"SELECT dados FROM {tabela} WHERE id = ?", (item_id,)
            ).fetchone()
        return json.loads(linha[0]) if linha else None

    def ler_todos(self, tabela: str) -> list[dict]:
        with self.trava:
            linhas = self.conexao.execute(f"SELECT dados FROM {tabela} ORDER BY rowid").fetchall()
        return [json.loads(l[0]) for l in linhas]


class _Sqlite:
    tabela = ""

    def __init__(self, banco: BancoSqlite) -> None:
        self.banco = banco

    def para_dict(self, item) -> dict:
        return asdict(item)

    def de_dict(self, dados: dict):
        raise NotImplementedError

    def salvar(self, item) -> None:
        self.banco.gravar(self.tabela, item.id, self.para_dict(item))

    def buscar(self, item_id: str):
        dados = self.banco.ler(self.tabela, item_id)
        return self.de_dict(dados) if dados else None

    def listar(self) -> list:
        return [self.de_dict(d) for d in self.banco.ler_todos(self.tabela)]


class EscolasSqlite(_Sqlite, EscolaRepository):
    tabela = "escolas"

    def de_dict(self, d: dict) -> Escola:
        return Escola(**d)


class AlunosSqlite(_Sqlite, AlunoRepository):
    tabela = "alunos"

    def de_dict(self, d: dict) -> Aluno:
        d = {**d, "projetos": tuple(Projeto(**p) for p in d.get("projetos", [])),
             "desempenho": Desempenho(**d["desempenho"])}
        for campo in ("turnos", "modalidades", "habilidades"):
            d[campo] = tuple(d[campo])
        return Aluno(**d)


class EmpresasSqlite(_Sqlite, EmpresaRepository):
    tabela = "empresas"

    def de_dict(self, d: dict) -> Empresa:
        return Empresa(**d)


class VagasSqlite(_Sqlite, VagaRepository):
    tabela = "vagas"

    def de_dict(self, d: dict) -> Vaga:
        return Vaga(**{**d, "obrigatorias": tuple(d["obrigatorias"]),
                       "desejaveis": tuple(d["desejaveis"])})


class PedidosSqlite(_Sqlite, PedidoRepository):
    tabela = "pedidos"

    def para_dict(self, p: Pedido) -> dict:
        d = asdict(p)
        d["status"] = p.status.value
        d["criado_em"] = p.criado_em.isoformat()
        d["decidido_em"] = p.decidido_em.isoformat() if p.decidido_em else None
        return d

    def de_dict(self, d: dict) -> Pedido:
        return Pedido(**{
            **d,
            "status": StatusPedido(d["status"]),
            "criado_em": datetime.fromisoformat(d["criado_em"]),
            "decidido_em": datetime.fromisoformat(d["decidido_em"]) if d["decidido_em"] else None,
        })
