"""Teste de arquitetura: garante que as dependências só apontam para dentro.

Se alguém importar FastAPI dentro de uma entidade, este teste quebra.
"""

import ast
from pathlib import Path

import pytest

PACOTE = Path(__file__).resolve().parents[1] / "enjoy"

PROIBIDOS = {
    "entidades": ["enjoy.casos_de_uso", "enjoy.adaptadores", "enjoy.frameworks_drivers",
                  "fastapi", "pydantic", "sqlite3", "httpx", "uvicorn"],
    "casos_de_uso": ["enjoy.adaptadores", "enjoy.frameworks_drivers",
                     "fastapi", "pydantic", "sqlite3", "httpx", "uvicorn"],
    "adaptadores": ["enjoy.frameworks_drivers"],
}


def imports_de(arquivo: Path) -> list[str]:
    arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
    nomes = []
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            nomes += [a.name for a in no.names]
        elif isinstance(no, ast.ImportFrom) and no.module and no.level == 0:
            # imports só para o editor (TYPE_CHECKING) não contam em execução
            nomes.append(no.module)
    return nomes


def _ignorar_type_checking(arquivo: Path) -> set[str]:
    arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
    ignorados = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.If) and getattr(no.test, "id", None) == "TYPE_CHECKING":
            for filho in ast.walk(no):
                if isinstance(filho, ast.ImportFrom) and filho.module:
                    ignorados.add(filho.module)
    return ignorados


@pytest.mark.parametrize("camada", list(PROIBIDOS))
def test_camada_nao_depende_de_camadas_externas(camada):
    violacoes = []
    for arquivo in (PACOTE / camada).rglob("*.py"):
        ignorados = _ignorar_type_checking(arquivo)
        for nome in imports_de(arquivo):
            if nome in ignorados:
                continue
            if any(nome == p or nome.startswith(p + ".") for p in PROIBIDOS[camada]):
                violacoes.append(f"{arquivo.relative_to(PACOTE)} importa {nome}")
    assert not violacoes, "Regra da Dependência violada:\n" + "\n".join(violacoes)
