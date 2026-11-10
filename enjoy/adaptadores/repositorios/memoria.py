"""Repositórios em memória: rápidos, ótimos para testes. Somem ao desligar."""

from __future__ import annotations

from enjoy.casos_de_uso.portas import (
    AlunoRepository,
    EmpresaRepository,
    EscolaRepository,
    PedidoRepository,
    VagaRepository,
)


class _EmMemoria:
    def __init__(self) -> None:
        self._itens: dict = {}

    def salvar(self, item) -> None:
        self._itens[item.id] = item

    def buscar(self, item_id: str):
        return self._itens.get(item_id)

    def listar(self) -> list:
        return list(self._itens.values())


class EscolasEmMemoria(_EmMemoria, EscolaRepository): ...
class AlunosEmMemoria(_EmMemoria, AlunoRepository): ...
class EmpresasEmMemoria(_EmMemoria, EmpresaRepository): ...
class VagasEmMemoria(_EmMemoria, VagaRepository): ...
class PedidosEmMemoria(_EmMemoria, PedidoRepository): ...
