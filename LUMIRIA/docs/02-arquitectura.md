# Arquitectura del Sistema — LUMIRIA

## Diagrama (alto nivel)

```
                          ┌────────────────────────────────────────┐
                          │              NAVEGADOR                   │
                          │  Frontend (React / Vite · o vanilla)     │
                          │  · Buscador  · Página de resultados      │
                          │  · Semáforo de riesgo y desglose visual  │
                          └───────────────┬──────────────────────────┘
                                          │  HTTPS / JSON
                                          │  GET /api/buscar?q=...
                                          ▼
                          ┌────────────────────────────────────────┐
                          │            BACKEND · API                 │
                          │  FastAPI (prod) / http.server (demo)     │
                          │  · validación   · paginación   · caché   │
                          └───────────────┬──────────────────────────┘
                                          │
                 ┌────────────────────────┼────────────────────────┐
                 ▼                         ▼                         ▼
   ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
   │  MOTOR DE SIMILITUD  │  │   PostgreSQL          │  │  CONCEPTUAL (NLP)     │
   │  paquete `lumiria`   │  │   tabla `marcas`      │  │  spaCy es_core_news_lg│
   │  · ortográfico       │  │   · claves fonéticas  │  │  / BETO (BERT-es) /   │
   │  · fonético ES       │◄─┤     precalculadas     │  │  lexicón offline      │
   │  · scoring + riesgo  │  │   · pg_trgm / fuzzy   │  │  (incluido)           │
   └──────────────────────┘  │   · fuzzystrmatch     │  └──────────────────────┘
                             └───────────┬───────────┘
                                         │  ingesta periódica
                                         ▼
                             ┌──────────────────────┐
                             │  SENADI (fuente)      │
                             │  Gaceta PI / buscador │
                             │  (o dataset simulado) │
                             └──────────────────────┘
```

## Flujo de una búsqueda

1. El usuario escribe la marca y (opcional) la clase de Niza.
2. El frontend llama a `GET /api/buscar?q=<marca>&clase=<n>`.
3. La API **pre-filtra candidatos en PostgreSQL** (trigramas + bucket fonético
   por `soundex_key` + Levenshtein ≤ 3) → ~200 marcas como mucho.
   *(En la demo, el motor recorre el dataset completo en memoria.)*
4. El **motor `lumiria`** calcula, para cada candidato, los tres ejes y el
   **puntaje general ponderado**, y asigna un **nivel de riesgo**.
5. La API devuelve los resultados ordenados con el desglose por eje.
6. El frontend los pinta con barras, resaltado de coincidencias y semáforo.

## Decisiones de diseño

- **Claves fonéticas precalculadas** en la BD: evitan recomputar fonética por
  cada consulta y permiten indexar/agrupar candidatos (rendimiento).
- **Pre-filtrado en BD + scoring fino en la app**: combina la velocidad de los
  índices con la precisión de los algoritmos a medida.
- **Degradación elegante del eje conceptual**: usa embeddings si están
  disponibles; si no, un lexicón curado, determinista y auditable.
- **Pesos y umbrales configurables** (`Pesos`): permiten calibrar el modelo con
  feedback legal sin tocar el código del motor.
- **Inclusión por eje**: una marca puede aparecer por riesgo solo conceptual
  (Rey↔Corona) aunque su puntaje general sea moderado.

## Componentes del repositorio

| Componente | Ruta |
|---|---|
| Motor de similitud | `backend/lumiria/` |
| API (demo, stdlib) | `backend/api.py` |
| API (producción, FastAPI) | `backend/app_fastapi.py` |
| Dataset simulado SENADI | `backend/data/marcas_senadi_demo.json` |
| Ejemplos de código (entregable) | `backend/examples/ejemplos_codigo.py` |
| Pruebas | `backend/tests/test_engine.py` |
| Frontend | `frontend/` |
| Esquema BD | `docs/03-esquema-base-de-datos.sql` |
