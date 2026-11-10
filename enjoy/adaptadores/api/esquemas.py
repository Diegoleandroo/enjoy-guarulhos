"""Formato dos dados que ENTRAM pela API (validação com Pydantic)."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field

# Limites: ninguém consegue lotar o sistema com listas ou textos gigantes.
Habilidade = Annotated[str, Field(min_length=1, max_length=40)]
Opcao = Annotated[str, Field(max_length=20)]


class ProjetoEntrada(BaseModel):
    titulo: str = Field(min_length=2, max_length=80)
    descricao: str = Field(default="", max_length=300)
    link: str = Field(default="", max_length=200)


class DesempenhoEntrada(BaseModel):
    media_tecnico: float = Field(ge=0, le=10)
    media_regular: float = Field(ge=0, le=10)
    frequencia: int = Field(ge=0, le=100)
    comprometimento: int = Field(ge=1, le=5)
    responsabilidade: int = Field(ge=1, le=5)
    disciplina: int = Field(ge=1, le=5)


class AlunoEntrada(BaseModel):
    """Cadastro feito pela coordenação da escola."""

    nome: str = Field(min_length=3, max_length=80)
    curso: str = Field(default="Técnico em Desenvolvimento de Sistemas", max_length=80)
    modulo: int = Field(ge=1, le=3)
    turnos: list[Opcao] = Field(max_length=3)
    modalidades: list[Opcao] = Field(max_length=3)
    habilidades: list[Habilidade] = Field(max_length=20)
    desempenho: DesempenhoEntrada
    observacao: str = Field(default="", max_length=400)
    projetos: list[ProjetoEntrada] = Field(default=[], max_length=5)
    autorizado: bool = False


class VagaEntrada(BaseModel):
    empresa_id: str = Field(max_length=40)
    titulo: str = Field(min_length=3, max_length=80)
    modalidade: Opcao
    turno: Opcao
    obrigatorias: list[Habilidade] = Field(max_length=15)
    desejaveis: list[Habilidade] = Field(default=[], max_length=15)
    descricao: str = Field(default="", max_length=500)


class PedidoEntrada(BaseModel):
    empresa_id: str = Field(max_length=40)
    mensagem: str = Field(max_length=500)
    escola_id: str = Field(default="", max_length=40)
    aluno_id: str | None = Field(default=None, max_length=40)
    vaga_id: str | None = Field(default=None, max_length=40)


class RespostaEntrada(BaseModel):
    aprovar: bool
    resposta: str = Field(default="", max_length=500)
