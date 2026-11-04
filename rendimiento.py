# R11. Mide cuánto tarda cada operación con redes cada vez más grandes.
#
# Es el método del Taller 1: medir con una red de tamaño n, duplicar n y
# volver a medir. Si el tiempo casi no cambia, es O(1) u O(log n); si se
# duplica, es O(n); si se multiplica por 4, es O(n²).
#
# n = número de estaciones. La red de prueba tiene n/5 rutas de 10 paradas
# y 10 buses por parada, así que todo crece al mismo ritmo que n.
#
# Uso: python rendimiento.py   (la app también usa la función medir)

import math
import random
import tempfile
import time

from motor import Red, simular_fila

TAMANOS = [1000, 2000, 4000, 8000]
VECES = 1000  # cuántas veces se repite cada operación para promediar


def nombre(i):
    return "EST " + str(i).zfill(6)


def generar_red(n, carpeta):
    random.seed(n)
    f_est = open(carpeta + "/estaciones.csv", "w")
    f_rut = open(carpeta + "/rutas.csv", "w")
    f_hor = open(carpeta + "/horarios.csv", "w")
    f_est.write("nombre\n")
    f_rut.write("ruta,orden,estacion\n")
    f_hor.write("ruta,estacion,hora\n")
    for i in range(n):
        f_est.write(nombre(i) + "\n")
    for r in range(n // 5):
        paradas = random.sample(range(n), 10)
        for orden in range(10):
            est = nombre(paradas[orden])
            f_rut.write(f"R{r},{orden + 1},{est}\n")
            for b in range(10):
                f_hor.write(f"R{r},{est},{5 + b:02d}:{orden * 3:02d}\n")
    f_est.close()
    f_rut.close()
    f_hor.close()


# "lambda i: ..." es una función de una línea, sin nombre. La usamos para
# pasarle a cronometrar la operación que queremos medir.
def cronometrar(funcion):
    """Microsegundos que tarda, en promedio, una llamada a funcion()."""
    inicio = time.perf_counter()
    for i in range(VECES):
        funcion(i)
    return (time.perf_counter() - inicio) / VECES * 1000000


def medir_una_red(n):
    carpeta = tempfile.mkdtemp()
    generar_red(n, carpeta)
    red = Red(carpeta)
    al_azar = [nombre(random.randrange(n)) for i in range(VECES)]
    paradas = red.recorrido("R0")
    red.ranking(10)

    def editar(i):
        red.agregar_parada("R0", al_azar[i], paradas[3])
        red.deshacer()

    def cerrar_y_reabrir(i):
        red.cerrar(al_azar[i])
        red.reabrir(al_azar[i])

    def deshacer_y_rehacer(i):
        red.deshacer()
        red.rehacer()

    llegadas = [random.randrange(600) for i in range(50 * n)]
    llegadas.sort()  # aquí sí se puede: estamos fuera de motor/
    inicio = time.perf_counter()
    simular_fila(llegadas, 5, 80)
    fila = (time.perf_counter() - inicio) * 1000000

    return {
        "R1 estado": cronometrar(lambda i: red.estado(al_azar[i])),
        "R2 autocompletar": cronometrar(lambda i: red.autocompletar(al_azar[i][:8], 5)),
        "R3 rango": cronometrar(lambda i: red.rango(nombre(5), nombre(14))),
        "R4 proximo_bus": cronometrar(lambda i: red.proximo_bus(paradas[2], "R0", "07:00")),
        "R6 ranking": cronometrar(lambda i: red.ranking(10)),
        "R7 agregar y quitar": cronometrar(editar),
        "R8 cerrar y reabrir": cronometrar(cerrar_y_reabrir),
        "R9 deshacer y rehacer": cronometrar(deshacer_y_rehacer),
        "R10 simular_fila (50n pasajeros)": fila,
    }


# Lo que esperábamos de cada una (ver README).
ESPERADO = {
    "R1 estado": "O(1)",
    "R2 autocompletar": "O(log n + k)",
    "R3 rango": "O(log n + m)",
    "R4 proximo_bus": "O(P + log h)",
    "R6 ranking": "O(k)",
    "R7 agregar y quitar": "O(P)",
    "R8 cerrar y reabrir": "O(1)",
    "R9 deshacer y rehacer": "O(P)",
    "R10 simular_fila (50n pasajeros)": "O(p)",
}


def curva_esperada(esperado, primer_tiempo):
    """Cómo debería crecer el tiempo según la O grande, empezando en primer_tiempo."""
    curva = []
    for n in TAMANOS:
        if esperado == "O(p)":
            # p crece igual que n: si n se duplica, el tiempo se duplica
            curva.append(primer_tiempo * n / TAMANOS[0])
        elif esperado.startswith("O(log n"):
            curva.append(primer_tiempo * math.log2(n) / math.log2(TAMANOS[0]))
        else:
            # O(1), O(k) y O(P): no dependen de n
            curva.append(primer_tiempo)
    return curva


def medir():
    """Devuelve una lista de resultados: uno por cada tamaño de red."""
    resultados = []
    for n in TAMANOS:
        resultados.append(medir_una_red(n))
    return resultados


if __name__ == "__main__":
    resultados = medir()
    print("Microsegundos por llamada")
    print("operación".ljust(34) + "esperado".ljust(15) + "".join(str(n).rjust(10) for n in TAMANOS))
    for operacion in ESPERADO:
        fila = operacion.ljust(34) + ESPERADO[operacion].ljust(15)
        for r in resultados:
            fila += f"{r[operacion]:10.1f}"
        print(fila)
