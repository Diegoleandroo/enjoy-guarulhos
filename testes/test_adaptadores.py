from datetime import datetime

import httpx

from conftest import aluno, vaga
from enjoy.adaptadores.assistente.claude import AssistenteClaude
from enjoy.adaptadores.assistente.local import AssistenteLocal
from enjoy.adaptadores.repositorios import sqlite
from enjoy.entidades import Compatibilidade, Pedido, Projeto


def test_sqlite_guarda_e_devolve_aluno_vaga_e_pedido(tmp_path):
    banco = sqlite.BancoSqlite(str(tmp_path / "t.db"))
    original = aluno()
    original = type(original)(**{**original.__dict__, "projetos": (Projeto("API", "Teste"),)})
    sqlite.AlunosSqlite(banco).salvar(original)
    sqlite.VagasSqlite(banco).salvar(vaga())
    p = Pedido("p1", "emp1", "e-centro", "Mensagem longa o bastante", datetime(2026, 11, 8, 10), aluno_id="a1")
    repo_p = sqlite.PedidosSqlite(banco)
    repo_p.salvar(p)
    repo_p.salvar(p.aprovar(datetime(2026, 11, 9), "Combinado"))

    novo = sqlite.BancoSqlite(str(tmp_path / "t.db"))  # reabre: os dados sobreviveram
    assert sqlite.AlunosSqlite(novo).buscar("a1") == original
    assert sqlite.VagasSqlite(novo).listar() == [vaga()]
    salvo = sqlite.PedidosSqlite(novo).buscar("p1")
    assert (salvo.status.value, salvo.resposta) == ("aprovado", "Combinado")


def _compat():
    return Compatibilidade.calcular(aluno(), vaga())


def test_assistente_claude_usa_a_resposta_da_ia():
    def responder(req: httpx.Request):
        assert req.headers["x-api-key"] == "chave"
        assert b"Ana Souza" not in req.content  # nome completo nunca vai para a IA
        return httpx.Response(200, json={"content": [{"type": "text", "text": "Estude Git."}]})

    cliente = httpx.Client(transport=httpx.MockTransport(responder))
    ia = AssistenteClaude("chave", "modelo", AssistenteLocal(), cliente)
    assert ia.orientar(aluno(), vaga(), _compat()) == "Estude Git."


def test_assistente_claude_cai_para_o_local_se_a_api_falhar():
    cliente = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(500)))
    ia = AssistenteClaude("chave", "modelo", AssistenteLocal(), cliente)
    assert "Git" in ia.orientar(aluno(), vaga(), _compat())
