"""Algoritmos fonéticos adaptados al español.

El español tiene equivalencias de sonido que un Soundex/Metaphone inglés no
captura. Aquí se modelan las particularidades exigidas por el análisis de
confundibilidad marcaria (Proceso 145-IP-2022):

    b ≈ v        casa  / vaca
    s ≈ c(e,i) ≈ z   cebra / sebra / zebra
    y ≈ ll       cayó  / calló
    g(e,i) ≈ j   gente / jente
    h muda       hola  / ola
    qu ≈ k ≈ c(a,o,u)
    x ≈ ks / s

Se generan dos claves precalculables y almacenables en la base de datos:

    clave_metaphone : cadena fonética completa (vocales + consonantes
                      canónicas). Útil para medir el GRADO de semejanza con
                      distancia de edición.
    clave_soundex   : código corto tipo Soundex hispano (letra + dígitos).
                      Útil para indexar y agrupar candidatos rápidamente.

Sin dependencias externas.
"""

from __future__ import annotations

from .syllables import quitar_tildes, silaba_tonica


def normalizar(texto: str) -> str:
    texto = quitar_tildes(texto.lower().strip())
    return "".join(c for c in texto if c.isalpha())


def clave_metaphone_es(palabra: str) -> str:
    """Transcripción fonética canónica del español.

    Convierte los grafemas a un alfabeto de fonemas reducido donde los
    sonidos equivalentes colapsan en el mismo símbolo.
    """
    s = normalizar(palabra)
    if not s:
        return ""

    out: list[str] = []
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        sig = s[i + 1] if i + 1 < n else ""

        # Dígrafos primero.
        par = c + sig
        if par == "ch":
            out.append("X")  # sonido /tʃ/
            i += 2
            continue
        if par == "ll":
            out.append("Y")  # yeísmo: ll ≈ y
            i += 2
            continue
        if par == "rr":
            out.append("R")
            i += 2
            continue
        if par == "qu":
            out.append("K")
            i += 2
            continue
        if par == "gu" and sig == "u" and i + 2 < n and s[i + 2] in "ei":
            out.append("G")  # gue/gui -> /g/ (u muda)
            i += 2
            continue

        # Letras simples.
        if c in "aeiou":
            out.append(c.upper())
        elif c == "h":
            pass  # h muda
        elif c in "bv":
            out.append("B")
        elif c == "w":
            out.append("B")  # préstamos: w ≈ b/gu
        elif c == "c":
            out.append("S" if sig in "ei" else "K")
        elif c in "sz":
            out.append("S")
        elif c == "k":
            out.append("K")
        elif c == "q":
            out.append("K")
        elif c == "g":
            out.append("J" if sig in "ei" else "G")
        elif c == "j":
            out.append("J")
        elif c == "x":
            out.append("KS")
        elif c == "y":
            # 'y' final o sola actúa como vocal /i/.
            if sig == "" or sig not in "aeiou":
                out.append("I")
            else:
                out.append("Y")
        elif c == "ñ":
            out.append("N")
        else:
            out.append(c.upper())  # l, m, n, p, t, d, f, r
        i += 1

    # Colapsar consonantes dobles repetidas (no vocales).
    clave: list[str] = []
    for ch in "".join(out):
        if clave and clave[-1] == ch and ch not in "AEIOU":
            continue
        clave.append(ch)
    return "".join(clave)


# Agrupación de consonantes por punto/modo de articulación para el Soundex ES.
_GRUPOS_SOUNDEX = {
    "b": "1", "v": "1", "w": "1", "p": "1", "f": "1",
    "c": "2", "k": "2", "q": "2", "g": "2", "j": "2", "x": "2",
    "s": "3", "z": "3",
    "d": "4", "t": "4",
    "l": "5",
    "m": "6", "n": "6", "ñ": "6",
    "r": "7",
    "y": "8",
}


def clave_soundex_es(palabra: str) -> str:
    """Soundex adaptado al español: letra inicial + 3 dígitos de grupo.

    'h' se ignora; vocales actúan como separadores; dígitos consecutivos
    iguales se colapsan (regla clásica de Soundex).
    """
    s = normalizar(palabra)
    if not s:
        return ""

    # Normalizar la inicial a su sonido (c->s/k, g->j, etc.) usando metaphone.
    meta = clave_metaphone_es(s)
    inicial = meta[0] if meta else s[0].upper()

    codigos: list[str] = []
    anterior = _GRUPOS_SOUNDEX.get(s[0], "")
    for c in s[1:]:
        if c == "h":
            continue
        cod = _GRUPOS_SOUNDEX.get(c, "")
        if cod == "":  # vocal -> rompe la racha
            anterior = ""
            continue
        if cod != anterior:
            codigos.append(cod)
        anterior = cod

    return (inicial + "".join(codigos) + "000")[:4]


def transcripcion_simple(palabra: str) -> str:
    """Transcripción legible para mostrar al usuario (UI)."""
    return clave_metaphone_es(palabra).lower()


def info_fonetica(palabra: str) -> dict:
    return {
        "metaphone": clave_metaphone_es(palabra),
        "soundex": clave_soundex_es(palabra),
        "tonica": silaba_tonica(palabra),
        "transcripcion": transcripcion_simple(palabra),
    }


if __name__ == "__main__":
    for p in ["Synergy", "Sinergia", "Xinergy", "Sinergía", "casa", "vasa",
              "cebra", "sebra", "zebra", "calló", "cayó", "México"]:
        print(f"{p:10} meta={clave_metaphone_es(p):10} soundex={clave_soundex_es(p)}")
