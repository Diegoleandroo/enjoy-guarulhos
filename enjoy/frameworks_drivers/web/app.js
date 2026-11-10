"use strict";

/* Enjoy (Guarulhos): a tela só conversa com a API. Nenhuma regra de negócio aqui. */

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (t) => String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const TURNO = { manha: "Manhã", tarde: "Tarde", noite: "Noite" };
const MODAL = { presencial: "Presencial", hibrido: "Híbrido", remoto: "Remoto" };
const ATITUDES = { comprometimento: "Comprometimento", responsabilidade: "Responsabilidade", disciplina: "Disciplina" };
const lista = (txt) => txt.split(",").map((s) => s.trim()).filter(Boolean);
const num = (n) => Number(n).toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 });

const estado = { ref: null, habilidades: [], bairro: "", vagaAtual: "", status: "pendente", sub: "pedidos" };

async function api(url, opcoes = {}) {
  const resp = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...opcoes,
    body: opcoes.body ? JSON.stringify(opcoes.body) : undefined,
  });
  const dados = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(dados.erro || (Array.isArray(dados.detail) ? "Confira os campos do formulário." : "Algo deu errado."));
  return dados;
}

let tempoAviso;
function avisar(texto, erro = false) {
  const el = $("#aviso");
  el.textContent = texto;
  el.classList.toggle("erro", erro);
  el.classList.add("ver");
  clearTimeout(tempoAviso);
  tempoAviso = setTimeout(() => el.classList.remove("ver"), 3400);
}

const empresaAtual = () => $("#persona-empresa").value;
const nomeEmpresa = () => estado.ref.empresas.find((e) => e.id === empresaAtual())?.nome || "";
const anel = (p) => `<div class="anel" style="--p:${p}"><span>${p}%</span></div>`;
const etiquetas = (hs, classe = "", destaque = []) =>
  hs.map((h) => `<span class="etq ${destaque.includes(h) ? "sim" : classe}">${esc(h)}</span>`).join("");
const selo = (d) => (d.destaque ? `<span class="selo-destaque" title="Boas notas, frequência e atitude">★ Destaque</span>` : "");
const indicadores = (d) => `<div class="indicadores">
  <span><b>${num(d.media_geral)}</b> média</span><span><b>${d.frequencia}%</b> frequência</span><span><b>${num(d.atitude)}</b>/5 atitude</span></div>`;
const pontos = (n) => `<span class="pontos" aria-label="${n} de 5">${[1, 2, 3, 4, 5].map((i) => `<i class="${i <= n ? "on" : ""}"></i>`).join("")}</span>`;

/* ================= navegação ================= */
function irPara() {
  const aba = (location.hash || "#mapa").slice(1);
  const valida = ["mapa", "vagas", "escola", "aluno"].includes(aba) ? aba : "mapa";
  $$(".aba").forEach((s) => (s.hidden = s.dataset.aba !== valida));
  $$(".abas a").forEach((a) => a.classList.toggle("ativa", a.dataset.aba === valida));
  if (valida === "mapa") setTimeout(enquadrar, 50);
  if (valida === "vagas") carregarVagas();
  if (valida === "escola") carregarEscola();
  if (valida === "aluno") carregarPanorama();
}
window.addEventListener("hashchange", irPara);

/* ================= mapa de Guarulhos ================= */
let mapa, camadaEscolas, camadaRuas, limites, contorno;

function enquadrar() {
  if (!mapa || !limites) return;
  mapa.invalidateSize();
  mapa.fitBounds(limites, { padding: [24, 24] });
}

async function iniciarMapa() {
  mapa = L.map("mapa-leaflet", { zoomSnap: 0.25, scrollWheelZoom: false });
  mapa.attributionControl.setPrefix(false);
  mapa.attributionControl.addAttribution("Malha: IBGE");
  const geo = await fetch("guarulhos.geojson").then((r) => r.json());
  contorno = L.geoJSON(geo, {
    style: { color: "#1D6B52", weight: 2, fillColor: "#FFFFFF", fillOpacity: 0.9, dashArray: "" },
    interactive: false,
  }).addTo(mapa);
  limites = contorno.getBounds();
  enquadrar();
  camadaEscolas = L.layerGroup().addTo(mapa);
  window.addEventListener("resize", enquadrar);

  $("#ruas").addEventListener("change", (e) => {
    if (e.target.checked) {
      camadaRuas = camadaRuas || L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 18,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      });
      camadaRuas.addTo(mapa).bringToBack();
      contorno.setStyle({ fillOpacity: 0.12 });
    } else if (camadaRuas) {
      mapa.removeLayer(camadaRuas);
      contorno.setStyle({ fillOpacity: 0.9 });
    }
  });
}

