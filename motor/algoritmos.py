"""Algoritmos propios: merge sort, búsqueda binaria y manejo de horas."""


def ordenar(datos, menor=None):
    """Merge sort: devuelve una lista nueva ordenada. O(n log n).

    menor(a, b) devuelve True si a va antes que b. Por defecto usa <.
    Se eligió merge sort porque siempre es O(n log n) y es estable
    (dos elementos iguales conservan su orden original).
    """
    if menor is None:
        menor = _menor_natural
    copia = [x for x in datos]
    _merge_sort(copia, 0, len(copia), menor)
    return copia


def _merge_sort(arr, ini, fin, menor):
    """Ordena arr[ini:fin] en su lugar."""
    if fin - ini <= 1:
        return
    medio = (ini + fin) // 2
    _merge_sort(arr, ini, medio, menor)
    _merge_sort(arr, medio, fin, menor)
    # Mezclar las dos mitades ya ordenadas.
    izq = arr[ini:medio]
    der = arr[medio:fin]
    i, j, k = 0, 0, ini
    while i < len(izq) and j < len(der):
        if menor(der[j], izq[i]):
            arr[k] = der[j]
            j += 1
        else:
            arr[k] = izq[i]
            i += 1
        k += 1
    while i < len(izq):
        arr[k] = izq[i]
        i += 1
        k += 1
    while j < len(der):
        arr[k] = der[j]
        j += 1
        k += 1


def _menor_natural(a, b):
    return a < b


def primer_mayor_o_igual(arreglo, x):
    """Búsqueda binaria: primer índice i con arreglo[i] >= x. O(log n).

    Devuelve len(arreglo) si ninguno cumple. El arreglo debe estar ordenado.
    """
    lo, hi = 0, len(arreglo)
    while lo < hi:
        mid = (lo + hi) // 2
        if arreglo[mid] < x:
            lo = mid + 1
        else:
            hi = mid
    return lo


def esta_ordenado(arreglo):
    for i in range(1, len(arreglo)):
        if arreglo[i] < arreglo[i - 1]:
            return False
    return True


def a_minutos(hora):
    """'HH:MM' -> minutos desde medianoche. Acepta horas >= 24 (formato GTFS)."""
    texto = hora.strip()
    partes = texto.split(":")
    if len(partes) < 2:
        raise ValueError("hora inválida: " + texto)
    h = int(partes[0])
    m = int(partes[1])
    if h < 0 or m < 0 or m > 59:
        raise ValueError("hora inválida: " + texto)
    return h * 60 + m


def a_texto(minutos):
    minutos = minutos % (24 * 60)
    h = minutos // 60
    m = minutos % 60
    return ("0" if h < 10 else "") + str(h) + ":" + ("0" if m < 10 else "") + str(m)


_TILDES = "ÁÉÍÓÚÜÑáéíóúüñ"
_SIN_TILDES = "AEIOUUNaeiouun"


def normalizar(nombre):
    """Mayúsculas, sin tildes y sin espacios repetidos ni de borde."""
    if nombre is None:
        return ""
    res = []
    for c in nombre.strip().upper():
        j = _TILDES.find(c)
        res.append(_SIN_TILDES[j].upper() if j >= 0 else c)
    return " ".join("".join(res).split())
