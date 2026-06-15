"""Motor de búsqueda de anterioridades marcarias.

Carga la base de marcas (SENADI o simulada), precalcula las claves fonéticas
de cada signo y, dada una consulta, devuelve las marcas ordenadas por riesgo
de confundibilidad con su desglose completo.
"""

from __future__ import annotations

import json
from pathlib import Path

from .phonetics import clave_metaphone_es, clave_soundex_es
from .scoring import Pesos, comparar

RUTA_DATOS = Path(__file__).resolve().parent.parent / "data" / "marcas_senadi_demo.json"


class MotorMarcario:
    def __init__(self, marcas: list[dict] | None = None):
        self.marcas: list[dict] = []
        if marcas is not None:
            self.cargar(marcas)

    @classmethod
    def desde_json(cls, ruta: str | Path = RUTA_DATOS) -> "MotorMarcario":
        with open(ruta, encoding="utf-8") as f:
            return cls(json.load(f))

    def cargar(self, marcas: list[dict]) -> None:
        """Precalcula y cachea las claves fonéticas (como columnas en la BD)."""
        self.marcas = []
        for m in marcas:
            den = m["denominacion"]
            self.marcas.append({
                **m,
                "metaphone_key": clave_metaphone_es(den),
                "soundex_key": clave_soundex_es(den),
            })

    def buscar(
        self,
        consulta: str,
        umbral: float = 40.0,
        limite: int = 20,
        clase_niza: int | None = None,
        pesos: Pesos = Pesos(),
        umbral_eje: float = 60.0,
    ) -> dict:
        """Busca anterioridades para `consulta`.

        umbral      : puntaje general mínimo para incluir un resultado.
        umbral_eje  : un signo también se incluye si destaca en CUALQUIER eje
                      (p. ej. solo conceptual: Rey ↔ Corona), aunque su puntaje
                      general quede por debajo del umbral.
        clase_niza  : si se indica, restringe a esa clase (criterio de conexión
                      competitiva; marcas en clases distintas suelen coexistir).
        """
        resultados = []
        for m in self.marcas:
            if clase_niza is not None and m.get("clase_niza") != clase_niza:
                continue
            dictamen = comparar(consulta, m["denominacion"], pesos)
            ejes_altos = [
                eje for eje, val in (
                    ("ortográfico", dictamen["ortografica"]["puntaje"]),
                    ("fonético", dictamen["fonetica"]["puntaje"]),
                    ("conceptual", dictamen["conceptual"]["puntaje"]),
                ) if val >= umbral_eje
            ]
            if dictamen["puntaje_general"] >= umbral or ejes_altos:
                resultados.append({
                    "motivo_inclusion": ("riesgo_general"
                                         if dictamen["puntaje_general"] >= umbral
                                         else "eje:" + ",".join(ejes_altos)),
                    "marca": {
                        "id": m.get("id"),
                        "denominacion": m["denominacion"],
                        "clase_niza": m.get("clase_niza"),
                        "titular": m.get("titular"),
                        "estado": m.get("estado"),
                        "numero_registro": m.get("numero_registro"),
                    },
                    "puntaje_general": dictamen["puntaje_general"],
                    "riesgo": dictamen["riesgo"],
                    "ortografica": {
                        "puntaje": dictamen["ortografica"]["puntaje"],
                        "detalle": dictamen["ortografica"]["detalle"],
                    },
                    "fonetica": {
                        "puntaje": dictamen["fonetica"]["puntaje"],
                        "explicacion": dictamen["fonetica"]["explicacion"],
                        "factores": dictamen["fonetica"]["factores"],
                    },
                    "conceptual": dictamen["conceptual"],
                })

        resultados.sort(key=lambda r: r["puntaje_general"], reverse=True)
        return {
            "consulta": consulta,
            "total": len(resultados),
            "umbral": umbral,
            "resultados": resultados[:limite],
        }


if __name__ == "__main__":
    motor = MotorMarcario.desde_json()
    import json as _j
    print(_j.dumps(motor.buscar("Synergy"), ensure_ascii=False, indent=2)[:2000])
