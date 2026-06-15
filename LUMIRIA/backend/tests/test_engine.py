"""Pruebas del motor LUMIRIA (ejecutables con: python3 -m pytest, o directamente).

No requieren pytest: si se ejecuta el archivo se corre un mini-runner propio.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lumiria import (  # noqa: E402
    comparar,
    clave_metaphone_es,
    similitud_fonetica,
    similitud_conceptual,
    silaba_tonica,
)
from lumiria.engine import MotorMarcario  # noqa: E402


def test_fonetica_b_v_equivalentes():
    assert clave_metaphone_es("baca") == clave_metaphone_es("vaca")


def test_fonetica_s_c_z_equivalentes():
    assert clave_metaphone_es("cebra") == clave_metaphone_es("zebra") == clave_metaphone_es("sebra")


def test_fonetica_yeismo():
    assert clave_metaphone_es("callo") == clave_metaphone_es("cayo")


def test_fonetica_h_muda():
    assert clave_metaphone_es("hola") == clave_metaphone_es("ola")


def test_silaba_tonica():
    assert silaba_tonica("camión") == "mión"
    assert silaba_tonica("corona") == "ro"


def test_fonetica_synergy_suena_a_sinergia():
    assert similitud_fonetica("Synergy", "Sinergia")["puntaje"] >= 60


def test_conceptual_sinonimos():
    assert similitud_conceptual("luna", "selene")["puntaje"] >= 80


def test_conceptual_mismo_campo():
    assert similitud_conceptual("rey", "corona")["puntaje"] >= 50


def test_conceptual_sin_relacion():
    assert similitud_conceptual("piano", "tornillo")["puntaje"] <= 20


def test_comparar_identicas_da_100():
    assert comparar("Corona", "Corona")["puntaje_general"] == 100.0


def test_riesgo_alto_para_marca_muy_similar():
    d = comparar("Acuabrite", "Acuafresh")
    assert d["riesgo"]["nivel"] in ("alto", "medio")
    assert d["ortografica"]["puntaje"] >= 50


def test_busqueda_encuentra_anterioridad_fonetica():
    motor = MotorMarcario.desde_json()
    res = motor.buscar("Synergy", umbral=40)
    nombres = [r["marca"]["denominacion"] for r in res["resultados"]]
    assert "Sinergia" in nombres or "Xinergy" in nombres


def test_busqueda_surfacea_conceptual():
    motor = MotorMarcario.desde_json()
    res = motor.buscar("Rey", umbral=40)
    nombres = [r["marca"]["denominacion"] for r in res["resultados"]]
    assert any(n in nombres for n in ("Corona", "Monarca", "Rey Sol"))


def test_resultados_ordenados_desc():
    motor = MotorMarcario.desde_json()
    res = motor.buscar("Acuabrite", umbral=30)
    puntajes = [r["puntaje_general"] for r in res["resultados"]]
    assert puntajes == sorted(puntajes, reverse=True)


if __name__ == "__main__":
    funcs = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    fallos = 0
    for f in funcs:
        try:
            f()
            print(f"  ✓ {f.__name__}")
        except AssertionError as e:
            fallos += 1
            print(f"  ✗ {f.__name__}  -> {e!r}")
    print(f"\n{len(funcs) - fallos}/{len(funcs)} pruebas OK")
    sys.exit(1 if fallos else 0)
