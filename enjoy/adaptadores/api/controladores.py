"""Controladores REST: recebem HTTP, chamam um caso de uso, devolvem JSON.

Não há regra de negócio aqui. Se aparecer um "if" de regra, ele está no lugar errado.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Query

from enjoy.casos_de_uso import FiltroTalentos, NovaVaga, NovoAluno
from enjoy.entidades import MODALIDADES, TURNOS, Desempenho, Projeto, habilidades as hab

from . import apresentadores as ap
from .esquemas import AlunoEntrada, PedidoEntrada, RespostaEntrada, VagaEntrada

if TYPE_CHECKING:  # só para o editor: o container vem de fora
    from enjoy.frameworks_drivers.container import Container


def _lista(texto: str) -> tuple[str, ...]:
    return tuple(p.strip() for p in texto.split(",") if p.strip())


def criar_rotas(c: "Container") -> APIRouter:
    r = APIRouter(prefix="/api")

    @r.get("/referencias", summary="Escolas, bairros, empresas e habilidades")
    def referencias():
        escolas = c.escolas.listar()
        usadas = {h for a in c.alunos.listar() for h in a.habilidades}
        return {
            "escolas": [ap.escola(e) for e in sorted(escolas, key=lambda e: e.nome)],
            "empresas": [ap.empresa(e) for e in sorted(c.empresas.listar(), key=lambda e: e.nome)],
            "bairros": sorted({e.bairro for e in escolas}),
            "habilidades": sorted({hab.exibir(h) for h in set(hab.NOMES) | usadas}),
            "turnos": list(TURNOS),
            "modalidades": list(MODALIDADES),
        }

    # ---------- empresa ----------
    @r.get("/talentos", summary="Buscar alunos autorizados por habilidade, bairro e desempenho")
    def buscar_talentos(
        habilidades: str = "", bairro: str = "", escola: str = "", turno: str = "",
        modalidade: str = "", modulo: int = Query(1, ge=1, le=3),
        media_minima: float = Query(0, ge=0, le=10), destaques: bool = False,
    ):
        filtro = FiltroTalentos(_lista(habilidades), bairro, escola, turno, modalidade,
                                modulo, media_minima, destaques)
        return [ap.talento(t) for t in c.buscar_talentos.executar(filtro)]

    @r.get("/talentos/{aluno_id}", summary="Perfil público de um aluno")
    def perfil(aluno_id: str):
        return ap.perfil_publico(*c.ver_perfil.executar(aluno_id))

    @r.get("/mapa", summary="Onde estão os talentos em Guarulhos: por bairro e escola")
    def mapa(habilidades: str = ""):
        return ap.mapa(c.mapear_talentos.executar(_lista(habilidades)))

    @r.get("/vagas", summary="Vagas abertas")
    def listar_vagas():
        return [ap.vaga(v, e) for v, e in c.listar_vagas.executar()]

    @r.post("/vagas", status_code=201, summary="Publicar uma vaga")
    def publicar_vaga(dados: VagaEntrada):
        vaga = c.publicar_vaga.executar(NovaVaga(
            empresa_id=dados.empresa_id, titulo=dados.titulo, modalidade=dados.modalidade,
            turno=dados.turno, obrigatorias=tuple(dados.obrigatorias),
            desejaveis=tuple(dados.desejaveis), descricao=dados.descricao,
        ))
        return ap.vaga(vaga, c.empresas.buscar(vaga.empresa_id))

    @r.get("/vagas/{vaga_id}/recomendados", summary="Alunos que mais combinam com a vaga")
    def recomendados(vaga_id: str):
        vaga, candidatos = c.recomendar_alunos.executar(vaga_id)
        return {
            "vaga": ap.vaga(vaga, c.empresas.buscar(vaga.empresa_id)),
            "candidatos": [{**ap.perfil_publico(x.aluno, x.escola),
                            "compatibilidade": ap.compatibilidade(x.compat)} for x in candidatos],
        }

    @r.get("/compatibilidade", summary="Compatibilidade aluno x vaga, com orientação")
    def compatibilidade(aluno: str, vaga: str):
        comp, orientacao = c.analisar.executar(aluno, vaga)
        return {**ap.compatibilidade(comp), "orientacao": orientacao,
                "assistente": c.assistente.nome}

    @r.post("/pedidos", status_code=201, summary="Empresa fala com a escola (sobre um aluno ou pedindo indicações)")
    def fazer_pedido(dados: PedidoEntrada):
        p = c.fazer_pedido.executar(dados.empresa_id, dados.mensagem, escola_id=dados.escola_id,
                                    aluno_id=dados.aluno_id, vaga_id=dados.vaga_id)
        return {"id": p.id, "status": p.status.value, "escola_id": p.escola_id}

    @r.get("/pedidos", summary="Pedidos, por escola, empresa e status")
    def listar_pedidos(escola: str = "", empresa: str = "", status: str = ""):
        return [ap.pedido(d) for d in c.listar_pedidos.executar(escola, status, empresa)]

    # ---------- escola ----------
    @r.post("/pedidos/{pedido_id}/resposta", summary="Escola aprova ou recusa o pedido")
    def responder(pedido_id: str, dados: RespostaEntrada):
        p = c.responder_pedido.executar(pedido_id, dados.aprovar, dados.resposta)
        return {"id": p.id, "status": p.status.value}

    @r.get("/escolas/{escola_id}/alunos", summary="Alunos da escola (visão da coordenação)")
    def alunos_da_escola(escola_id: str):
        escola, alunos = c.listar_alunos_da_escola.executar(escola_id)
        return [ap.aluno_da_escola(a, escola) for a in alunos]

    @r.post("/escolas/{escola_id}/alunos", status_code=201, summary="Coordenação cadastra um aluno")
    def cadastrar_aluno(escola_id: str, dados: AlunoEntrada):
        aluno = c.cadastrar_aluno.executar(NovoAluno(
            nome=dados.nome, escola_id=escola_id, curso=dados.curso, modulo=dados.modulo,
            turnos=tuple(dados.turnos), modalidades=tuple(dados.modalidades),
            habilidades=tuple(dados.habilidades), desempenho=Desempenho(**dados.desempenho.model_dump()),
            observacao=dados.observacao,
            projetos=tuple(Projeto(**p.model_dump()) for p in dados.projetos),
            autorizado=dados.autorizado,
        ))
        return ap.aluno_da_escola(aluno, c.escolas.buscar(escola_id))

    # ---------- aluno ----------
    @r.get("/panorama", summary="Oportunidades em Guarulhos e o que é preciso para ser indicado")
    def panorama():
        return ap.panorama(c.mostrar_panorama.executar())

    @r.get("/sistema", summary="Quais peças estão ligadas em cada camada")
    def sistema():
        return c.descrever()

    return r