const VERDE = "#1D6B52";
const DIRECAO_ROTULO = { "Vila Fátima": "left", "Haroldo Veloso": "bottom", "Ponte Alta": "bottom", "Parque Cecap": "top" };
function corPorProporcao(p) {
  const a = [248, 190, 170], b = [214, 62, 24];
  p = Math.min(1, p * 1.5);
  return `rgb(${a.map((v, i) => Math.round(v + (b[i] - v) * p)).join(",")})`;
}

async function atualizarMapa() {
  const dados = await api(`/api/mapa?${new URLSearchParams({ habilidades: estado.habilidades.join(",") })}`);
  const filtro = estado.habilidades.length > 0;

  $("#resumo").innerHTML = filtro
    ? `<strong>${dados.com_habilidades}</strong><span>de ${dados.total} alunos autorizados têm ${esc(dados.habilidades.join(" + "))}, em ${dados.bairros.filter((b) => b.com_habilidades).length} bairros de Guarulhos</span>`
    : `<strong>${dados.total}</strong><span>alunos autorizados em ${dados.bairros.length} bairros · <b class="claro">${dados.destaques}</b> são destaque na escola</span>`;

  $("#hab-sugestoes").innerHTML = dados.mais_comuns
    .filter((h) => !estado.habilidades.includes(h.habilidade)).slice(0, 6)
    .map((h) => `<button type="button" data-h="${esc(h.habilidade)}">+ ${esc(h.habilidade)}</button>`).join("");

  const max = Math.max(1, ...dados.bairros.map((b) => (filtro ? b.com_habilidades : b.total)));
  $("#ranking").innerHTML = dados.bairros.map((b) => {
    const n = filtro ? b.com_habilidades : b.total;
    const escolas = b.escolas.map((e) => e.nome).join(", ");
    return `<li class="${estado.bairro === b.bairro ? "ativo" : ""}">
      <button type="button" class="linha-bairro" data-bairro="${esc(b.bairro)}">
        <span><span class="cid">${esc(b.bairro)}</span><br><span class="reg">${esc(escolas)}</span></span>
        <span class="num">${n}${filtro ? `<small> / ${b.total}</small>` : ""}</span>
        <span class="barra"><i style="width:${(100 * n) / max}%"></i></span>
      </button>
      <button type="button" class="falar-escola" data-escola="${esc(b.escolas[0].id)}">Falar com a escola</button></li>`;
  }).join("");

  camadaEscolas.clearLayers();
  dados.bairros.forEach((b) => b.escolas.forEach((e) => {
    const valor = filtro ? e.com_habilidades : e.total;
    const raio = 8 + Math.sqrt(valor) * 4.5;
    const apagado = filtro && !e.com_habilidades;
    const m = L.circleMarker([e.latitude, e.longitude], {
      radius: apagado ? 7 : raio, color: "#fff", weight: 2.5,
      fillColor: apagado ? "#C5D1CA" : filtro ? corPorProporcao(e.com_habilidades / Math.max(1, e.total)) : VERDE,
      fillOpacity: filtro ? 0.95 : 0.82,
    }).addTo(camadaEscolas);
    m.bindTooltip(`<b>${esc(e.nome)}</b><br>${esc(e.endereco ? e.endereco + " · " : "")}${esc(e.bairro)}<br>${filtro ? `<b>${e.com_habilidades}</b> de ${e.total} alunos combinam` : `${e.total} alunos autorizados`} · ${e.destaques} destaque${e.destaques === 1 ? "" : "s"}<br><span style="color:#6B7D74">Forte em: ${esc(e.principais.join(", "))}</span>`,
      { className: "dica", direction: "top", offset: [0, -raio] });
    m.on("click", () => selecionarBairro(e.bairro));
    const r = apagado ? 7 : raio, dir = DIRECAO_ROTULO[e.bairro] || "right";
    const desloc = { right: [r, 0], left: [-r, 0], top: [0, -r], bottom: [0, r] }[dir];
    L.tooltip({ permanent: true, direction: dir, className: "rotulo-cidade", offset: desloc, interactive: false })
      .setLatLng([e.latitude, e.longitude]).setContent(esc(e.bairro)).addTo(camadaEscolas);
  }));

  $("#legenda").innerHTML = filtro
    ? `<div class="linha"><i style="width:12px;height:12px;background:${corPorProporcao(1)}"></i> muitos alunos combinam</div>
       <div class="linha"><i style="width:12px;height:12px;background:${corPorProporcao(0.2)}"></i> poucos combinam</div>
       <div class="linha"><i style="width:8px;height:8px;background:#C5D1CA"></i> nenhum por enquanto</div>`
    : `<div class="linha"><i style="width:12px;height:12px;background:${VERDE}"></i> escola · tamanho = nº de alunos</div>`;
}

