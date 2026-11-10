"""Raiz de composição: o único lugar que conhece todas as peças e as encaixa."""

from __future__ import annotations

import logging

from enjoy.adaptadores.assistente.claude import AssistenteClaude
from enjoy.adaptadores.assistente.local import AssistenteLocal
from enjoy.adaptadores.carga import carregar_exemplo
from enjoy.adaptadores.repositorios import memoria, sqlite
from enjoy.adaptadores.sistema import IdsAleatorios, RelogioDoSistema
from enjoy.casos_de_uso import (
    AnalisarCompatibilidade,
    BuscarTalentos,
    CadastrarAluno,
    FazerPedido,
    ListarAlunosDaEscola,
    ListarPedidos,
    ListarVagas,
    MapearTalentos,
    MostrarPanorama,
    PublicarVaga,
    RecomendarAlunosParaVaga,
    ResponderPedido,
    VerPerfilPublico,
)
from enjoy.casos_de_uso.portas import AssistenteDeCarreira, GeradorDeIds, Relogio

from .config import Config

log = logging.getLogger("enjoy")


class Container:
    def __init__(self, config: Config, *, relogio: Relogio | None = None,
                 ids: GeradorDeIds | None = None,
                 assistente: AssistenteDeCarreira | None = None) -> None:
        self.config = config

        if config.repositorio == "memoria":
            self.escolas = memoria.EscolasEmMemoria()
            self.alunos = memoria.AlunosEmMemoria()
            self.empresas = memoria.EmpresasEmMemoria()
            self.vagas = memoria.VagasEmMemoria()
            self.pedidos = memoria.PedidosEmMemoria()
            self.nome_repositorio = "Em memória"
        elif config.repositorio == "sqlite":
            banco = sqlite.BancoSqlite(config.caminho_banco)
            self.escolas = sqlite.EscolasSqlite(banco)
            self.alunos = sqlite.AlunosSqlite(banco)
            self.empresas = sqlite.EmpresasSqlite(banco)
            self.vagas = sqlite.VagasSqlite(banco)
            self.pedidos = sqlite.PedidosSqlite(banco)
            self.nome_repositorio = "SQLite"
        else:
            raise ValueError(f"ENJOY_REPOSITORIO inválido: {config.repositorio!r}")

        self.relogio = relogio or RelogioDoSistema(config.fuso)
        self.ids = ids or IdsAleatorios()
        local = AssistenteLocal()
        self.assistente = assistente or (
            AssistenteClaude(config.chave_ia, config.modelo_ia, reserva=local)
            if config.chave_ia else local
        )

        a, e, emp, v, p = self.alunos, self.escolas, self.empresas, self.vagas, self.pedidos
        self.buscar_talentos = BuscarTalentos(a, e)
        self.mapear_talentos = MapearTalentos(a, e)
        self.ver_perfil = VerPerfilPublico(a, e)
        self.cadastrar_aluno = CadastrarAluno(a, e, self.ids)
        self.publicar_vaga = PublicarVaga(v, emp, self.ids)
        self.listar_vagas = ListarVagas(v, emp)
        self.recomendar_alunos = RecomendarAlunosParaVaga(v, a, e)
        self.listar_alunos_da_escola = ListarAlunosDaEscola(a, e)
        self.analisar = AnalisarCompatibilidade(a, v, self.assistente)
        self.fazer_pedido = FazerPedido(p, a, e, emp, v, self.relogio, self.ids)
        self.listar_pedidos = ListarPedidos(p, a, e, emp, v)
        self.responder_pedido = ResponderPedido(p, self.relogio)
        self.mostrar_panorama = MostrarPanorama(v, emp, p)

    def inicializar(self) -> None:
        if self.config.carregar_exemplo:
            n = carregar_exemplo(self.config.arquivo_exemplo, self.escolas, self.alunos,
                                 self.empresas, self.vagas, self.pedidos)
            if n:
                log.info("Dados de exemplo carregados: %d alunos fictícios.", n)
        log.info("Repositório: %s | Assistente: %s", self.nome_repositorio, self.assistente.nome)

    def descrever(self) -> dict:
        return {
            "nome": "Enjoy",
            "camadas": [
                {"camada": "Frameworks & Drivers", "peca": "Servidor web", "usa": "FastAPI + Uvicorn"},
                {"camada": "Frameworks & Drivers", "peca": "Mapa", "usa": "Leaflet + malha de Guarulhos (IBGE)"},
                {"camada": "Interface Adapters", "peca": "API", "usa": "REST com OpenAPI (/docs)"},
                {"camada": "Interface Adapters", "peca": "Repositórios", "usa": self.nome_repositorio},
                {"camada": "Interface Adapters", "peca": "Assistente de carreira", "usa": self.assistente.nome},
            ],
        }
