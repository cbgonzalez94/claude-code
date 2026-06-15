"""Silabación y detección de sílaba tónica en español.

Implementación pragmática de las reglas ortográficas del español (RAE),
suficiente para el análisis fonético exigido por la jurisprudencia andina
(Proceso 145-IP-2022): identificar la sílaba tónica y comparar la estructura
silábica de dos signos denominativos.

No requiere dependencias externas.
"""

from __future__ import annotations

import unicodedata

VOCALES_FUERTES = set("aeoáéó")
VOCALES_DEBILES = set("iuü")
VOCALES_DEBILES_ACENTUADAS = set("íú")
VOCALES = VOCALES_FUERTES | VOCALES_DEBILES | VOCALES_DEBILES_ACENTUADAS
VOCALES_ACENTUADAS = set("áéíóú")

# Grupos consonánticos inseparables (la consonante arranca la sílaba siguiente).
GRUPOS_INSEPARABLES = {
    "pr", "br", "tr", "dr", "cr", "gr", "fr",
    "pl", "bl", "cl", "gl", "fl",
    "ll", "rr", "ch",
}


def quitar_tildes(texto: str) -> str:
    """Elimina diacríticos conservando la 'ñ' y la 'ü' como letras base."""
    texto = texto.replace("ñ", "\x00").replace("Ñ", "\x00")
    descompuesto = unicodedata.normalize("NFD", texto)
    sin_marcas = "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")
    return unicodedata.normalize("NFC", sin_marcas).replace("\x00", "ñ")


def _es_vocal(c: str) -> bool:
    return c in VOCALES


def _es_diptongo(v1: str, v2: str) -> bool:
    """Dos vocales forman diptongo (misma sílaba) salvo hiato.

    Hay hiato cuando ambas son fuertes, o cuando una débil va acentuada.
    """
    if v1 in VOCALES_DEBILES_ACENTUADAS or v2 in VOCALES_DEBILES_ACENTUADAS:
        return False
    base1 = quitar_tildes(v1)
    base2 = quitar_tildes(v2)
    if base1 in "aeo" and base2 in "aeo":
        return False  # dos vocales fuertes -> hiato
    return True


def silabar(palabra: str) -> list[str]:
    """Divide una palabra en sílabas.

    >>> silabar("synergia")
    ['sy', 'ner', 'gia']  # aproximado; sirve para análisis comparativo
    """
    palabra = palabra.strip().lower()
    if not palabra:
        return []

    # 1) Tokenizar en núcleos vocálicos agrupando diptongos/triptongos.
    n = len(palabra)
    nucleos: list[tuple[int, int]] = []  # (inicio, fin) de cada núcleo vocálico
    i = 0
    while i < n:
        if _es_vocal(palabra[i]):
            ini = i
            i += 1
            while i < n and _es_vocal(palabra[i]) and _es_diptongo(palabra[i - 1], palabra[i]):
                i += 1
            nucleos.append((ini, i))
        else:
            i += 1

    if not nucleos:
        return [palabra]

    # 2) Repartir las consonantes entre núcleos según reglas de ataque/coda.
    silabas: list[str] = []
    inicio_silaba = 0
    for idx, (n_ini, n_fin) in enumerate(nucleos):
        if idx == len(nucleos) - 1:
            silabas.append(palabra[inicio_silaba:])
            break

        sig_ini = nucleos[idx + 1][0]
        consonantes = palabra[n_fin:sig_ini]
        c = len(consonantes)

        if c == 0:
            corte = n_fin
        elif c == 1:
            corte = n_fin  # la consonante ataca la sílaba siguiente
        else:
            par = consonantes[:2].lower()
            if c == 2:
                corte = n_fin if par in GRUPOS_INSEPARABLES else n_fin + 1
            else:
                # 3+ consonantes: las dos últimas pueden ser grupo inseparable.
                ult_par = consonantes[-2:].lower()
                if ult_par in GRUPOS_INSEPARABLES:
                    corte = sig_ini - 2
                else:
                    corte = sig_ini - 1

        silabas.append(palabra[inicio_silaba:corte])
        inicio_silaba = corte

    return [s for s in silabas if s]


def indice_silaba_tonica(palabra: str) -> int:
    """Devuelve el índice (0-based) de la sílaba tónica.

    Reglas:
      1. Si alguna sílaba lleva tilde, esa es la tónica.
      2. Palabra terminada en vocal, 'n' o 's' -> grave (penúltima).
      3. En otro caso -> aguda (última).
    """
    silabas = silabar(palabra)
    if not silabas:
        return -1

    for idx, sil in enumerate(silabas):
        if any(c in VOCALES_ACENTUADAS for c in sil):
            return idx

    base = quitar_tildes(palabra.lower().strip())
    if not base:
        return len(silabas) - 1
    ultima = base[-1]
    if ultima in "nsaeiou":
        return max(0, len(silabas) - 2)
    return len(silabas) - 1


def silaba_tonica(palabra: str) -> str:
    silabas = silabar(palabra)
    idx = indice_silaba_tonica(palabra)
    if 0 <= idx < len(silabas):
        return silabas[idx]
    return ""


if __name__ == "__main__":
    for p in ["synergy", "sinergia", "corona", "selene", "acuafresh", "lápiz", "camión"]:
        print(f"{p:12} -> {silabar(p)}  tónica={silaba_tonica(p)!r}")
