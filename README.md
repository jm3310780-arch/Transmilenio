# Planeador de viajes TransMilenio

Proyecto final de Estructuras de Datos y Algoritmos. Una app web donde se
busca una estación, se planea un viaje y se consulta a qué hora pasa el
siguiente bus, con la red real de TransMilenio.

## Arrancar la app (un solo comando)

```bash
python app/servidor.py
```

Luego abrir <http://localhost:8000>. Solo necesita Python 3.9 o más nuevo; no
hay que instalar nada. Para usar otra red: `python app/servidor.py otra/carpeta`.

Otros comandos:

| Qué | Comando |
| --- | --- |
| Pruebas del motor | `python -m unittest discover tests` |
| Revisar que motor/ no use nada prohibido | `python tests/revisar_reglas.py` |
| Panel de rendimiento en consola | `python rendimiento/medir.py` |
| Convertir el GTFS (necesita pandas) | `python conversion/convertir_gtfs.py gtfs.zip datos/` |

## Cómo está organizado

```
motor/            toda la lógica (solo usa list, str, csv, time y random)
  red.py          clase Red: R1 a R9
  fila.py         simular_fila: R10
  tabla_hash.py   tabla hash propia (reemplaza a dict)
  avl.py          árbol AVL propio
  lineales.py     pila, cola circular y lista doblemente enlazada
  algoritmos.py   merge sort, búsqueda binaria, horas y nombres
app/              servidor web y página (solo llama al motor)
conversion/       script GTFS -> CSV
datos/            estaciones.csv, rutas.csv, horarios.csv ya generados
rendimiento/      generador de redes de tamaño n y medición (R11)
tests/            pruebas y revisor de reglas
```

El script del profesor hace `from motor import Red, simular_fila`.

## Los datos

`datos/` tiene la red: 147 estaciones, 181 rutas y unos 140.000 horarios.
Cada ruta va en un solo sentido (por ejemplo `B10-1` y `B10-2`).

Decisiones de la conversión (`conversion/convertir_gtfs.py`):

- **Nombres:** mayúsculas, sin tildes y sin espacios repetidos. Los vagones de
  una estación se unen usando `parent_station`.
- **Rutas:** cada secuencia de paradas distinta de una ruta es una ruta de un
  solo sentido, numerada `-1`, `-2`, … de la que tiene más viajes a la que
  tiene menos.
- **Un solo día:** se usa el `service_id` con más viajes (un día hábil), para
  que "buses al día" tenga sentido en el ranking.
- **Horas como 25:10:** en GTFS son buses del mismo día de servicio que pasan
  después de medianoche. Se guardan como la hora del reloj (`25:10` → `01:10`),
  porque el usuario pregunta por la hora que ve en su reloj. El motor ordena
  los horarios al cargarlos, así que no importa que queden al final del CSV.

## Qué devuelve cada operación

El enunciado manda las reglas exactas. Si alguna no coincide con esto, se
cambia solo la línea del `return`.

| Llamada | Devuelve |
| --- | --- |
| `Red(carpeta)` | Carga los tres CSV de la carpeta. |
| `estado(nombre)` | `(existe, abierta)`, dos booleanos. |
| `autocompletar(prefijo, k)` | Lista de hasta k nombres abiertos, en orden alfabético. |
| `rango(desde, hasta)` | Lista de nombres abiertos con desde ≤ nombre ≤ hasta. |
| `proximo_bus(estacion, ruta, hora)` | `"HH:MM"` del primer bus a esa hora o después; `None` si no hay más ese día, si la ruta no para ahí o si la estación está cerrada. |
| `viaje(origen, destino)` | Lista de tramos `(ruta, sube_en, baja_en, paradas)`; `[]` si origen = destino; `None` si no hay viaje. |
| `ranking(k)` | Lista de `(nombre, buses_al_dia)`, de más a menos buses; empates en orden alfabético. |
| `agregar_parada(ruta, nueva, despues_de)` | `True` o `False`. `despues_de=None` la pone al inicio. |
| `quitar_parada(ruta, estacion)` | `True` o `False`. |
| `recorrido(ruta, al_reves=False)` | Lista de estaciones en ese sentido; `[]` si la ruta no existe. |
| `cerrar(nombre)`, `reabrir(nombre)` | `True` o `False` (no existe o ya estaba así). |
| `deshacer()`, `rehacer()` | `True` o `False` (no había nada). |
| `simular_fila(llegadas, frecuencia, capacidad)` | Lista con la hora de salida del bus que tomó cada pasajero. |

Los nombres se normalizan al entrar (`"calle 26"` funciona igual que `"CALLE 26"`).

## Decisiones por requisito (R12)

