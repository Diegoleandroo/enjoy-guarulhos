"""Assistente com IA (API do Claude). Opcional: só liga com ANTHROPIC_API_KEY.

A IA recebe apenas o necessário (habilidades, vaga e o cálculo já feito),
nunca o nome completo do aluno. Se a API falhar, o assistente local responde.
"""

from __future__ import annotations

import logging

import httpx

from enjoy.casos_de_uso.portas import AssistenteDeCarreira
from enjoy.entidades import Aluno, Compatibilidade, Vaga, habilidades as hab

log = logging.getLogger("enjoy")

URL = "https://api.anthropic.com/v1/messages"
INSTRUCOES = (
    "Você ajuda a coordenação de uma escola técnica a orientar um aluno de Desenvolvimento de Sistemas. "
    "Responda em português do Brasil, em no máximo 4 frases, tom encorajador e concreto, "
    "falando do aluno na terceira pessoa. Use somente os dados fornecidos. "
    "Sugira um passo prático para a principal habilidade que falta."
)


class AssistenteClaude(AssistenteDeCarreira):
    nome = "Claude (IA)"

    def __init__(self, chave: str, modelo: str, reserva: AssistenteDeCarreira,
                 cliente: httpx.Client | None = None) -> None:
        self.chave, self.modelo, self.reserva = chave, modelo, reserva
        self.cliente = cliente or httpx.Client(timeout=15)

    def orientar(self, aluno: Aluno, vaga: Vaga, compat: Compatibilidade) -> str:
        def lista(hs):
            return ", ".join(hab.exibir(h) for h in hs) or "nenhuma"

        dados = (
            f"Aluno do módulo {aluno.modulo}. Habilidades: {lista(aluno.habilidades)}.\n"
            f"Vaga: {vaga.titulo}. Obrigatórias: {lista(vaga.obrigatorias)}. "
            f"Desejáveis: {lista(vaga.desejaveis)}.\n"
            f"Compatibilidade calculada: {compat.percentual}%. "
            f"Faltam obrigatórias: {lista(compat.faltam_obrigatorias)}. "
            f"Turno compatível: {'sim' if compat.turno_ok else 'não'}. "
            f"Modalidade compatível: {'sim' if compat.modalidade_ok else 'não'}."
        )
        try:
            resposta = self.cliente.post(
                URL,
                headers={"x-api-key": self.chave, "anthropic-version": "2023-06-01"},
                json={
                    "model": self.modelo,
                    "max_tokens": 300,
                    "system": INSTRUCOES,
                    "messages": [{"role": "user", "content": dados}],
                },
            )
            resposta.raise_for_status()
            blocos = resposta.json().get("content", [])
            texto = "".join(b.get("text", "") for b in blocos if b.get("type") == "text").strip()
            if texto:
                return texto
        except (httpx.HTTPError, ValueError) as erro:
            log.warning("IA indisponível (%s). Usando o assistente local.", erro)
        return self.reserva.orientar(aluno, vaga, compat)
