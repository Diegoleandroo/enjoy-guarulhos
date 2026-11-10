"""Gera dados/exemplo.json com escolas, empresas, vagas, alunos e pedidos FICTÍCIOS de Guarulhos.

Os bairros e as coordenadas (aproximadas) são reais; escolas, empresas e pessoas são inventadas.
Rodar:  python dados/gerar_exemplo.py
"""

import json
import random
from pathlib import Path

random.seed(2026)

# Escolas REAIS de Guarulhos. Endereços: Centro Paula Souza e lista oficial da
# Diretoria de Ensino Guarulhos Norte. Coordenadas aproximadas (centro do bairro).
# Oferta do Técnico em Desenvolvimento de Sistemas confirmada em fontes públicas:
# Etec de Guarulhos e EE Pimentas III. Nas demais, a oferta não foi verificada.
# Os ALUNOS, notas e pedidos continuam fictícios.
ESCOLAS = [
    ("esc-etec", "Etec de Guarulhos", "Parque Cecap", -23.4560, -46.4960,
     "R. Cristobal Claudio Elillo, 88"),
    ("esc-pimentas3", "EE Pimentas III", "Pimentas", -23.4460, -46.4060, ""),
    ("esc-allyrio", "EE Prof. Allyrio de Figueiredo Brasil", "Vila Fátima", -23.4560, -46.5180,
     "R. Duque de Caxias, 195"),
    ("esc-plinio", "EE Plinio Paulo Braga", "Taboão", -23.4200, -46.5330,
     "Av. Otávio Braga de Mesquita, 3900"),
    ("esc-mhelena", "EE Maria Helena Faria Lima e Cunha", "Cabuçu", -23.3850, -46.5300,
     "Av. Pedro de Souza Lopes, 7800"),
    ("esc-hernani", "EE Hernani Furini", "Jardim São João", -23.4150, -46.4520,
     "Av. Bom Jesus, 371"),
    ("esc-haroldo", "EE Brigadeiro Haroldo Veloso", "Haroldo Veloso", -23.4500, -46.4620,
     "R. Ester, 58"),
    ("esc-carmina", "EE Carmina Mendes Seródio", "Cidade Seródio", -23.3980, -46.4180,
     "Av. Abílio Mendes de Oliveira, 23"),
    ("esc-maestro", "EE Maestro João Carlos Martins", "Bonsucesso", -23.4120, -46.3940,
     "R. Gabriela Gurgel de Freitas, 179"),
    ("esc-mbombassei", "EE Prof. Mario Bombassei Filho", "Ponte Alta", -23.4300, -46.4180,
     "R. Olvídio Camilo, 100"),
]
PESOS = [9, 8, 6, 5, 3, 5, 4, 4, 5, 3]

TRILHAS = {
    "back-end": ["Python", "SQL", "Git", "API REST", "FastAPI", "Testes automatizados", "Docker", "PostgreSQL", "Java"],
    "front-end": ["HTML", "CSS", "JavaScript", "Git", "React", "Figma", "TypeScript"],
    "mobile": ["Kotlin", "Flutter", "Git", "Figma", "Java", "API REST"],
    "dados": ["Excel", "SQL", "Python", "Power BI", "Git"],
    "suporte": ["Suporte técnico", "Redes", "Excel", "Lógica de programação"],
}
PESO_TRILHA = {"back-end": 4, "front-end": 4, "mobile": 2, "dados": 3, "suporte": 3}

PROJETOS = {
    "back-end": [("API de biblioteca escolar", "Empréstimos e devoluções com regras de prazo e testes."),
                 ("Controle de estoque da cantina", "API com relatório de itens mais vendidos.")],
    "front-end": [("Site da feira de profissões", "Página responsiva com agenda e inscrições."),
                  ("Portfólio pessoal", "Site com projetos, feito do zero com HTML e CSS.")],
    "mobile": [("App de horários de ônibus de Guarulhos", "Consulta linhas e avisa o próximo horário."),
               ("App de lista de compras", "Listas compartilhadas com a família.")],
    "dados": [("Painel de frequência da turma", "Gráficos de presença por mês, sem expor nomes."),
              ("Análise de vagas de estágio", "Planilha com as habilidades mais pedidas na cidade.")],
    "suporte": [("Inventário do laboratório", "Planilha com o estado de cada computador."),
                ("Rede do grêmio estudantil", "Montagem e documentação de uma rede pequena.")],
}

NOMES = ["Ana", "Bruno", "Carla", "Davi", "Eduarda", "Felipe", "Gabriela", "Heitor", "Isabela",
         "João", "Kauã", "Larissa", "Matheus", "Nicole", "Otávio", "Pietra", "Rafael", "Sofia",
         "Thiago", "Valentina", "Vitor", "Yasmin", "Lucas", "Beatriz", "Enzo", "Lívia", "Miguel",
         "Rebeca", "Samuel", "Júlia", "Gustavo", "Manuela", "Caio", "Helena", "Pedro", "Alice"]
