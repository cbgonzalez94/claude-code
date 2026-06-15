"""LUMIRIA — motor de búsqueda de anterioridades marcarias para Ecuador.

Análisis de confundibilidad de signos denominativos en tres ejes
(ortográfico, fonético y conceptual) según los criterios del Tribunal de
Justicia de la Comunidad Andina (Proceso 145-IP-2022).
"""

from .engine import MotorMarcario
from .scoring import Pesos, comparar, nivel_riesgo, similitud_fonetica
from .orthographic import similitud_ortografica
from .conceptual import similitud_conceptual
from .phonetics import clave_metaphone_es, clave_soundex_es, info_fonetica
from .syllables import silabar, silaba_tonica

__version__ = "0.1.0"

__all__ = [
    "MotorMarcario",
    "Pesos",
    "comparar",
    "nivel_riesgo",
    "similitud_fonetica",
    "similitud_ortografica",
    "similitud_conceptual",
    "clave_metaphone_es",
    "clave_soundex_es",
    "info_fonetica",
    "silabar",
    "silaba_tonica",
]
