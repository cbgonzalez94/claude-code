# Plan de Proyecto — LUMIRIA

Aplicación web de búsqueda de anterioridades marcarias para Ecuador, con
análisis de confundibilidad en tres ejes (ortográfico, fonético y conceptual)
según los criterios del Tribunal de Justicia de la Comunidad Andina
(**Proceso 145-IP-2022**).

---

## Fase 0 — Fundamentos jurídicos y de datos (semana 1)

1. **Mapear los criterios del 145-IP-2022** a reglas algorítmicas
   (ver `05-criterios-juridicos.md`). Este es el insumo conceptual del motor.
2. **Conseguir los datos del SENADI**: la Gaceta de la Propiedad Intelectual
   y el buscador de signos distintivos publican marcas registradas y en
   trámite. Opciones:
   - Convenio/solicitud formal de acceso a datos al SENADI.
   - Scraping del buscador público (respetando términos de uso).
   - **Para el desarrollo: dataset simulado** (`backend/data/marcas_senadi_demo.json`).
3. Definir el modelo de datos y el catálogo de **clases de Niza** (1–45).

## Fase 1 — Configuración del entorno (semana 1)

- Repositorio + estructura (`backend/`, `frontend/`, `docs/`).
- Python 3.11+, entorno virtual, `requirements.txt`.
- PostgreSQL 14+ con extensiones `pg_trgm`, `fuzzystrmatch`, `unaccent`.
- Linter/formatter (ruff/black) y CI (lint + tests).

## Fase 2 — Motor de similitud (semanas 2–4) · *núcleo del producto*

- **Ortográfico**: Levenshtein, trigramas, serie vocálica, raíz común, longitud.
- **Fonético ES**: normalización de grafemas equivalentes, clave metaphone y
  soundex hispanos, **detección de sílaba tónica**.
- **Conceptual**: lexicón de campos semánticos (offline) y, en producción,
  embeddings (spaCy `es_core_news_lg` / BERT en español, p. ej. BETO) o API de
  tesauro ES.
- **Ponderación y semáforo de riesgo** (pesos configurables; fonético+ortográfico
  pesan más para signos denominativos).
- Pruebas unitarias por eje y casos de oro (Synergy↔Sinergia, Rey↔Corona…).

> En este repo el motor ya está implementado y probado en Python puro
> (`backend/lumiria/`, 14/14 tests OK).

## Fase 3 — Persistencia y rendimiento (semana 4)

- Esquema PostgreSQL (`03-esquema-base-de-datos.sql`) con **claves fonéticas
  precalculadas** (`soundex_key`, `metaphone_key`, `serie_vocalica`, `silaba_tonica`).
- **Pre-filtrado en la BD** (trigramas + bucket fonético + Levenshtein ≤ 3) para
  traer ~200 candidatos; el **scoring fino** lo hace el motor en la app.
- Job de ingesta/actualización periódica desde el SENADI.

## Fase 4 — API (semana 5)

- FastAPI: `/api/buscar`, `/api/comparar`, `/api/health` (ver `app_fastapi.py`).
- Validación, paginación, OpenAPI/Swagger, rate limiting y caché.
- Registro de búsquedas para analítica y mejora del modelo.

## Fase 5 — Frontend (semanas 5–6)

- Página principal minimalista (un gran buscador).
- Página de resultados con **puntaje general**, **desglose por eje**, resaltado
  de coincidencias y **semáforo de color** (rojo/amarillo/verde).
- Producción: React/Vite + componentes accesibles. (Aquí se incluye una versión
  vanilla funcional sin build en `frontend/`.)

## Fase 6 — Calidad y validación legal (semana 7)

- Validar resultados con un abogado de PI sobre casos reales de oposición.
- Ajustar pesos y umbrales con ese feedback (calibración).
- Pruebas de carga sobre el dataset completo del SENADI.

## Fase 7 — Despliegue (semana 8)

- Backend: contenedor (Docker) + Uvicorn/Gunicorn detrás de Nginx; o un PaaS.
- Base de datos: PostgreSQL gestionado (con respaldos).
- Frontend: build estático en CDN.
- Observabilidad: logs, métricas, alertas. CI/CD para despliegues.

---

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Acceso/licenciamiento de datos del SENADI | Convenio formal; dataset simulado mientras tanto |
| Falsos positivos/negativos del modelo | Calibración con casos reales; pesos configurables; umbrales por eje |
| Calidad de embeddings en español | Usar `es_core_news_lg` o BETO; fallback a lexicón curado |
| Expectativa de “valor legal” | Disclaimer claro: herramienta orientativa, no sustituye al examinador |

## Stack

- **Frontend**: React/Vite (incluida demo vanilla).
- **Backend**: Python 3.11 + FastAPI (incluido servidor stdlib para demo).
- **NLP/algoritmos**: implementación propia ES; spaCy/jellyfish opcionales.
- **BD**: PostgreSQL + `pg_trgm`, `fuzzystrmatch`, `unaccent` (+ pgvector opcional).