function selecionarBairro(bairro) {
  estado.bairro = estado.bairro === bairro ? "" : bairro;
  atualizarTudo();
  if (estado.bairro) $("#talentos-titulo").scrollIntoView({ behavior: "smooth", block: "start" });
}

async function buscarTalentos() {
  const q = new URLSearchParams({
    habilidades: estado.habilidades.join(","), bairro: estado.bairro,
    turno: $("#f-turno").value, modulo: $("#f-modulo").value,
    media_minima: $("#f-media").value, destaques: $("#f-destaques").checked,
  });
  const talentos = await api(`/api/talentos?${q}`);
  $("#talentos-titulo").textContent = `${talentos.length} talento${talentos.length === 1 ? "" : "s"}${estado.bairro ? ` em ${estado.bairro}` : " em Guarulhos"}`;
  $("#limpar-local").hidden = !estado.bairro;
  $("#talentos").innerHTML = talentos.length
    ? talentos.map(cartaoTalento).join("")
    : `<div class="vazio"><p>Ninguém com esse filtro ainda. Tente tirar uma habilidade ou baixar a média mínima.</p></div>`;
}

function cartaoTalento(t) {
  const filtro = estado.habilidades.length > 0;
  return `<button type="button" class="talento" data-aluno="${esc(t.id)}">
    <div class="talento-topo">
      <div class="avatar">${esc(t.iniciais)}</div>
      <div class="quem"><b>${esc(t.nome)} ${selo(t.desempenho)}</b><span>${esc(t.escola.nome)} · ${esc(t.escola.bairro)}</span></div>
      ${filtro ? anel(t.aderencia) : ""}
    </div>
    ${indicadores(t.desempenho)}
    <div class="etiquetas">${etiquetas(t.habilidades.slice(0, 6), "", t.combinam)}</div>
    <div class="meta"><span>${t.modulo}º módulo</span><span>${t.turnos.map((x) => TURNO[x]).join(" / ")}</span></div>
  </button>`;
}

async function atualizarTudo() {
  try { await Promise.all([atualizarMapa(), buscarTalentos()]); } catch (e) { avisar(e.message, true); }
}

function renderChips() {
  const caixa = $("#hab-escolhidas");
  $$(".chip", caixa).forEach((c) => c.remove());
  estado.habilidades.forEach((h) => {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.innerHTML = `${esc(h)}<button type="button" aria-label="Remover ${esc(h)}">×</button>`;
    chip.querySelector("button").onclick = () => { estado.habilidades = estado.habilidades.filter((x) => x !== h); renderChips(); atualizarTudo(); };
    caixa.insertBefore(chip, $("#hab-entrada"));
  });
}

function adicionarHabilidade(h) {
  h = h.trim();
  if (!h) return;
  const oficial = estado.ref.habilidades.find((x) => x.toLowerCase() === h.toLowerCase()) || h;
  if (!estado.habilidades.includes(oficial)) estado.habilidades.push(oficial);
  renderChips();
  atualizarTudo();
}

