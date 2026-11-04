# App del planeador. Solo muestra cosas y llama al motor:
# todas las reglas del sistema están en motor/.
#
# Uso:
#   pip install streamlit
#   streamlit run app.py
#
# Streamlit vuelve a correr este archivo de arriba a abajo cada vez que el
# usuario toca algo. Por eso la red se guarda en st.session_state: así no se
# vuelve a cargar y no se pierden los cambios (cierres, ediciones, etc.).

import random

import streamlit as st

from motor import Red, simular_fila
import rendimiento

st.set_page_config(page_title="Planeador TransMilenio")
st.title("Planeador TransMilenio")

if "red" not in st.session_state:
    st.session_state.red = Red("datos")
red = st.session_state.red

pestanas = st.tabs(["Buscar", "Rango", "Próximo bus", "Viaje", "Ranking",
                    "Operar", "Fila", "Rendimiento"])

# ---------- R1 y R2 ----------
with pestanas[0]:
    texto = st.text_input("Escribe una estación", "CAL")
    sugerencias = red.autocompletar(texto, 8)
    if len(sugerencias) > 0:
        st.write("Sugerencias: " + ", ".join(sugerencias))
    existe, abierta = red.estado(texto)
    if not existe:
        st.info(f"{texto.upper()} no es el nombre exacto de una estación.")
    elif abierta:
        st.success(f"{texto.upper()} existe y está abierta.")
    else:
        st.warning(f"{texto.upper()} existe pero está cerrada.")

# ---------- R3 ----------
with pestanas[1]:
    desde = st.text_input("Desde", "CALLE 26")
    hasta = st.text_input("Hasta", "CALLE 80")
    st.write(red.rango(desde, hasta))

# ---------- R4 ----------
with pestanas[2]:
    estacion = st.selectbox("Estación", red.nombres, key="bus_estacion")
    rutas = red.rutas_de.obtener(estacion)
    ruta = st.selectbox("Ruta", rutas)
    hora = st.text_input("Hora (HH:MM)", "07:00")
    if ruta is not None:
        siguiente = red.proximo_bus(estacion, ruta, hora)
        if siguiente is None:
            st.warning("No pasan más buses de esa ruta hoy, o la estación está cerrada.")
        else:
            st.success(f"El próximo bus de la ruta {ruta} pasa a las {siguiente}.")

# ---------- R5 ----------
with pestanas[3]:
    origen = st.selectbox("Origen", red.nombres, index=red.nombres.index("PORTAL NORTE"))
    destino = st.selectbox("Destino", red.nombres, index=red.nombres.index("PORTAL SUR"))
    tramos = red.viaje(origen, destino)
    if tramos is None:
        st.warning("No hay viaje directo ni con un solo transbordo.")
    elif len(tramos) == 0:
        st.info("Ya estás en el destino.")
    else:
        for ruta, sube, baja, paradas in tramos:
            st.write(f"Toma la ruta **{ruta}** en {sube} y bájate en {baja} ({paradas} paradas).")

# ---------- R6 ----------
with pestanas[4]:
    k = st.number_input("¿Cuántas estaciones?", 1, 50, 10)
    tabla = []
    for nombre, buses in red.ranking(k):
        tabla.append({"Estación": nombre, "Buses al día": buses})
    st.table(tabla)

# ---------- R7, R8 y R9 ----------
with pestanas[5]:
    st.subheader("Recorrido de una ruta")
    todas_las_rutas = sorted([par[0] for par in red.rutas.pares()])
    ruta = st.selectbox("Ruta", todas_las_rutas, key="op_ruta")
    al_reves = st.checkbox("Ver al revés")
    st.write(" → ".join(red.recorrido(ruta, al_reves)))

    st.subheader("Editar la ruta")
    parada = st.selectbox("Estación", red.nombres, key="op_parada")
    despues = st.selectbox("Después de", ["(al inicio)"] + red.recorrido(ruta))
    if despues == "(al inicio)":
        despues = None
    col1, col2 = st.columns(2)
    if col1.button("Agregar parada"):
        st.write("Listo." if red.agregar_parada(ruta, parada, despues) else "No se pudo.")
    if col2.button("Quitar parada"):
        st.write("Listo." if red.quitar_parada(ruta, parada) else "Esa estación no está en la ruta.")

    st.subheader("Cerrar o reabrir")
    cual = st.selectbox("Estación", red.nombres, key="op_cerrar")
    col1, col2 = st.columns(2)
    if col1.button("Cerrar"):
        st.write("Cerrada." if red.cerrar(cual) else "Ya estaba cerrada.")
    if col2.button("Reabrir"):
        st.write("Reabierta." if red.reabrir(cual) else "Ya estaba abierta.")

    st.subheader("Historial")
    col1, col2 = st.columns(2)
    if col1.button("Deshacer"):
        st.write("Se deshizo el último cambio." if red.deshacer() else "No hay nada para deshacer.")
    if col2.button("Rehacer"):
        st.write("Se rehízo." if red.rehacer() else "No hay nada para rehacer.")

# ---------- R10 ----------
with pestanas[6]:
    pasajeros = st.number_input("Pasajeros", 1, 1000000, 20000)
    minutos = st.number_input("Llegan entre el minuto 0 y el", 1, 1000, 120)
    frecuencia = st.number_input("Sale un bus cada (minutos)", 1, 60, 1)
    capacidad = st.number_input("Cupo de cada bus", 1, 500, 160)
    if st.button("Simular"):
        llegadas = [random.randrange(minutos) for i in range(pasajeros)]
        llegadas.sort()
        salidas = simular_fila(llegadas, frecuencia, capacidad)
        esperas = [salidas[i] - llegadas[i] for i in range(pasajeros)]
        st.write(f"Espera promedio: {sum(esperas) / pasajeros:.1f} minutos")
        st.write(f"Espera máxima: {max(esperas)} minutos")

# ---------- R11 ----------
with pestanas[7]:
    st.write("Mide cada operación con redes de 1000, 2000, 4000 y 8000 estaciones. "
             "Si una operación es O(1) u O(log n), la línea debe quedar casi plana; "
             "si es O(n), debe duplicarse cada vez que n se duplica. La línea "
             "'esperado' es la complejidad que calculamos, empezando en el primer punto medido.")
    if st.button("Medir"):
        resultados = rendimiento.medir()
        for operacion, esperado in rendimiento.ESPERADO.items():
            st.subheader(f"{operacion}  (esperado {esperado})")
            medido = [r[operacion] for r in resultados]
            datos = {"n": rendimiento.TAMANOS,
                     "medido": medido,
                     "esperado": rendimiento.curva_esperada(esperado, medido[0])}
            st.line_chart(datos, x="n", y=["medido", "esperado"])
