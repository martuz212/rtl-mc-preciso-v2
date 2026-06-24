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
    # VISUALIZACIÓN
    # =====================================================

    st.markdown("### 🗺️ Visualización del polígono")

    x, y = [], []

    for p in puntos:
        N, E = coords[p]
        x.append(E)
        y.append(N)

    x.append(x[0])
    y.append(y[0])

    fig, ax = plt.subplots()
    ax.plot(x, y, marker='o')

    for i, p in enumerate(puntos):
        ax.text(x[i], y[i], p)

    st.pyplot(fig)

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
bloques.append(actual)

    # =====================================================
    # ✅ VALIDADOR PRO POR LINDERO
    # =====================================================

    val_linderos = []

    for i, b in enumerate(bloques):

        dist_calc_sum = sum(x["DIST_CALC"] for x in b)
        dist_tab_sum = sum(x["DIST_TAB"] for x in b)

        diff = dist_calc_sum - dist_tab_sum

        if dist_calc_sum != 0:
            error_pct = (diff / dist_calc_sum) * 100
        else:
            error_pct = 0

        val_linderos.append({
            "LINDERO": i + 1,
            "DIST_CALC (m)": round(dist_calc_sum, 2),
            "DIST_RTL (m)": round(dist_tab_sum, 2),
            "DIF (m)": round(diff, 2),
            "% ERROR": round(error_pct, 2),
            "ESTADO": "✅ OK" if abs(diff) <= 0.1 else "❌ ERROR"
        })

    df_val = pd.DataFrame(val_linderos)

    errores = df_val[df_val["ESTADO"] == "❌ ERROR"]

    if len(errores) > 0:
        estado_global = "❌ RTL NO VIABLE"
    else:
        estado_global = "✅ RTL APROBADO"

    st.subheader("🧠 Validación por Linderos (MC PRECISO)")
    st.dataframe(df_val)

    st.markdown(f"### Resultado global: {estado_global}")

    # =====================================================
    # TABLAS
    # =====================================================

    st.subheader("📍 Coordenadas de puntos")
    st.dataframe(df_p[["PUNTO", "NORTE", "ESTE"]])

    st.subheader("📐 Tramos técnicos")
    st.dataframe(df_tramos)

    # =====================================================
    # RTL FINAL (CONTINÚA IGAC REAL)
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

        segmento = [b[0]]
        primera = True

        for t in b[1:]:

            prev = segmento[-1]

            delta = abs(t["ANGULO"] - prev["ANGULO"])
            if delta > 180:
                delta = 360 - delta

            dist_acum = sum(x["DIST_TAB"] for x in segmento)
# ✅ REGLA IGAC AJUSTADA (EVITA SOBRE-FRAGMENTACIÓN)

            cond_quiebre = delta > 15
            cond_longitud = dist_acum > 300
            cond_densidad = len(segmento) >= 5

            if cond_longitud or cond_densidad or (cond_quiebre and dist_acum > 120):

                p_ini = segmento[0]["INI"]
                p_fin = segmento[-1]["FIN"]

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
                    N,E = coords[p]
                    texto_int = f"pasando por el punto de coordenadas punto {p} N= {f(N)} m, E= {f(E)} m, "

                elif len(inter) > 1:
                    texto_int = "pasando por los puntos de coordenadas "
                    for p in inter:
                        N,E = coords[p]
                        texto_int += f"punto {p} N= {f(N)} m, E= {f(E)} m, "

                dist = round(sum(x["DIST_TAB"] for x in segmento), 1)
                dist_txt = str(dist).replace(".", ",")

                tipo = "recta" if len(segmento) == 1 else "quebrada"
                sentido = clasificar_sentido(segmento[0]["ANGULO"])

                N_ini,E_ini = coords[p_ini]
                N_fin,E_fin = coords[p_fin]

                if primera:
                    salida += (
                        f"Inicia en el punto {p_ini} con coordenadas planas N= {f(N_ini)} m, E= {f(E_ini)} m, "
                        f"en línea {tipo} en sentido {sentido}, "
                        f"{texto_int}"
                        f"en una distancia de {dist_txt} m, hasta encontrar el punto {p_fin} "
                        f"con coordenadas planas N= {f(N_fin)} m, E= {f(E_fin)} m.\n"
                    )
                    primera = False
                else:
                    salida += (
                        f"Continúa en el punto {p_ini} con coordenadas planas N= {f(N_ini)} m, E= {f(E_ini)} m, "
                        f"en línea {tipo} en sentido {sentido}, "
                        f"{texto_int}"
                        f"en una distancia de {dist_txt} m, hasta encontrar el punto {p_fin} "
                        f"con coordenadas planas N= {f(N_fin)} m, E= {f(E_fin)} m.\n"
                    )

                segmento = [t]

            else:
                segmento.append(t)

        # ✅ ÚLTIMO SEGMENTO
        if segmento:

            p_ini = segmento[0]["INI"]
            p_fin = segmento[-1]["FIN"]

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
                N,E = coords[p]
                texto_int = f"pasando por el punto de coordenadas punto {p} N= {f(N)} m, E= {f(E)} m, "

            elif len(inter) > 1:
                texto_int = "pasando por los puntos de coordenadas "
                for p in inter:
                    N,E = coords[p]
                    texto_int += f"punto {p} N= {f(N)} m, E= {f(E)} m, "

            dist = round(sum(x["DIST_TAB"] for x in segmento), 1)
            dist_txt = str(dist).replace(".", ",")

            tipo = "recta" if len(segmento) == 1 else "quebrada"
            sentido = clasificar_sentido(segmento[0]["ANGULO"])

            N_ini,E_ini = coords[p_ini]
            N_fin,E_fin = coords[p_fin]

            if primera:
                salida += (
                    f"Inicia en el punto {p_ini} con coordenadas planas N= {f(N_ini)} m, E= {f(E_ini)} m, "
                    f"en línea {tipo} en sentido {sentido}, "
                    f"{texto_int}"
                    f"en una distancia de {dist_txt} m, hasta encontrar el punto {p_fin} "
                    f"con coordenadas planas N= {f(N_fin)} m, E= {f(E_fin)} m.\n"
                )
            else:
                salida += (
                    f"Continúa en el punto {p_ini} con coordenadas planas N= {f(N_ini)} m, E= {f(E_ini)} m, "
                    f"en línea {tipo} en sentido {sentido}, "
                    f"{texto_int}"
                    f"en una distancia de {dist_txt} m, hasta encontrar el punto {p_fin} "
                    f"con coordenadas planas N= {f(N_fin)} m, E= {f(E_fin)} m.\n"
                )

        # ✅ COLINDANTE FINAL
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
