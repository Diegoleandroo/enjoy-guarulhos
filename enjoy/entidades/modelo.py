"""Entidades do Enjoy: escolas de Guarulhos, seus alunos, empresas, vagas e pedidos.

Quem cadastra e acompanha o aluno é a ESCOLA. O perfil traz o que a escola
observa no dia a dia: notas do técnico e do regular, frequência e competências comportamentais
(comprometimento, responsabilidade e disciplina).

Privacidade: muitos alunos são menores de idade. O perfil só aparece para
empresas com autorização do responsável, e todo contato passa pela escola.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import Enum

from . import habilidades as hab
from .erros import Conflito, DadosInvalidos

TURNOS = ("manha", "tarde", "noite")
MODALIDADES = ("presencial", "hibrido", "remoto")
ATITUDES = ("comprometimento", "responsabilidade", "disciplina")


def _validar_opcoes(valores, permitidos, nome: str) -> tuple[str, ...]:
    valores = tuple(dict.fromkeys(valores))
    if not valores:
        raise DadosInvalidos(f"Informe ao menos um(a) {nome}.")
    invalidos = [v for v in valores if v not in permitidos]
    if invalidos:
        raise DadosInvalidos(f"{nome.capitalize()} inválido(a): {', '.join(invalidos)}.")
    return valores


@dataclass(frozen=True)
class Escola:
    id: str
    nome: str
    bairro: str
    cidade: str = "Guarulhos"
    latitude: float = 0.0
    longitude: float = 0.0
    endereco: str = ""


@dataclass(frozen=True)
class Projeto:
    titulo: str
    descricao: str
    link: str = ""


@dataclass(frozen=True)
class Desempenho:
    """O que a escola observa. Notas de 0 a 10, frequência em %, competências comportamentais de 1 a 5."""

    media_tecnico: float
    media_regular: float
    frequencia: int
    comprometimento: int
    responsabilidade: int
    disciplina: int

    MEDIA_DESTAQUE = 8.0
    FREQUENCIA_DESTAQUE = 90
    ATITUDE_DESTAQUE = 4.0

    def __post_init__(self) -> None:
        for nome in ("media_tecnico", "media_regular"):
            if not 0 <= getattr(self, nome) <= 10:
                raise DadosInvalidos("As médias devem ficar entre 0 e 10.")
        if not 0 <= self.frequencia <= 100:
            raise DadosInvalidos("A frequência deve ficar entre 0 e 100%.")
        for nome in ATITUDES:
            if getattr(self, nome) not in (1, 2, 3, 4, 5):
                raise DadosInvalidos(f"Avalie {nome} de 1 a 5.")

    @property
    def media_geral(self) -> float:
        return round((self.media_tecnico + self.media_regular) / 2, 1)

    @property
    def atitude(self) -> float:
        return round(sum(getattr(self, a) for a in ATITUDES) / len(ATITUDES), 1)

    @property
    def destaque(self) -> bool:
        """Boas notas nos dois cursos, presença e comportamento: o aluno que a escola indica."""
        return (
            min(self.media_tecnico, self.media_regular) >= self.MEDIA_DESTAQUE
            and self.frequencia >= self.FREQUENCIA_DESTAQUE
            and self.atitude >= self.ATITUDE_DESTAQUE
        )


@dataclass(frozen=True)
class Aluno:
    id: str
    nome: str
    escola_id: str
    curso: str
    modulo: int
    turnos: tuple[str, ...]
    modalidades: tuple[str, ...]
    habilidades: tuple[str, ...]
    desempenho: Desempenho
    observacao: str = ""  # comentário da coordenação
    projetos: tuple[Projeto, ...] = ()
    autorizado: bool = True  # autorização do responsável para aparecer às empresas

    def __post_init__(self) -> None:
        if len(self.nome.split()) < 2:
            raise DadosInvalidos("Informe nome e sobrenome.")
        if self.modulo not in (1, 2, 3):
            raise DadosInvalidos("O módulo deve ser 1, 2 ou 3.")
        object.__setattr__(self, "turnos", _validar_opcoes(self.turnos, TURNOS, "turno"))
        object.__setattr__(
            self, "modalidades", _validar_opcoes(self.modalidades, MODALIDADES, "modalidade")
        )
        normalizadas = hab.normalizar_todas(self.habilidades)
        if not normalizadas:
            raise DadosInvalidos("Informe ao menos uma habilidade.")
        object.__setattr__(self, "habilidades", normalizadas)

    @property
    def nome_publico(self) -> str:
        """A empresa vê "Ana S.", nunca o nome completo."""
        partes = self.nome.split()
        return f"{partes[0]} {partes[-1][0]}."


@dataclass(frozen=True)
class Empresa:
    id: str
    nome: str
    bairro: str
    setor: str
    cidade: str = "Guarulhos"


@dataclass(frozen=True)
class Vaga:
    id: str
    empresa_id: str
    titulo: str
    modalidade: str
    turno: str
    obrigatorias: tuple[str, ...]
    desejaveis: tuple[str, ...] = ()
    descricao: str = ""
    cidade: str = "Guarulhos"
    aberta: bool = True

    def __post_init__(self) -> None:
        if not self.titulo.strip():
            raise DadosInvalidos("A vaga precisa de um título.")
        if self.modalidade not in MODALIDADES:
            raise DadosInvalidos(f"Modalidade inválida: {self.modalidade}.")
        if self.turno not in TURNOS:
            raise DadosInvalidos(f"Turno inválido: {self.turno}.")
        obrigatorias = hab.normalizar_todas(self.obrigatorias)
        if not obrigatorias:
            raise DadosInvalidos("A vaga precisa de ao menos uma habilidade obrigatória.")
        desejaveis = tuple(h for h in hab.normalizar_todas(self.desejaveis) if h not in obrigatorias)
        object.__setattr__(self, "obrigatorias", obrigatorias)
        object.__setattr__(self, "desejaveis", desejaveis)


@dataclass(frozen=True)
class Compatibilidade:
    """Quanto um aluno combina com uma vaga, e por quê."""

    percentual: int
    tem: tuple[str, ...]
    faltam_obrigatorias: tuple[str, ...]
    faltam_desejaveis: tuple[str, ...]
    turno_ok: bool
    modalidade_ok: bool

    PESO_OBRIGATORIAS = 70
    PESO_DESEJAVEIS = 30

    @classmethod
    def calcular(cls, aluno: Aluno, vaga: Vaga) -> "Compatibilidade":
        tem_set = set(aluno.habilidades)
        obrig_ok = [h for h in vaga.obrigatorias if h in tem_set]
        desej_ok = [h for h in vaga.desejaveis if h in tem_set]

        nota = cls.PESO_OBRIGATORIAS * len(obrig_ok) / len(vaga.obrigatorias)
        if vaga.desejaveis:
            nota += cls.PESO_DESEJAVEIS * len(desej_ok) / len(vaga.desejaveis)
        else:
            nota = nota * 100 / cls.PESO_OBRIGATORIAS

        turno_ok = vaga.turno in aluno.turnos
        modalidade_ok = vaga.modalidade in aluno.modalidades
        # Não adianta saber tudo e não poder estar lá no horário ou no formato da vaga.
        if not turno_ok:
            nota *= 0.5
        if not modalidade_ok:
            nota *= 0.7

        return cls(
            percentual=round(nota),
            tem=tuple(obrig_ok + desej_ok),
            faltam_obrigatorias=tuple(h for h in vaga.obrigatorias if h not in tem_set),
            faltam_desejaveis=tuple(h for h in vaga.desejaveis if h not in tem_set),
            turno_ok=turno_ok,
            modalidade_ok=modalidade_ok,
        )


class StatusPedido(str, Enum):
    PENDENTE = "pendente"
    APROVADO = "aprovado"
    RECUSADO = "recusado"


@dataclass(frozen=True)
class Pedido:
    """A empresa fala com a ESCOLA: sobre um aluno específico ou pedindo indicações para uma vaga."""

    id: str
    empresa_id: str
    escola_id: str
    mensagem: str
    criado_em: datetime
    aluno_id: str | None = None
    vaga_id: str | None = None
    status: StatusPedido = StatusPedido.PENDENTE
    resposta: str = ""
    decidido_em: datetime | None = field(default=None)

    def __post_init__(self) -> None:
        if len(self.mensagem.strip()) < 10:
            raise DadosInvalidos("Escreva uma mensagem de ao menos 10 caracteres para a escola.")
        if not self.aluno_id and not self.vaga_id:
            raise DadosInvalidos("Indique um aluno ou uma vaga para a escola saber do que se trata.")

    @property
    def tipo(self) -> str:
        return "aluno" if self.aluno_id else "indicacao"

    def aprovar(self, quando: datetime, resposta: str = "") -> "Pedido":
        return self._decidir(StatusPedido.APROVADO, quando, resposta)

    def recusar(self, quando: datetime, resposta: str = "") -> "Pedido":
        return self._decidir(StatusPedido.RECUSADO, quando, resposta)

    def _decidir(self, status: StatusPedido, quando: datetime, resposta: str) -> "Pedido":
        if self.status is not StatusPedido.PENDENTE:
            raise Conflito(f"Este pedido já foi {self.status.value}.")
        return replace(self, status=status, decidido_em=quando, resposta=resposta.strip())
