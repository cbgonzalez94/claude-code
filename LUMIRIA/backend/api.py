"""Servidor HTTP de LUMIRIA usando solo la biblioteca estándar.

Pensado para arrancar sin instalar nada (ideal para demo/entornos restringidos):

    python3 api.py            # -> http://localhost:8000

Expone:
    GET  /api/health
    GET  /api/buscar?q=<marca>&umbral=40&clase=<niza>
    GET  /api/comparar?a=<marca1>&b=<marca2>
    GET  /                    -> sirve el frontend estático (../frontend)

Para producción se incluye también `app_fastapi.py` (FastAPI + Uvicorn).
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from lumiria.engine import MotorMarcario
from lumiria.scoring import comparar

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
MOTOR = MotorMarcario.desde_json()

_MIME = {".html": "text/html", ".css": "text/css", ".js": "application/javascript",
         ".json": "application/json", ".svg": "image/svg+xml"}


class Handler(BaseHTTPRequestHandler):
    def _json(self, payload, code=200):
        cuerpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def _archivo(self, ruta: Path):
        if not ruta.is_file():
            self._json({"error": "no encontrado"}, 404)
            return
        cuerpo = ruta.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", _MIME.get(ruta.suffix, "application/octet-stream"))
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_GET(self):
        url = urlparse(self.path)
        q = parse_qs(url.query)

        if url.path == "/api/health":
            return self._json({"estado": "ok", "marcas_cargadas": len(MOTOR.marcas)})

        if url.path == "/api/buscar":
            consulta = (q.get("q", [""])[0]).strip()
            if not consulta:
                return self._json({"error": "falta el parámetro 'q'"}, 400)
            umbral = float(q.get("umbral", ["40"])[0])
            clase = q.get("clase", [None])[0]
            clase_niza = int(clase) if clase not in (None, "", "todas") else None
            return self._json(MOTOR.buscar(consulta, umbral=umbral, clase_niza=clase_niza))

        if url.path == "/api/comparar":
            a = (q.get("a", [""])[0]).strip()
            b = (q.get("b", [""])[0]).strip()
            if not a or not b:
                return self._json({"error": "faltan 'a' y/o 'b'"}, 400)
            return self._json(comparar(a, b))

        # Frontend estático.
        rel = url.path.lstrip("/") or "index.html"
        return self._archivo(FRONTEND / rel)

    def log_message(self, *args):  # silencia el log por defecto
        pass


def main(host: str = "0.0.0.0", puerto: int = 8000):
    servidor = ThreadingHTTPServer((host, puerto), Handler)
    print(f"LUMIRIA escuchando en http://localhost:{puerto}  ({len(MOTOR.marcas)} marcas)")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        servidor.shutdown()


if __name__ == "__main__":
    main()
