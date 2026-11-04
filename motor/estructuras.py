# Estructuras y algoritmos hechos por nosotros.
#
# Dentro de motor/ el enunciado NO deja usar dict, set, sorted, .sort(),
# min, max, "x in lista", .index() ni .count(). Por eso aquí están:
#   1. TablaHash   -> reemplaza a dict
#   2. ordenar     -> merge sort, reemplaza a sorted
#   3. buscar_desde -> búsqueda binaria


# ---------------------------------------------------------------
# 1. Tabla hash
# ---------------------------------------------------------------
# Es una lista de "cubetas". Cada cubeta es una lista de pares [clave, valor].
# Para saber en qué cubeta va una clave, convertimos el texto en un número
# (función hash) y sacamos el residuo con el número de cubetas.

def numero_hash(texto):
    h = 0
    for letra in texto:
        h = (h * 31 + ord(letra)) % 1000000007
    return h


class TablaHash:
    def __init__(self):
        self.cubetas = []
        for i in range(64):
            self.cubetas.append([])
        self.cantidad = 0

    def _cubeta(self, clave):
        posicion = numero_hash(clave) % len(self.cubetas)
        return self.cubetas[posicion]

    def obtener(self, clave):
        """Devuelve el valor guardado con esa clave, o None si no está."""
        for par in self._cubeta(clave):
            if par[0] == clave:
                return par[1]
        return None

    def poner(self, clave, valor):
        """Guarda el valor. Si la clave ya estaba, lo reemplaza."""
        cubeta = self._cubeta(clave)
        for par in cubeta:
            if par[0] == clave:
                par[1] = valor
                return
        cubeta.append([clave, valor])
        self.cantidad += 1
        # Si las cubetas se llenan mucho, las duplicamos para que siga rápido.
        if self.cantidad > len(self.cubetas):
            self._agrandar()

    def _agrandar(self):
        viejas = self.cubetas
        self.cubetas = []
        for i in range(len(viejas) * 2):
            self.cubetas.append([])
        for cubeta in viejas:
            for par in cubeta:
                self._cubeta(par[0]).append(par)

    def pares(self):
        """Lista de todos los pares [clave, valor]."""
        todos = []
        for cubeta in self.cubetas:
            for par in cubeta:
                todos.append(par)
        return todos


# ---------------------------------------------------------------
# 2. Merge sort
# ---------------------------------------------------------------
# Parte la lista en dos mitades, ordena cada una y después las mezcla.
# "va_antes(a, b)" dice si a debe ir antes que b.

def menor(a, b):
    return a < b


def ordenar(lista, va_antes=menor):
    if len(lista) <= 1:
        return lista
    mitad = len(lista) // 2
    izquierda = ordenar(lista[:mitad], va_antes)
    derecha = ordenar(lista[mitad:], va_antes)

    resultado = []
    i = 0
    j = 0
    while i < len(izquierda) and j < len(derecha):
        if va_antes(derecha[j], izquierda[i]):
            resultado.append(derecha[j])
            j += 1
        else:
            resultado.append(izquierda[i])
            i += 1
    # Lo que sobró de alguna de las dos mitades ya está ordenado.
    while i < len(izquierda):
        resultado.append(izquierda[i])
        i += 1
    while j < len(derecha):
        resultado.append(derecha[j])
        j += 1
    return resultado


# ---------------------------------------------------------------
# 3. Búsqueda binaria
# ---------------------------------------------------------------
# En una lista ORDENADA, devuelve la primera posición cuyo valor es >= x.
# Si ninguno lo es, devuelve len(lista).

def buscar_desde(lista, x):
    inicio = 0
    fin = len(lista)
    while inicio < fin:
        medio = (inicio + fin) // 2
        if lista[medio] < x:
            inicio = medio + 1
        else:
            fin = medio
    return inicio
