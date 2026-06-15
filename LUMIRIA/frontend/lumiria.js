/* LUMIRIA — motor de similitud en JavaScript (port fiel del paquete Python).
   Permite cotejar cualquier signo contra el listado SIN servidor, en el navegador.
   Expone window.LUMIRIA con comparar() y buscar(). */
(function (global) {
  "use strict";

  // ---------------------------------------------------------------- básicos
  function quitarTildes(texto) {
    texto = texto.replace(/ñ/g, "\uE000").replace(/Ñ/g, "\uE000");
    texto = texto.normalize("NFD").replace(/\p{Mn}/gu, "");
    return texto.replace(/\uE000/g, "ñ");
  }
  function normalizar(texto) {
    texto = quitarTildes((texto || "").toLowerCase().trim());
    return (texto.match(/[a-zñ]/g) || []).join("");
  }

  const VOC_ACENT = new Set("áéíóú");
  const VOCALES = new Set("aeiou");

  // ---------------------------------------------------------- silabación ES
  const VOCALES_DEBILES_ACENTUADAS = new Set("íú");
  function esVocalSil(c) {
    return "aeoáéóiuü".includes(c);
  }
  function esDiptongo(v1, v2) {
    if (VOCALES_DEBILES_ACENTUADAS.has(v1) || VOCALES_DEBILES_ACENTUADAS.has(v2)) return false;
    const b1 = quitarTildes(v1), b2 = quitarTildes(v2);
    if ("aeo".includes(b1) && "aeo".includes(b2)) return false;
    return true;
  }
  const GRUPOS = new Set(["pr","br","tr","dr","cr","gr","fr","pl","bl","cl","gl","fl","ll","rr","ch"]);

  function silabar(palabra) {
    palabra = (palabra || "").trim().toLowerCase();
    if (!palabra) return [];
    const n = palabra.length;
    const nucleos = [];
    let i = 0;
    while (i < n) {
      if (esVocalSil(palabra[i])) {
        const ini = i; i++;
        while (i < n && esVocalSil(palabra[i]) && esDiptongo(palabra[i - 1], palabra[i])) i++;
        nucleos.push([ini, i]);
      } else i++;
    }
    if (!nucleos.length) return [palabra];
    const silabas = [];
    let inicio = 0;
    for (let idx = 0; idx < nucleos.length; idx++) {
      const [, nFin] = nucleos[idx];
      if (idx === nucleos.length - 1) { silabas.push(palabra.slice(inicio)); break; }
      const sigIni = nucleos[idx + 1][0];
      const cons = palabra.slice(nFin, sigIni);
      const c = cons.length;
      let corte;
      if (c === 0) corte = nFin;
      else if (c === 1) corte = nFin;
      else {
        const par = cons.slice(0, 2).toLowerCase();
        if (c === 2) corte = GRUPOS.has(par) ? nFin : nFin + 1;
        else {
          const ultPar = cons.slice(-2).toLowerCase();
          corte = GRUPOS.has(ultPar) ? sigIni - 2 : sigIni - 1;
        }
      }
      silabas.push(palabra.slice(inicio, corte));
      inicio = corte;
    }
    return silabas.filter(Boolean);
  }

  function indiceSilabaTonica(palabra) {
    const silabas = silabar(palabra);
    if (!silabas.length) return -1;
    for (let idx = 0; idx < silabas.length; idx++)
      if ([...silabas[idx]].some((c) => VOC_ACENT.has(c))) return idx;
    const base = quitarTildes((palabra || "").toLowerCase().trim());
    if (!base) return silabas.length - 1;
    const ultima = base[base.length - 1];
    if ("nsaeiou".includes(ultima)) return Math.max(0, silabas.length - 2);
    return silabas.length - 1;
  }
  function silabaTonica(palabra) {
    const silabas = silabar(palabra);
    const idx = indiceSilabaTonica(palabra);
    return idx >= 0 && idx < silabas.length ? silabas[idx] : "";
  }

  // -------------------------------------------------------------- fonética
  function claveMetaphoneEs(palabra) {
    const s = normalizar(palabra);
    if (!s) return "";
    const out = [];
    let i = 0; const n = s.length;
    while (i < n) {
      const c = s[i], sig = i + 1 < n ? s[i + 1] : "";
      const par = c + sig;
      if (par === "ch") { out.push("X"); i += 2; continue; }
      if (par === "ll") { out.push("Y"); i += 2; continue; }
      if (par === "rr") { out.push("R"); i += 2; continue; }
      if (par === "qu") { out.push("K"); i += 2; continue; }
      if (par === "gu" && sig === "u" && i + 2 < n && "ei".includes(s[i + 2])) { out.push("G"); i += 2; continue; }
      if ("aeiou".includes(c)) out.push(c.toUpperCase());
      else if (c === "h") {}
      else if ("bv".includes(c)) out.push("B");
      else if (c === "w") out.push("B");
      else if (c === "c") out.push("ei".includes(sig) ? "S" : "K");
      else if ("sz".includes(c)) out.push("S");
      else if (c === "k") out.push("K");
      else if (c === "q") out.push("K");
      else if (c === "g") out.push("ei".includes(sig) ? "J" : "G");
      else if (c === "j") out.push("J");
      else if (c === "x") out.push("KS");
      else if (c === "y") out.push((sig === "" || !"aeiou".includes(sig)) ? "I" : "Y");
      else if (c === "ñ") out.push("N");
      else out.push(c.toUpperCase());
      i++;
    }
    const clave = [];
    for (const ch of out.join("")) {
      if (clave.length && clave[clave.length - 1] === ch && !"AEIOU".includes(ch)) continue;
      clave.push(ch);
    }
    return clave.join("");
  }

  const GRUPOS_SOUNDEX = {
    b:"1",v:"1",w:"1",p:"1",f:"1", c:"2",k:"2",q:"2",g:"2",j:"2",x:"2",
    s:"3",z:"3", d:"4",t:"4", l:"5", m:"6",n:"6","ñ":"6", r:"7", y:"8",
  };
  function claveSoundexEs(palabra) {
    const s = normalizar(palabra);
    if (!s) return "";
    const meta = claveMetaphoneEs(s);
    const inicial = meta ? meta[0] : s[0].toUpperCase();
    const codigos = [];
    let anterior = GRUPOS_SOUNDEX[s[0]] || "";
    for (const c of s.slice(1)) {
      if (c === "h") continue;
      const cod = GRUPOS_SOUNDEX[c] || "";
      if (cod === "") { anterior = ""; continue; }
      if (cod !== anterior) codigos.push(cod);
      anterior = cod;
    }
    return (inicial + codigos.join("") + "000").slice(0, 4);
  }

  // ----------------------------------------------------------- ortográfica
  function levenshtein(a, b) {
    if (a === b) return 0;
    if (!a) return b.length;
    if (!b) return a.length;
    let prev = Array.from({ length: b.length + 1 }, (_, i) => i);
    for (let i = 1; i <= a.length; i++) {
      const cur = [i];
      for (let j = 1; j <= b.length; j++) {
        const costo = a[i - 1] === b[j - 1] ? 0 : 1;
        cur.push(Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + costo));
      }
      prev = cur;
    }
    return prev[b.length];
  }
  function ratioLev(a, b) {
    if (!a && !b) return 1;
    return 1 - levenshtein(a, b) / Math.max(a.length, b.length);
  }
  function trigramas(s) {
    s = "  " + s + " ";
    const set = new Set();
    for (let i = 0; i < s.length - 2; i++) set.add(s.slice(i, i + 3));
    return set;
  }
  function jaccard(a, b) {
    const ta = trigramas(a), tb = trigramas(b);
    if (!ta.size && !tb.size) return 1;
    let inter = 0; ta.forEach((x) => { if (tb.has(x)) inter++; });
    const union = new Set([...ta, ...tb]).size;
    return union ? inter / union : 0;
  }
  function serieVocalica(s) { return [...s].filter((c) => VOCALES.has(c)).join(""); }
  function simVocalica(a, b) { return ratioLev(serieVocalica(a), serieVocalica(b)); }
  function raizComun(a, b) {
    let pref = 0;
    for (let i = 0; i < Math.min(a.length, b.length); i++) { if (a[i] === b[i]) pref++; else break; }
    let suf = 0;
    for (let i = 0; i < Math.min(a.length, b.length); i++) { if (a[a.length - 1 - i] === b[b.length - 1 - i]) suf++; else break; }
    const menor = Math.min(a.length, b.length) || 1;
    const bruto = Math.max(pref, suf);
    const bonus = bruto >= 3 ? 1 : bruto / 3;
    return Math.min(1, (Math.max(pref, suf) / menor) * 0.7 + bonus * 0.3);
  }
  function factorLongitud(a, b) {
    const la = a.length, lb = b.length;
    if (Math.max(la, lb) === 0) return 1;
    return 1 - Math.abs(la - lb) / Math.max(la, lb);
  }
  function r1(x) { return Math.round(x * 1000) / 10; }

  function similitudOrtografica(pa, pb) {
    const a = normalizar(pa), b = normalizar(pb);
    const lev = ratioLev(a, b), trg = jaccard(a, b), voc = simVocalica(a, b),
      raiz = raizComun(a, b), longitud = factorLongitud(a, b);
    const puntaje = lev * 0.4 + trg * 0.2 + voc * 0.15 + raiz * 0.15 + longitud * 0.1;
    return {
      puntaje: r1(puntaje),
      detalle: {
        distancia_edicion: levenshtein(a, b),
        serie_vocalica_a: serieVocalica(a),
        serie_vocalica_b: serieVocalica(b),
        silabas_a: silabar(pa), silabas_b: silabar(pb),
      },
    };
  }

  // -------------------------------------------------------------- fonética
  function explicacionFonetica(p, tonica, soundexIgual) {
    let base;
    if (p >= 0.85) base = "Sonido casi idéntico.";
    else if (p >= 0.6) base = "Sonido marcadamente parecido.";
    else if (p >= 0.4) base = "Cierta semejanza de sonido.";
    else base = "Sonido diferente.";
    if (tonica) base += " Sílaba tónica coincidente.";
    else if (soundexIgual) base += " Misma estructura consonántica.";
    return base;
  }
  function similitudFonetica(pa, pb) {
    const metaA = claveMetaphoneEs(pa), metaB = claveMetaphoneEs(pb);
    const sxA = claveSoundexEs(pa), sxB = claveSoundexEs(pb);
    const base = ratioLev(metaA, metaB);
    const bonusSoundex = sxA && sxA === sxB ? 0.1 : 0;
    const tonA = silabaTonica(pa), tonB = silabaTonica(pb);
    const tonicaIgual = !!tonA && claveMetaphoneEs(tonA) === claveMetaphoneEs(tonB);
    const bonusTonica = tonicaIgual ? 0.12 : 0;
    const bonusPos = indiceSilabaTonica(pa) === indiceSilabaTonica(pb) ? 0.03 : 0;
    const puntaje = Math.min(1, base + bonusSoundex + bonusTonica + bonusPos);
    return {
      puntaje: r1(puntaje),
      factores: { metaphone_a: metaA, metaphone_b: metaB, soundex_a: sxA, soundex_b: sxB,
        tonica_a: tonA, tonica_b: tonB, tonica_coincide: tonicaIgual },
      explicacion: explicacionFonetica(puntaje, tonicaIgual, sxA === sxB),
    };
  }

  // ------------------------------------------------------------ conceptual
  const CAMPOS = [
    ["rey","reina","corona","monarca","trono","imperio","real","realeza","principe"],
    ["luna","selene","lunar","satelite","creciente"],
    ["sol","solar","astro","rayo","helios","amanecer","aurora"],
    ["agua","acua","aqua","hidro","rio","mar","oceano","ola","gota","fuente"],
    ["fuego","llama","fuga","ardor","brasa","fenix","incendio","ignis"],
    ["tierra","terra","campo","suelo","monte","montana","roca","piedra"],
    ["aire","viento","brisa","cielo","nube","tormenta","huracan","vento"],
    ["leon","tigre","felino","fiera","pantera","jaguar","puma"],
    ["aguila","halcon","ave","pajaro","condor","vuelo","ala","pluma"],
    ["oro","dorado","aurum","tesoro","lingote","joya","diamante","gema"],
    ["fuerza","poder","potencia","vigor","energia","titan","hercules"],
    ["rapido","veloz","flecha","rayo","turbo","express","vento","sprint"],
    ["salud","vida","vital","bienestar","sano","cura","medic","farma"],
    ["belleza","bella","linda","hermosa","glamour","estilo","chic","vella"],
    ["casa","hogar","techo","morada","nido","refugio","domus"],
    ["estrella","star","astral","estelar","lucero","constelacion"],
    ["verde","eco","natura","natural","bio","organico","planta","hoja","flor"],
    ["nieve","hielo","frio","polar","artico","glaciar","blanco","nevado"],
    ["dulce","miel","azucar","caramelo","endulza","sweet"],
    ["cafe","grano","aroma","tueste","barista","espresso"],
  ];
  const SINONIMOS = [
    ["rey","monarca"],["luna","selene"],["sol","helios"],["agua","acua","aqua"],
    ["rapido","veloz"],["fuerza","potencia","poder"],["bella","linda","hermosa"],
  ];
  function contieneLema(palabra, lema) { return palabra.includes(lema) || lema.includes(palabra); }
  function conceptosDe(palabra) {
    const p = normalizar(palabra);
    const campos = new Set(), sinon = new Set();
    CAMPOS.forEach((g, i) => { if (g.some((t) => contieneLema(p, normalizar(t)))) campos.add(i); });
    SINONIMOS.forEach((g, i) => { if (g.some((t) => contieneLema(p, normalizar(t)))) sinon.add(i); });
    return [campos, sinon];
  }
  function inter(a, b) { for (const x of a) if (b.has(x)) return true; return false; }
  function similitudConceptual(pa, pb) {
    if (normalizar(pa) === normalizar(pb)) return { puntaje: 100, metodo: "identico", explicacion: "Mismo término." };
    const [ca, sa] = conceptosDe(pa), [cb, sb] = conceptosDe(pb);
    if (inter(sa, sb)) return { puntaje: 90, metodo: "lexicon", explicacion: "Términos sinónimos: evocan la misma idea." };
    if (inter(ca, cb)) {
      const i = [...ca].find((x) => cb.has(x));
      return { puntaje: 65, metodo: "lexicon", explicacion: "Mismo campo semántico (" + CAMPOS[i][0] + "…)." };
    }
    if (ca.size || cb.size) return { puntaje: 15, metodo: "lexicon", explicacion: "Baja conexión de ideas." };
    return { puntaje: 5, metodo: "lexicon", explicacion: "Sin relación conceptual detectable." };
  }

  // --------------------------------------------------------------- scoring
  const PESOS = { fonetico: 0.4, ortografico: 0.35, conceptual: 0.25 };
  function nivelRiesgo(p) {
    if (p >= 70) return { nivel: "alto", color: "rojo", mensaje: "Alto riesgo de confundibilidad. Registro poco viable." };
    if (p >= 45) return { nivel: "medio", color: "amarillo", mensaje: "Riesgo medio. Conviene un análisis legal detallado." };
    return { nivel: "bajo", color: "verde", mensaje: "Bajo riesgo. Registro probablemente viable." };
  }
  function comparar(pa, pb, pesos) {
    pesos = pesos || PESOS;
    const orto = similitudOrtografica(pa, pb), fon = similitudFonetica(pa, pb), con = similitudConceptual(pa, pb);
    const general = Math.round((fon.puntaje * pesos.fonetico + orto.puntaje * pesos.ortografico + con.puntaje * pesos.conceptual) * 10) / 10;
    return { marca_a: pa, marca_b: pb, puntaje_general: general, riesgo: nivelRiesgo(general),
      ortografica: orto, fonetica: fon, conceptual: con };
  }

  // ---------------------------------------------------------------- buscar
  function buscar(marcas, consulta, opts) {
    opts = opts || {};
    const umbral = opts.umbral != null ? opts.umbral : 40;
    const umbralEje = opts.umbralEje != null ? opts.umbralEje : 60;
    const claseNiza = opts.claseNiza != null ? opts.claseNiza : null;
    const limite = opts.limite != null ? opts.limite : 20;
    const resultados = [];
    for (const m of marcas) {
      if (claseNiza != null && m.clase_niza !== claseNiza) continue;
      const d = comparar(consulta, m.denominacion);
      const ejes = [];
      if (d.ortografica.puntaje >= umbralEje) ejes.push("ortográfico");
      if (d.fonetica.puntaje >= umbralEje) ejes.push("fonético");
      if (d.conceptual.puntaje >= umbralEje) ejes.push("conceptual");
      if (d.puntaje_general >= umbral || ejes.length) {
        resultados.push({
          motivo_inclusion: d.puntaje_general >= umbral ? "riesgo_general" : "eje:" + ejes.join(","),
          marca: { id: m.id, denominacion: m.denominacion, clase_niza: m.clase_niza, titular: m.titular,
            estado: m.estado, numero_registro: m.numero_registro },
          puntaje_general: d.puntaje_general, riesgo: d.riesgo,
          ortografica: { puntaje: d.ortografica.puntaje, detalle: d.ortografica.detalle },
          fonetica: { puntaje: d.fonetica.puntaje, explicacion: d.fonetica.explicacion, factores: d.fonetica.factores },
          conceptual: d.conceptual,
        });
      }
    }
    resultados.sort((a, b) => b.puntaje_general - a.puntaje_general);
    return { consulta, total: resultados.length, umbral, resultados: resultados.slice(0, limite) };
  }

  global.LUMIRIA = { comparar, buscar, nivelRiesgo, claveMetaphoneEs, claveSoundexEs, silabaTonica, similitudFonetica, similitudConceptual, similitudOrtografica };
})(typeof window !== "undefined" ? window : globalThis);
