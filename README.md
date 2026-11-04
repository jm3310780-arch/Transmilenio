# Planeador de viajes TransMilenio

Proyecto final de Estructuras de Datos y Algoritmos. Una app donde se busca
una estación, se planea un viaje y se ve a qué hora pasa el siguiente bus.

## Cómo arrancar la app

```bash
pip install -r requirements.txt
streamlit run app.py
```

Se abre sola en el navegador. Otros comandos:

- `python pruebas.py`: prueba el motor (R1 a R10).
- `python rendimiento.py`: el panel de rendimiento, en la consola.
- `python convertir_gtfs.py gtfs.zip datos`: convierte el GTFS a los tres CSV.

## Archivos

| Archivo | Qué tiene |
| --- | --- |
| `motor/estructuras.py` | Tabla hash, merge sort y búsqueda binaria hechos por nosotros |
| `motor/red.py` | La clase `Red` (R1 a R9) y `simular_fila` (R10) |
| `app.py` | La app (Streamlit). Solo llama al motor |
| `rendimiento.py` | Genera redes de tamaño n y mide cada operación (R11) |
| `convertir_gtfs.py` | GTFS → `estaciones.csv`, `rutas.csv`, `horarios.csv` |
| `datos/` | Los tres CSV ya generados |
| `pruebas.py` | Pruebas del motor |

## Por qué hay estructuras hechas a mano

Dentro de `motor/` el enunciado prohíbe `dict`, `set`, `sorted`, `.sort()`,
`min`, `max`, `x in lista`, `.index()`, `.count()`, `bisect`, `heapq`,
`collections` y `functools`. Por eso hicimos:

- **TablaHash:** reemplaza a `dict`. Es una lista de cubetas. El nombre se
  convierte en un número (hash) y ese número dice en qué cubeta va.
- **ordenar:** merge sort. Reemplaza a `sorted`.
- **buscar_desde:** búsqueda binaria en una lista ordenada.
- **esta_en, posicion_de, insertar_en, borrar_en:** recorren la lista con un
  `for`, en vez de usar `in`, `.index()` o `.insert()`.

## Qué devuelve cada función

| Llamada | Devuelve |
| --- | --- |
| `estado(nombre)` | `(existe, abierta)` |
| `autocompletar(prefijo, k)` | lista de hasta k nombres |
| `rango(desde, hasta)` | lista de nombres |
| `proximo_bus(estacion, ruta, hora)` | `"HH:MM"`, o `None` si no hay más buses hoy |
| `viaje(origen, destino)` | lista de tramos `(ruta, sube_en, baja_en, paradas)`; `[]` si es la misma estación; `None` si no hay viaje |
| `ranking(k)` | lista de `(nombre, buses_al_dia)` |
| `agregar_parada`, `quitar_parada`, `cerrar`, `reabrir`, `deshacer`, `rehacer` | `True` si se pudo, `False` si no |
| `recorrido(ruta, al_reves=False)` | lista de estaciones |
| `simular_fila(llegadas, frecuencia, capacidad)` | minuto de salida del bus de cada pasajero |

Si el enunciado pide otro formato, se cambia solo el `return`.

## Decisiones por requisito (R12)

Qué es cada letra: **n** = estaciones, **P** = paradas de una ruta,
**h** = buses de una ruta en una estación, **k** y **m** = cuántos
resultados se devuelven, **p** = pasajeros.

**R1. Buscar una estación.** Tabla hash nombre → abierta (True/False). Es la
consulta más usada y la tabla hash la responde en O(1) promedio.
Descartamos recorrer la lista de estaciones, que es O(n).

**R2. Autocompletar.** Lista de todas las estaciones ordenada al cargar
(merge sort). Con búsqueda binaria saltamos al primer nombre que empieza por
el prefijo y avanzamos hasta tener k abiertas. **O(log n + k)**. Descartamos
recorrer todas las estaciones (O(n)). Pensamos en un árbol AVL, pero como las
estaciones nunca se agregan ni se borran (solo se cierran), una lista
ordenada es más sencilla y sirve igual.

**R3. Rango.** La misma lista ordenada: búsqueda binaria hasta `desde` y se
avanza hasta pasar `hasta`. **O(log n + m)**.

