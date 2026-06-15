-- =====================================================================
-- LUMIRIA · Esquema de base de datos (PostgreSQL 14+)
-- Entregable 2: tabla de marcas con claves fonéticas precalculadas
-- =====================================================================
--
-- Extensiones recomendadas:
--   pg_trgm        -> similitud por trigramas (operador % y similarity())
--   fuzzystrmatch  -> soundex(), metaphone(), levenshtein()
--   unaccent       -> normalización sin tildes para indexar/buscar
--   (opcional) vector (pgvector) -> embeddings para similitud conceptual
--
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS unaccent;
-- CREATE EXTENSION IF NOT EXISTS vector;   -- si se usa pgvector

-- ---------------------------------------------------------------------
-- Catálogo de estados y clases
-- ---------------------------------------------------------------------
CREATE TYPE estado_marca AS ENUM (
    'registrada', 'en_tramite', 'rechazada', 'caducada', 'opuesta'
);

-- ---------------------------------------------------------------------
-- Tabla principal de marcas (anterioridades SENADI)
-- ---------------------------------------------------------------------
CREATE TABLE marcas (
    id                BIGSERIAL PRIMARY KEY,
    denominacion      TEXT         NOT NULL,           -- signo tal cual fue solicitado
    denominacion_norm TEXT         NOT NULL,           -- sin tildes, minúsculas, sin signos
    clase_niza        SMALLINT     NOT NULL CHECK (clase_niza BETWEEN 1 AND 45),
    titular           TEXT,
    estado            estado_marca NOT NULL DEFAULT 'registrada',
    numero_registro   TEXT UNIQUE,
    fecha_concesion   DATE,
    fecha_vencimiento DATE,

    -- ---- Claves fonéticas precalculadas (clave del rendimiento) ----
    -- Se llenan por TRIGGER (ver abajo) o desde la capa de aplicación
    -- usando los algoritmos del paquete `lumiria`.
    soundex_key       TEXT,        -- Soundex hispano (letra + 3 dígitos)
    metaphone_key     TEXT,        -- transcripción fonética completa ES
    serie_vocalica    TEXT,        -- p. ej. 'oa' de 'corona' -> útil para cotejo
    silaba_tonica     TEXT,        -- sílaba con el acento prosódico
    num_silabas       SMALLINT,

    -- ---- Conceptual (opcional, si se usa pgvector) ----
    -- embedding       vector(300),

    creado_en         TIMESTAMPTZ  NOT NULL DEFAULT now(),
    actualizado_en    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- Índices
-- ---------------------------------------------------------------------
-- Trigramas sobre la denominación normalizada (búsqueda difusa rápida).
CREATE INDEX idx_marcas_trgm        ON marcas USING gin (denominacion_norm gin_trgm_ops);
-- Agrupación/“bucketing” fonético: candidatos que comparten clave.
CREATE INDEX idx_marcas_soundex     ON marcas (soundex_key);
CREATE INDEX idx_marcas_metaphone   ON marcas USING gin (metaphone_key gin_trgm_ops);
-- Filtro por clase (conexión competitiva).
CREATE INDEX idx_marcas_clase       ON marcas (clase_niza);
CREATE INDEX idx_marcas_estado      ON marcas (estado);
-- CREATE INDEX idx_marcas_embedding ON marcas USING hnsw (embedding vector_cosine_ops);

-- ---------------------------------------------------------------------
-- Trigger: normaliza y precalcula claves al insertar/actualizar.
-- (metaphone() de fuzzystrmatch es inglés; para ES, lo ideal es calcular
--  metaphone_key/soundex_key en la app con `lumiria` y solo dejar aquí el
--  fallback. Se muestran ambas vías.)
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION marcas_precalcular()
RETURNS TRIGGER AS $$
BEGIN
    NEW.denominacion_norm := lower(unaccent(NEW.denominacion));
    -- Fallback con extensiones nativas (sustituir por claves ES de `lumiria`):
    IF NEW.soundex_key IS NULL THEN
        NEW.soundex_key := soundex(NEW.denominacion_norm);
    END IF;
    NEW.serie_vocalica := regexp_replace(NEW.denominacion_norm, '[^aeiou]', '', 'g');
    NEW.actualizado_en := now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_marcas_precalcular
    BEFORE INSERT OR UPDATE ON marcas
    FOR EACH ROW EXECUTE FUNCTION marcas_precalcular();

-- ---------------------------------------------------------------------
-- Tabla de auditoría de búsquedas (analítica / mejora del modelo)
-- ---------------------------------------------------------------------
CREATE TABLE busquedas (
    id              BIGSERIAL PRIMARY KEY,
    consulta        TEXT NOT NULL,
    clase_niza      SMALLINT,
    total_resultados INT,
    realizada_en    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================================================================
-- CONSULTA DE EJEMPLO: pre-filtrado de candidatos en la BD
-- La app trae un conjunto reducido y aplica el scoring fino de `lumiria`.
-- =====================================================================
-- :q       = denominación buscada (texto)
-- :q_norm  = lower(unaccent(:q))
-- :q_sndx  = clave soundex ES de :q
-- :clase   = clase de Niza (o NULL para todas)
--
--   SELECT id, denominacion, clase_niza, titular, estado,
--          similarity(denominacion_norm, :q_norm) AS sim_trgm
--   FROM   marcas
--   WHERE  (:clase IS NULL OR clase_niza = :clase)
--     AND  estado IN ('registrada', 'en_tramite')
--     AND  (
--            denominacion_norm % :q_norm          -- vecindad por trigramas
--         OR soundex_key = :q_sndx                -- mismo bucket fonético
--         OR levenshtein(denominacion_norm, :q_norm) <= 3
--          )
--   ORDER BY sim_trgm DESC
--   LIMIT 200;
-- =====================================================================
