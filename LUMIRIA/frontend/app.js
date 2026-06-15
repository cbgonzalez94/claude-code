// LUMIRIA · lógica del frontend (sin frameworks ni build).
const API = ""; // mismo origen que sirve api.py

const form = document.getElementById("form-busqueda");
const inputQ = document.getElementById("q");
const selClase = document.getElementById("clase");
const $res = document.getElementById("resultados");
const $lista = document.getElementById("lista");
const $vacio = document.getElementById("vacio");
const $marcaBuscada = document.getElementById("marca-buscada");
const $resumen = document.getElementById("resumen-total");

// Clases de Niza usadas en el dataset demo (en producción: catálogo completo 1-45).
const CLASES = [3, 9, 11, 12, 16, 18, 24, 25, 28, 29, 30, 31, 32, 33, 35, 39, 41, 43, 44, 45];
for (const c of CLASES) {
  const o = document.createElement("option");
  o.value = c; o.textContent = `Clase ${c}`;
  selClase.appendChild(o);
}

document.querySelectorAll(".ejemplos a").forEach((a) =>
  a.addEventListener("click", () => { inputQ.value = a.dataset.q; form.requestSubmit(); })
);

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const q = inputQ.value.trim();
  if (!q) return;
  await buscar(q, selClase.value);
});

async function buscar(q, clase) {
  $marcaBuscada.textContent = q;
  $res.classList.remove("oculto");
  $lista.innerHTML = `<p class="vacio">Analizando…</p>`;
  $vacio.classList.add("oculto");

  const url = `${API}/api/buscar?q=${encodeURIComponent(q)}&umbral=40` +
    (clase && clase !== "todas" ? `&clase=${clase}` : "");
  let data;
  try {
    data = await (await fetch(url)).json();
  } catch (err) {
    $lista.innerHTML = `<p class="vacio">No se pudo conectar con el servidor.</p>`;
    return;
  }

  $resumen.textContent = `${data.total} coincidencia(s) sobre el umbral`;
  $lista.innerHTML = "";
  if (!data.resultados || data.resultados.length === 0) {
    $vacio.classList.remove("oculto");
    return;
  }
  data.resultados.forEach((r) => $lista.appendChild(tarjeta(q, r)));
}

function tarjeta(consulta, r) {
  const nivel = r.riesgo.nivel; // alto | medio | bajo
  const el = document.createElement("article");
  el.className = `tarjeta ${nivel}`;

  const m = r.marca;
  el.innerHTML = `
    <div class="fila-top">
      <div>
        <div class="nombre-marca">${resaltarComunes(m.denominacion, consulta)}</div>
        <div class="meta-marca">Clase ${m.clase_niza ?? "—"} · ${m.titular ?? ""} · ${estado(m.estado)}</div>
      </div>
      <div style="text-align:right">
        <div class="badge ${nivel}">Riesgo ${nivel} · ${r.puntaje_general}%</div>
      </div>
    </div>
    <div class="barras">
      ${barra("Ortográfica", r.ortografica.puntaje)}
      ${barra("Fonética", r.fonetica.puntaje)}
      ${barra("Conceptual", r.conceptual.puntaje)}
    </div>
    <div class="explica">
      <div><b>Ortográfica:</b> ${detalleOrto(consulta, m.denominacion, r.ortografica)}</div>
      <div><b>Fonética:</b> ${r.fonetica.explicacion}
        <span style="opacity:.7">(${r.fonetica.factores.metaphone_a} ≈ ${r.fonetica.factores.metaphone_b})</span></div>
      <div><b>Conceptual:</b> ${r.conceptual.explicacion}</div>
      <span class="motivo">${motivo(r.motivo_inclusion)}</span>
    </div>`;
  return el;
}

function barra(etq, val) {
  const nivel = val >= 70 ? "alto" : val >= 45 ? "medio" : "bajo";
  return `<div class="barra-fila">
    <span class="barra-etq">${etq}</span>
    <span class="barra-track"><span class="barra-fill ${nivel}" style="width:${val}%"></span></span>
    <span class="barra-val">${val}%</span>
  </div>`;
}

function detalleOrto(a, b, orto) {
  const d = orto.detalle || {};
  const partes = [];
  if (d.distancia_edicion != null) partes.push(`${d.distancia_edicion} edición(es) de diferencia`);
  if (d.serie_vocalica_a && d.serie_vocalica_b)
    partes.push(`vocales «${d.serie_vocalica_a}» vs «${d.serie_vocalica_b}»`);
  return `${orto.puntaje}% — ${partes.join("; ")}.`;
}

// Resalta en `texto` las letras que comparte con `ref` (visualización simple).
function resaltarComunes(texto, ref) {
  const set = new Set(ref.toLowerCase().replace(/[^a-záéíóúñ]/gi, ""));
  return [...texto].map((ch) =>
    set.has(ch.toLowerCase()) ? `<span class="resaltado">${ch}</span>` : ch
  ).join("");
}

function estado(e) {
  return ({ registrada: "Registrada", en_tramite: "En trámite", rechazada: "Rechazada" }[e]) || e || "";
}
function motivo(m) {
  if (!m) return "";
  if (m === "riesgo_general") return "Incluida por riesgo general.";
  return "Incluida por similitud " + m.replace("eje:", "").replace(/,/g, " y ") + ".";
}
