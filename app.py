import streamlit as st
import pandas as pd
import math
import matplotlib.pyplot as plt
import plotly.express as px  # <-- Nueva librería para el gráfico dinámico

st.set_page_config(page_title="RTL–MC PRECISO PRO", layout="wide")
st.title("🧭 RTL–MC PRECISO PRO")
# =========================================================
# FUNCIONES
# =========================================================

def cargar_archivo(file):
    if file.name.endswith(".xlsx"):
        return pd.read_excel(file, dtype=str)
    else:
        return pd.read_csv(file, dtype=str)

def f(v):
    return f"{v:.2f}".replace(".", ",")

def clasificar_sentido(ang):
    if ang < 22.5:
        return "norte"
    elif ang < 67.5:
        return "noreste"
    elif ang < 112.5:
        return "este"
    elif ang < 157.5:
        return "sureste"
    elif ang < 202.5:
        return "sur"
    elif ang < 247.5:
        return "suroeste"
    elif ang < 292.5:
        return "oeste"
    elif ang < 337.5:
        return "noroeste"
    else:
        return "norte"

# =========================================================
# CARGA
# =========================================================

puntos_file = st.file_uploader("📌 Tabla de puntos", type=["xlsx", "csv"])
lineas_file = st.file_uploader("📐 Tabla de líneas", type=["xlsx", "csv"])
# =========================================================
# PROCESO
# =========================================================

