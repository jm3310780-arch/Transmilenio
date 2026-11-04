"""La clase Red: toda la lógica del planeador (R1 a R9).

Estructuras que usa (todas implementadas en motor/):
- self._estaciones : TablaHash  nombre -> Estacion          (R1, R8)
- self._abiertas   : ArbolAVL   con los nombres abiertos      (R2, R3)
- self._rutas      : TablaHash  ruta -> Ruta                  (R5, R7)
     cada Ruta tiene una ListaDoble de paradas y una TablaHash
     estacion -> nodo para llegar a una parada en O(1).
- self._horarios   : TablaHash  "ruta|estacion" -> lista ordenada de minutos (R4)
- self._ranking    : lista ya ordenada que se reconstruye solo si algo cambió (R6)
- self._pila_deshacer, self._pila_rehacer : Pila             (R9)
"""

import csv

from .tabla_hash import TablaHash
from .avl import ArbolAVL
from .lineales import Pila, ListaDoble, NodoParada
from .algoritmos import (ordenar, primer_mayor_o_igual, a_minutos, a_texto,
                         normalizar)


class Estacion:
    def __init__(self, nombre):
        self.nombre = nombre
        self.abierta = True
        self.rutas = TablaHash(4)   # rutas que paran aquí: ruta -> True
        self.buses = 0              # buses al día que paran aquí (para R6)


class Ruta:
    def __init__(self, nombre):
        self.nombre = nombre
        self.paradas = ListaDoble()  # recorrido en orden
        self.nodos = TablaHash(8)    # estacion -> NodoParada


def _clave_horario(ruta, estacion):
    return ruta + "|" + estacion


def _archivo(carpeta, nombre):
    # Se arma la ruta a mano porque os no está en los módulos permitidos.
    if carpeta.endswith("/") or carpeta.endswith("\\"):
        return carpeta + nombre
    return carpeta + "/" + nombre


def _leer_csv(ruta_archivo):
    """Devuelve las filas del CSV sin el encabezado, como listas de texto."""
    filas = []
    with open(ruta_archivo, encoding="utf-8-sig", newline="") as f:
        lector = csv.reader(f)
        primera = True
        for fila in lector:
            if primera:
                primera = False
                continue
            if len(fila) > 0:
                filas.append(fila)
    return filas


def _menor_por_orden(a, b):
    return a[0] < b[0]


def _menor_ranking(a, b):
    # Más buses primero; si empatan, alfabético.
    if a[1] != b[1]:
        return a[1] > b[1]
    return a[0] < b[0]


