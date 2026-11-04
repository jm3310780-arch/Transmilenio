"""App web del planeador. Solo llama al motor: aquí no hay reglas del sistema.

Uso (desde la carpeta del proyecto):
    python app/servidor.py
y abrir http://localhost:8000 en el navegador.

Usa solo la librería estándar de Python (http.server y json), así no hay
que instalar nada.
"""

import json
import random
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from motor import Red, simular_fila  # noqa: E402
from rendimiento.medir import medir  # noqa: E402

CARPETA_DATOS = sys.argv[1] if len(sys.argv) > 1 else str(RAIZ / "datos")
PUERTO = 8000
red = Red(CARPETA_DATOS)


def tramos_a_json(tramos):
    if tramos is None:
        return None
    return [{"ruta": r, "sube": a, "baja": b, "paradas": p} for r, a, b, p in tramos]


def atender(accion, p):
    """Traduce cada pedido de la página a una llamada del motor."""
    if accion == "estado":
        existe, abierta = red.estado(p["nombre"])
        return {"existe": existe, "abierta": abierta}
    if accion == "autocompletar":
        return red.autocompletar(p["prefijo"], int(p.get("k", 8)))
    if accion == "rango":
        return red.rango(p["desde"], p["hasta"])
    if accion == "rutas_de":
        return red.rutas_de(p["estacion"])
    if accion == "rutas":
        return red.nombres_rutas()
    if accion == "proximo_bus":
        return red.proximo_bus(p["estacion"], p["ruta"], p["hora"])
    if accion == "viaje":
        return tramos_a_json(red.viaje(p["origen"], p["destino"]))
    if accion == "ranking":
        return [{"nombre": n, "buses": b} for n, b in red.ranking(int(p.get("k", 10)))]
    if accion == "recorrido":
        return red.recorrido(p["ruta"], p.get("al_reves") == "1")
    if accion == "agregar_parada":
        return red.agregar_parada(p["ruta"], p["nueva"], p.get("despues_de") or None)
    if accion == "quitar_parada":
        return red.quitar_parada(p["ruta"], p["estacion"])
    if accion == "cerrar":
        return red.cerrar(p["nombre"])
    if accion == "reabrir":
        return red.reabrir(p["nombre"])
    if accion == "deshacer":
        return red.deshacer()
    if accion == "rehacer":
        return red.rehacer()
    if accion == "fila":
        # Llegadas al azar: n pasajeros entre el minuto 0 y "minutos".
        llegadas = [random.randrange(int(p["minutos"])) for _ in range(int(p["n"]))]
        abordajes = simular_fila(llegadas, int(p["frecuencia"]), int(p["capacidad"]))
        ordenadas = sorted(llegadas)
        esperas = [b - a for a, b in zip(ordenadas, abordajes)]
        return {
            "abordajes": abordajes[:200],
            "pasajeros": len(llegadas),
            "espera_promedio": sum(esperas) / len(esperas) if esperas else 0,
            "espera_maxima": max(esperas) if esperas else 0,
        }
    if accion == "rendimiento":
        return medir()
    raise KeyError(accion)


class Manejador(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        if url.path in ("/", "/index.html"):
            contenido = (RAIZ / "app" / "static" / "index.html").read_bytes()
            self._responder(200, contenido, "text/html; charset=utf-8")
            return
        if url.path.startswith("/api/"):
            params = {k: v[0] for k, v in parse_qs(url.query).items()}
            try:
                datos = atender(url.path[5:], params)
                self._responder(200, json.dumps(datos).encode(), "application/json")
            except (KeyError, ValueError) as e:
                self._responder(400, json.dumps({"error": str(e)}).encode(),
                                "application/json")
            return
        self._responder(404, b"No encontrado", "text/plain")

    def _responder(self, codigo, cuerpo, tipo):
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def log_message(self, *args):
        pass  # no llenar la consola con cada pedido


if __name__ == "__main__":
    print(f"Planeador TransMilenio en http://localhost:{PUERTO}  (Ctrl+C para salir)")
    HTTPServer(("", PUERTO), Manejador).serve_forever()
