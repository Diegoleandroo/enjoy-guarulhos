"""Assistente por regras: funciona sem internet e sem custo. É o padrão.

Fala com a coordenação, que é quem orienta o aluno.
"""

from __future__ import annotations

from enjoy.casos_de_uso.portas import AssistenteDeCarreira
from enjoy.entidades import Aluno, Compatibilidade, Vaga, habilidades as hab

DICAS = {
    "git": "publicar um projeto no GitHub com commits frequentes",
    "sql": "montar um banco simples (biblioteca, cantina) e praticar consultas com JOIN",
    "python": "fazer um script que automatize uma tarefa da escola",
    "javascript": "adicionar filtros e formulários a uma página que já fez",
    "react": "refazer uma tela de HTML usando componentes React",
    "api rest": "criar uma API com rotas de listar, criar, editar e excluir",
    "testes automatizados": "escrever testes para as funções principais de um projeto",
    "docker": "colocar um projeto para rodar com um Dockerfile",
    "figma": "desenhar no Figma as telas de um app antes de programar",
    "excel": "montar uma planilha de controle com fórmulas e gráfico",
    "power bi": "transformar uma planilha pública em um painel",
    "suporte tecnico": "ajudar na manutenção do laboratório da escola",
    "redes": "documentar a rede do laboratório com o professor",
}


class AssistenteLocal(AssistenteDeCarreira):
    nome = "Assistente local (regras)"

    def orientar(self, aluno: Aluno, vaga: Vaga, compat: Compatibilidade) -> str:
        nome = aluno.nome.split()[0]
        partes = []
        if compat.tem:
            fortes = ", ".join(hab.exibir(h) for h in compat.tem[:4])
            partes.append(f"{nome} já tem {fortes}, que esta vaga pede.")
        if compat.faltam_obrigatorias:
            falta = compat.faltam_obrigatorias[0]
            dica = DICAS.get(falta, f"estudar o básico de {hab.exibir(falta)} e aplicar em um projeto")
            nomes = ", ".join(hab.exibir(h) for h in compat.faltam_obrigatorias)
            partes.append(f"Falta {nomes}. Um bom próximo passo: {dica}.")
        elif compat.faltam_desejaveis:
            nomes = ", ".join(hab.exibir(h) for h in compat.faltam_desejaveis)
            partes.append(f"Cobre tudo o que é obrigatório. Para se destacar: {nomes}.")
        else:
            partes.append("Cobre todas as habilidades da vaga.")
        if not compat.turno_ok:
            partes.append("O turno da vaga não bate com a disponibilidade do aluno.")
        if not compat.modalidade_ok:
            partes.append("A modalidade da vaga não está entre as que o aluno aceita.")
        return " ".join(partes)
