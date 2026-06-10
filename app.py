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

def format_dist(x):
    return str(round(x, 1)).replace(".", ",")

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

    df_p["PUNTO"] = df_p["ORDEN"].astype(str).str.zfill(2)

    # ✅ coordenadas doble manejo
    df_p["NORTE"] = df_p["Y"].str.replace(",", ".").astype(float)
    df_p["ESTE"] = df_p["X"].str.replace(",", ".").astype(float)

    df_p["NORTE_TXT"] = df_p["Y"]
    df_p["ESTE_TXT"] = df_p["X"]

    df_l["ORDEN"] = df_l["ORDEN"].astype(int)
    df_l = df_l.sort_values("ORDEN")

    df_l["LONGITUD"] = df_l["LONGITUD"].str.replace(",", ".").astype(float)
    df_l["COL"] = df_l["NOM_COLINDANTE"].str.strip()

    puntos = df_p["PUNTO"].tolist()

    coords = {
        r["PUNTO"]: {
            "N": r["NORTE"],
            "E": r["ESTE"],
            "N_txt": r["NORTE_TXT"],
            "E_txt": r["ESTE_TXT"]
        }
        for _, r in df_p.iterrows()
    }

    # =====================================================
    # VISUALIZACIÓN
    # =====================================================

    st.markdown("### 🗺️ Polígono")

    x, y = [], []
    for p in puntos:
        x.append(coords[p]["E"])
        y.append(coords[p]["N"])

    x.append(x[0])
    y.append(y[0])

    fig, ax = plt.subplots()
    ax.plot(x, y, marker='o')

    for i, p in enumerate(puntos):
        ax.text(x[i], y[i], p)

    st.pyplot(fig)

    # =====================================================
    # TRAMOS + VALIDACIÓN
    # =====================================================

    tramos = []

    for i in range(len(puntos)):

        p1 = puntos[i]
        p2 = puntos[(i+1)%len(puntos)]

        N1 = coords[p1]["N"]
        E1 = coords[p1]["E"]
        N2 = coords[p2]["N"]
        E2 = coords[p2]["E"]

        dx = E2 - E1
        dy = N2 - N1

        ang = math.degrees(math.atan2(dx, dy)) % 360

        dist_calc = round(math.sqrt((N2-N1)**2 + (E2-E1)**2),1)
        dist_tab = df_l.iloc[i]["LONGITUD"]

        dif = round(abs(dist_calc - dist_tab),1)

        tramos.append({
            "INI":p1,
            "FIN":p2,
            "DIST_CALC":dist_calc,
            "DIST_TAB":dist_tab,
            "DIF":dif,
            "ESTADO":"✅ OK" if dif==0 else "❌ ERROR",
            "ANGULO":ang,
            "CARD":df_l.iloc[i]["CARDINALDIAD"],
            "COL":df_l.iloc[i]["COL"]
        })

    df_tramos = pd.DataFrame(tramos)

    st.subheader("📐 VALIDACIÓN DE DISTANCIAS")
    st.dataframe(df_tramos)

    # =====================================================
    # QUIEBRES REALES
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
    # RTL FINAL
    # =====================================================

    salida = "LINDEROS TÉCNICOS\n\n"
    orden = df_p["PUNTO"].tolist()

    card_actual = None

    for b in bloques:

        card = b[0]["CARD"]

        if card != card_actual:
            salida += f"POR EL {card}:\n\n"
            card_actual = card

        p_ini = b[0]["INI"]
        p_fin = b[-1]["FIN"]

        # ✅ sentido promedio real
        sen, cos = 0, 0
        for t in b:
            ang_rad = math.radians(t["ANGULO"])
            sen += math.sin(ang_rad)
            cos += math.cos(ang_rad)

        ang = math.degrees(math.atan2(sen, cos)) % 360
        sentido = clasificar_sentido(ang)

        i1 = orden.index(p_ini)
        i2 = orden.index(p_fin)

        ruta = orden[i1:i2] if i2>i1 else orden[i1:]+orden[:i2]
        inter = orden[i1+1:i2] if i2>i1 else orden[i1+1:]+orden[:i2]

        tipo = "recta" if len(inter)==0 else "quebrada"

        # -------- intermedios con coordenadas EXACTAS
        texto_int = ""

        if len(inter)>0:
            texto_int = "pasando por los puntos de coordenadas "
            for p in inter:
                texto_int += f"punto {p} N= {coords[p]['N_txt']} m, E= {coords[p]['E_txt']} m, "
            texto_int = texto_int.rstrip(", ") + ", "

        # -------- distancia desde tabla
        dist_total = sum(df_l.iloc[orden.index(p)]["LONGITUD"] for p in ruta)
        dist = format_dist(dist_total)

        N_ini = coords[p_ini]["N_txt"]
        E_ini = coords[p_ini]["E_txt"]
        N_fin = coords[p_fin]["N_txt"]
        E_fin = coords[p_fin]["E_txt"]

        texto = (
            f"Inicia en el punto {p_ini} con coordenadas planas N= {N_ini} m, E= {E_ini} m; "
            f"en línea {tipo}, en sentido {sentido}, {texto_int}"
            f"en una distancia de {dist} m, hasta encontrar el punto número {p_fin} "
            f"de coordenadas planas N= {N_fin} m, E= {E_fin} m"
        )

        fila = b[-1]

        texto += f"; colinda con {fila['COL']}."

        salida += texto + "\n\n"

    st.text_area("📄 RTL FINAL", salida, height=600)