SOBRENOMES = ["Almeida", "Barbosa", "Cardoso", "Dias", "Esteves", "Ferraz", "Gomes", "Henrique",
              "Lacerda", "Moraes", "Nogueira", "Prado", "Queiroz", "Ribeiro", "Siqueira", "Teles",
              "Vasconcelos", "Moura", "Pacheco", "Rocha", "Campos", "Freitas"]

OBSERVACOES = [
    "Muito comprometido(a) com as entregas; ajuda os colegas nos projetos.",
    "Pontual e organizado(a). Lidera bem trabalhos em grupo.",
    "Evoluiu muito neste semestre, principalmente em lógica.",
    "Curioso(a), sempre traz soluções além do pedido.",
    "Precisa melhorar a frequência, mas tem bom potencial técnico.",
    "Responsável com prazos; participa da monitoria do laboratório.",
    "",
]


def nota(base, var=1.0):
    return round(min(10, max(4, random.gauss(base, var))), 1)


def desempenho():
    perfil = random.random()  # perfis mais e menos dedicados
    base = 6.2 + perfil * 3.4
    atitude = lambda: max(1, min(5, round(random.gauss(2.2 + perfil * 2.9, 0.6))))
    return {
        "media_tecnico": nota(base, 0.6),
        "media_regular": nota(base - 0.2, 0.7),
        "frequencia": int(min(100, max(65, random.gauss(78 + perfil * 20, 4)))),
        "comprometimento": atitude(),
        "responsabilidade": atitude(),
        "disciplina": atitude(),
    }


def aluno(i, escola_id=None, trilha=None):
    escola_id = escola_id or random.choices([e[0] for e in ESCOLAS], PESOS)[0]
    trilha = trilha or random.choices(list(PESO_TRILHA), list(PESO_TRILHA.values()))[0]
    modulo = random.choice([1, 2, 2, 3, 3])
    base = TRILHAS[trilha]
    qtd = min(len(base), 2 + modulo + random.randint(0, 2))
    habilidades = base[:3] + random.sample(base[3:], max(0, qtd - 3))
    if random.random() < 0.5:
        habilidades.append(random.choice(["Scrum", "Kanban", "Lógica de programação", "Inteligência Artificial"]))
    return {
        "id": f"aluno-{i:03d}",
        "nome": f"{random.choice(NOMES)} {random.choice(SOBRENOMES)}",
        "escola_id": escola_id,
        "curso": "Técnico em Desenvolvimento de Sistemas",
        "modulo": modulo,
        "turnos": random.choice([["manha"], ["tarde"], ["manha", "tarde"], ["tarde", "noite"], ["noite"]]),
        "modalidades": random.choice([["presencial"], ["hibrido", "presencial"],
                                      ["hibrido", "presencial", "remoto"], ["hibrido", "remoto"]]),
        "habilidades": list(dict.fromkeys(habilidades)),
        "desempenho": desempenho(),
        "observacao": random.choice(OBSERVACOES),
        "projetos": [{"titulo": t, "descricao": d, "link": ""}
                     for t, d in random.sample(PROJETOS[trilha], 1 if modulo < 3 else 2)],
        "autorizado": random.random() > 0.12,
    }


EMPRESAS = [
    {"id": "emp-trilha", "nome": "Trilha Software", "bairro": "Centro", "setor": "Software sob medida"},
    {"id": "emp-pista", "nome": "Pista Azul Logística", "bairro": "Cumbica", "setor": "Logística aeroportuária"},
    {"id": "emp-pixel", "nome": "Pixel Guaru", "bairro": "Vila Galvão", "setor": "Agência digital"},
    {"id": "emp-forja", "nome": "Forja Nova Metalurgia", "bairro": "Bonsucesso", "setor": "Indústria"},
    {"id": "emp-cuidar", "nome": "Cuidar+ Clínicas", "bairro": "Centro", "setor": "Saúde"},
    {"id": "emp-mercado", "nome": "Mercado Bom Preço", "bairro": "Pimentas", "setor": "Varejo"},
]

