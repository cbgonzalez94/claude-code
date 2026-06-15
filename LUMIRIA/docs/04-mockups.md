# Mockups de Interfaz — LUMIRIA

> Versión funcional implementada en `frontend/` (HTML/CSS/JS). Estos mockups
> describen el diseño visual y el comportamiento esperado.

## 1. Página principal (minimalista)

```
┌──────────────────────────────────────────────────────────────────────┐
│  LUMIRIA            Análisis de confundibilidad marcaria · Ecuador     │
├──────────────────────────────────────────────────────────────────────┤
│                                                                        │
│                  Ingresa el nombre de tu marca                         │
│       Evaluamos el riesgo de confusión frente a marcas del SENADI      │
│             según los criterios del Tribunal Andino (145-IP-2022).     │
│                                                                        │
│     ┌───────────────────────────────────┐  ┌───────────┐  ┌────────┐  │
│     │  Ej.: Synergy, Rey, Acuabrite…    │  │ Clase ▾   │  │Analizar│  │
│     └───────────────────────────────────┘  └───────────┘  └────────┘  │
│                                                                        │
│        Prueba:  Synergy · Rey · Acuabrite · Luna · Baca                │
└──────────────────────────────────────────────────────────────────────┘
```

## 2. Página de resultados (el corazón del producto)

```
┌──────────────────────────────────────────────────────────────────────┐
│  MARCA ANALIZADA                                  3 coincidencias       │
│  Synergy                                          sobre el umbral       │
├──────────────────────────────────────────────────────────────────────┤
│ ▌Xinergy                                      ●  Riesgo ALTO · 72%      │  ← borde ROJO
│ ▌Clase 9 · TechXi Cía. Ltda. · Registrada                              │
│ ▌                                                                      │
│ ▌ Ortográfica  ▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░  65%                                │
│ ▌ Fonética     ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░  88%                                │
│ ▌ Conceptual   ▓░░░░░░░░░░░░░░░░░░   5%                                │
│ ▌                                                                      │
│ ▌ Ortográfica: 65% — 2 ediciones de diferencia; vocales «ie»vs«ie».    │
│ ▌ Fonética: Sonido casi idéntico. (SINERGI ≈ KSINERGI)                 │
│ ▌ Conceptual: Sin relación conceptual detectable.                      │
├──────────────────────────────────────────────────────────────────────┤
│ ▌Sinergia                                     ●  Riesgo MEDIO · 47%     │  ← borde AMARILLO
│ ▌Clase 35 · Consultora Andina S.A. · Registrada                        │
│ ▌ Ortográfica  ▓▓▓▓▓▓▓▓▓░░░░░░░░░░  45%                                │
│ ▌ Fonética     ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░  75%                                │
│ ▌ Conceptual   ▓░░░░░░░░░░░░░░░░░░   5%                                │
│ ▌ Fonética: Sonido marcadamente parecido. Sílaba tónica coincidente.   │
└──────────────────────────────────────────────────────────────────────┘
```

### Para una búsqueda conceptual (`Rey`)

```
┌──────────────────────────────────────────────────────────────────────┐
│ ▌Corona                                       ●  Riesgo BAJO · 27%     │  ← borde VERDE
│ ▌Clase 32 · Bebidas del Pacífico S.A. · Registrada                     │
│ ▌ Ortográfica  ▓▓░░░░░░░░░░░░░░░░░  12%                                │
│ ▌ Fonética     ▓▓▓░░░░░░░░░░░░░░░░  18%                                │
│ ▌ Conceptual   ▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░  65%                                │
│ ▌ Conceptual: Mismo campo semántico (realeza…).                        │
│ ▌ → Incluida por similitud conceptual.                                 │
└──────────────────────────────────────────────────────────────────────┘
```

## Sistema de color (semáforo de riesgo)

| Nivel | Color | Puntaje general | Lectura para el usuario |
|---|---|---|---|
| Alto  | 🔴 Rojo     | ≥ 70 | Registro poco viable; alta probabilidad de oposición |
| Medio | 🟡 Amarillo | 45–69 | Zona gris; conviene análisis legal detallado |
| Bajo  | 🟢 Verde    | < 45 | Registro probablemente viable |

## Principios de UX

- **Un solo objetivo por pantalla**: la principal solo invita a buscar.
- **El “por qué” siempre visible**: cada resultado explica en lenguaje llano
  por qué se considera similar (no solo un número).
- **Jerarquía visual por riesgo**: color del borde + badge + orden descendente.
- **Resaltado de coincidencias**: letras/sílabas compartidas marcadas en el nombre.
- **Honestidad**: disclaimer permanente de que es una herramienta orientativa.
```
