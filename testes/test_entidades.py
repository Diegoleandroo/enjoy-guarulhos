from datetime import datetime

import pytest

from conftest import aluno, desempenho, vaga
from enjoy.entidades import (
    Compatibilidade,
    Conflito,
    DadosInvalidos,
    Desempenho,
    Pedido,
    StatusPedido,
    habilidades as hab,
)


@pytest.mark.parametrize("entrada, esperado", [
    ("JS", "javascript"), ("  Node ", "node.js"), ("Lógica", "logica de programacao"),
    ("GitHub", "git"), ("PostgreSQL", "postgresql"), ("IA", "inteligencia artificial"),
])
def test_normaliza_sinonimos_e_acentos(entrada, esperado):
    assert hab.normalizar(entrada) == esperado


def test_aluno_normaliza_e_remove_habilidades_repetidas():
    assert aluno(habilidades=("JS", "javascript", "Git", "github")).habilidades == ("javascript", "git")


def test_empresa_ve_so_primeiro_nome_e_inicial():
    assert aluno(nome="Ana Clara Souza").nome_publico == "Ana S."


@pytest.mark.parametrize("campos", [
    {"nome": "Ana"}, {"modulo": 4}, {"turnos": ()}, {"turnos": ("madrugada",)}, {"habilidades": ()},
])
def test_aluno_invalido(campos):
    with pytest.raises(DadosInvalidos):
        aluno(**campos)


# ---------- desempenho: o que a escola observa ----------

def test_destaque_exige_notas_frequencia_e_atitude():
    assert desempenho(media=8.5, frequencia=95, atitude=5).destaque


@pytest.mark.parametrize("d", [
    desempenho(media=9.5, regular=7.5),  # nota baixa no regular também conta
    desempenho(frequencia=85),            # faltas
    desempenho(atitude=3),                # nota alta sem comprometimento não basta
])
def test_nao_e_destaque(d):
    assert not d.destaque


def test_medias_e_atitude_calculadas():
    d = Desempenho(9.0, 8.0, 100, 5, 4, 3)
    assert (d.media_geral, d.atitude) == (8.5, 4.0)


@pytest.mark.parametrize("args", [(11, 8, 90, 4, 4, 4), (8, 8, 101, 4, 4, 4), (8, 8, 90, 0, 4, 4)])
def test_desempenho_invalido(args):
    with pytest.raises(DadosInvalidos):
        Desempenho(*args)


# ---------- compatibilidade ----------

def test_vaga_tira_desejavel_que_ja_e_obrigatoria():
    assert vaga(obrigatorias=("Python",), desejaveis=("py", "Docker")).desejaveis == ("docker",)


def test_compatibilidade_total():
    c = Compatibilidade.calcular(aluno(habilidades=("Python", "SQL", "Git", "Docker")), vaga())
    assert c.percentual == 100 and not c.faltam_obrigatorias


def test_compatibilidade_mostra_o_que_falta():
    c = Compatibilidade.calcular(aluno(), vaga())
    assert c.percentual == round(70 * 2 / 3)
    assert c.faltam_obrigatorias == ("git",) and c.faltam_desejaveis == ("docker",)


def test_turno_e_modalidade_incompativeis_derrubam_a_nota():
    a = aluno(habilidades=("Python", "SQL", "Git", "Docker"), turnos=("manha",))
    c = Compatibilidade.calcular(a, vaga(modalidade="remoto"))
    assert not c.turno_ok and not c.modalidade_ok
    assert c.percentual == round(100 * 0.5 * 0.7)


# ---------- pedido: a empresa fala com a escola ----------

def _pedido(**campos):
    base = dict(id="p1", empresa_id="emp1", escola_id="e-centro",
                mensagem="Queremos conversar sobre o estágio.", criado_em=datetime(2026, 11, 8), vaga_id="v1")
    return Pedido(**{**base, **campos})


def test_pedido_exige_mensagem_e_assunto():
    with pytest.raises(DadosInvalidos):
        _pedido(mensagem="Oi")
    with pytest.raises(DadosInvalidos):
        _pedido(vaga_id=None)


def test_tipo_do_pedido():
    assert _pedido().tipo == "indicacao"
    assert _pedido(aluno_id="a1").tipo == "aluno"


def test_pedido_so_pode_ser_respondido_uma_vez():
    aprovado = _pedido().aprovar(datetime(2026, 11, 9), "  Vamos indicar dois alunos. ")
    assert aprovado.status is StatusPedido.APROVADO and aprovado.resposta == "Vamos indicar dois alunos."
    with pytest.raises(Conflito):
        aprovado.recusar(datetime(2026, 11, 10))