VAGAS = [
    {"id": "vaga-backend", "empresa_id": "emp-trilha", "titulo": "Estágio em desenvolvimento back-end",
     "modalidade": "hibrido", "turno": "tarde",
     "obrigatorias": ["Python", "SQL", "Git"], "desejaveis": ["API REST", "Testes automatizados", "Docker"],
     "descricao": "Apoiar o time na criação de APIs para clientes do comércio de Guarulhos."},
    {"id": "vaga-front", "empresa_id": "emp-pixel", "titulo": "Estágio em front-end",
     "modalidade": "presencial", "turno": "manha",
     "obrigatorias": ["HTML", "CSS", "JavaScript"], "desejaveis": ["React", "Figma", "Git"],
     "descricao": "Construir sites e landing pages para clientes da agência."},
    {"id": "vaga-dados", "empresa_id": "emp-pista", "titulo": "Jovem aprendiz em dados",
     "modalidade": "presencial", "turno": "tarde",
     "obrigatorias": ["Excel", "SQL"], "desejaveis": ["Power BI", "Python"],
     "descricao": "Montar relatórios de movimentação de cargas do aeroporto."},
    {"id": "vaga-suporte", "empresa_id": "emp-forja", "titulo": "Estágio em suporte de TI",
     "modalidade": "presencial", "turno": "manha",
     "obrigatorias": ["Suporte técnico", "Redes"], "desejaveis": ["Excel"],
     "descricao": "Atender os setores da fábrica e manter os equipamentos."},
    {"id": "vaga-mobile", "empresa_id": "emp-cuidar", "titulo": "Estágio em desenvolvimento mobile",
     "modalidade": "remoto", "turno": "tarde",
     "obrigatorias": ["Kotlin", "Git"], "desejaveis": ["Flutter", "API REST", "Figma"],
     "descricao": "Evoluir o app de agendamento de consultas."},
    {"id": "vaga-sistemas", "empresa_id": "emp-mercado", "titulo": "Jovem aprendiz em sistemas",
     "modalidade": "presencial", "turno": "tarde",
     "obrigatorias": ["Lógica de programação", "Excel"], "desejaveis": ["SQL", "Python"],
     "descricao": "Automatizar planilhas de estoque das lojas."},
]

TRILHA_DA_VAGA = {"vaga-backend": "back-end", "vaga-front": "front-end", "vaga-dados": "dados",
                  "vaga-suporte": "suporte", "vaga-mobile": "mobile", "vaga-sistemas": "dados"}

alunos = [aluno(i) for i in range(1, 79)]

# Garante bons candidatos para cada vaga: alunos destaque, no turno e modalidade certos.
n = len(alunos)
for vaga in VAGAS:
    for k in range(2):
        n += 1
        a = aluno(n, trilha=TRILHA_DA_VAGA[vaga["id"]])
        a.update(
            modulo=3 - k,
            turnos=sorted({vaga["turno"], random.choice(["manha", "tarde", "noite"])}),
            modalidades=sorted({vaga["modalidade"], "presencial"}),
            habilidades=list(dict.fromkeys(vaga["obrigatorias"] + vaga["desejaveis"][: 1 + k]
                                           + TRILHAS[TRILHA_DA_VAGA[vaga["id"]]][:2])),
            desempenho={"media_tecnico": round(random.uniform(8.3, 9.8), 1),
                        "media_regular": round(random.uniform(8.0, 9.5), 1),
                        "frequencia": random.randint(92, 100),
                        "comprometimento": 5, "responsabilidade": random.choice([4, 5]),
                        "disciplina": random.choice([4, 5])},
            observacao=random.choice(OBSERVACOES[:4] + OBSERVACOES[5:6]),
            autorizado=True,
        )
        alunos.append(a)

destaques = [a for a in alunos[78:]]
PEDIDOS = [
    {"id": "ped-001", "empresa_id": "emp-trilha", "escola_id": destaques[0]["escola_id"],
     "aluno_id": destaques[0]["id"], "vaga_id": "vaga-backend",
     "mensagem": "Gostamos muito do perfil e do projeto de API. Podemos conversar sobre o estágio?",
     "criado_em": "2026-11-05T10:12:00-03:00"},
    {"id": "ped-002", "empresa_id": "emp-pixel", "escola_id": "esc-allyrio", "vaga_id": "vaga-front",
     "mensagem": "Estamos com vaga de estágio em front-end, pertinho da escola. A coordenação poderia indicar dois alunos?",
     "criado_em": "2026-11-06T15:40:00-03:00"},
    {"id": "ped-003", "empresa_id": "emp-pista", "escola_id": "esc-haroldo", "vaga_id": "vaga-dados",
     "mensagem": "Procuramos jovem aprendiz para relatórios de cargas, bem perto da escola. Há alunos com perfil?",
     "criado_em": "2026-11-07T09:05:00-03:00"},
    {"id": "ped-004", "empresa_id": "emp-forja", "escola_id": destaques[6]["escola_id"],
     "aluno_id": destaques[6]["id"], "vaga_id": "vaga-suporte",
     "mensagem": "O perfil combina com nossa vaga de suporte na fábrica. Podemos chamar para entrevista?",
     "criado_em": "2026-11-03T14:20:00-03:00", "status": "aprovado",
     "resposta": "Conversamos com o aluno e a família. Ele tem interesse; combinamos a entrevista pela escola.",
     "decidido_em": "2026-11-04T11:00:00-03:00"},
]

dados = {
    "escolas": [dict(id=e[0], nome=e[1], bairro=e[2], cidade="Guarulhos", latitude=e[3], longitude=e[4],
                     endereco=e[5]) for e in ESCOLAS],
    "empresas": EMPRESAS,
    "vagas": VAGAS,
    "alunos": alunos,
    "pedidos": PEDIDOS,
}

destino = Path(__file__).with_name("exemplo.json")
destino.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{len(alunos)} alunos fictícios em {len(ESCOLAS)} escolas de Guarulhos -> {destino}")
