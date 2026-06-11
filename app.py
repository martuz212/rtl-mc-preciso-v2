import streamlit as st
import pandas as pd
import math
import matplotlib.pyplot as plt

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

# ✅ coordenadas a 2 decimales
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

    coords = {r["PUNTO"]:(r["NORTE"],r["ESTE"]) for _,r in df_p.iterrows()}

    # =====================================================
    # VISUALIZACIÓN
    # =====================================================

    st.markdown("### 🗺️ Visualización del polígono")

    x,y = [],[]

    for p in puntos:
        N,E = coords[p]
        x.append(E)
        y.append(N)

    x.append(x[0])
    y.append(y[0])

    fig, ax = plt.subplots()
    ax.plot(x, y, marker='o')

    for i,p in enumerate(puntos):
        ax.text(x[i], y[i], p)

    st.pyplot(fig)

    # =====================================================
    # TRAMOS
    # =====================================================

    tramos = []

    for i in range(len(puntos)):

        p1 = puntos[i]
        p2 = puntos[(i+1)%len(puntos)]

        N1,E1 = coords[p1]
        N2,E2 = coords[p2]

        dx = E2 - E1
        dy = N2 - N1

        ang = math.degrees(math.atan2(dx, dy)) % 360

        dist_calc = round(math.sqrt((N2-N1)**2 + (E2-E1)**2),1)
        dist_tab = df_l.iloc[i]["LONGITUD"]
        dif = round(abs(dist_calc - dist_tab),1)

        tramos.append({
            "INI":p1,
            "FIN":p2,
            "ANGULO":ang,
            "DIST_CALC":dist_calc,
            "DIST_TAB":dist_tab,
            "DIF":dif,
            "ESTADO":"✅ OK" if dif==0 else "❌ ERROR",
            "CARD":df_l.iloc[i]["CARDINALDIAD"],
            "COL":df_l.iloc[i]["COL"],
            "COND":df_l.iloc[i]["OBSERVACIONES"],
            "NPN":df_l.iloc[i]["NPN_COLINDANTE"],
            "FMI":df_l.iloc[i]["FMI_COLINDANTE"],
            "TIT":df_l.iloc[i]["NOMBRE_PREDIO_COL"]
        })

    df_tramos = pd.DataFrame(tramos)

    # =====================================================
    # QUIEBRES
    # =====================================================

    bloques = []
    actual = [df_tramos.iloc[0]]

    for i in range(1,len(df_tramos)):

        t = df_tramos.iloc[i]
        u = actual[-1]

        delta = abs(t["ANGULO"] - u["ANGULO"])
        if delta > 180:
            delta = 360 - delta

        if (
            t["CARD"]==u["CARD"] and
            t["COL"]==u["COL"] and
            delta < 30
        ):
            actual.append(t)
        else:
            bloques.append(actual)
            actual = [t]

    bloques.append(actual)

    # =====================================================
    # TABLAS
    # =====================================================

    # 🔥 TABLA DE COORDENADAS (PUNTOS)
    st.subheader("📍 Coordenadas de puntos")
    st.dataframe(
        df_p[[
            "PUNTO",
            "NORTE",
            "ESTE"
        ]]
    )

    # 🔥 TABLA DE TRAMOS
    st.subheader("📐 Tramos técnicos")
    st.dataframe(df_tramos)

    # 🔥 TABLA DE LINDEROS
    info = []
    for i, b in enumerate(bloques, 1):
        info.append({
            "LINDERO": i,
            "INI": b[0]["INI"],
            "FIN": b[-1]["FIN"],
            "CARD": b[0]["CARD"],
            "COL": b[0]["COL"]
        })

    st.subheader("📊 Linderos agrupados")
    st.dataframe(pd.DataFrame(info))


# =====================================================
# RTL FINAL
# =====================================================

    salida = "LINDEROS TÉCNICOS\n\n"
    orden = df_p["PUNTO"].tolist()

    card_actual = None

    # ✅ contador de linderos
    contador_lindero = 1

    for b in bloques:

        card = b[0]["CARD"]

        if card != card_actual:
            salida += f"POR EL {card}:\n\n"
            card_actual = card

        # ✅ LINDERO
        salida += f"Lindero {contador_lindero}:\n"

        p_ini = b[0]["INI"]
        p_fin = b[-1]["FIN"]

        # ---------------- sentido promedio (NO se toca)
        sen,cos = 0,0
        for t in b:
            ang_rad = math.radians(t["ANGULO"])
            sen += math.sin(ang_rad)
            cos += math.cos(ang_rad)

        ang = math.degrees(math.atan2(sen, cos)) % 360
        sentido = clasificar_sentido(ang)

        i1 = orden.index(p_ini)
        i2 = orden.index(p_fin)

        ruta = orden[i1:i2] if i2 > i1 else orden[i1:] + orden[:i2]

        tipo = "recta" if len(b) == 1 else "quebrada"

        # =====================================================
        # ✅ CONTINÚA 
        # =====================================================

        texto_int = ""
        prev_ang = None

        for i, tramo in enumerate(b):

            p = tramo["FIN"]
            N, E = coords[p]

            ang_tramo = tramo["ANGULO"]
            sentido_tramo = clasificar_sentido(ang_tramo)

            if i == 0:
                prev_ang = ang_tramo
                continue

            delta = abs(ang_tramo - prev_ang)
            if delta > 180:
                delta = 360 - delta

            if delta > 20:
                texto_int += (
                    f"continúa en sentido {sentido_tramo}, "
                    f"pasando por el punto de coordenadas punto {p} "
                    f"N= {f(N)} m, E= {f(E)} m, "
                )
            else:
                texto_int += (
                    f"punto {p} N= {f(N)} m, E= {f(E)} m, "
                )

            prev_ang = ang_tramo

        if texto_int != "":
            texto_int = texto_int.rstrip(", ") + ", "

        # -----------------------------------------------------

        dist = f(sum(df_l.iloc[orden.index(p)]["LONGITUD"] for p in ruta))

        N_ini,E_ini = coords[p_ini]
        N_fin,E_fin = coords[p_fin]

        texto = (
            f"Inicia en el punto {p_ini} con coordenadas planas N= {f(N_ini)} m, E= {f(E_ini)} m; "
            f"en línea {tipo}, en sentido {sentido}, {texto_int}"
            f"en una distancia de {dist} m, hasta encontrar el punto número {p_fin} "
            f"de coordenadas planas N= {f(N_fin)} m, E= {f(E_fin)} m"
        )

        fila = b[-1]

        col = str(fila["COL"]).strip()

        if col.upper() == "SIN INFORMACION":
            texto += "; colinda con un elemento sin información definida"

        elif any(x in col.lower() for x in ["rio", "río", "quebrada", "caño"]):
            texto += f"; colinda con el {col}"

        elif "carretera" in col.lower() or "via" in col.lower():
            texto += f"; colinda con la {col}"

        else:
            texto += f"; colinda con {col}"

        if str(fila["COND"]).upper() == "TRASLAPA":
            texto += f", que traslapa con el Número Predial Nacional {fila['NPN']}, Folio de Matrícula Inmobiliaria {fila['FMI']}, y cuyo titular catastral es {fila['TIT']}."
        elif str(fila["COND"]).upper() == "CORRESPONDE":
            texto += f", que corresponde con el Número Predial Nacional {fila['NPN']}, Folio de Matrícula Inmobiliaria {fila['FMI']}, y cuyo titular catastral es {fila['TIT']}."
        else:
            texto += "."

        salida += texto + "\n\n"

        # ✅ incremento
        contador_lindero += 1

    st.text_area("📄 RTL FINAL", salida, height=600)
