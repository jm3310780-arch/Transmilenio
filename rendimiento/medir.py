"""R11: mide cada operación con redes de tamaño creciente.

Uso desde consola:  python rendimiento/medir.py
La app usa la función medir() para dibujar el panel de rendimiento.

Método del Taller 1: generar una red de tamaño n, medir; duplicar n y volver
a medir. Si el tiempo casi no cambia es O(1) u O(log n); si se duplica es
O(n); si se multiplica por 4 es O(n²).

Aquí n = número de estaciones. La red generada crece proporcional a n:
n/5 rutas de 10 paradas y 10 buses por parada, así que paradas y horarios
también se duplican cuando n se duplica.
"""

import math
import random
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from motor import Red, simular_fila  # noqa: E402

TAMANOS = [1000, 2000, 4000, 8000]
REPETICIONES = 2000


def nombre(i):
    return f"EST {i:06d}"


def generar_red(n, carpeta, semilla=7):
    rnd = random.Random(semilla)
    carpeta = Path(carpeta)
    with open(carpeta / "estaciones.csv", "w") as f:
        f.write("nombre\n")
        for i in range(n):
            f.write(nombre(i) + "\n")
    rutas = []
    with open(carpeta / "rutas.csv", "w") as fr, open(carpeta / "horarios.csv", "w") as fh:
        fr.write("ruta,orden,estacion\n")
        fh.write("ruta,estacion,hora\n")
        for r in range(n // 5):
            ruta = f"R{r}"
            paradas = rnd.sample(range(n), 10)
            rutas.append((ruta, [nombre(p) for p in paradas]))
            for orden, p in enumerate(paradas, start=1):
                fr.write(f"{ruta},{orden},{nombre(p)}\n")
                for b in range(10):
                    minuto = 300 + b * 90 + orden * 3
                    fh.write(f"{ruta},{nombre(p)},{minuto // 60:02d}:{minuto % 60:02d}\n")
    return rutas


def _tiempo(funcion, veces):
    inicio = time.perf_counter()
    for _ in range(veces):
        funcion()
    return (time.perf_counter() - inicio) / veces * 1e6  # microsegundos


# Lo que esperamos de cada operación (R12) y cómo crece f(n).
ESPERADO = {
    "estado (R1)": ("O(1)", lambda n: 1),
    "autocompletar k=5 (R2)": ("O(log n + k)", lambda n: math.log2(n)),
    "rango de 10 (R3)": ("O(log n + m)", lambda n: math.log2(n)),
    "proximo_bus (R4)": ("O(log h)", lambda n: 1),
    "ranking k=10 (R6)": ("O(k)", lambda n: 1),
    "agregar + quitar parada (R7)": ("O(1)", lambda n: 1),
    "recorrido (R7)": ("O(P)", lambda n: 1),
    "cerrar + reabrir (R8)": ("O(log n)", lambda n: math.log2(n)),
    "deshacer + rehacer (R9)": ("O(log n)", lambda n: math.log2(n)),
    "simular_fila p=50n (R10)": ("O(p)", lambda n: n),
}


def medir_una(n, repeticiones=REPETICIONES):
    rnd = random.Random(n)
    with tempfile.TemporaryDirectory() as carpeta:
        rutas = generar_red(n, carpeta)
        red = Red(carpeta)
    nombres = [nombre(rnd.randrange(n)) for _ in range(repeticiones)]
    prefijos = [x[:8] for x in nombres]
    ruta, paradas = rutas[0]
    it = iter(range(10 ** 9))

    def siguiente():
        return nombres[next(it) % repeticiones]

    def editar():
        red.agregar_parada(ruta, siguiente(), paradas[3])
        red.deshacer()

    def cerrar_reabrir():
        x = siguiente()
        red.cerrar(x)
        red.reabrir(x)

    red.cerrar(paradas[0])
    red.ranking(10)  # deja el ranking calculado; luego no cambia

    def undo_redo():
        red.deshacer()
        red.rehacer()

    llegadas = sorted(rnd.randrange(600) for _ in range(50 * n))
    res = {
        "estado (R1)": _tiempo(lambda: red.estado(siguiente()), repeticiones),
        "autocompletar k=5 (R2)": _tiempo(
            lambda: red.autocompletar(prefijos[next(it) % repeticiones], 5), repeticiones),
        "rango de 10 (R3)": _tiempo(lambda: red.rango(nombre(5), nombre(14)), repeticiones),
        "proximo_bus (R4)": _tiempo(lambda: red.proximo_bus(paradas[2], ruta, "07:00"), repeticiones),
        "ranking k=10 (R6)": _tiempo(lambda: red.ranking(10), repeticiones),
        "agregar + quitar parada (R7)": _tiempo(editar, repeticiones),
        "recorrido (R7)": _tiempo(lambda: red.recorrido(ruta), repeticiones),
        "cerrar + reabrir (R8)": _tiempo(cerrar_reabrir, repeticiones),
        "deshacer + rehacer (R9)": _tiempo(undo_redo, repeticiones),
        "simular_fila p=50n (R10)": _tiempo(lambda: simular_fila(llegadas, 5, 80), 1),
    }
    return res


def medir(tamanos=TAMANOS):
    """Devuelve {operacion: {"esperado", "n", "tiempos", "teorico"}}."""
    por_tamano = [medir_una(n) for n in tamanos]
    salida = {}
    for op, (etiqueta, f) in ESPERADO.items():
        tiempos = [m[op] for m in por_tamano]
        # Curva teórica escalada para que empiece en el primer tiempo medido.
        escala = tiempos[0] / f(tamanos[0])
        salida[op] = {
            "esperado": etiqueta,
            "n": tamanos,
            "tiempos": tiempos,
            "teorico": [escala * f(n) for n in tamanos],
        }
    return salida


if __name__ == "__main__":
    resultados = medir()
    print(f"{'operación':32s}{'esperado':16s}" + "".join(f"{n:>10d}" for n in TAMANOS)
          + "   razón última/primera")
    for op, d in resultados.items():
        fila = "".join(f"{t:10.2f}" for t in d["tiempos"])
        print(f"{op:32s}{d['esperado']:16s}{fila}   x{d['tiempos'][-1] / d['tiempos'][0]:.2f}")
    print("(tiempos en microsegundos por llamada)")
