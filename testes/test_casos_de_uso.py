import pytest

from conftest import IdsSequenciais, RelogioParado, aluno, desempenho, vaga
from enjoy.adaptadores.assistente.local import AssistenteLocal
from enjoy.casos_de_uso import (
    AnalisarCompatibilidade,
    BuscarTalentos,
    CadastrarAluno,
    FazerPedido,
    FiltroTalentos,
    ListarAlunosDaEscola,
    ListarPedidos,
    MapearTalentos,
    MostrarPanorama,
    NovaVaga,
    NovoAluno,
    PublicarVaga,
    RecomendarAlunosParaVaga,
    ResponderPedido,
)
from enjoy.entidades import Conflito, DadosInvalidos, NaoEncontrado


@pytest.fixture
def povoado(repos):
    a = repos["alunos"]
    a.salvar(aluno("a1", "Ana Souza", "e-centro", ("Python", "SQL", "Git"), modulo=3))
    a.salvar(aluno("a2", "Bruno Lima", "e-centro", ("HTML", "CSS"), turnos=("manha",),
                   desemp=desempenho(media=6.5, frequencia=80, atitude=3)))
    a.salvar(aluno("a3", "Carla Dias", "e-pimentas", ("Python", "SQL", "Git"),
                   desemp=desempenho(media=7.5, atitude=4)))
    a.salvar(aluno("a4", "Davi Reis", "e-pimentas", ("Python", "SQL", "Git"), autorizado=False))
    repos["vagas"].salvar(vaga())
    return repos


def _buscar(repos, **filtro):
    return [t.aluno.id for t in BuscarTalentos(repos["alunos"], repos["escolas"]).executar(FiltroTalentos(**filtro))]


def test_busca_ignora_sem_autorizacao_e_desempata_pelo_desempenho(povoado):
    # a1 e a3 têm as mesmas habilidades; a1 é destaque, então vem primeiro.
    assert _buscar(povoado, habilidades=("python", "sql")) == ["a1", "a3"]


def test_filtros_por_bairro_turno_media_e_destaque(povoado):
    assert _buscar(povoado, bairro="Centro", turno="manha") == ["a2"]
    assert _buscar(povoado, media_minima=7) == ["a1", "a3"]
    assert _buscar(povoado, so_destaques=True) == ["a1"]


def test_mapa_mostra_bairros_com_quem_tem_todas_as_habilidades(povoado):
    m = MapearTalentos(povoado["alunos"], povoado["escolas"]).executar(("Python", "SQL"))
    assert (m.total, m.com_habilidades, m.destaques) == (3, 2, 1)
    assert {b.bairro: b.com_habilidades for b in m.bairros} == {"Centro": 1, "Pimentas": 1}


def test_recomendacao_empata_pela_escola(povoado):
    _, candidatos = RecomendarAlunosParaVaga(povoado["vagas"], povoado["alunos"], povoado["escolas"]).executar("v1")
    assert [c.aluno.id for c in candidatos] == ["a1", "a3"]


def test_escola_cadastra_aluno_sem_autorizacao_por_padrao(repos):
    caso = CadastrarAluno(repos["alunos"], repos["escolas"], IdsSequenciais())
    dados = dict(nome="Eva Prado", curso="DS", modulo=1, turnos=("tarde",), modalidades=("presencial",),
                 habilidades=("Excel",), desempenho=desempenho())
    novo = caso.executar(NovoAluno(escola_id="e-centro", **dados))
    assert not novo.autorizado
    assert _buscar(repos) == []  # não aparece para empresas até o responsável autorizar
    with pytest.raises(DadosInvalidos):
        caso.executar(NovoAluno(escola_id="nao-existe", **dados))


def test_coordenacao_ve_todos_os_seus_alunos(povoado):
    _, alunos = ListarAlunosDaEscola(povoado["alunos"], povoado["escolas"]).executar("e-pimentas")
    assert {a.id for a in alunos} == {"a3", "a4"}


def test_publicar_vaga_exige_empresa(repos):
    caso = PublicarVaga(repos["vagas"], repos["empresas"], IdsSequenciais())
    assert caso.executar(NovaVaga("emp2", "Aprendiz", "presencial", "manha", ("Excel",))).cidade == "Guarulhos"
    with pytest.raises(DadosInvalidos):
        caso.executar(NovaVaga("x", "Aprendiz", "presencial", "manha", ("Excel",)))


def test_orientacao_aponta_o_que_estudar(povoado):
    povoado["alunos"].salvar(aluno("a5", "Eva Prado", habilidades=("Python",)))
    compat, texto = AnalisarCompatibilidade(povoado["alunos"], povoado["vagas"], AssistenteLocal()).executar("a5", "v1")
    assert "SQL" in texto and compat.faltam_obrigatorias


def _pedir(repos):
    return FazerPedido(repos["pedidos"], repos["alunos"], repos["escolas"], repos["empresas"],
                       repos["vagas"], RelogioParado(), IdsSequenciais())


def test_pedido_sobre_aluno_vai_para_a_escola_dele(povoado):
    p = _pedir(povoado).executar("emp1", "Queremos conversar sobre a Ana.", aluno_id="a3", vaga_id="v1")
    assert p.escola_id == "e-pimentas"


def test_fluxo_de_indicacao_ate_a_resposta(povoado):
    p = _pedir(povoado).executar("emp1", "Podem indicar alunos para a vaga?", escola_id="e-centro", vaga_id="v1")
    listar = ListarPedidos(povoado["pedidos"], povoado["alunos"], povoado["escolas"],
                           povoado["empresas"], povoado["vagas"])
    assert [d.pedido.id for d in listar.executar("e-centro", "pendente")] == [p.id]
    ResponderPedido(povoado["pedidos"], RelogioParado()).executar(p.id, True, "Vamos indicar a Ana.")
    assert listar.executar("e-centro", "aprovado")[0].pedido.resposta == "Vamos indicar a Ana."
    panorama = MostrarPanorama(povoado["vagas"], povoado["empresas"], povoado["pedidos"]).executar()
    assert panorama.pedidos_aprovados == 1 and panorama.vagas_abertas == 1


def test_nao_duplica_pedido_nem_expoe_aluno_sem_autorizacao(povoado):
    caso = _pedir(povoado)
    caso.executar("emp1", "Queremos conversar com a escola.", aluno_id="a1", vaga_id="v1")
    with pytest.raises(Conflito):
        caso.executar("emp1", "De novo, queremos conversar.", aluno_id="a1", vaga_id="v1")
    with pytest.raises(NaoEncontrado):
        caso.executar("emp1", "Queremos conversar com a escola.", aluno_id="a4")


def test_empresa_nao_usa_vaga_de_outra(povoado):
    with pytest.raises(DadosInvalidos):
        _pedir(povoado).executar("emp2", "Queremos conversar com a escola.", escola_id="e-centro", vaga_id="v1")