Reglas del motor: dentro de `motor/` no se usa `dict`, `set`, `sorted`,
`.sort()`, `min`, `max`, `x in lista`, `.index()`, `.count()`, `bisect`,
`heapq`, `collections` ni `functools`. Por eso las estructuras están hechas a
mano. `tests/revisar_reglas.py` lo verifica.

Notación: **n** = número de estaciones, **L** = largo del nombre de una
estación (casi constante), **P** = paradas de una ruta, **h** = buses de una
ruta en una estación, **k** y **m** = cuántos resultados se devuelven,
**p** = pasajeros.

### R1 · Buscar una estación

- **Estructura:** tabla hash propia (`tabla_hash.py`) con encadenamiento:
  nombre → estación. Función hash polinomial (`h = h·31 + código`), y la
  tabla se duplica cuando hay más de 0,75 elementos por cubeta.
- **Por qué:** es la consulta más usada y la tabla hash la responde en O(1)
  promedio, sin importar cuántas estaciones haya.
- **Descartada:** buscar en la lista (O(n)) o búsqueda binaria en un arreglo
  ordenado (O(log n)): ambas peores que O(1).
- **O grande:** O(L) promedio, O(n·L) en el peor caso (todas en la misma cubeta).

### R2 · Autocompletar

- **Estructura:** árbol AVL (`avl.py`) que guarda **solo las estaciones
  abiertas**. Se baja hasta el primer nombre ≥ prefijo y desde ahí se hace un
  recorrido en orden hasta tener k nombres o hasta el primero que ya no
  empieza por el prefijo.
- **Por qué:** pide orden alfabético y las estaciones cambian (cerrar/reabrir);
  el AVL mantiene el orden y se mantiene balanceado, así que siempre es O(log n).
  Como las cerradas no están en el árbol, nunca hay que saltarlas.
- **Descartadas:** arreglo ordenado con búsqueda binaria (consulta igual de
  rápida, pero cerrar y reabrir costarían O(n) por correr elementos); trie
  (también sirve para prefijos, pero no ayuda con R3 y usa más memoria);
  ordenar en cada consulta (O(n log n)).
- **O grande:** O(log n + k).

### R3 · Listar un rango

- **Estructura:** el mismo AVL de R2, con el mismo recorrido en orden
  empezando en `desde` y parando al pasar `hasta`.
- **Descartada:** recorrer todas las estaciones y filtrar: O(n).
- **O grande:** O(log n + m), m = estaciones devueltas.

### R4 · Próximo bus

- **Estructura:** tabla hash con clave `"ruta|estacion"` → arreglo de horas
  (en minutos) ordenado al cargar con merge sort. La consulta hace búsqueda
  binaria del primer horario ≥ hora.
- **Por qué:** las troncales pasan cientos de veces al día; la búsqueda binaria
  no recorre todos los horarios.
- **Descartada:** recorrer los horarios de la ruta hasta encontrar uno mayor:
  O(h). Un montículo no sirve porque la consulta es "el primero después de
  una hora", no "el menor".
- **O grande:** O(L + log h). La carga cuesta O(H log H) una sola vez.
- **Borde:** si ya no pasan más buses ese día devuelve `None` (no da la vuelta
  al día siguiente).

### R5 · Planear un viaje

- **Estructuras:** cada ruta es una lista doblemente enlazada de paradas, con
  una tabla hash estación → nodo; cada estación sabe qué rutas paran en ella.
- **Algoritmo:** es una búsqueda en anchura limitada a dos tramos.
  1. Desde el origen se avanza por cada ruta que pasa por él y se anota, en una
     tabla hash, la menor cantidad de paradas para llegar a cada estación (y
     con qué ruta). Si aparece el destino, es un viaje directo.
  2. Desde el destino se retrocede por cada ruta que pasa por él. Cada
     estación **abierta** que también se alcanzó en el paso 1 (con otra ruta)
     es un transbordo posible: total = paradas del tramo 1 + paradas del tramo 2.
  3. Se queda el de menos paradas; si empatan, se prefiere el directo.
- **Descartadas:** BFS completo sobre el grafo de estaciones (encuentra el
  camino más corto, pero no controla que sea máximo un transbordo); probar
  todas las parejas de rutas (O(rutas² · P)).
- **O grande:** O(suma de P de las rutas que pasan por origen y destino).
- **Cerradas:** no se puede subir, bajar ni transbordar en una estación
  cerrada, pero el bus sí pasa por ella y la parada se cuenta.

### R6 · Ranking

- **Estructura:** cada estación guarda cuántos buses paran en ella al día
  (suma de sus horarios en las rutas que la incluyen). El ranking es un
  arreglo ya ordenado (merge sort, más buses primero y desempate alfabético)
  que se guarda y solo se vuelve a calcular cuando hubo un cierre, reapertura,
  edición, deshacer o rehacer.
- **Por qué:** se consulta muy seguido y cambia poco; así la consulta normal
  es solo copiar k elementos.
