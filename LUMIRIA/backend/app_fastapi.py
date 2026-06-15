"""Versión de producción de la API con FastAPI.

    pip install -r requirements.txt
    uvicorn app_fastapi:app --reload

Documentación interactiva en /docs (Swagger UI). Comparte el mismo motor que
`api.py`; usa esta variante cuando quieras validación de tipos, OpenAPI y
despliegue ASGI real.
"""

from __future__ import annotations

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from lumiria.engine import MotorMarcario
from lumiria.scoring import comparar

app = FastAPI(
    title="LUMIRIA API",
    description="Búsqueda de anterioridades marcarias para Ecuador "
                "(criterios del Proceso 145-IP-2022).",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

motor = MotorMarcario.desde_json()


@app.get("/api/health")
def health():
    return {"estado": "ok", "marcas_cargadas": len(motor.marcas)}


@app.get("/api/buscar")
def buscar(
    q: str = Query(..., description="Nombre de la marca a evaluar"),
    umbral: float = Query(40.0, ge=0, le=100),
    clase: int | None = Query(None, description="Clase de Niza para filtrar"),
):
    return motor.buscar(q, umbral=umbral, clase_niza=clase)


@app.get("/api/comparar")
def comparar_endpoint(a: str, b: str):
    return comparar(a, b)
