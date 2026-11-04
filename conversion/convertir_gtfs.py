"""Convierte el GTFS de TransMilenio a los tres CSV que lee el motor.

Uso:
    python conversion/convertir_gtfs.py ruta/al/gtfs.zip datos/

Aquí se puede usar cualquier librería (está fuera de motor/), así que se usa
pandas.

Decisiones de la conversión:
- Nombres: mayúsculas, sin tildes y sin espacios repetidos. Si una parada
  tiene parent_station, se usa el nombre de la estación padre, para que los
  vagones de una misma estación cuenten como una sola.
- Rutas: cada combinación de route_short_name con una secuencia de paradas
  distinta es una ruta en un solo sentido. Se numeran -1, -2, ... de la que
  tiene más viajes a la que tiene menos (por ejemplo B10-1, B10-2).
- Día: se usa solo el service_id con más viajes (un día hábil típico), para
  que "buses al día" tenga sentido.
- Horas >= 24 (por ejemplo 25:10): son buses que salen después de medianoche
  del mismo día de servicio. Se guardan como la hora real del reloj
  (25:10 -> 01:10), porque el usuario pregunta por la hora que ve en el reloj.
"""

import sys
import unicodedata
import zipfile
from pathlib import Path

import pandas as pd


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.upper().split())


def hora_reloj(hora_gtfs):
    h, m = str(hora_gtfs).strip().split(":")[:2]
    return f"{int(h) % 24:02d}:{int(m):02d}"


def leer(zip_gtfs, nombre):
    with zipfile.ZipFile(zip_gtfs) as z:
        with z.open(nombre) as f:
            return pd.read_csv(f, dtype=str, keep_default_na=False)


def convertir(zip_gtfs, salida):
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)

    stops = leer(zip_gtfs, "stops.txt")
    routes = leer(zip_gtfs, "routes.txt")
    trips = leer(zip_gtfs, "trips.txt")
    stop_times = leer(zip_gtfs, "stop_times.txt")

    # 1. Nombre de estación de cada stop_id (usando la estación padre).
    nombre_de = dict(zip(stops["stop_id"], stops["stop_name"].map(normalizar)))
    if "parent_station" in stops.columns:
        padre = dict(zip(stops["stop_id"], stops["parent_station"]))
        for sid in list(nombre_de):
            if padre.get(sid) and padre[sid] in nombre_de:
                nombre_de[sid] = nombre_de[padre[sid]]
    stop_times["estacion"] = stop_times["stop_id"].map(nombre_de)

    # 2. Un solo día de servicio: el service_id con más viajes.
    servicio = trips["service_id"].value_counts().idxmax()
    trips = trips[trips["service_id"] == servicio]
    nombre_ruta = dict(zip(routes["route_id"], routes["route_short_name"]))
    trips = trips.assign(corto=trips["route_id"].map(nombre_ruta).map(normalizar))

    st = stop_times[stop_times["trip_id"].isin(trips["trip_id"])].copy()
    st["stop_sequence"] = st["stop_sequence"].astype(int)
    st = st.sort_values(["trip_id", "stop_sequence"])
    # Quitar paradas seguidas en la misma estación (dos vagones seguidos).
    st = st[st["estacion"] != st.groupby("trip_id")["estacion"].shift()]

    # 3. Patrón (secuencia de estaciones) de cada viaje.
    patron = st.groupby("trip_id")["estacion"].apply(tuple).rename("patron")
    trips = trips.join(patron, on="trip_id").dropna(subset=["patron"])

    filas_rutas, filas_horarios = [], []
    for corto, grupo in trips.groupby("corto"):
        conteo = grupo["patron"].value_counts()
        for numero, (pat, _) in enumerate(conteo.items(), start=1):
            if len(pat) < 2 or len(set(pat)) != len(pat):
                continue  # ruta circular o de una parada: no sirve
            ruta = f"{corto}-{numero}"
            for orden, est in enumerate(pat, start=1):
                filas_rutas.append((ruta, orden, est))
            ids = grupo.loc[grupo["patron"] == pat, "trip_id"]
            tiempos = st[st["trip_id"].isin(ids)]
            columna = "departure_time" if "departure_time" in st else "arrival_time"
            for est, hora in zip(tiempos["estacion"], tiempos[columna]):
                if hora:
                    filas_horarios.append((ruta, est, hora_reloj(hora)))

    df_rutas = pd.DataFrame(filas_rutas, columns=["ruta", "orden", "estacion"])
    df_horarios = pd.DataFrame(filas_horarios, columns=["ruta", "estacion", "hora"])
    estaciones = sorted(set(df_rutas["estacion"]))
    pd.DataFrame({"nombre": estaciones}).to_csv(salida / "estaciones.csv", index=False)
    df_rutas.to_csv(salida / "rutas.csv", index=False)
    df_horarios.to_csv(salida / "horarios.csv", index=False)
    print(f"{len(estaciones)} estaciones, {df_rutas['ruta'].nunique()} rutas, "
          f"{len(df_horarios)} horarios -> {salida}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    convertir(sys.argv[1], sys.argv[2])
