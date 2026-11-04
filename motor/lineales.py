"""Estructuras lineales propias: pila, cola y lista doblemente enlazada."""


class _Nodo:
    def __init__(self, valor, sig=None):
        self.valor = valor
        self.sig = sig


class Pila:
    """Pila enlazada. apilar, desapilar y vaciar: O(1)."""

    def __init__(self):
        self._tope = None
        self._n = 0

    def __len__(self):
        return self._n

    def vacia(self):
        return self._tope is None

    def apilar(self, valor):
        self._tope = _Nodo(valor, self._tope)
        self._n += 1

    def desapilar(self):
        if self._tope is None:
            raise IndexError("pila vacía")
        valor = self._tope.valor
        self._tope = self._tope.sig
        self._n -= 1
        return valor

    def vaciar(self):
        self._tope = None
        self._n = 0


class Cola:
    """Cola FIFO sobre un arreglo circular.

    encolar y desencolar son O(1) (encolar es O(1) amortizado: cuando el
    arreglo se llena se duplica). Se prefirió al arreglo circular en vez de
    nodos enlazados porque con cientos de miles de pasajeros no crea un
    objeto por pasajero, y eso hace que Python vaya más rápido.
    """

    def __init__(self, capacidad=16):
        if capacidad < 1:
            capacidad = 1
        self._datos = [None] * capacidad
        self._inicio = 0   # posición del primero de la fila
        self._n = 0

    def __len__(self):
        return self._n

    def vacia(self):
        return self._n == 0

    def encolar(self, valor):
        if self._n == len(self._datos):
            self._crecer()
        fin = (self._inicio + self._n) % len(self._datos)
        self._datos[fin] = valor
        self._n += 1

    def desencolar(self):
        if self._n == 0:
            raise IndexError("cola vacía")
        valor = self._datos[self._inicio]
        self._datos[self._inicio] = None
        self._inicio = (self._inicio + 1) % len(self._datos)
        self._n -= 1
        return valor

    def _crecer(self):
        nuevos = [None] * (len(self._datos) * 2)
        for i in range(self._n):
            nuevos[i] = self._datos[(self._inicio + i) % len(self._datos)]
        self._datos = nuevos
        self._inicio = 0


class NodoParada:
    def __init__(self, estacion):
        self.estacion = estacion
        self.ant = None
        self.sig = None


class ListaDoble:
    """Lista doblemente enlazada de paradas de una ruta.

    Con el nodo en la mano (lo da la tabla hash de la ruta), insertar después
    de él o quitarlo es O(1). Recorrer en cualquier sentido es O(L).
    """

    def __init__(self):
        self.cabeza = None
        self.cola = None
        self.n = 0

    def agregar_al_final(self, nodo):
        nodo.ant = self.cola
        nodo.sig = None
        if self.cola is None:
            self.cabeza = nodo
        else:
            self.cola.sig = nodo
        self.cola = nodo
        self.n += 1

    def insertar_despues(self, previo, nodo):
        """Inserta nodo después de previo; si previo es None, al inicio."""
        if previo is None:
            nodo.ant = None
            nodo.sig = self.cabeza
            if self.cabeza is None:
                self.cola = nodo
            else:
                self.cabeza.ant = nodo
            self.cabeza = nodo
        else:
            nodo.ant = previo
            nodo.sig = previo.sig
            if previo.sig is None:
                self.cola = nodo
            else:
                previo.sig.ant = nodo
            previo.sig = nodo
        self.n += 1

    def quitar(self, nodo):
        if nodo.ant is None:
            self.cabeza = nodo.sig
        else:
            nodo.ant.sig = nodo.sig
        if nodo.sig is None:
            self.cola = nodo.ant
        else:
            nodo.sig.ant = nodo.ant
        nodo.ant = None
        nodo.sig = None
        self.n -= 1

    def a_lista(self, al_reves=False):
        res = []
        nodo = self.cola if al_reves else self.cabeza
        while nodo is not None:
            res.append(nodo.estacion)
            nodo = nodo.ant if al_reves else nodo.sig
        return res