/* ================= gaveta ================= */
function abrirGaveta(html) {
  $("#gaveta-conteudo").innerHTML = html;
  $("#veu").hidden = false;
  $("#gaveta").classList.add("aberta");
  $("#gaveta").setAttribute("aria-hidden", "false");
  $("#fechar-gaveta").focus();
}
function fecharGaveta() {
  $("#gaveta").classList.remove("aberta");
  $("#gaveta").setAttribute("aria-hidden", "true");
  $("#veu").hidden = true;
}

const avisoPrivacidade = (escola) => `<div class="privacidade"><span aria-hidden="true">🔒</span><span>O pedido vai para a coordenação da ${esc(escola)}. A escola analisa, conversa com o aluno e a família e responde. A empresa nunca recebe telefone ou e-mail do aluno.</span></div>`;

async function enviarPedido(corpo) {
  try {
    await api("/api/pedidos", { method: "POST", body: { empresa_id: empresaAtual(), ...corpo } });
    fecharGaveta();
    avisar("Pedido enviado à escola.");
  } catch (e) { avisar(e.message, true); }
}

async function abrirPerfil(id) {
  try {
    const [p, vagas] = await Promise.all([api(`/api/talentos/${id}`), api("/api/vagas")]);
    const minhas = vagas.filter((v) => v.empresa.id === empresaAtual());
    const d = p.desempenho;
    abrirGaveta(`
      <div class="g-topo"><div class="avatar">${esc(p.iniciais)}</div>
        <div><h2>${esc(p.nome)} ${selo(d)}</h2><p>${esc(p.curso)} · ${p.modulo}º módulo</p><p>${esc(p.escola.nome)} · ${esc(p.escola.bairro)}</p></div></div>
      <div class="g-bloco"><h3>Na escola</h3>
        <div class="notas">
          <div><span>Técnico</span><b>${num(d.media_tecnico)}</b></div>
          <div><span>Regular</span><b>${num(d.media_regular)}</b></div>
          <div><span>Frequência</span><b>${d.frequencia}%</b></div>
        </div>
        <ul class="atitudes">${Object.entries(ATITUDES).map(([k, rot]) => `<li><span>${rot}</span>${pontos(d.atitudes[k])}</li>`).join("")}</ul>
        <p class="nota">Informações registradas pela escola, com autorização do responsável.</p>
      </div>
      <div class="g-bloco"><h3>Habilidades</h3><div class="etiquetas">${etiquetas(p.habilidades, "", estado.habilidades)}</div>
        <div class="meta" style="margin-top:10px"><span>${p.turnos.map((x) => TURNO[x]).join(" / ")}</span><span>${p.modalidades.map((x) => MODAL[x]).join(", ")}</span></div></div>
      ${p.projetos.length ? `<div class="g-bloco"><h3>Projetos</h3>${p.projetos.map((x) => `<div class="projeto"><b>${esc(x.titulo)}</b><span>${esc(x.descricao)}</span></div>`).join("")}</div>` : ""}
      <div class="g-bloco"><h3>Combina com a sua vaga?</h3>
        ${minhas.length ? `<select id="g-vaga" aria-label="Vaga">${minhas.map((v) => `<option value="${esc(v.id)}">${esc(v.titulo)}</option>`).join("")}</select><div id="g-compat"></div>`
          : `<p class="nota">${esc(nomeEmpresa())} ainda não tem vagas publicadas.</p>`}
      </div>
      <div class="g-bloco"><h3>Falar com a escola sobre este aluno</h3>
        <form id="form-pedido" class="form-pilha">
          <textarea name="mensagem" rows="3" required minlength="10" placeholder="Conte à coordenação por que o perfil interessa à ${esc(nomeEmpresa())}."></textarea>
          <button class="botao coral">Enviar pedido à escola</button>
          ${avisoPrivacidade(p.escola.nome)}
        </form>
      </div>`);
    const sel = $("#g-vaga");
    const compara = async () => {
      const c = await api(`/api/compatibilidade?aluno=${encodeURIComponent(id)}&vaga=${encodeURIComponent(sel.value)}`);
      $("#g-compat").innerHTML = `<div class="compat">${anel(c.percentual)}<div class="etiquetas">${etiquetas(c.tem, "", c.tem)}${etiquetas(c.faltam_obrigatorias, "falta")}</div></div>
        ${!c.turno_ok ? `<p class="nota">⚠ Turno diferente do da vaga.</p>` : ""}${!c.modalidade_ok ? `<p class="nota">⚠ Modalidade não combina.</p>` : ""}`;
    };
    if (sel) { sel.onchange = compara; compara(); }
    $("#form-pedido").onsubmit = (ev) => { ev.preventDefault(); enviarPedido({ aluno_id: id, vaga_id: sel ? sel.value : null, mensagem: ev.target.mensagem.value }); };
  } catch (e) { avisar(e.message, true); }
}

