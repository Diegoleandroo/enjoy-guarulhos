"""Casos de uso do lado da empresa: onde estão os alunos em Guarulhos e quem combina comigo."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from enjoy.entidades import Aluno, Escola, NaoEncontrado, habilidades as hab

from .portas import AlunoRepository, EscolaRepository


@dataclass(frozen=True)
class FiltroTalentos:
    habilidades: tuple[str, ...] = ()
    bairro: str = ""
    escola_id: str = ""
    turno: str = ""
    modalidade: str = ""
    modulo_minimo: int = 1
    media_minima: float = 0.0
    so_destaques: bool = False


@dataclass(frozen=True)
class TalentoEncontrado:
    aluno: Aluno
    escola: Escola
    aderencia: int  # % das habilidades buscadas que o aluno tem
    combinam: tuple[str, ...]


def alunos_autorizados(alunos: AlunoRepository, escolas: EscolaRepository):
    """Só aparecem para empresas os alunos com autorização do responsável."""
    mapa = {e.id: e for e in escolas.listar()}
    for aluno in alunos.listar():
        escola = mapa.get(aluno.escola_id)
        if aluno.autorizado and escola:
            yield aluno, escola


def ordem_de_desempenho(aluno: Aluno):
    d = aluno.desempenho
    return (not d.destaque, -d.media_geral, -d.atitude, aluno.nome)


class BuscarTalentos:
    def __init__(self, alunos: AlunoRepository, escolas: EscolaRepository) -> None:
        self.alunos, self.escolas = alunos, escolas

    def executar(self, filtro: FiltroTalentos) -> list[TalentoEncontrado]:
        buscadas = hab.normalizar_todas(filtro.habilidades)
        achados: list[TalentoEncontrado] = []
        for aluno, escola in alunos_autorizados(self.alunos, self.escolas):
            d = aluno.desempenho
            if filtro.bairro and escola.bairro != filtro.bairro:
                continue
            if filtro.escola_id and escola.id != filtro.escola_id:
                continue
            if filtro.turno and filtro.turno not in aluno.turnos:
                continue
            if filtro.modalidade and filtro.modalidade not in aluno.modalidades:
                continue
            if aluno.modulo < filtro.modulo_minimo or d.media_geral < filtro.media_minima:
                continue
            if filtro.so_destaques and not d.destaque:
                continue
            combinam = tuple(h for h in buscadas if h in aluno.habilidades)
            if buscadas and not combinam:
                continue
            aderencia = round(100 * len(combinam) / len(buscadas)) if buscadas else 100
            achados.append(TalentoEncontrado(aluno, escola, aderencia, combinam))
        achados.sort(key=lambda t: (-t.aderencia, *ordem_de_desempenho(t.aluno)))
        return achados


@dataclass
class ResumoEscola:
    escola: Escola
    total: int = 0
    com_habilidades: int = 0
    destaques: int = 0
    habilidades: Counter = field(default_factory=Counter)

    @property
    def principais(self) -> list[str]:
        return [h for h, _ in self.habilidades.most_common(4)]


@dataclass
class ResumoBairro:
    bairro: str
    total: int = 0
    com_habilidades: int = 0
    destaques: int = 0
    escolas: list[ResumoEscola] = field(default_factory=list)


@dataclass
class MapaDeTalentos:
    habilidades: tuple[str, ...]
    total: int
    com_habilidades: int
    destaques: int
    bairros: list[ResumoBairro]
    habilidades_mais_comuns: list[tuple[str, int]]


class MapearTalentos:
    """Responde à empresa: em quais bairros e escolas de Guarulhos estão os alunos que procuro?

    Conta, por escola e bairro, quantos alunos autorizados têm TODAS as habilidades
    pedidas e quantos são destaque. Assim a empresa sabe com qual escola conversar.
    """

    def __init__(self, alunos: AlunoRepository, escolas: EscolaRepository) -> None:
        self.alunos, self.escolas = alunos, escolas

    def executar(self, habilidades: tuple[str, ...] = ()) -> MapaDeTalentos:
        buscadas = set(hab.normalizar_todas(habilidades))
        por_escola: dict[str, ResumoEscola] = {}
        geral = Counter()
        for aluno, escola in alunos_autorizados(self.alunos, self.escolas):
            r = por_escola.setdefault(escola.id, ResumoEscola(escola))
            r.total += 1
            r.destaques += aluno.desempenho.destaque
            r.habilidades.update(aluno.habilidades)
            geral.update(aluno.habilidades)
            if buscadas and buscadas <= set(aluno.habilidades):
                r.com_habilidades += 1

        bairros: dict[str, ResumoBairro] = {}
        for r in por_escola.values():
            b = bairros.setdefault(r.escola.bairro, ResumoBairro(r.escola.bairro))
            b.total += r.total
            b.com_habilidades += r.com_habilidades
            b.destaques += r.destaques
            b.escolas.append(r)

        chave = (lambda x: (-x.com_habilidades, -x.total)) if buscadas else (lambda x: -x.total)
        ordenados = sorted(bairros.values(), key=chave)
        for b in ordenados:
            b.escolas.sort(key=chave)

        return MapaDeTalentos(
            habilidades=tuple(sorted(buscadas)),
            total=sum(b.total for b in ordenados),
            com_habilidades=sum(b.com_habilidades for b in ordenados),
            destaques=sum(b.destaques for b in ordenados),
            bairros=ordenados,
            habilidades_mais_comuns=geral.most_common(8),
        )


class VerPerfilPublico:
    def __init__(self, alunos: AlunoRepository, escolas: EscolaRepository) -> None:
        self.alunos, self.escolas = alunos, escolas

    def executar(self, aluno_id: str) -> tuple[Aluno, Escola]:
        aluno = self.alunos.buscar(aluno_id)
        if not aluno or not aluno.autorizado:
            raise NaoEncontrado("Perfil não encontrado ou sem autorização para aparecer.")
        escola = self.escolas.buscar(aluno.escola_id)
        if not escola:
            raise NaoEncontrado("Escola do aluno não encontrada.")
        return aluno, escola
