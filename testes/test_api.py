import pytest
from fastapi.testclient import TestClient

from enjoy.frameworks_drivers.app import criar_app
from enjoy.frameworks_drivers.config import Config


@pytest.fixture
def api():
    with TestClient(criar_app(Config(repositorio="memoria"))) as cliente:
        yield cliente


def test_mapa_so_tem_escolas_de_guarulhos(api):
    ref = api.get("/api/referencias").json()
    assert {e["cidade"] for e in ref["escolas"]} == {"Guarulhos"}
    mapa = api.get("/api/mapa?habilidades=Python,SQL").json()
    assert mapa["total"] > 50 and 0 < mapa["com_habilidades"] < mapa["total"]
    assert "Pimentas" in [b["bairro"] for b in mapa["bairros"]]


def test_busca_por_bairro_e_destaque(api):
    talentos = api.get("/api/talentos?bairro=Pimentas&destaques=true").json()
    assert talentos and all(t["escola"]["bairro"] == "Pimentas" and t["desempenho"]["destaque"] for t in talentos)


def test_perfil_publico_nao_expoe_nome_completo_nem_observacao(api):
    t = api.get("/api/talentos").json()[0]
    perfil = api.get(f"/api/talentos/{t['id']}").json()
    assert perfil["nome"].endswith(".") and "observacao" not in perfil
    assert set(perfil["desempenho"]["atitudes"]) == {"comprometimento", "responsabilidade", "disciplina"}


def test_empresa_pede_indicacao_e_escola_responde(api):
    r = api.post("/api/pedidos", json={"empresa_id": "emp-trilha", "escola_id": "esc-pimentas3",
                                       "vaga_id": "vaga-backend", "mensagem": "Podem indicar alunos para a vaga?"})
    assert r.status_code == 201
    assert api.post("/api/pedidos", json={"empresa_id": "emp-trilha", "escola_id": "esc-pimentas3",
                                          "vaga_id": "vaga-backend", "mensagem": "Podem indicar alunos?"}).status_code == 409
    d = api.post(f"/api/pedidos/{r.json()['id']}/resposta", json={"aprovar": True, "resposta": "Indicaremos dois."})
    assert d.json()["status"] == "aprovado"
    assert api.get("/api/panorama").json()["pedidos_aprovados"] >= 1


def test_escola_cadastra_e_lista_seus_alunos(api):
    r = api.post("/api/escolas/esc-etec/alunos", json={
        "nome": "Teste da Silva", "modulo": 2, "turnos": ["tarde"], "modalidades": ["hibrido"],
        "habilidades": ["py", "sql", "github"], "autorizado": True,
        "desempenho": {"media_tecnico": 9, "media_regular": 8.5, "frequencia": 97,
                       "comprometimento": 5, "responsabilidade": 5, "disciplina": 4 }})
    assert r.status_code == 201
    novo = r.json()
    assert novo["habilidades"] == ["Python", "SQL", "Git"] and novo["desempenho"]["destaque"]
    assert novo["nome_publico"] == "Teste S."
    assert novo["id"] in [a["id"] for a in api.get("/api/escolas/esc-etec/alunos").json()]


def test_erros_viram_codigos_http(api):
    assert api.get("/api/talentos/nao-existe").status_code == 404
    assert api.post("/api/escolas/esc-etec/alunos", json={
        "nome": "Teste da Silva", "modulo": 2, "turnos": ["tarde"], "modalidades": ["hibrido"],
        "habilidades": ["Git"], "desempenho": {"media_tecnico": 12, "media_regular": 8, "frequencia": 90,
        "comprometimento": 4, "responsabilidade": 4, "disciplina": 4 }}).status_code == 422


def test_rejeita_listas_gigantes(api):
    r = api.post("/api/escolas/esc-etec/alunos", json={
        "nome": "Ana Souza", "modulo": 2, "turnos": ["tarde"], "modalidades": ["presencial"],
        "habilidades": [f"h{i}" for i in range(500)],
        "desempenho": {"media_tecnico": 9, "media_regular": 9, "frequencia": 95,
                       "comprometimento": 5, "responsabilidade": 5, "disciplina": 5}})
    assert r.status_code == 422


def test_limita_envios_e_manda_cabecalhos_de_seguranca(api):
    pagina = api.get("/")
    assert "script-src 'self'" in pagina.headers["content-security-policy"]
    assert pagina.headers["x-frame-options"] == "DENY"
    corpo = {"empresa_id": "x", "mensagem": "Mensagem de teste longa", "escola_id": "esc-etec", "vaga_id": "y"}
    codigos = [api.post("/api/pedidos", json=corpo).status_code for _ in range(31)]
    assert codigos[-1] == 429


def test_rejeita_envio_grande_demais(api):
    r = api.post("/api/pedidos", content=b"x" * 20_000, headers={"content-type": "application/json"})
    assert r.status_code == 413