async function abrirContatoEscola(escolaId) {
  const escola = estado.ref.escolas.find((e) => e.id === escolaId);
  const vagas = (await api("/api/vagas")).filter((v) => v.empresa.id === empresaAtual());
  abrirGaveta(`
    <p class="sobretitulo">Pedido de indicação</p>
    <h2>${esc(escola.nome)}</h2><p class="nota">${esc(escola.endereco ? escola.endereco + " · " : "")}${esc(escola.bairro)} · Guarulhos</p>
    <p class="apoio">Peça à coordenação que indique alunos para uma vaga. A escola conhece o dia a dia de cada um e sabe quem está pronto.</p>
    <form id="form-indicacao" class="form-pilha" style="margin-top:18px">
      ${vagas.length ? `<label class="rotulo">Vaga<select name="vaga">${vagas.map((v) => `<option value="${esc(v.id)}">${esc(v.titulo)}</option>`).join("")}</select></label>`
        : `<p class="nota">Publique uma vaga na aba Vagas para pedir indicações.</p>`}
      <label class="rotulo">Mensagem<textarea name="mensagem" rows="4" required minlength="10" placeholder="Ex.: Temos uma vaga de estágio à tarde aqui no bairro. Poderiam indicar dois alunos?"></textarea></label>
      <button class="botao coral" ${vagas.length ? "" : "disabled"}>Enviar à escola</button>
      ${avisoPrivacidade(escola.nome)}
    </form>`);
  $("#form-indicacao").onsubmit = (ev) => { ev.preventDefault(); enviarPedido({ escola_id: escolaId, vaga_id: ev.target.vaga.value, mensagem: ev.target.mensagem.value }); };
}

/* ================= vagas ================= */
async function carregarVagas() {
  const vagas = await api("/api/vagas");
  if (!vagas.some((v) => v.id === estado.vagaAtual)) estado.vagaAtual = vagas[0]?.id || "";
  $("#lista-vagas").innerHTML = vagas.map((v) => `<li><button type="button" data-vaga="${esc(v.id)}" class="${v.id === estado.vagaAtual ? "ativa" : ""}">
      <b>${esc(v.titulo)}</b><small>${esc(v.empresa.nome)} · ${esc(v.empresa.bairro)} · ${MODAL[v.modalidade]} · ${TURNO[v.turno]}</small>
      <div class="etiquetas">${etiquetas(v.obrigatorias, "sim")}${etiquetas(v.desejaveis)}</div></button></li>`).join("");
  if (estado.vagaAtual) carregarRecomendados(estado.vagaAtual);
}

async function carregarRecomendados(id) {
  estado.vagaAtual = id;
  $$("#lista-vagas button").forEach((b) => b.classList.toggle("ativa", b.dataset.vaga === id));
  const r = await api(`/api/vagas/${id}/recomendados`);
  $("#recomendados").innerHTML = `<div><p class="sobretitulo">Mais compatíveis</p><h2>${esc(r.vaga.titulo)}</h2><p class="apoio">${esc(r.vaga.descricao)}</p></div>` +
    (r.candidatos.length ? r.candidatos.map((c, i) => `<div class="candidato" data-aluno="${esc(c.id)}" role="button" tabindex="0">
        <span class="pos">${i + 1}</span>
        <div class="info"><b>${esc(c.nome)} ${selo(c.desempenho)}</b><small>${esc(c.escola.nome)} · ${esc(c.escola.bairro)} · ${c.modulo}º módulo</small>
          ${indicadores(c.desempenho)}
          <div class="etiquetas">${etiquetas(c.compatibilidade.tem, "sim")}${etiquetas(c.compatibilidade.faltam_obrigatorias, "falta")}</div></div>
        <div class="pct">${c.compatibilidade.percentual}%<small>compatível</small></div></div>`).join("")
      : `<div class="vazio"><p>Nenhum aluno combina com esta vaga ainda.</p></div>`);
}

