"""Análisis de similitud conceptual o ideológica.

Detecta marcas que evocan la misma idea aunque no se parezcan ni ortográfica
ni fonéticamente (REY ↔ CORONA, LUNA ↔ SELENE).

Estrategia por capas (degrada con elegancia):

  1. Si está disponible spaCy con un modelo español que tenga vectores
     (es_core_news_md / _lg), se usa la similitud coseno de los embeddings.
  2. Si no, se usa un GRAFO DE CONCEPTOS curado offline (incluido aquí) que
     agrupa lemas por campo semántico. Es determinista, auditable y no
     requiere descargar modelos — ideal para este entorno y para explicar
     un dictamen ante el examinador del SENADI.

Para producción se recomienda (1) con embeddings o una API de tesauro ES.
"""

from __future__ import annotations

import unicodedata

# --------------------------------------------------------------------------- #
# Grafo de conceptos curado (campos semánticos del español).
# Cada conjunto agrupa términos que comparten idea/evocación.
# --------------------------------------------------------------------------- #
CAMPOS_SEMANTICOS: list[set[str]] = [
    {"rey", "reina", "corona", "monarca", "trono", "imperio", "real", "realeza", "principe"},
    {"luna", "selene", "lunar", "satelite", "creciente", "claro de luna"},
    {"sol", "solar", "astro", "rayo", "helios", "amanecer", "aurora"},
    {"agua", "acua", "aqua", "hidro", "rio", "mar", "oceano", "ola", "gota", "fuente"},
    {"fuego", "llama", "fuga", "ardor", "brasa", "fenix", "incendio", "ignis"},
    {"tierra", "terra", "campo", "suelo", "monte", "montana", "roca", "piedra"},
    {"aire", "viento", "brisa", "cielo", "nube", "tormenta", "huracan"},
    {"leon", "tigre", "felino", "fiera", "pantera", "jaguar", "puma"},
    {"aguila", "halcon", "ave", "pajaro", "condor", "vuelo", "ala", "pluma"},
    {"oro", "dorado", "aurum", "tesoro", "lingote", "joya", "diamante", "gema"},
    {"fuerza", "poder", "potencia", "vigor", "energia", "titan", "hercules"},
    {"rapido", "veloz", "flecha", "rayo", "turbo", "express", "vento", "sprint"},
    {"salud", "vida", "vital", "bienestar", "sano", "cura", "medic", "farma"},
    {"belleza", "bella", "linda", "hermosa", "glamour", "estilo", "chic"},
    {"casa", "hogar", "techo", "morada", "nido", "refugio", "domus"},
    {"estrella", "star", "astral", "estelar", "lucero", "constelacion"},
    {"verde", "eco", "natura", "natural", "bio", "organico", "planta", "hoja", "flor"},
    {"nieve", "hielo", "frio", "polar", "artico", "glaciar", "blanco", "nevado"},
    {"dulce", "miel", "azucar", "caramelo", "endulza", "sweet"},
    {"cafe", "grano", "aroma", "tueste", "barista", "espresso"},
]

# Sinónimos directos (peso máximo de confusión conceptual).
SINONIMOS: list[set[str]] = [
    {"rey", "monarca"},
    {"luna", "selene"},
    {"sol", "helios"},
    {"agua", "acua", "aqua"},
    {"rapido", "veloz"},
    {"fuerza", "potencia", "poder"},
    {"bella", "linda", "hermosa"},
]


def _norm(p: str) -> str:
    p = unicodedata.normalize("NFD", p.lower().strip())
    p = "".join(c for c in p if unicodedata.category(c) != "Mn")
    return "".join(c for c in p if c.isalpha())


def _contiene_lema(palabra: str, lema: str) -> bool:
    """Coincidencia por inclusión de raíz (acuafresh contiene 'acua')."""
    return lema in palabra or palabra in lema


def _conceptos_de(palabra: str) -> tuple[set[int], set[int]]:
    """Devuelve (índices de campos, índices de grupos de sinónimos) que tocan."""
    p = _norm(palabra)
    campos = {i for i, grupo in enumerate(CAMPOS_SEMANTICOS)
              if any(_contiene_lema(p, _norm(t)) for t in grupo)}
    sinon = {i for i, grupo in enumerate(SINONIMOS)
             if any(_contiene_lema(p, _norm(t)) for t in grupo)}
    return campos, sinon


def _similitud_spacy(a: str, b: str):
    """Intenta usar spaCy. Devuelve float o None si no está disponible."""
    try:
        import spacy
    except Exception:
        return None
    for modelo in ("es_core_news_lg", "es_core_news_md"):
        try:
            nlp = _cargar_modelo(modelo)
        except Exception:
            continue
        da, db = nlp(a), nlp(b)
        if da.vector_norm and db.vector_norm:
            return max(0.0, float(da.similarity(db)))
    return None


_MODELOS: dict = {}


def _cargar_modelo(nombre: str):
    import spacy
    if nombre not in _MODELOS:
        _MODELOS[nombre] = spacy.load(nombre)
    return _MODELOS[nombre]


def similitud_conceptual(palabra_a: str, palabra_b: str) -> dict:
    """Puntaje 0-100 de cercanía de ideas, con explicación."""
    if _norm(palabra_a) == _norm(palabra_b):
        return {"puntaje": 100.0, "metodo": "identico", "explicacion": "Mismo término."}

    via_spacy = _similitud_spacy(palabra_a, palabra_b)
    if via_spacy is not None:
        return {
            "puntaje": round(via_spacy * 100, 1),
            "metodo": "embeddings_spacy",
            "explicacion": "Cercanía semántica por vectores de palabras.",
        }

    campos_a, sin_a = _conceptos_de(palabra_a)
    campos_b, sin_b = _conceptos_de(palabra_b)

    if sin_a & sin_b:
        return {"puntaje": 90.0, "metodo": "lexicon",
                "explicacion": "Términos sinónimos: evocan la misma idea."}
    if campos_a & campos_b:
        compartidos = sorted({t for i in (campos_a & campos_b) for t in list(CAMPOS_SEMANTICOS[i])[:1]})
        return {"puntaje": 65.0, "metodo": "lexicon",
                "explicacion": f"Mismo campo semántico ({', '.join(compartidos)}…)."}
    if campos_a or campos_b:
        return {"puntaje": 15.0, "metodo": "lexicon",
                "explicacion": "Baja conexión de ideas."}
    return {"puntaje": 5.0, "metodo": "lexicon",
            "explicacion": "Sin relación conceptual detectable."}


if __name__ == "__main__":
    import json
    for a, b in [("rey", "corona"), ("luna", "selene"), ("agua", "fuego"), ("sol", "estrella")]:
        print(a, b, json.dumps(similitud_conceptual(a, b), ensure_ascii=False))
