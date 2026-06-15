# LUMIRIA

**Búsqueda de anterioridades marcarias para Ecuador** con análisis de
confundibilidad en tres ejes —ortográfico, fonético y conceptual— según los
criterios del Tribunal de Justicia de la Comunidad Andina
(**Proceso 145-IP-2022**).

No es una simple coincidencia de texto: mide el **grado** de semejanza y lo
traduce en un **puntaje general** y un **semáforo de riesgo** (🔴/🟡/🟢) con el
desglose de *por qué* dos marcas se parecen.

---

## Arranque rápido (sin instalar nada)

El motor y la API de demo están escritos en **Python puro de la stdlib**:

```bash
cd backend
python3 api.py
# Abre http://localhost:8000  (frontend + API)
```

Probar la API directamente:

```bash
curl "http://localhost:8000/api/buscar?q=Synergy"
curl "http://localhost:8000/api/comparar?a=Rey&b=Corona"
```

## Ejecutar las pruebas

```bash
cd backend
python3 tests/test_engine.py        # mini-runner, sin dependencias
# o, si tienes pytest:  python3 -m pytest
```

## Ejemplos de código (entregable)

```bash
cd backend
python3 examples/ejemplos_codigo.py
```

## Versión de producción (FastAPI + spaCy)

```bash
cd backend
pip install -r requirements.txt
python -m spacy download es_core_news_md      # mejora el eje conceptual
uvicorn app_fastapi:app --reload              # Swagger en /docs
```

El eje conceptual **degrada con elegancia**: usa embeddings de spaCy si están
instalados; si no, un lexicón curado de campos semánticos (determinista y
auditable). Todo lo demás funciona sin dependencias.

---

## Estructura

```
LUMIRIA/
├── README.md
├── docs/
│   ├── 01-plan-de-proyecto.md
│   ├── 02-arquitectura.md
│   ├── 03-esquema-base-de-datos.sql
│   ├── 04-mockups.md
│   └── 05-criterios-juridicos.md      ← cómo el 145-IP-2022 se vuelve algoritmo
├── backend/
│   ├── api.py                         ← servidor demo (stdlib)
│   ├── app_fastapi.py                 ← API de producción
│   ├── requirements.txt
│   ├── lumiria/                       ← motor de similitud (núcleo)
│   │   ├── syllables.py               ← silabación + sílaba tónica (ES)
│   │   ├── phonetics.py               ← metaphone/soundex hispanos
│   │   ├── orthographic.py            ← Levenshtein, trigramas, raíz común
│   │   ├── conceptual.py              ← lexicón / embeddings
│   │   ├── scoring.py                 ← ponderación + semáforo de riesgo
│   │   └── engine.py                  ← búsqueda sobre la base de marcas
│   ├── data/marcas_senadi_demo.json   ← dataset simulado SENADI
│   ├── examples/ejemplos_codigo.py    ← funciones de ejemplo (entregable)
│   └── tests/test_engine.py
└── frontend/                          ← UI (HTML/CSS/JS, sin build)
    ├── index.html
    ├── styles.css
    └── app.js
```

## Cómo funciona (resumen)

| Eje | Qué mide | Técnica |
|---|---|---|
| **Ortográfico** | Escritura: secuencia de letras, vocales, raíz, longitud | Levenshtein + trigramas + serie vocálica + lexema común |
| **Fonético** | Cómo suena (b/v, s/c/z, y/ll, g/j, h muda…) y **sílaba tónica** | Metaphone/Soundex adaptados al español |
| **Conceptual** | Si evocan la misma idea (Rey↔Corona, Luna↔Selene) | Embeddings ES / lexicón de campos semánticos |

Puntaje general por defecto (signos denominativos):
`0.40·fonético + 0.35·ortográfico + 0.25·conceptual` (pesos configurables).

> **Aviso**: herramienta orientativa. No sustituye el dictamen del examinador
> del SENADI ni la asesoría legal profesional.