- **Descartadas:** ordenar en cada consulta (O(n log n) siempre); un montículo
  (sacar k cuesta O(k log n) y hay que reconstruirlo igual tras cambios).
- **O grande:** O(k) si nada cambió; O(n log n) la primera consulta después de
  un cambio.

### R7 · Editar rutas

- **Estructura:** lista doblemente enlazada por ruta + tabla hash
  estación → nodo. Con el nodo en la mano, insertar después de él o quitarlo
  es cambiar unos punteros. `recorrido` camina la lista hacia adelante o hacia
  atrás (por eso es doble).
- **Descartada:** arreglo de paradas: insertar o quitar en la mitad obliga a
  correr todo lo que viene después (O(P)) y además hay que buscar la posición.
- **O grande:** agregar y quitar O(L); recorrido O(P).
- **Bordes:** no se agrega una estación que no existe ni una que ya está en la
  ruta; `despues_de=None` pone la parada al inicio. Los horarios de una parada
  quitada se conservan, así deshacer la devuelve con sus horarios.

### R8 · Cerrar y reabrir

- **Estructura:** bandera `abierta` en la estación (tabla hash) y se saca o se
  mete del AVL de abiertas. El ranking se marca para recalcular.
- **Efecto en todo:** como el AVL solo tiene abiertas, R2 y R3 dejan de verla
  sin hacer nada más; R4 y R5 revisan la bandera; R6 solo cuenta abiertas.
- **O grande:** O(L + log n).

### R9 · Deshacer y rehacer

- **Estructura:** dos pilas enlazadas. Cada cambio se guarda como una tupla
  (`"cerrar"`, nombre), (`"agregar"`, ruta, estación, después_de), etc.
  Deshacer saca de la pila de deshacer, aplica la operación contraria y lo
  pasa a la de rehacer. Un cambio nuevo vacía la pila de rehacer.
- **Por qué:** el último cambio es el primero que se deshace (LIFO).
- **Descartada:** guardar una copia de toda la red en cada cambio: O(n) en
  tiempo y memoria por cambio.
- **O grande:** O(1) para mover entre pilas + lo que cueste la operación
  contraria (O(L + log n) como máximo).

### R10 · Fila de abordaje

- **Estructura:** cola FIFO sobre un **arreglo circular** (`lineales.py`).
- **Algoritmo:** los buses salen en 0, f, 2f, … Antes de cada salida entran a
  la cola todos los que ya llegaron; se suben en orden hasta llenar el cupo.
  Si la cola está vacía se salta directo al siguiente bus útil.
- **Por qué arreglo circular y no nodos enlazados:** probamos primero con
  nodos y, con cientos de miles de pasajeros, el tiempo crecía más que lineal
  porque Python crea un objeto por pasajero y el recolector de basura se
  vuelve lento. El arreglo circular no crea objetos y volvió a crecer lineal.
- **Descartada:** una lista de Python con `pop(0)`: cada `pop(0)` es O(p) y
  todo sería O(p²).
- **O grande:** O(p + b), b = buses que salen con gente. Si las llegadas no
  vienen ordenadas, se ordenan antes con merge sort: O(p log p).

## Panel de rendimiento (R11)

Pestaña **Rendimiento** de la app (o `python rendimiento/medir.py`). Genera
redes de 1.000, 2.000, 4.000 y 8.000 estaciones (n/5 rutas de 10 paradas, 10
buses por parada) y mide cada operación muchas veces. Grafica el tiempo medido
junto a la curva esperada.

Resultados de una corrida (microsegundos por llamada):

| Operación | Esperado | n=1000 | n=8000 | Cambio |
| --- | --- | --- | --- | --- |
| estado (R1) | O(1) | 2.0 | 2.3 | x1.2 |
| autocompletar (R2) | O(log n + k) | 2.5 | 2.4 | x1.0 |
| rango (R3) | O(log n + m) | 4.5 | 3.5 | x0.8 |
| proximo_bus (R4) | O(log h) | 4.9 | 4.0 | x0.8 |
| ranking (R6) | O(k) | 0.1 | 0.1 | x0.8 |
| agregar + quitar (R7) | O(1) | 15 | 13 | x0.9 |
| cerrar + reabrir (R8) | O(log n) | 14 | 18 | x1.3 |
| simular_fila (R10) | O(p) | 29 ms | 213 ms | x7.3 (p x8) |

**Cómo leerlo:** al multiplicar n por 8, las operaciones O(1) y O(log n) casi
no cambian (log₂ 8000 / log₂ 1000 ≈ 1,3), y la fila crece ≈ 8 veces porque es
lineal en p. Las variaciones pequeñas (subir de 2,0 a 3,1 y bajar otra vez)
son ruido del computador, no de la complejidad: si fuera O(n) tendría que
llegar a x8.
