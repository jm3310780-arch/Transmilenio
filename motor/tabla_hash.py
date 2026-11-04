"""Tabla hash propia con encadenamiento separado.

Reemplaza a dict, que está prohibido dentro de motor/.
Las claves son str. Cada cubeta es una lista de nodos enlazados.

Complejidad (n = número de claves guardadas, L = largo de la clave):
- obtener, poner, quitar, contiene: O(L) promedio, O(n·L) peor caso.
- Redimensionar: O(n) cada vez que el factor de carga pasa de 0.75;
  amortizado O(1) por inserción porque la capacidad se duplica.
"""


class _Nodo:
    """Un elemento de la cubeta: clave, valor y el siguiente de la cadena."""

    def __init__(self, clave, valor, sig):
        self.clave = clave
        self.valor = valor
        self.sig = sig


def hash_texto(texto):
    """Hash polinomial: h = h * 31 + código del carácter, para cada carácter.

    Se toma el residuo con un primo grande para que el número no crezca.
    """
    h = 0
    for c in texto:
        h = (h * 31 + ord(c)) % 1000000007
    return h


class TablaHash:
    def __init__(self, capacidad=16):
        if capacidad < 8:
            capacidad = 8
        self._cubetas = [None] * capacidad
        self._n = 0

    def __len__(self):
        return self._n

    def _indice(self, clave):
        return hash_texto(clave) % len(self._cubetas)

    def _buscar_nodo(self, clave):
        nodo = self._cubetas[self._indice(clave)]
        while nodo is not None:
            if nodo.clave == clave:
                return nodo
            nodo = nodo.sig
        return None

    def obtener(self, clave, defecto=None):
        nodo = self._buscar_nodo(clave)
        if nodo is None:
            return defecto
        return nodo.valor

    def contiene(self, clave):
        return self._buscar_nodo(clave) is not None

    def poner(self, clave, valor):
        nodo = self._buscar_nodo(clave)
        if nodo is not None:
            nodo.valor = valor
            return
        i = self._indice(clave)
        self._cubetas[i] = _Nodo(clave, valor, self._cubetas[i])
        self._n += 1
        # Si hay más de 0.75 elementos por cubeta, duplicamos el tamaño.
        if self._n * 4 > len(self._cubetas) * 3:
            self._redimensionar(len(self._cubetas) * 2)

    def quitar(self, clave):
        """Quita la clave. Devuelve True si existía."""
        i = self._indice(clave)
        previo = None
        nodo = self._cubetas[i]
        while nodo is not None:
            if nodo.clave == clave:
                if previo is None:
                    self._cubetas[i] = nodo.sig
                else:
                    previo.sig = nodo.sig
                self._n -= 1
                return True
            previo = nodo
            nodo = nodo.sig
        return False

    def _redimensionar(self, nueva_cap):
        viejas = self._cubetas
        self._cubetas = [None] * nueva_cap
        for nodo in viejas:
            while nodo is not None:
                sig = nodo.sig
                i = self._indice(nodo.clave)
                nodo.sig = self._cubetas[i]
                self._cubetas[i] = nodo
                nodo = sig

    def claves(self):
        """Todas las claves, en un orden cualquiera. O(capacidad + n)."""
        res = []
        for nodo in self._cubetas:
            while nodo is not None:
                res.append(nodo.clave)
                nodo = nodo.sig
        return res

    def pares(self):
        res = []
        for nodo in self._cubetas:
            while nodo is not None:
                res.append((nodo.clave, nodo.valor))
                nodo = nodo.sig
        return res