class Red:
    # ------------------------------------------------------------------
    # Carga
    # ------------------------------------------------------------------
    def __init__(self, carpeta):
        """Lee estaciones.csv, rutas.csv y horarios.csv de la carpeta.

        O(E + P log P + H log H): E estaciones, P paradas, H horarios.
        """
        self._estaciones = TablaHash(1024)
        self._abiertas = ArbolAVL()
        self._rutas = TablaHash(256)
        self._horarios = TablaHash(4096)
        self._ranking = None
        self._pila_deshacer = Pila()
        self._pila_rehacer = Pila()

        for fila in _leer_csv(_archivo(carpeta, "estaciones.csv")):
            self._crear_estacion(normalizar(fila[0]))

        # rutas.csv: agrupar por ruta y ordenar cada grupo por "orden".
        grupos = TablaHash(256)
        for fila in _leer_csv(_archivo(carpeta, "rutas.csv")):
            nombre_ruta = fila[0].strip()
            grupo = grupos.obtener(nombre_ruta)
            if grupo is None:
                grupo = []
                grupos.poner(nombre_ruta, grupo)
            grupo.append((int(fila[1]), normalizar(fila[2])))
        for nombre_ruta, grupo in grupos.pares():
            ruta = Ruta(nombre_ruta)
            self._rutas.poner(nombre_ruta, ruta)
            for orden, est in ordenar(grupo, _menor_por_orden):
                if ruta.nodos.contiene(est):
                    continue  # una ruta no repite estación
                self._crear_estacion(est)
                nodo = NodoParada(est)
                ruta.paradas.agregar_al_final(nodo)
                ruta.nodos.poner(est, nodo)
                self._estaciones.obtener(est).rutas.poner(nombre_ruta, True)

        # horarios.csv: una lista de minutos por (ruta, estación), ordenada.
        for fila in _leer_csv(_archivo(carpeta, "horarios.csv")):
            clave = _clave_horario(fila[0].strip(), normalizar(fila[1]))
            lista = self._horarios.obtener(clave)
            if lista is None:
                lista = []
                self._horarios.poner(clave, lista)
            lista.append(a_minutos(fila[2]))
        for clave, lista in self._horarios.pares():
            self._horarios.poner(clave, ordenar(lista))

        # Buses por estación (para el ranking).
        for nombre_ruta, ruta in self._rutas.pares():
            nodo = ruta.paradas.cabeza
            while nodo is not None:
                est = self._estaciones.obtener(nodo.estacion)
                est.buses += self._num_buses(nombre_ruta, nodo.estacion)
                nodo = nodo.sig

    def _crear_estacion(self, nombre):
        if nombre == "" or self._estaciones.contiene(nombre):
            return
        self._estaciones.poner(nombre, Estacion(nombre))
        self._abiertas.insertar(nombre)

    def _num_buses(self, ruta, estacion):
        lista = self._horarios.obtener(_clave_horario(ruta, estacion))
        return 0 if lista is None else len(lista)

    def _abierta(self, nombre):
        est = self._estaciones.obtener(nombre)
        return est is not None and est.abierta

    # ------------------------------------------------------------------
    # R1 a R3: consultar estaciones
    # ------------------------------------------------------------------
    def estado(self, nombre):
        """R1. Devuelve (existe, abierta). O(L) promedio con la tabla hash."""
        est = self._estaciones.obtener(normalizar(nombre))
        if est is None:
            return (False, False)
        return (True, est.abierta)

    def autocompletar(self, prefijo, k):
        """R2. Hasta k estaciones abiertas que empiezan por prefijo, en orden.

        O(log n + k) con el árbol AVL de estaciones abiertas.
        """
        if k <= 0:
            return []
        prefijo = normalizar(prefijo)

        def empieza(nombre):
            return nombre.startswith(prefijo)

        return self._abiertas.desde(prefijo, empieza, k)

    def rango(self, desde, hasta):
        """R3. Estaciones abiertas con desde <= nombre <= hasta, en orden.

        O(log n + m), m = estaciones devueltas.
        """
        desde = normalizar(desde)
        hasta = normalizar(hasta)

        def no_pasa(nombre):
            return nombre <= hasta

        return self._abiertas.desde(desde, no_pasa)

    # ------------------------------------------------------------------
    # R4: próximo bus
    # ------------------------------------------------------------------
    def proximo_bus(self, estacion, ruta, hora):
        """R4. Hora 'HH:MM' del primer bus de la ruta en esa estación a partir
        de hora (incluida). None si la estación está cerrada, si la ruta no
        para ahí o si ya no pasan más buses ese día.

        O(L + log h), h = buses de esa ruta en esa estación (búsqueda binaria).
        """
        estacion = normalizar(estacion)
        r = self._rutas.obtener(ruta)
        if r is None or not r.nodos.contiene(estacion):
            return None
        if not self._abierta(estacion):
            return None
        horas = self._horarios.obtener(_clave_horario(ruta, estacion))
        if horas is None:
            return None
        i = primer_mayor_o_igual(horas, a_minutos(hora))
        if i == len(horas):
            return None
        return a_texto(horas[i])

    # ------------------------------------------------------------------
    # R5: planear un viaje
    # ------------------------------------------------------------------
    def viaje(self, origen, destino):
        """R5. Viaje directo o con un transbordo que pase por menos paradas.

        Devuelve una lista de tramos (ruta, sube_en, baja_en, paradas), [] si
        origen == destino, o None si no hay viaje. A igual número de paradas
        se prefiere el viaje directo.

        Idea: 1) desde el origen, avanzar por cada ruta que pasa por él y
        anotar en una tabla hash la menor distancia a cada estación alcanzable
        (si una es el destino, es un viaje directo). 2) desde el destino,
        retroceder por cada ruta que pasa por él; cada estación abierta que
        también se alcanzó en el paso 1 es un posible transbordo.
        O(suma de largos de las rutas que pasan por origen y destino).
        """
        origen = normalizar(origen)
        destino = normalizar(destino)
        if not self._abierta(origen) or not self._abierta(destino):
            return None
        if origen == destino:
            return []

        mejor = None          # lista de tramos de la mejor respuesta
        mejor_paradas = -1
        alcanzadas = TablaHash(64)  # estacion -> (paradas, ruta)

        for nombre_ruta in self._estaciones.obtener(origen).rutas.claves():
            ruta = self._rutas.obtener(nombre_ruta)
            nodo = ruta.nodos.obtener(origen).sig
            paradas = 1
            while nodo is not None:
                est = nodo.estacion
                if est == destino:
                    if mejor is None or paradas < mejor_paradas:
                        mejor = [(nombre_ruta, origen, destino, paradas)]
                        mejor_paradas = paradas
                    break  # más allá del destino no sirve en esta ruta
                previo = alcanzadas.obtener(est)
                if previo is None or paradas < previo[0]:
                    alcanzadas.poner(est, (paradas, nombre_ruta))
                nodo = nodo.sig
                paradas += 1

        for nombre_ruta in self._estaciones.obtener(destino).rutas.claves():
            ruta = self._rutas.obtener(nombre_ruta)
            nodo = ruta.nodos.obtener(destino).ant
            paradas2 = 1
            while nodo is not None:
                t = nodo.estacion
                if t == origen:
                    break  # eso ya sería el viaje directo en esta ruta
                llegada = alcanzadas.obtener(t)
                if (llegada is not None and llegada[1] != nombre_ruta
                        and self._abierta(t)):
                    total = llegada[0] + paradas2
                    if mejor is None or total < mejor_paradas:
                        mejor = [(llegada[1], origen, t, llegada[0]),
                                 (nombre_ruta, t, destino, paradas2)]
                        mejor_paradas = total
                nodo = nodo.ant
                paradas2 += 1

        return mejor

    # ------------------------------------------------------------------
    # R6: ranking
    # ------------------------------------------------------------------
    def ranking(self, k):
        """R6. Las k estaciones abiertas con más buses al día: [(nombre, buses)].

        La lista ordenada se guarda y solo se recalcula (merge sort,
        O(n log n)) cuando hubo un cierre, reapertura o edición. Si nada
        cambió, la consulta es O(k).
        """
        if self._ranking is None:
            pares = []
            for nombre, est in self._estaciones.pares():
                if est.abierta:
                    pares.append((nombre, est.buses))
            self._ranking = ordenar(pares, _menor_ranking)
        if k <= 0:
            return []
        return self._ranking[:k]

    # ------------------------------------------------------------------
    # R7: editar rutas
    # ------------------------------------------------------------------
    def agregar_parada(self, ruta, nueva, despues_de):
        """R7. Pone la estación nueva justo después de despues_de en la ruta.

        despues_de=None la pone al inicio. Devuelve True si se pudo.
        O(L) promedio: tabla hash para hallar el nodo + inserción en O(1).
        """
        nueva = normalizar(nueva)
        if despues_de is not None:
            despues_de = normalizar(despues_de)
        if not self._agregar(ruta, nueva, despues_de):
            return False
        self._registrar(("agregar", ruta, nueva, despues_de))
        return True

    def quitar_parada(self, ruta, estacion):
        """R7. Quita la parada de la ruta. Devuelve True si se pudo. O(L)."""
        estacion = normalizar(estacion)
        r = self._rutas.obtener(ruta)
        if r is None:
            return False
        nodo = r.nodos.obtener(estacion)
        if nodo is None:
            return False
        previo = None if nodo.ant is None else nodo.ant.estacion
        self._quitar(ruta, estacion)
        self._registrar(("quitar", ruta, estacion, previo))
        return True

    def recorrido(self, ruta, al_reves=False):
        """R7. Lista de estaciones de la ruta, en un sentido o en el otro.

        [] si la ruta no existe. O(P), P = paradas de la ruta.
        """
        r = self._rutas.obtener(ruta)
        if r is None:
            return []
        return r.paradas.a_lista(al_reves)

    def _agregar(self, ruta, nueva, despues_de):
        r = self._rutas.obtener(ruta)
        est = self._estaciones.obtener(nueva)
        if r is None or est is None or r.nodos.contiene(nueva):
            return False
        previo = None
        if despues_de is not None:
            previo = r.nodos.obtener(despues_de)
            if previo is None:
                return False
        nodo = NodoParada(nueva)
        r.paradas.insertar_despues(previo, nodo)
        r.nodos.poner(nueva, nodo)
        est.rutas.poner(ruta, True)
        est.buses += self._num_buses(ruta, nueva)
        self._ranking = None
        return True

    def _quitar(self, ruta, estacion):
        r = self._rutas.obtener(ruta)
        nodo = r.nodos.obtener(estacion)
        r.paradas.quitar(nodo)
        r.nodos.quitar(estacion)
        est = self._estaciones.obtener(estacion)
        est.rutas.quitar(ruta)
        est.buses -= self._num_buses(ruta, estacion)
        self._ranking = None

    # ------------------------------------------------------------------
    # R8: cerrar y reabrir
    # ------------------------------------------------------------------
    def cerrar(self, nombre):
        """R8. Cierra la estación. False si no existe o ya estaba cerrada.

        O(L + log n): tabla hash + quitarla del AVL de abiertas.
        """
        nombre = normalizar(nombre)
        est = self._estaciones.obtener(nombre)
        if est is None or not est.abierta:
            return False
        self._cerrar(nombre)
        self._registrar(("cerrar", nombre))
        return True

    def reabrir(self, nombre):
        """R8. Reabre la estación. False si no existe o ya estaba abierta."""
        nombre = normalizar(nombre)
        est = self._estaciones.obtener(nombre)
        if est is None or est.abierta:
            return False
        self._reabrir(nombre)
        self._registrar(("reabrir", nombre))
        return True

    def _cerrar(self, nombre):
        self._estaciones.obtener(nombre).abierta = False
        self._abiertas.eliminar(nombre)
        self._ranking = None

    def _reabrir(self, nombre):
        self._estaciones.obtener(nombre).abierta = True
        self._abiertas.insertar(nombre)
        self._ranking = None

    # ------------------------------------------------------------------
    # R9: deshacer y rehacer
    # ------------------------------------------------------------------
    def _registrar(self, cambio):
        """Todo cambio nuevo va a la pila de deshacer y borra lo de rehacer."""
        self._pila_deshacer.apilar(cambio)
        self._pila_rehacer.vaciar()

    def deshacer(self):
        """R9. Deshace el último cambio. False si no hay nada. O(L + log n)."""
        if self._pila_deshacer.vacia():
            return False
        cambio = self._pila_deshacer.desapilar()
        tipo = cambio[0]
        if tipo == "cerrar":
            self._reabrir(cambio[1])
        elif tipo == "reabrir":
            self._cerrar(cambio[1])
        elif tipo == "agregar":
            self._quitar(cambio[1], cambio[2])
        elif tipo == "quitar":
            self._agregar(cambio[1], cambio[2], cambio[3])
        self._pila_rehacer.apilar(cambio)
        return True

    def rehacer(self):
        """R9. Vuelve a aplicar el último cambio deshecho. False si no hay."""
        if self._pila_rehacer.vacia():
            return False
        cambio = self._pila_rehacer.desapilar()
        tipo = cambio[0]
        if tipo == "cerrar":
            self._cerrar(cambio[1])
        elif tipo == "reabrir":
            self._reabrir(cambio[1])
        elif tipo == "agregar":
            self._agregar(cambio[1], cambio[2], cambio[3])
        elif tipo == "quitar":
            self._quitar(cambio[1], cambio[2])
        self._pila_deshacer.apilar(cambio)
        return True

    # ------------------------------------------------------------------
    # Ayudas para la app (no son parte del contrato)
    # ------------------------------------------------------------------
    def nombres_rutas(self):
        return ordenar(self._rutas.claves())

    def rutas_de(self, estacion):
        est = self._estaciones.obtener(normalizar(estacion))
        if est is None:
            return []
        return ordenar(est.rutas.claves())

    def total_estaciones(self):
        return len(self._estaciones)