if puntos_file and lineas_file:

    df_p = cargar_archivo(puntos_file)
    df_l = cargar_archivo(lineas_file)

    cons = st.selectbox("🔍 CONSECUTIVO", df_p["CONSECUTIVO"].unique())

    df_p = df_p[df_p["CONSECUTIVO"] == cons]
    df_l = df_l[df_l["CONSECUTIVO"] == cons]

    # ---------------- LIMPIEZA ----------------
    df_p["ORDEN"] = df_p["ORDEN"].astype(int)
    df_p = df_p.sort_values("ORDEN")

    df_p["NORTE"] = df_p["Y"].str.replace(",", ".").astype(float)
    df_p["ESTE"] = df_p["X"].str.replace(",", ".").astype(float)
    df_p["PUNTO"] = df_p["ORDEN"].astype(str).str.zfill(2)

    df_l["ORDEN"] = df_l["ORDEN"].astype(int)
    df_l = df_l.sort_values("ORDEN")

    df_l["LONGITUD"] = df_l["LONGITUD"].str.replace(",", ".").astype(float)
    df_l["COL"] = df_l["NOM_COLINDANTE"].str.strip()

    puntos = df_p["PUNTO"].tolist()
    coords = {r["PUNTO"]: (r["NORTE"], r["ESTE"]) for _, r in df_p.iterrows()}

    # =====================================================
    # VISUALIZACIÓN DINÁMICA (NUEVO CON PLOTLY)
    # =====================================================

    st.markdown("### 🗺️ Visualización Dinámica del Polígono")

    # Duplicamos temporalmente los puntos para cerrar el polígono visual en el gráfico
    df_plot = df_p.copy()
    first_point = df_plot.iloc[[0]]
    df_plot_closed = pd.concat([df_plot, first_point], ignore_index=True)

    # Crear gráfico interactivo
    fig = px.scatter(
        df_plot_closed,
        x="ESTE",
        y="NORTE",
        text="PUNTO",
        hover_data=["PUNTO", "NORTE", "ESTE"]
    )

    # Estilo de líneas, vértices y etiquetas
    fig.update_traces(
        mode='lines+markers+text',
        marker=dict(size=9, symbol='circle', color='#1f77b4', line=dict(width=1, color='DarkSlateGrey')),
        line=dict(color='#ff7f0e', width=3),
        textposition='top right',
        textfont=dict(size=11, color='black'),
        selector=dict(type='scatter')
    )

    # Ajustes de diseño y Relación de Aspecto 1:1 (Evita distorsión topográfica)
    fig.update_layout(
        title_text=f"Polígono del Predio - Consecutivo: {cons}",
        xaxis=dict(tickformat=",.1f", title_text="Este (X) [m]"),
        yaxis=dict(tickformat=",.1f", title_text="Norte (Y) [m]", scaleanchor="x", scaleratio=1),
        margin=dict(l=40, r=40, b=40, t=80),
        paper_bgcolor="#f8f9fb",
        plot_bgcolor="white",
        hovermode="closest",
        dragmode='pan'
    )

    # Configuración de herramientas del gráfico
    config = {
        'displaylogo': False,
        'modeBarButtonsToRemove': ['lasso2d', 'select2d', 'autoScale2d', 'toggleSpikelines'],
        'scrollZoom': True
    }

    # Desplegar en Streamlit
    st.plotly_chart(fig, use_container_width=True, config=config)

    # =====================================================
    # TRAMOS
    # =====================================================

    tramos = []

    for i in range(len(puntos)):
        p1 = puntos[i]
        p2 = puntos[(i + 1) % len(puntos)]

        N1, E1 = coords[p1]
        N2, E2 = coords[p2]

        dx = E2 - E1
        dy = N2 - N1

        ang = math.degrees(math.atan2(dx, dy)) % 360

        dist_calc = round(math.sqrt((N2 - N1)**2 + (E2 - E1)**2), 1)
        dist_tab = df_l.iloc[i]["LONGITUD"]
        dif = round(abs(dist_calc - dist_tab), 1)

        tramos.append({
            "INI": p1,
            "FIN": p2,
            "ANGULO": ang,
            "DIST_CALC": dist_calc,
            "DIST_TAB": dist_tab,
            "DIF": dif,
            "ESTADO": "✅ OK" if dif == 0 else "❌ ERROR",
            "CARD": df_l.iloc[i]["CARDINALDIAD"],
            "COL": df_l.iloc[i]["COL"],
            "COND": df_l.iloc[i]["OBSERVACIONES"],
            "NPN": df_l.iloc[i]["NPN_COLINDANTE"],
            "FMI": df_l.iloc[i]["FMI_COLINDANTE"],
            "TIT": df_l.iloc[i]["NOMBRE_PREDIO_COL"]
        })

    df_tramos = pd.DataFrame(tramos)

    # =====================================================
    # QUIEBRES
    # =====================================================

    bloques = []
    actual = [df_tramos.iloc[0]]

    for i in range(1, len(df_tramos)):

        t = df_tramos.iloc[i]
        u = actual[-1]

        if (
            t["CARD"] == u["CARD"] and
            t["COL"] == u["COL"] and
            str(t["NPN"]).strip() == str(u["NPN"]).strip() and
            str(t["FMI"]).strip() == str(u["FMI"]).strip()
        ):
            actual.append(t)
        else:
            bloques.append(actual)
            actual = [t]

    bloques.append(actual)

    # =====================================================
    # TABLAS
    # =====================================================

    st.subheader("📍 Coordenadas de puntos")
    st.dataframe(df_p[["PUNTO", "NORTE", "ESTE"]])

    st.subheader("📐 Tramos técnicos")
    st.dataframe(df_tramos)

    # =====================================================
    # RTL FINAL (CORRECTO)
    # =====================================================

    salida = "LINDEROS TÉCNICOS\n\n"
    orden = df_p["PUNTO"].tolist()

    card_actual = None
    contador_lindero = 1

    for b in bloques:

        card = b[0]["CARD"]

        if card != card_actual:
            salida += f"POR EL {card}:\n\n"
            card_actual = card

        salida += f"Lindero {contador_lindero}:\n"

        p_ini = b[0]["INI"]
        p_fin = b[-1]["FIN"]

        i1 = orden.index(p_ini)
        i2 = orden.index(p_fin)

        if i2 > i1:
            inter = orden[i1+1:i2]
            ruta = orden[i1:i2]
        else:
            inter = orden[i1+1:] + orden[:i2]
            ruta = orden[i1:] + orden[:i2]

        texto_int = ""

        if len(inter) == 1:
            p = inter[0]
            N, E = coords[p]
            texto_int = f"pasando por el punto de coordenadas; punto {p} N= {f(N)} m, E= {f(E)} m; "

        elif len(inter) > 1:
            texto_int = "pasando por los puntos de coordenadas "
            for p in inter:
                N, E = coords[p]
                texto_int += f"punto {p} N= {f(N)} m, E= {f(E)} m, "
            texto_int = texto_int.rstrip(", ") + "; "

        dist = round(sum(df_l.iloc[orden.index(p)]["LONGITUD"] for p in ruta), 1)
        dist_txt = str(dist).replace(".", ",")

        tipo = "recta" if len(inter) == 0 else "quebrada"
        sentido = clasificar_sentido(b[0]["ANGULO"])

        N_ini, E_ini = coords[p_ini]
        N_fin, E_fin = coords[p_fin]

        salida += (
            f"Inicia en el punto {p_ini} con coordenadas planas N= {f(N_ini)} m, E= {f(E_ini)} m, "
            f"en línea {tipo} en sentido {sentido}, "
            f"{texto_int}"
            f"en una distancia de {dist_txt} m, hasta encontrar el punto número {p_fin} "
            f"de coordenadas planas N= {f(N_fin)} m, E= {f(E_fin)} m"
        )

        fila = b[-1]

        salida += f"; colindando con {fila['COL']}"

        if str(fila["COND"]).upper() == "TRASLAPA":
            salida += f", que traslapa con el Numero Predial nacional {fila['NPN']}"
        elif str(fila["COND"]).upper() == "CORRESPONDE":
            salida += f", que corresponde con el Numero Predial nacional {fila['NPN']}"

        salida += f", Folio de matrícula inmobiliaria {fila['FMI']}"
        salida += f" y catastralmente a nombre de {fila['TIT']}.\n\n"

        contador_lindero += 1

    salida = salida.strip() + " y encierra"

    st.text_area("📄 RTL FINAL", salida, height=600)
