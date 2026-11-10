"""Carrega os dados de exemplo (fictícios) quando o banco está vazio."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from enjoy.entidades import Aluno, Desempenho, Empresa, Escola, Pedido, Projeto, StatusPedido, Vaga


def carregar_exemplo(arquivo: str, escolas, alunos, empresas, vagas, pedidos) -> int:
    if escolas.listar() or not Path(arquivo).exists():
        return 0
    dados = json.loads(Path(arquivo).read_text(encoding="utf-8"))
    for e in dados["escolas"]:
        escolas.salvar(Escola(**e))
    for e in dados["empresas"]:
        empresas.salvar(Empresa(**e))
    for v in dados["vagas"]:
        vagas.salvar(Vaga(**{**v, "obrigatorias": tuple(v["obrigatorias"]),
                             "desejaveis": tuple(v.get("desejaveis", []))}))
    for a in dados["alunos"]:
        alunos.salvar(Aluno(**{
            **a,
            "turnos": tuple(a["turnos"]),
            "modalidades": tuple(a["modalidades"]),
            "habilidades": tuple(a["habilidades"]),
            "desempenho": Desempenho(**a["desempenho"]),
            "projetos": tuple(Projeto(**p) for p in a.get("projetos", [])),
        }))
    for p in dados.get("pedidos", []):
        decidido = p.get("decidido_em")
        pedidos.salvar(Pedido(**{
            **p,
            "status": StatusPedido(p.get("status", "pendente")),
            "criado_em": datetime.fromisoformat(p["criado_em"]),
            "decidido_em": datetime.fromisoformat(decidido) if decidido else None,
        }))
    return len(dados["alunos"])