/* ================= escola ================= */
async function carregarEscola() {
  const escola = estado.ref.escolas.find((e) => e.id === $("#escola-atual").value);
  $("#escola-titulo").textContent = escola ? escola.nome : "Sua escola";
  $$("[data-painel]").forEach((p) => (p.hidden = p.dataset.painel !== estado.sub));
  $$("#sub-escola button").forEach((b) => b.classList.toggle("ativa", b.dataset.sub === estado.sub));
  if (estado.sub === "pedidos") carregarPedidos();
  if (estado.sub === "alunos") carregarAlunosDaEscola();
}

async function carregarPedidos() {
  const itens = await api(`/api/pedidos?escola=${encodeURIComponent($("#escola-atual").value)}&status=${estado.status}`);
  const fmt = (iso) => new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
  $("#pedidos").innerHTML = itens.length ? itens.map((p) => `<article class="cartao pedido">
      <div>
        <div class="pedido-tags"><span class="status ${p.status}">${p.status}</span><span class="tipo">${p.tipo === "aluno" ? "Sobre um aluno" : "Pedido de indicação"}</span></div>
        <h3>${p.tipo === "aluno" ? `${esc(p.empresa.nome)} quer falar sobre ${esc(p.aluno.nome)}` : `${esc(p.empresa.nome)} pede indicação de alunos`}</h3>
        <p>${p.vaga ? `Vaga: ${esc(p.vaga.titulo)} · ` : ""}${esc(p.empresa.setor)} · ${esc(p.empresa.bairro)} · ${fmt(p.criado_em)}</p>
        <blockquote>${esc(p.mensagem)}</blockquote>
        ${p.resposta ? `<p class="resposta"><b>Resposta da escola:</b> ${esc(p.resposta)}</p>` : ""}
        ${p.status === "pendente" ? `<textarea class="campo-resposta" data-resposta="${esc(p.id)}" rows="2" placeholder="Resposta para a empresa (opcional). Ex.: Vamos conversar com o aluno e a família e retornamos até sexta."></textarea>` : ""}
      </div>
      ${p.status === "pendente" ? `<div class="acoes coluna"><button class="botao pequeno" data-decidir="${esc(p.id)}" data-aprovar="1">Aprovar</button><button class="botao fantasma pequeno" data-decidir="${esc(p.id)}" data-aprovar="0">Recusar</button></div>` : ""}
    </article>`).join("")
    : `<div class="vazio"><p>Nenhum pedido ${estado.status === "pendente" ? "pendente" : estado.status === "aprovado" ? "aprovado" : "recusado"} para esta escola.</p></div>`;
}

async function carregarAlunosDaEscola() {
  const alunos = await api(`/api/escolas/${encodeURIComponent($("#escola-atual").value)}/alunos`);
  $("#tabela-alunos").innerHTML = `<thead><tr><th>Aluno</th><th>Módulo</th><th>Técnico</th><th>Regular</th><th>Frequência</th><th>Atitude</th><th>Para empresas</th></tr></thead><tbody>` +
    alunos.map((a) => `<tr>
      <td><b>${esc(a.nome)}</b> ${selo(a.desempenho)}<br><small>${esc(a.habilidades.slice(0, 4).join(", "))}</small>${a.observacao ? `<br><small class="obs">“${esc(a.observacao)}”</small>` : ""}</td>
      <td>${a.modulo}º</td><td>${num(a.desempenho.media_tecnico)}</td><td>${num(a.desempenho.media_regular)}</td>
      <td>${a.desempenho.frequencia}%</td><td>${num(a.desempenho.atitude)}</td>
      <td>${a.autorizado ? `<span class="status aprovado">aparece como ${esc(a.nome_publico)}</span>` : `<span class="status pendente">sem autorização</span>`}</td></tr>`).join("") +
    `</tbody>`;
}

