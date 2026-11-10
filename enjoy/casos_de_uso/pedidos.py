"""A empresa fala com a escola, nunca direto com o aluno.

Dois tipos de pedido:
- sobre um aluno que a empresa viu no mapa;
- pedindo à escola que indique alunos para uma vaga.
A escola responde e, se aprovar, ela mesma conversa com o aluno e a família.
"""

from __future__ import annotations

from dataclasses import dataclass

from enjoy.entidades import (
    Aluno,
    Conflito,
    DadosInvalidos,
    Empresa,
    Escola,
    NaoEncontrado,
    Pedido,
    StatusPedido,
    Vaga,
)

from .portas import (
    AlunoRepository,
    EmpresaRepository,
    EscolaRepository,
    GeradorDeIds,
    PedidoRepository,
    Relogio,
    VagaRepository,
)


class FazerPedido:
    def __init__(self, pedidos: PedidoRepository, alunos: AlunoRepository,
                 escolas: EscolaRepository, empresas: EmpresaRepository,
                 vagas: VagaRepository, relogio: Relogio, ids: GeradorDeIds):
        self.pedidos, self.alunos, self.escolas, self.empresas = pedidos, alunos, escolas, empresas
        self.vagas, self.relogio, self.ids = vagas, relogio, ids

    def executar(self, empresa_id: str, mensagem: str, *, escola_id: str = "",
                 aluno_id: str | None = None, vaga_id: str | None = None) -> Pedido:
        if not self.empresas.buscar(empresa_id):
            raise DadosInvalidos("Empresa não encontrada.")
        if aluno_id:
            aluno = self.alunos.buscar(aluno_id)
            if not aluno or not aluno.autorizado:
                raise NaoEncontrado("Perfil não encontrado ou sem autorização para aparecer.")
            escola_id = aluno.escola_id  # o pedido vai para a escola do aluno
        if not self.escolas.buscar(escola_id):
            raise DadosInvalidos("Escola não encontrada.")
        if vaga_id:
            vaga = self.vagas.buscar(vaga_id)
            if not vaga or vaga.empresa_id != empresa_id:
                raise DadosInvalidos("Essa vaga não pertence à empresa.")
        chave = (empresa_id, escola_id, aluno_id or None, vaga_id or None)
        for p in self.pedidos.listar():
            if (p.empresa_id, p.escola_id, p.aluno_id, p.vaga_id) == chave and \
                    p.status is not StatusPedido.RECUSADO:
                raise Conflito("A empresa já fez este pedido para esta escola.")
        pedido = Pedido(
            id=self.ids.novo_id(), empresa_id=empresa_id, escola_id=escola_id,
            mensagem=mensagem.strip(), criado_em=self.relogio.agora(),
            aluno_id=aluno_id or None, vaga_id=vaga_id or None,
        )
        self.pedidos.salvar(pedido)
        return pedido


@dataclass(frozen=True)
class PedidoDetalhado:
    pedido: Pedido
    escola: Escola
    empresa: Empresa
    aluno: Aluno | None
    vaga: Vaga | None


class ListarPedidos:
    def __init__(self, pedidos: PedidoRepository, alunos: AlunoRepository,
                 escolas: EscolaRepository, empresas: EmpresaRepository, vagas: VagaRepository):
        self.pedidos, self.alunos, self.escolas = pedidos, alunos, escolas
        self.empresas, self.vagas = empresas, vagas

    def executar(self, escola_id: str = "", status: str = "", empresa_id: str = "") -> list[PedidoDetalhado]:
        saida = []
        for p in self.pedidos.listar():
            if (escola_id and p.escola_id != escola_id) or (status and p.status.value != status):
                continue
            if empresa_id and p.empresa_id != empresa_id:
                continue
            escola, empresa = self.escolas.buscar(p.escola_id), self.empresas.buscar(p.empresa_id)
            if not escola or not empresa:
                continue
            aluno = self.alunos.buscar(p.aluno_id) if p.aluno_id else None
            vaga = self.vagas.buscar(p.vaga_id) if p.vaga_id else None
            saida.append(PedidoDetalhado(p, escola, empresa, aluno, vaga))
        saida.sort(key=lambda d: d.pedido.criado_em, reverse=True)
        return saida


class ResponderPedido:
    def __init__(self, pedidos: PedidoRepository, relogio: Relogio):
        self.pedidos, self.relogio = pedidos, relogio

    def executar(self, pedido_id: str, aprovar: bool, resposta: str = "") -> Pedido:
        pedido = self.pedidos.buscar(pedido_id)
        if not pedido:
            raise NaoEncontrado("Pedido não encontrado.")
        agora = self.relogio.agora()
        respondido = pedido.aprovar(agora, resposta) if aprovar else pedido.recusar(agora, resposta)
        self.pedidos.salvar(respondido)
        return respondido
