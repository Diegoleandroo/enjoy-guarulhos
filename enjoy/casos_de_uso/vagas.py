"""Vagas, alunos cadastrados pela escola e recomendações."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from enjoy.entidades import (
    Aluno,
    Compatibilidade,
    DadosInvalidos,
    Desempenho,
    Empresa,
    Escola,
    NaoEncontrado,
    Projeto,
    Vaga,
)

from .portas import (
    AlunoRepository,
    AssistenteDeCarreira,
    EmpresaRepository,
    EscolaRepository,
    GeradorDeIds,
    PedidoRepository,
    VagaRepository,
)
from .talentos import alunos_autorizados, ordem_de_desempenho


@dataclass(frozen=True)
class NovoAluno:
    nome: str
    escola_id: str
    curso: str
    modulo: int
    turnos: tuple[str, ...]
    modalidades: tuple[str, ...]
    habilidades: tuple[str, ...]
    desempenho: Desempenho
    observacao: str = ""
    projetos: tuple[Projeto, ...] = ()
    autorizado: bool = False


class CadastrarAluno:
    """Quem cadastra é a coordenação da escola: o perfil nasce do acompanhamento dela."""

    def __init__(self, alunos: AlunoRepository, escolas: EscolaRepository, ids: GeradorDeIds):
        self.alunos, self.escolas, self.ids = alunos, escolas, ids

    def executar(self, dados: NovoAluno) -> Aluno:
        if not self.escolas.buscar(dados.escola_id):
            raise DadosInvalidos("Escola não encontrada.")
        aluno = Aluno(id=self.ids.novo_id(), **dados.__dict__)
        self.alunos.salvar(aluno)
        return aluno


class ListarAlunosDaEscola:
    def __init__(self, alunos: AlunoRepository, escolas: EscolaRepository):
        self.alunos, self.escolas = alunos, escolas

    def executar(self, escola_id: str) -> tuple[Escola, list[Aluno]]:
        escola = self.escolas.buscar(escola_id)
        if not escola:
            raise NaoEncontrado("Escola não encontrada.")
        alunos = [a for a in self.alunos.listar() if a.escola_id == escola_id]
        return escola, sorted(alunos, key=ordem_de_desempenho)


@dataclass(frozen=True)
class NovaVaga:
    empresa_id: str
    titulo: str
    modalidade: str
    turno: str
    obrigatorias: tuple[str, ...]
    desejaveis: tuple[str, ...] = ()
    descricao: str = ""


class PublicarVaga:
    def __init__(self, vagas: VagaRepository, empresas: EmpresaRepository, ids: GeradorDeIds):
        self.vagas, self.empresas, self.ids = vagas, empresas, ids

    def executar(self, dados: NovaVaga) -> Vaga:
        if not self.empresas.buscar(dados.empresa_id):
            raise DadosInvalidos("Empresa não encontrada.")
        vaga = Vaga(id=self.ids.novo_id(), **dados.__dict__)
        self.vagas.salvar(vaga)
        return vaga


class ListarVagas:
    def __init__(self, vagas: VagaRepository, empresas: EmpresaRepository):
        self.vagas, self.empresas = vagas, empresas

    def executar(self) -> list[tuple[Vaga, Empresa]]:
        empresas = {e.id: e for e in self.empresas.listar()}
        return [(v, empresas[v.empresa_id]) for v in self.vagas.listar()
                if v.aberta and v.empresa_id in empresas]


@dataclass(frozen=True)
class Candidato:
    aluno: Aluno
    escola: Escola
    compat: Compatibilidade


class RecomendarAlunosParaVaga:
    """Ordena por compatibilidade e, no empate, pelo desempenho na escola."""

    def __init__(self, vagas: VagaRepository, alunos: AlunoRepository, escolas: EscolaRepository):
        self.vagas, self.alunos, self.escolas = vagas, alunos, escolas

    def executar(self, vaga_id: str, limite: int = 12) -> tuple[Vaga, list[Candidato]]:
        vaga = self.vagas.buscar(vaga_id)
        if not vaga:
            raise NaoEncontrado("Vaga não encontrada.")
        candidatos = []
        for aluno, escola in alunos_autorizados(self.alunos, self.escolas):
            compat = Compatibilidade.calcular(aluno, vaga)
            if compat.percentual > 0:
                candidatos.append(Candidato(aluno, escola, compat))
        candidatos.sort(key=lambda c: (-c.compat.percentual, *ordem_de_desempenho(c.aluno)))
        return vaga, candidatos[:limite]


class AnalisarCompatibilidade:
    """Compara aluno e vaga e pede ao assistente (regra local ou IA) uma orientação."""

    def __init__(self, alunos: AlunoRepository, vagas: VagaRepository,
                 assistente: AssistenteDeCarreira):
        self.alunos, self.vagas, self.assistente = alunos, vagas, assistente

    def executar(self, aluno_id: str, vaga_id: str) -> tuple[Compatibilidade, str]:
        aluno = self.alunos.buscar(aluno_id)
        vaga = self.vagas.buscar(vaga_id)
        if not aluno or not vaga:
            raise NaoEncontrado("Aluno ou vaga não encontrados.")
        compat = Compatibilidade.calcular(aluno, vaga)
        return compat, self.assistente.orientar(aluno, vaga, compat)


@dataclass(frozen=True)
class Panorama:
    vagas_abertas: int
    empresas_contratando: int
    pedidos_aprovados: int
    habilidades_mais_pedidas: list[tuple[str, int]]
    vagas: list[tuple[Vaga, Empresa]]


class MostrarPanorama:
    """O que o aluno precisa saber: quais oportunidades existem em Guarulhos e o que pedem."""

    def __init__(self, vagas: VagaRepository, empresas: EmpresaRepository, pedidos: PedidoRepository):
        self.vagas, self.empresas, self.pedidos = vagas, empresas, pedidos

    def executar(self) -> Panorama:
        abertas = ListarVagas(self.vagas, self.empresas).executar()
        contagem = Counter()
        for vaga, _ in abertas:
            contagem.update(vaga.obrigatorias)
            contagem.update(vaga.desejaveis)
        return Panorama(
            vagas_abertas=len(abertas),
            empresas_contratando=len({e.id for _, e in abertas}),
            pedidos_aprovados=sum(p.status.value == "aprovado" for p in self.pedidos.listar()),
            habilidades_mais_pedidas=contagem.most_common(8),
            vagas=abertas,
        )