async function cadastrarAluno(ev) {
  ev.preventDefault();
  const f = ev.target;
  const marcados = (n) => $$(`input[name=${n}]:checked`, f).map((i) => i.value);
  const corpo = {
    nome: f.nome.value.trim(), modulo: Number(f.modulo.value),
    turnos: marcados("turnos"), modalidades: marcados("modalidades"), habilidades: lista(f.habilidades.value),
    desempenho: {
      media_tecnico: Number(f.media_tecnico.value), media_regular: Number(f.media_regular.value), frequencia: Number(f.frequencia.value),
      ...Object.fromEntries(Object.keys(ATITUDES).map((k) => [k, Number(f[k].value)])),
    },
    observacao: f.observacao.value.trim(),
    projetos: f.projeto.value.trim() ? [{ titulo: f.projeto.value.trim(), descricao: "", link: "" }] : [],
    autorizado: f.autorizado.checked,
  };
  try {
    const a = await api(`/api/escolas/${encodeURIComponent($("#escola-atual").value)}/alunos`, { method: "POST", body: corpo });
    f.reset();
    avisar(a.autorizado ? `${a.nome} cadastrado. Aparece para empresas como ${a.nome_publico}.` : `${a.nome} cadastrado, ainda sem autorização para aparecer.`);
    estado.sub = "alunos";
    carregarEscola();
    atualizarTudo();
  } catch (e) { avisar(e.message, true); }
}

/* ================= para o aluno ================= */
async function carregarPanorama() {
  const p = await api("/api/panorama");
  const c = p.criterios;
  const pilares = [
    ["Comprometimento", "Fazer o que combinou, até o fim. Entregar os projetos do curso com capricho."],
    ["Responsabilidade", "Cumprir prazos, cuidar do que é seu e do que é da turma."],
    ["Disciplina", "Estudar mesmo quando ninguém está cobrando. Constância vale mais que pressa."],
    ["Boas notas", `Média de pelo menos ${num(c.media_minima)} no técnico e no ensino regular. As empresas olham os dois.`],
    ["Frequência", `Pelo menos ${c.frequencia_minima}% de presença. Quem falta na escola, falta no estágio.`],
  ];
  $("#pilares").innerHTML = pilares.map(([t, d], i) => `<div class="pilar"><span class="pilar-num">${String(i + 1).padStart(2, "0")}</span><h3>${t}</h3><p>${d}</p></div>`).join("");
  $("#numeros").innerHTML = `
    <div class="numero"><b>${p.vagas_abertas}</b><span>vagas abertas</span></div>
    <div class="numero"><b>${p.empresas_contratando}</b><span>empresas de Guarulhos procurando</span></div>
    <div class="numero"><b>${p.pedidos_aprovados}</b><span>contatos já aprovados pelas escolas</span></div>`;
  const max = Math.max(1, ...p.habilidades_mais_pedidas.map((h) => h.vagas));
  $("#mais-pedidas").innerHTML = p.habilidades_mais_pedidas.map((h) => `<div class="barra-h"><span>${esc(h.habilidade)}</span><i style="width:${(100 * h.vagas) / max}%"></i><b>${h.vagas}</b></div>`).join("");
  $("#vagas-simples").innerHTML = p.vagas.map((v) => `<li><b>${esc(v.titulo)}</b><span>${esc(v.empresa.nome)} · ${esc(v.empresa.bairro)} · ${TURNO[v.turno]}</span></li>`).join("");
}

