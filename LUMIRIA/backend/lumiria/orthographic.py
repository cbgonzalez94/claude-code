"""Análisis de similitud ortográfica (morfosintáctica).

Mide el GRADO de semejanza en la escritura de dos signos (no es binario),
combinando los factores que la jurisprudencia andina valora:

  * Composición y secuencia de letras  -> distancia de Levenshtein
  * Coincidencia de trigramas          -> índice de Jaccard (estilo pg_trgm)
  * Vocales y estructura silábica       -> Levenshtein sobre la serie vocálica
  * Raíces o lexemas comunes           -> prefijo/sufijo común (Acuafresh/Acuadent)
  * Longitud y nº de palabras          -> penalización por diferencia de tamaño

Sin dependencias externas.
"""

from __future__ import annotations

from .phonetics import normalizar
from .syllables import silabar

VOCALES = set("aeiou")


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    anterior = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        actual = [i]
        for j, cb in enumerate(b, 1):
            costo = 0 if ca == cb else 1
            actual.append(min(
                anterior[j] + 1,        # borrado
                actual[j - 1] + 1,      # inserción
                anterior[j - 1] + costo,  # sustitución
            ))
        anterior = actual
    return anterior[-1]


def ratio_levenshtein(a: str, b: str) -> float:
    if not a and not b:
        return 1.0
    dist = levenshtein(a, b)
    return 1.0 - dist / max(len(a), len(b))


def trigramas(s: str) -> set[str]:
    s = f"  {s} "
    return {s[i:i + 3] for i in range(len(s) - 2)}


def jaccard_trigramas(a: str, b: str) -> float:
    ta, tb = trigramas(a), trigramas(b)
    if not ta and not tb:
        return 1.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return inter / union if union else 0.0


def serie_vocalica(s: str) -> str:
    return "".join(c for c in s if c in VOCALES)


def similitud_vocalica(a: str, b: str) -> float:
    return ratio_levenshtein(serie_vocalica(a), serie_vocalica(b))


def raiz_comun(a: str, b: str) -> float:
    """Puntúa el lexema/raíz compartido (prefijo y sufijo comunes).

    Captura casos como 'Acuafresh' vs 'Acuadent' (raíz 'acua') o
    'Solar' vs 'Soles' (raíz 'sol').
    """
    pref = 0
    for ca, cb in zip(a, b):
        if ca == cb:
            pref += 1
        else:
            break
    suf = 0
    for ca, cb in zip(reversed(a), reversed(b)):
        if ca == cb:
            suf += 1
        else:
            break
    menor = min(len(a), len(b)) or 1
    # Una raíz compartida >= 3 letras es jurídicamente relevante.
    bruto = max(pref, suf)
    bonus = 1.0 if bruto >= 3 else bruto / 3.0
    return min(1.0, (max(pref, suf) / menor) * 0.7 + bonus * 0.3)


def factor_longitud(a: str, b: str) -> float:
    la, lb = len(a), len(b)
    if max(la, lb) == 0:
        return 1.0
    return 1.0 - abs(la - lb) / max(la, lb)


def letras_comunes(a: str, b: str) -> list[int]:
    """Índices de 'a' que coinciden con 'b' (para resaltar en la UI)."""
    b_chars = list(b)
    indices = []
    for i, ca in enumerate(a):
        if ca in b_chars:
            indices.append(i)
            b_chars.remove(ca)
    return indices


def similitud_ortografica(palabra_a: str, palabra_b: str) -> dict:
    """Devuelve un puntaje 0-100 y el desglose de factores."""
    a = normalizar(palabra_a)
    b = normalizar(palabra_b)

    lev = ratio_levenshtein(a, b)
    trg = jaccard_trigramas(a, b)
    voc = similitud_vocalica(a, b)
    raiz = raiz_comun(a, b)
    longitud = factor_longitud(a, b)

    # Ponderación de los factores ortográficos.
    puntaje = (
        lev * 0.40
        + trg * 0.20
        + voc * 0.15
        + raiz * 0.15
        + longitud * 0.10
    )

    sil_a, sil_b = silabar(palabra_a), silabar(palabra_b)
    return {
        "puntaje": round(puntaje * 100, 1),
        "factores": {
            "levenshtein": round(lev * 100, 1),
            "trigramas": round(trg * 100, 1),
            "vocales": round(voc * 100, 1),
            "raiz_comun": round(raiz * 100, 1),
            "longitud": round(longitud * 100, 1),
        },
        "detalle": {
            "distancia_edicion": levenshtein(a, b),
            "serie_vocalica_a": serie_vocalica(a),
            "serie_vocalica_b": serie_vocalica(b),
            "silabas_a": sil_a,
            "silabas_b": sil_b,
            "letras_comunes_idx": letras_comunes(a, b),
        },
    }


if __name__ == "__main__":
    import json
    print(json.dumps(similitud_ortografica("Solar", "Soles"), ensure_ascii=False, indent=2))
    print(json.dumps(similitud_ortografica("Acuafresh", "Acuadent"), ensure_ascii=False, indent=2))
