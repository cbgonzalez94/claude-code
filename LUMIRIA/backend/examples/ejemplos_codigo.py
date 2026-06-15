"""Ejemplos de código solicitados (entregable 3).

Versiones AUTOCONTENIDAS y comentadas de las tres funciones pedidas:

  1. Similitud ortográfica entre dos palabras (Levenshtein + factores).
  2. Algoritmo fonético adaptado al español.
  3. Similitud conceptual con spaCy.

Las versiones de producción (más completas) viven en el paquete `lumiria`.
Aquí se priorizó la legibilidad para el entregable.

Ejecutar:  python3 ejemplos_codigo.py
"""

from __future__ import annotations

import unicodedata


# --------------------------------------------------------------------------- #
# 1) SIMILITUD ORTOGRÁFICA
# --------------------------------------------------------------------------- #
def distancia_levenshtein(a: str, b: str) -> int:
    """Número mínimo de ediciones (inserción/borrado/sustitución)."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    fila = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        prev, fila[0] = fila[0], i
        for j, cb in enumerate(b, 1):
            prev, fila[j] = fila[j], min(
                fila[j] + 1, fila[j - 1] + 1, prev + (ca != cb)
            )
    return fila[-1]


def similitud_ortografica(palabra_a: str, palabra_b: str) -> float:
    """Devuelve un puntaje 0-100 de semejanza en la escritura.

    Combina la distancia de Levenshtein (secuencia de letras) con la
    coincidencia de la serie de vocales, factor relevante en el cotejo
    marcario andino.
    """
    a = "".join(c for c in palabra_a.lower() if c.isalpha())
    b = "".join(c for c in palabra_b.lower() if c.isalpha())
    if not a or not b:
        return 0.0

    lev = 1 - distancia_levenshtein(a, b) / max(len(a), len(b))

    vocales = set("aeiouáéíóú")
    va = "".join(c for c in a if c in vocales)
    vb = "".join(c for c in b if c in vocales)
    sim_voc = 1 - distancia_levenshtein(va, vb) / max(len(va), len(vb), 1)

    return round((lev * 0.7 + sim_voc * 0.3) * 100, 1)


# --------------------------------------------------------------------------- #
# 2) ALGORITMO FONÉTICO ADAPTADO AL ESPAÑOL
# --------------------------------------------------------------------------- #
def clave_fonetica_es(palabra: str) -> str:
    """Transcribe una palabra a una clave fonética del español.

    Colapsa los grafemas que suenan igual: b/v, s/c(e,i)/z, y/ll, g(e,i)/j,
    'h' muda, qu/k/c(a,o,u), x/ks. Dos marcas con la misma clave 'suenan' igual.
    """
    s = unicodedata.normalize("NFD", palabra.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = "".join(c for c in s if c.isalpha())

    out, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        sig = s[i + 1] if i + 1 < n else ""
        par = c + sig
        if par == "ch":
            out.append("X"); i += 2; continue
        if par == "ll":
            out.append("Y"); i += 2; continue
        if par == "qu":
            out.append("K"); i += 2; continue
        if par == "rr":
            out.append("R"); i += 2; continue
        if c in "aeiou":
            out.append(c.upper())
        elif c == "h":
            pass
        elif c in "bvw":
            out.append("B")
        elif c == "c":
            out.append("S" if sig in "ei" else "K")
        elif c in "sz":
            out.append("S")
        elif c in "kq":
            out.append("K")
        elif c == "g":
            out.append("J" if sig in "ei" else "G")
        elif c == "j":
            out.append("J")
        elif c == "x":
            out.append("KS")
        elif c == "y":
            out.append("I" if sig == "" or sig not in "aeiou" else "Y")
        elif c == "ñ":
            out.append("N")
        else:
            out.append(c.upper())
        i += 1

    # Colapsa consonantes dobles.
    clave = []
    for ch in "".join(out):
        if clave and clave[-1] == ch and ch not in "AEIOU":
            continue
        clave.append(ch)
    return "".join(clave)


def suenan_igual(a: str, b: str) -> bool:
    return clave_fonetica_es(a) == clave_fonetica_es(b)


# --------------------------------------------------------------------------- #
# 3) SIMILITUD CONCEPTUAL CON spaCy (embeddings)
# --------------------------------------------------------------------------- #
def similitud_conceptual_spacy(palabra_a: str, palabra_b: str) -> float:
    """Similitud semántica 0-100 usando vectores de palabras de spaCy.

    Requiere un modelo con vectores:
        pip install spacy
        python -m spacy download es_core_news_md

    REY ↔ CORONA o LUNA ↔ SELENE deberían dar puntajes altos porque sus
    vectores están próximos en el espacio semántico.
    """
    import spacy  # import diferido: el ejemplo no rompe si spaCy no está

    nlp = spacy.load("es_core_news_md")  # _lg da mejores vectores
    doc_a, doc_b = nlp(palabra_a), nlp(palabra_b)
    if not doc_a.vector_norm or not doc_b.vector_norm:
        return 0.0
    return round(max(0.0, doc_a.similarity(doc_b)) * 100, 1)


if __name__ == "__main__":
    print("1) Ortográfica")
    for a, b in [("Solar", "Soles"), ("Acuafresh", "Acuadent"), ("Casa", "Perro")]:
        print(f"   {a:10} vs {b:10} -> {similitud_ortografica(a, b)}%")

    print("\n2) Fonética (clave ES)")
    for a, b in [("Synergy", "Sinergia"), ("baca", "vaca"), ("cebra", "zebra"),
                 ("calló", "cayó"), ("tubo", "tuvo")]:
        print(f"   {a:10} [{clave_fonetica_es(a):8}] vs {b:10} [{clave_fonetica_es(b):8}]"
              f"  ¿suenan igual? {suenan_igual(a, b)}")

    print("\n3) Conceptual (spaCy)")
    try:
        print(f"   rey vs corona -> {similitud_conceptual_spacy('rey', 'corona')}%")
    except Exception as e:
        print(f"   [spaCy no disponible en este entorno: {type(e).__name__}]")
        print("   Instala:  pip install spacy && python -m spacy download es_core_news_md")