/* ================= eventos ================= */
function ligarEventos() {
  $("#hab-entrada").addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === ",") { e.preventDefault(); adicionarHabilidade(e.target.value); e.target.value = ""; }
    if (e.key === "Backspace" && !e.target.value && estado.habilidades.length) { estado.habilidades.pop(); renderChips(); atualizarTudo(); }
  });
  $("#hab-entrada").addEventListener("change", (e) => { if (estado.ref.habilidades.includes(e.target.value)) { adicionarHabilidade(e.target.value); e.target.value = ""; } });
  $("#hab-escolhidas").addEventListener("click", () => $("#hab-entrada").focus());
  $("#hab-sugestoes").addEventListener("click", (e) => { const b = e.target.closest("button"); if (b) adicionarHabilidade(b.dataset.h); });
  ["#f-turno", "#f-modulo", "#f-media", "#f-destaques"].forEach((s) => $(s).addEventListener("change", buscarTalentos));
  $("#ranking").addEventListener("click", (e) => {
    const f = e.target.closest(".falar-escola"); if (f) return abrirContatoEscola(f.dataset.escola);
    const b = e.target.closest(".linha-bairro"); if (b) selecionarBairro(b.dataset.bairro);
  });
  $("#limpar-local").addEventListener("click", () => selecionarBairro(estado.bairro));
  document.addEventListener("click", (e) => { const a = e.target.closest("[data-aluno]"); if (a) abrirPerfil(a.dataset.aluno); });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") fecharGaveta();
    if (e.key === "Enter" && e.target.matches(".candidato")) abrirPerfil(e.target.dataset.aluno);
  });
  $("#veu").addEventListener("click", fecharGaveta);
  $("#fechar-gaveta").addEventListener("click", fecharGaveta);

  $("#lista-vagas").addEventListener("click", (e) => { const b = e.target.closest("button"); if (b) carregarRecomendados(b.dataset.vaga); });
  $("#abrir-nova-vaga").addEventListener("click", () => { $("#form-vaga").hidden = false; $("#form-vaga").titulo.focus(); });
  $("#cancelar-vaga").addEventListener("click", () => ($("#form-vaga").hidden = true));
  $("#form-vaga").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const f = ev.target;
    try {
      const v = await api("/api/vagas", { method: "POST", body: {
        empresa_id: empresaAtual(), titulo: f.titulo.value, modalidade: f.modalidade.value, turno: f.turno.value,
        obrigatorias: lista(f.obrigatorias.value), desejaveis: lista(f.desejaveis.value), descricao: f.descricao.value } });
      f.reset(); f.hidden = true; estado.vagaAtual = v.id;
      await carregarVagas();
      avisar("Vaga publicada. Veja quem combina com ela.");
    } catch (e) { avisar(e.message, true); }
  });

  $("#escola-atual").addEventListener("change", carregarEscola);
  $("#sub-escola").addEventListener("click", (e) => { const b = e.target.closest("button"); if (b) { estado.sub = b.dataset.sub; carregarEscola(); } });
  $("#filtro-status").addEventListener("click", (e) => {
    const b = e.target.closest("button"); if (!b) return;
    estado.status = b.dataset.status;
    $$("#filtro-status button").forEach((x) => x.classList.toggle("ativa", x === b));
    carregarPedidos();
  });
  $("#pedidos").addEventListener("click", async (e) => {
    const b = e.target.closest("[data-decidir]"); if (!b) return;
    const resposta = $(`[data-resposta="${b.dataset.decidir}"]`)?.value || "";
    try {
      await api(`/api/pedidos/${b.dataset.decidir}/resposta`, { method: "POST", body: { aprovar: b.dataset.aprovar === "1", resposta } });
      avisar(b.dataset.aprovar === "1" ? "Aprovado. Agora a escola conversa com o aluno e a família." : "Pedido recusado.");
      carregarPedidos();
    } catch (err) { avisar(err.message, true); }
  });
  $("#form-aluno").addEventListener("submit", cadastrarAluno);
}

/* ================= início ================= */
async function iniciar() {
  estado.ref = await api("/api/referencias");
  $("#persona-empresa").innerHTML = estado.ref.empresas.map((e) => `<option value="${esc(e.id)}">${esc(e.nome)}</option>`).join("");
  $("#escola-atual").innerHTML = estado.ref.escolas.map((e) => `<option value="${esc(e.id)}">${esc(e.nome)} · ${esc(e.bairro)}</option>`).join("");
  $("#hab-lista").innerHTML = estado.ref.habilidades.map((h) => `<option value="${esc(h)}">`).join("");
  $("#atitudes-form").innerHTML = Object.entries(ATITUDES).map(([k, r]) =>
    `<label>${r}<select name="${k}">${[5, 4, 3, 2, 1].map((n) => `<option value="${n}" ${n === 4 ? "selected" : ""}>${n}</option>`).join("")}</select></label>`).join("");
  $("#persona-empresa").addEventListener("change", () => { if (location.hash === "#vagas") carregarVagas(); });
  ligarEventos();
  await iniciarMapa();
  await atualizarTudo();
  irPara();
}

iniciar().catch((e) => avisar(e.message, true));
