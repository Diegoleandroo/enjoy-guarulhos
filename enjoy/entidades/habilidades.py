"""Habilidades: a "moeda" do sistema.

Aluno escreve "JS", empresa escreve "JavaScript". Sem normalizar, os dois
nunca se encontram. Esta é uma regra de negócio, por isso mora no núcleo.
"""

from __future__ import annotations

import unicodedata

# chave normalizada -> nome de exibição
NOMES = {
    "python": "Python",
    "java": "Java",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "html": "HTML",
    "css": "CSS",
    "react": "React",
    "node.js": "Node.js",
    "sql": "SQL",
    "postgresql": "PostgreSQL",
    "mysql": "MySQL",
    "git": "Git",
    "fastapi": "FastAPI",
    "flutter": "Flutter",
    "kotlin": "Kotlin",
    "c#": "C#",
    "php": "PHP",
    "docker": "Docker",
    "testes automatizados": "Testes automatizados",
    "api rest": "API REST",
    "scrum": "Scrum",
    "kanban": "Kanban",
    "figma": "Figma",
    "excel": "Excel",
    "power bi": "Power BI",
    "inteligencia artificial": "Inteligência Artificial",
    "logica de programacao": "Lógica de programação",
    "suporte tecnico": "Suporte técnico",
    "redes": "Redes",
}

SINONIMOS = {
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "html5": "html",
    "css3": "css",
    "reactjs": "react",
    "react.js": "react",
    "node": "node.js",
    "nodejs": "node.js",
    "postgres": "postgresql",
    "github": "git",
    "gitlab": "git",
    "csharp": "c#",
    "c sharp": "c#",
    "rest": "api rest",
    "apis rest": "api rest",
    "pytest": "testes automatizados",
    "testes": "testes automatizados",
    "ia": "inteligencia artificial",
    "ai": "inteligencia artificial",
    "logica": "logica de programacao",
    "powerbi": "power bi",
}


def _sem_acento(texto: str) -> str:
    decomposto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in decomposto if not unicodedata.combining(c))


def normalizar(habilidade: str) -> str:
    chave = " ".join(_sem_acento(habilidade).lower().split())
    return SINONIMOS.get(chave, chave)


def normalizar_todas(habilidades) -> tuple[str, ...]:
    vistas: list[str] = []
    for h in habilidades:
        chave = normalizar(h)
        if chave and chave not in vistas:
            vistas.append(chave)
    return tuple(vistas)


def exibir(chave: str) -> str:
    return NOMES.get(chave, chave.capitalize())
