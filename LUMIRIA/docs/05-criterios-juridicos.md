# De la jurisprudencia al algoritmo — Proceso 145-IP-2022

Mapa de cómo los criterios de confundibilidad del Tribunal de Justicia de la
Comunidad Andina se traducen en reglas medibles dentro del motor `lumiria`.

> Nota: LUMIRIA es una herramienta de apoyo. El cotejo marcario es una
> valoración jurídica integral que realiza el examinador del SENADI; aquí se
> automatizan los **indicios técnicos** que la jurisprudencia considera.

## Reglas generales del cotejo (interiorización doctrinaria)

- La comparación se hace **en conjunto**, según la impresión global, no
  diseccionando los signos. → puntaje **general ponderado**.
- Debe atender a las **semejanzas** antes que a las diferencias. → umbrales por
  eje que **afloran** coincidencias parciales.
- Visión del **consumidor medio** y memoria imperfecta. → tolerancia a pequeñas
  variaciones (Levenshtein/trigramas, no igualdad exacta).
- **Conexión competitiva** (clases de Niza / productos relacionados). →
  filtro opcional por `clase_niza`.

## Ejes y su implementación

### 1. Similitud ortográfica (morfosintáctica)

| Criterio jurisprudencial | Implementación (`orthographic.py`) |
|---|---|
| Composición y secuencia de letras | Distancia de **Levenshtein** (ratio) |
| Parecido global de la cadena | **Trigramas** (Jaccard, estilo `pg_trgm`) |
| Coincidencia de **vocales** y estructura silábica | Levenshtein sobre la **serie vocálica**; silabación |
| **Raíces o lexemas comunes** (Acuafresh/Acuadent) | Prefijo/sufijo común ≥ 3 letras |
| Longitud y número de palabras | Factor de diferencia de longitud |

### 2. Similitud fonética *(crítica)*

| Criterio jurisprudencial | Implementación (`phonetics.py`, `scoring.py`) |
|---|---|
| Marcas que **suenan** igual aunque se escriban distinto | Clave **metaphone ES** + Levenshtein |
| Particularidades del español (b/v, s/c/z, y/ll, g/j, h muda…) | Normalización de grafemas equivalentes |
| Agrupación rápida de candidatos | **Soundex hispano** (bucket) |
| **Sílaba tónica** idéntica ⇒ semejanza evidente | Detección de tónica + **bonus** en el puntaje |

> Ejemplo: *Synergy* recupera *Sinergia*, *Xinergy*, *Sinergía* porque sus
> claves fonéticas son casi idénticas y la sílaba tónica coincide.

### 3. Similitud conceptual o ideológica

| Criterio jurisprudencial | Implementación (`conceptual.py`) |
|---|---|
| Signos que **evocan la misma idea** (Rey/Corona, Luna/Selene) | Embeddings (spaCy/BETO) **o** lexicón de campos semánticos |
| Sinónimos / mismo campo semántico | Grupos de sinónimos (peso alto) y campos (peso medio) |

## Ponderación por defecto

Para signos **denominativos**, el plano fonético y el ortográfico priman:

```
general = 0.40 · fonético + 0.35 · ortográfico + 0.25 · conceptual
```

Los pesos son configurables (`Pesos`) para calibrar con casos reales. Además,
una marca se incluye si **cualquier eje** supera el umbral, de modo que las
coincidencias puramente conceptuales o puramente fonéticas no se pierdan.

## Semáforo de riesgo

| Puntaje | Nivel | Color |
|---|---|---|
| ≥ 70 | Alto | 🔴 |
| 45–69 | Medio | 🟡 |
| < 45 | Bajo | 🟢 |
