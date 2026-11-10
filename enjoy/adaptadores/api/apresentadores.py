"""Apresentadores: transformam entidades no JSON que a tela usa.

Regra de exposição: a empresa recebe o perfil PÚBLICO (primeiro nome e inicial,
sem contato). Só a escola vê o nome completo e a observação da coordenação.
"""

from __future__ import annotations

from enjoy.casos_de_uso import MapaDeTalentos, Panorama, PedidoDetalhado, TalentoEncontrado
from enjoy.entidades import (
    ATITUDES,
    Aluno,
    Compatibilidade,
    Desempenho,
    Empresa,
    Escola,
    Vaga,
    habilidades as hab,
)


def _hs(chaves) -> list[str]:
    return [hab.exibir(h) for h in chaves]


def escola(e: Escola) -> dict:
    return {"id": e.id, "nome": e.nome, "bairro": e.bairro, "cidade": e.cidade,
            "latitude": e.latitude, "longitude": e.longitude, "endereco": e.endereco}


def empresa(e: Empresa) -> dict:
    return {"id": e.id, "nome": e.nome, "bairro": e.bairro, "setor": e.setor}


def desempenho(d: Desempenho) -> dict:
    return {
        "media_tecnico": d.media_tecnico, "media_regular": d.media_regular,
        "media_geral": d.media_geral, "frequencia": d.frequencia,
        "atitudes": {a: getattr(d, a) for a in ATITUDES},
        "atitude": d.atitude, "destaque": d.destaque,
    }


def perfil_publico(a: Aluno, e: Escola) -> dict:
    return {
        "id": a.id,
        "nome": a.nome_publico,
        "iniciais": a.nome_publico[0] + a.nome_publico.split()[-1][0],
        "escola": escola(e),
        "curso": a.curso,
        "modulo": a.modulo,
        "turnos": list(a.turnos),
        "modalidades": list(a.modalidades),
        "habilidades": _hs(a.habilidades),
        "desempenho": desempenho(a.desempenho),
        "projetos": [{"titulo": p.titulo, "descricao": p.descricao, "link": p.link}
                     for p in a.projetos],
    }


def aluno_da_escola(a: Aluno, e: Escola) -> dict:
    """Visão da coordenação: inclui nome completo, observação e autorização."""
    return {**perfil_publico(a, e), "nome": a.nome, "nome_publico": a.nome_publico,
            "observacao": a.observacao, "autorizado": a.autorizado}


def talento(t: TalentoEncontrado) -> dict:
    return {**perfil_publico(t.aluno, t.escola), "aderencia": t.aderencia,
            "combinam": _hs(t.combinam)}


def compatibilidade(c: Compatibilidade) -> dict:
    return {
        "percentual": c.percentual,
        "tem": _hs(c.tem),
        "faltam_obrigatorias": _hs(c.faltam_obrigatorias),
        "faltam_desejaveis": _hs(c.faltam_desejaveis),
        "turno_ok": c.turno_ok,
        "modalidade_ok": c.modalidade_ok,
    }


def vaga(v: Vaga, emp: Empresa) -> dict:
    return {
        "id": v.id, "titulo": v.titulo, "empresa": empresa(emp),
        "modalidade": v.modalidade, "turno": v.turno, "descricao": v.descricao,
        "obrigatorias": _hs(v.obrigatorias), "desejaveis": _hs(v.desejaveis),
    }


def mapa(m: MapaDeTalentos) -> dict:
    return {
        "habilidades": _hs(m.habilidades),
        "total": m.total,
        "com_habilidades": m.com_habilidades,
        "destaques": m.destaques,
        "mais_comuns": [{"habilidade": hab.exibir(h), "alunos": n}
                        for h, n in m.habilidades_mais_comuns],
        "bairros": [
            {
                "bairro": b.bairro, "total": b.total, "com_habilidades": b.com_habilidades,
                "destaques": b.destaques,
                "escolas": [
                    {**escola(r.escola), "total": r.total, "com_habilidades": r.com_habilidades,
                     "destaques": r.destaques, "principais": _hs(r.principais)}
                    for r in b.escolas
                ],
            }
            for b in m.bairros
        ],
    }


def pedido(d: PedidoDetalhado) -> dict:
    p = d.pedido
    return {
        "id": p.id,
        "tipo": p.tipo,
        "status": p.status.value,
        "mensagem": p.mensagem,
        "resposta": p.resposta,
        "criado_em": p.criado_em.isoformat(),
        "decidido_em": p.decidido_em.isoformat() if p.decidido_em else None,
        # Pedidos são lidos pela escola: ela vê o nome completo do próprio aluno.
        "aluno": {"id": d.aluno.id, "nome": d.aluno.nome, "nome_publico": d.aluno.nome_publico,
                  "modulo": d.aluno.modulo} if d.aluno else None,
        "escola": escola(d.escola),
        "empresa": empresa(d.empresa),
        "vaga": {"id": d.vaga.id, "titulo": d.vaga.titulo} if d.vaga else None,
    }


def panorama(p: Panorama) -> dict:
    return {
        "vagas_abertas": p.vagas_abertas,
        "empresas_contratando": p.empresas_contratando,
        "pedidos_aprovados": p.pedidos_aprovados,
        "habilidades_mais_pedidas": [{"habilidade": hab.exibir(h), "vagas": n}
                                     for h, n in p.habilidades_mais_pedidas],
        "vagas": [vaga(v, e) for v, e in p.vagas],
        "criterios": {
            "media_minima": Desempenho.MEDIA_DESTAQUE,
            "frequencia_minima": Desempenho.FREQUENCIA_DESTAQUE,
            "atitude_minima": Desempenho.ATITUDE_DESTAQUE,
        },
    }
