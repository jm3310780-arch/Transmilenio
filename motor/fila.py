"""R10: fila de abordaje en hora pico."""

from .lineales import Cola
from .algoritmos import ordenar, esta_ordenado


def simular_fila(llegadas, frecuencia, capacidad):
    """Simula una fila FIFO en una estación.

    llegadas   : lista con el minuto (número) en que llega cada pasajero.
    frecuencia : cada cuántos minutos sale un bus. Los buses salen en
                 0, frecuencia, 2·frecuencia, ...
    capacidad  : cuántos pasajeros caben en cada bus.

    Un pasajero que llega justo cuando sale un bus alcanza a subirse.
    Devuelve una lista con la hora de salida del bus en que se subió cada
    pasajero, en el mismo orden de llegada (llegadas ordenadas).

    Complejidad: O(p + b) con p pasajeros y b buses con gente; cada pasajero
    entra y sale de la cola una sola vez. Si las llegadas no vienen
    ordenadas, se ordenan antes con merge sort: O(p log p).
    """
    if frecuencia <= 0 or capacidad <= 0:
        raise ValueError("frecuencia y capacidad deben ser positivas")
    if not esta_ordenado(llegadas):
        llegadas = ordenar(llegadas)

    n = len(llegadas)
    abordajes = [0] * n
    cola = Cola(n)  # guarda el índice de cada pasajero que espera
    i = 0           # siguiente pasajero que todavía no ha llegado
    bus = 0         # hora de salida del bus actual

    while i < n or not cola.vacia():
        if cola.vacia() and llegadas[i] > bus:
            # Nadie espera: saltar directo al primer bus útil.
            bus = ((llegadas[i] + frecuencia - 1) // frecuencia) * frecuencia
        # Llegan a la fila todos los que llegan antes de que salga el bus.
        while i < n and llegadas[i] <= bus:
            cola.encolar(i)
            i += 1
        # Se suben en orden de llegada hasta llenar el bus.
        subidos = 0
        while subidos < capacidad and not cola.vacia():
            abordajes[cola.desencolar()] = bus
            subidos += 1
        bus += frecuencia

    return abordajes