**R4. Próximo bus.** Tabla hash `"ruta|estación"` → lista de horas ordenada.
Búsqueda binaria de la primera hora ≥ la pedida. Las horas van como texto
`"HH:MM"` con dos dígitos, así que se comparan bien como texto.
**O(P + log h)** (P por revisar que la ruta para ahí). Descartamos recorrer
todos los horarios: O(h), y las troncales tienen cientos.

**R5. Planear un viaje.** Dos pasos:
1. Desde el origen avanzamos por cada ruta que pasa por ahí y anotamos en una
   tabla hash cuántas paradas toma llegar a cada estación. Si llegamos al
   destino, es un viaje directo.
2. Desde el destino retrocedemos por cada ruta que llega ahí. Si una estación
   abierta también se alcanzó en el paso 1 con otra ruta, se puede
   transbordar ahí. Nos quedamos con el viaje de menos paradas.

Descartamos probar todas las parejas de rutas porque es mucho más lento. El
bus sí pasa por una estación cerrada (y cuenta como parada), pero ahí nadie
sube, baja ni transborda.

**R6. Ranking.** Cada estación guarda cuántos buses paran ahí al día. La
lista ordenada (merge sort) se guarda y solo se vuelve a ordenar si hubo un
cambio. Así la consulta normal es **O(k)**, y **O(n log n)** la primera vez
después de un cambio. Descartamos ordenar en cada consulta porque se
consulta mucho y cambia poco.

**R7. Editar rutas.** Cada ruta es una lista de estaciones. Para agregar,
buscamos la posición y corremos los demás una casilla; para quitar, los
corremos al otro lado. **O(P)**. Recorrido al revés: **O(P)**. Una lista
doblemente enlazada lo haría en O(1), pero es más difícil y las rutas son
cortas (máximo 33 paradas en estos datos).

**R8. Cerrar y reabrir.** Se cambia el True/False en la tabla hash: **O(1)**.
Las demás funciones revisan ese valor, así que la estación cerrada
desaparece de búsquedas, rangos, ranking y viajes.

**R9. Deshacer y rehacer.** Dos pilas (listas con `append` y `pop`). Cada
cambio se guarda como una tupla, por ejemplo `("cerrar", "CALLE 26")`.
Deshacer saca el último y hace lo contrario. Un cambio nuevo vacía la pila
de rehacer. **O(1)** para cerrar/reabrir y **O(P)** para las rutas.
Descartamos guardar una copia de toda la red en cada cambio: O(n).

**R10. Fila de abordaje.** Una cola: lista donde se agrega al final y un
índice `frente` marca quién sigue. No usamos `pop(0)` porque corre a todos
los pasajeros cada vez y quedaría O(p²). **O(p)**. Si las llegadas vienen
desordenadas, primero se ordenan con merge sort: O(p log p).

## Los datos

`datos/` tiene 147 estaciones, 181 rutas y unos 140.000 horarios. Cada ruta
va en un solo sentido (por ejemplo `B10-1` y `B10-2`). Decisiones del script
de conversión:

- Nombres en mayúsculas y sin tildes. Los vagones se juntan en una estación.
- Se usa un solo día de servicio (el que tiene más viajes).
- Las horas como `25:10` son buses que pasan después de medianoche. Se
  guardan con la hora del reloj: `25:10` → `01:10`.

## Panel de rendimiento (R11)

Pestaña **Rendimiento** de la app. Mide con redes de 1000, 2000, 4000 y
8000 estaciones y dibuja lo medido junto a lo esperado. Una corrida
(microsegundos por llamada):

| Operación | Esperado | n=1000 | n=8000 |
| --- | --- | --- | --- |
| R1 estado | O(1) | 1.6 | 2.1 |
| R2 autocompletar | O(log n + k) | 7.3 | 8.1 |
| R3 rango | O(log n + m) | 12.9 | 12.0 |
| R4 proximo_bus | O(P + log h) | 4.2 | 4.0 |
| R6 ranking | O(k) | 0.1 | 0.1 |
| R7 agregar y quitar | O(P) | 10.4 | 12.2 |
| R8 cerrar y reabrir | O(1) | 5.0 | 5.6 |
| R10 simular_fila | O(p) | 9 569 | 89 389 |

Al multiplicar n por 8, casi todo queda igual (como se esperaba) y la fila
crece unas 9 veces porque tiene 8 veces más pasajeros (lineal). Las
diferencias pequeñas son ruido del computador.
