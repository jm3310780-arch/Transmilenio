"""Árbol AVL de claves str (sin valores).

Guarda solo las estaciones ABIERTAS. Así autocompletar, rango y búsquedas
ordenadas nunca tienen que saltarse estaciones cerradas.

Complejidad (n = número de claves en el árbol):
- insertar, eliminar, contiene: O(log n) comparaciones de texto.
- desde(clave) y recorrer m claves en orden: O(log n + m).
"""


class _NodoAVL:
    def __init__(self, clave):
        self.clave = clave
        self.izq = None
        self.der = None
        self.altura = 1


def _alt(nodo):
    return 0 if nodo is None else nodo.altura


def _actualizar(nodo):
    a = _alt(nodo.izq)
    b = _alt(nodo.der)
    nodo.altura = (a if a > b else b) + 1


def _rotar_der(y):
    x = y.izq
    y.izq = x.der
    x.der = y
    _actualizar(y)
    _actualizar(x)
    return x


def _rotar_izq(x):
    y = x.der
    x.der = y.izq
    y.izq = x
    _actualizar(x)
    _actualizar(y)
    return y


def _balancear(nodo):
    _actualizar(nodo)
    bal = _alt(nodo.izq) - _alt(nodo.der)
    if bal > 1:
        if _alt(nodo.izq.izq) < _alt(nodo.izq.der):
            nodo.izq = _rotar_izq(nodo.izq)
        return _rotar_der(nodo)
    if bal < -1:
        if _alt(nodo.der.der) < _alt(nodo.der.izq):
            nodo.der = _rotar_der(nodo.der)
        return _rotar_izq(nodo)
    return nodo


class ArbolAVL:
    def __init__(self):
        self._raiz = None
        self._n = 0

    def __len__(self):
        return self._n

    def contiene(self, clave):
        nodo = self._raiz
        while nodo is not None:
            if clave == nodo.clave:
                return True
            nodo = nodo.izq if clave < nodo.clave else nodo.der
        return False

    def insertar(self, clave):
        """Inserta la clave. Devuelve False si ya estaba."""
        antes = self._n
        self._raiz = self._insertar(self._raiz, clave)
        return self._n > antes

    def _insertar(self, nodo, clave):
        if nodo is None:
            self._n += 1
            return _NodoAVL(clave)
        if clave == nodo.clave:
            return nodo
        if clave < nodo.clave:
            nodo.izq = self._insertar(nodo.izq, clave)
        else:
            nodo.der = self._insertar(nodo.der, clave)
        return _balancear(nodo)

    def eliminar(self, clave):
        """Elimina la clave. Devuelve False si no estaba."""
        antes = self._n
        self._raiz = self._eliminar(self._raiz, clave)
        return self._n < antes

    def _eliminar(self, nodo, clave):
        if nodo is None:
            return None
        if clave < nodo.clave:
            nodo.izq = self._eliminar(nodo.izq, clave)
        elif clave > nodo.clave:
            nodo.der = self._eliminar(nodo.der, clave)
        else:
            if nodo.izq is None or nodo.der is None:
                self._n -= 1
                return nodo.izq if nodo.izq is not None else nodo.der
            sucesor = nodo.der
            while sucesor.izq is not None:
                sucesor = sucesor.izq
            nodo.clave = sucesor.clave
            nodo.der = self._eliminar(nodo.der, sucesor.clave)
        return _balancear(nodo)

    def desde(self, clave, cumple, k=-1):
        """Lista, en orden alfabético, de claves >= clave mientras cumple(c).

        Se detiene en la primera clave que no cumple o al juntar k claves
        (k = -1 significa sin límite). Es un recorrido en orden que empieza
        en la clave buscada, sin visitar las ramas que quedan antes de ella.
        Complejidad: O(log n + m), m = claves devueltas.
        """
        res = []
        self._desde(self._raiz, clave, cumple, k, res)
        return res

    def _desde(self, nodo, clave, cumple, k, res):
        """Devuelve False cuando ya hay que parar."""
        if nodo is None:
            return True
        if nodo.clave >= clave:
            # La rama izquierda puede tener claves >= clave: primero ella.
            if not self._desde(nodo.izq, clave, cumple, k, res):
                return False
            if k != -1 and len(res) >= k:
                return False
            if not cumple(nodo.clave):
                return False
            res.append(nodo.clave)
        # La rama derecha siempre puede tener claves mayores.
        return self._desde(nodo.der, clave, cumple, k, res)

    def todas(self):
        return self.desde("", _siempre)


def _siempre(clave):
    return True
