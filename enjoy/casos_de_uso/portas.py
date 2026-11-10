"""Portas: o que os casos de uso precisam do mundo lá fora, sem saber quem entrega.

Os adaptadores (SQLite, memória, IA local ou Claude) implementam estas interfaces.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from enjoy.entidades import Aluno, Compatibilidade, Empresa, Escola, Pedido, Vaga


class EscolaRepository(ABC):
    @abstractmethod
    def salvar(self, escola: Escola) -> None: ...
    @abstractmethod
    def buscar(self, escola_id: str) -> Escola | None: ...
    @abstractmethod
    def listar(self) -> list[Escola]: ...


class AlunoRepository(ABC):
    @abstractmethod
    def salvar(self, aluno: Aluno) -> None: ...
    @abstractmethod
    def buscar(self, aluno_id: str) -> Aluno | None: ...
    @abstractmethod
    def listar(self) -> list[Aluno]: ...


class EmpresaRepository(ABC):
    @abstractmethod
    def salvar(self, empresa: Empresa) -> None: ...
    @abstractmethod
    def buscar(self, empresa_id: str) -> Empresa | None: ...
    @abstractmethod
    def listar(self) -> list[Empresa]: ...


class VagaRepository(ABC):
    @abstractmethod
    def salvar(self, vaga: Vaga) -> None: ...
    @abstractmethod
    def buscar(self, vaga_id: str) -> Vaga | None: ...
    @abstractmethod
    def listar(self) -> list[Vaga]: ...


class PedidoRepository(ABC):
    @abstractmethod
    def salvar(self, pedido: Pedido) -> None: ...
    @abstractmethod
    def buscar(self, pedido_id: str) -> Pedido | None: ...
    @abstractmethod
    def listar(self) -> list[Pedido]: ...


class Relogio(ABC):
    @abstractmethod
    def agora(self) -> datetime: ...


class GeradorDeIds(ABC):
    @abstractmethod
    def novo_id(self) -> str: ...


class AssistenteDeCarreira(ABC):
    """Explica a compatibilidade para a escola orientar o aluno. Regra local ou IA."""

    nome: str = "Assistente"

    @abstractmethod
    def orientar(self, aluno: Aluno, vaga: Vaga, compat: Compatibilidade) -> str: ...
