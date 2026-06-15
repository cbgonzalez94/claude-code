"""Ponderación de los análisis y cálculo del riesgo de confundibilidad.

Reúne los tres ejes del cotejo marcario (Proceso 145-IP-2022) en un único
'Puntaje de Similitud General' y lo traduce a un semáforo de riesgo.

Para signos DENOMINATIVOS, la jurisprudencia andina prioriza el plano
fonético y el ortográfico sobre el conceptual; de ahí los pesos por defecto.
"""

from __future__ import annotations

from dataclasses import dataclass

from .orthographic import ratio_levenshtein, similitud_ortografica
from .phonetics import clave_metaphone_es, clave_soundex_es
from .syllables import indice_silaba_tonica, silaba_tonica
from .conceptual import similitud_conceptual


@dataclass(frozen=True)
class Pesos:
    fonetico: float = 0.40
    ortografico: float = 0.35
    conceptual: float = 0.25


def similitud_fonetica(palabra_a: str, palabra_b: str) -> dict:
    """Puntaje 0-100 de semejanza de sonido.

    Combina la distancia entre claves metaphone, la coincidencia de soundex
    y un bonus determinante si la SÍLABA TÓNICA coincide (criterio explícito
    de la jurisprudencia: tónica idéntica => semejanza evidente).
    """
    meta_a = clave_metaphone_es(palabra_a)
    meta_b = clave_metaphone_es(palabra_b)
    sx_a = clave_soundex_es(palabra_a)
    sx_b = clave_soundex_es(palabra_b)

    base = ratio_levenshtein(meta_a, meta_b)
    bonus_soundex = 0.10 if sx_a and sx_a == sx_b else 0.0

    ton_a = silaba_tonica(palabra_a)
    ton_b = silaba_tonica(palabra_b)
    tonica_igual = bool(ton_a) and (
        clave_metaphone_es(ton_a) == clave_metaphone_es(ton_b)
    )
    bonus_tonica = 0.12 if tonica_igual else 0.0

    # Misma posición de tónica también acerca el ritmo del signo.
    misma_posicion = indice_silaba_tonica(palabra_a) == indice_silaba_tonica(palabra_b)
    bonus_posicion = 0.03 if misma_posicion else 0.0

    puntaje = min(1.0, base + bonus_soundex + bonus_tonica + bonus_posicion)
    return {
        "puntaje": round(puntaje * 100, 1),
        "factores": {
            "metaphone_a": meta_a,
            "metaphone_b": meta_b,
            "soundex_a": sx_a,
            "soundex_b": sx_b,
            "tonica_a": ton_a,
            "tonica_b": ton_b,
            "tonica_coincide": tonica_igual,
        },
        "explicacion": _explicacion_fonetica(puntaje, tonica_igual, sx_a == sx_b),
    }


def _explicacion_fonetica(p: float, tonica: bool, soundex_igual: bool) -> str:
    if p >= 0.85:
        base = "Sonido casi idéntico."
    elif p >= 0.6:
        base = "Sonido marcadamente parecido."
    elif p >= 0.4:
        base = "Cierta semejanza de sonido."
    else:
        base = "Sonido diferente."
    if tonica:
        base += " Sílaba tónica coincidente."
    elif soundex_igual:
        base += " Misma estructura consonántica."
    return base


def nivel_riesgo(puntaje: float) -> dict:
    """Semáforo de riesgo a partir del puntaje general (0-100)."""
    if puntaje >= 70:
        return {"nivel": "alto", "color": "rojo",
                "mensaje": "Alto riesgo de confundibilidad. Registro poco viable."}
    if puntaje >= 45:
        return {"nivel": "medio", "color": "amarillo",
                "mensaje": "Riesgo medio. Conviene un análisis legal detallado."}
    return {"nivel": "bajo", "color": "verde",
            "mensaje": "Bajo riesgo. Registro probablemente viable."}


def comparar(palabra_a: str, palabra_b: str, pesos: Pesos = Pesos()) -> dict:
    """Compara dos signos y devuelve el dictamen completo."""
    orto = similitud_ortografica(palabra_a, palabra_b)
    fon = similitud_fonetica(palabra_a, palabra_b)
    con = similitud_conceptual(palabra_a, palabra_b)

    general = (
        fon["puntaje"] * pesos.fonetico
        + orto["puntaje"] * pesos.ortografico
        + con["puntaje"] * pesos.conceptual
    )
    general = round(general, 1)

    return {
        "marca_a": palabra_a,
        "marca_b": palabra_b,
        "puntaje_general": general,
        "riesgo": nivel_riesgo(general),
        "ortografica": orto,
        "fonetica": fon,
        "conceptual": con,
        "pesos": {"fonetico": pesos.fonetico, "ortografico": pesos.ortografico,
                  "conceptual": pesos.conceptual},
    }


if __name__ == "__main__":
    import json
    print(json.dumps(comparar("Synergy", "Sinergia"), ensure_ascii=False, indent=2))
