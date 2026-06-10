import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="RTL–MC PRECISO PRO", layout="wide")
st.title("🧭 RTL–MC PRECISO PRO")

# =========================================================
# 🔹 FUNCIONES
# =========================================================

def cargar_archivo(file):
    if file.name.endswith(".xlsx"):
        df = pd.read_excel(file, dtype=str)
    else:
        df = pd.read_csv(file, dtype=str)

    df.columns = df.columns.str.strip()
    return df

def f(v):
    return f"{v:.1f}".replace(".", ",")

# =========================================================
# 🔹 CARGA
# =========================================================

puntos_file = st.file_uploader("📌 Tabla de puntos", type=["xlsx", "csv"])
lineas_file = st.file_uploader("📐 Tabla de líneas", type=["xlsx", "csv"])

# =========================================================
# 🔹 PROCESO
# =========================================================

if puntos_file and lineas_file:

    df_p = cargar_archivo(puntos_file)
    df_l = cargar_archivo(lineas_file)

    # ---------------- SELECCIÓN ----------------
    cons_sel = st.selectbox("🔍 CONSECUTIVO", df_p["CONSECUTIVO"].unique())
    st.success(f"✅ Polígono seleccionado: {cons_sel}")

    df_p = df_p[df_p["CONSECUTIVO"] == cons_sel]
    df_l = df_l[df_l["CONSECUTIVO"] == cons_sel]

    # =====================================================
    # 🔹 LIMPIEZA
    # =====================================================

    df_p["ORDEN"] = df_p["ORDEN"].astype(int)
    df_p = df_p.sort_values("ORDEN")

    df_p["NORTE"] = df_p["Y"].str.replace(",", ".").astype(float)
    df_p["ESTE"] = df_p["X"].str.replace(",", ".").astype(float)
    df_p["PUNTO"] = df_p["ORDEN"].astype(str).str.zfill(2)

    df_l["ORDEN"] = df_l["ORDEN"].astype(int)
    df_l = df_l.sort_values("ORDEN")

    df_l["LONGITUD"] = df_l["LONGITUD"].str.replace(",", ".").astype(float)
    df_l["COLINDANTE"] = df_l["NOM_COLINDANTE"].str.strip()
    df_l["COND"] = df_l["OBSERVACIONES"].str.strip()

    # =====================================================
    # 🔹 GEOMETRÍA
    # =====================================================

    puntos = df_p["PUNTO"].tolist()

    coords = {
        r["PUNTO"]: (r["NORTE"], r["ESTE"])
        for _, r in df_p.iterrows()
    }

    tramos = []

    for i in range(len(puntos)):

        p1 = puntos[i]
        p2 = puntos[(i + 1) % len(puntos)]

        N1, E1 = coords[p1]
        N2, E2 = coords[p2]

        dist_calc = round(math.sqrt((N2-N1)**2 + (E2-E1)**2), 1)
        dist_tab = df_l.iloc[i]["LONGITUD"]

        dx = E2 - E1
        dy = N2 - N1
        ang = math.degrees(math.atan2(dx, dy)) % 360

        if ang < 22.5:
            sentido = "norte"
        elif ang < 67.5:
            sentido = "noreste"
        elif ang < 112.5:
            sentido = "este"
        elif ang < 157.5:
            sentido = "sureste"
        elif ang < 202.5:
            sentido = "sur"
        elif ang < 247.5:
            sentido = "suroeste"
        elif ang < 292.5:
            sentido = "oeste"
        elif ang < 337.5:
            sentido = "noroeste"
        else:
            sentido = "norte"

        fila = df_l.iloc[i]

        tramos.append({
            "INI": p1,
            "FIN": p2,
            "DIST": dist_calc,
            "SENTIDO": sentido,
            "CARD": fila["CARDINALDIAD"],
            "COL": fila["COLINDANTE"],
            "COND": fila["OBSERVACIONES"],
            "NPN": fila["NPN_COLINDANTE"],
            "FMI": fila["FMI_COLINDANTE"],
            "TIT": fila["NOMBRE_PREDIO_COL"]
        })

    df_tramos = pd.DataFrame(tramos)

    # =====================================================
    # 🔹 AGRUPACIÓN
    # =====================================================

    bloques = []
    actual = [df_tramos.iloc[0]]

    for i in range(1, len(df_tramos)):
        t = df_tramos.iloc[i]
        u = actual[-1]

        if (t["CARD"] == u["CARD"] and t["COL"] == u["COL"] and t["SENTIDO"] == u["SENTIDO"]):
            actual.append(t)
        else:
            bloques.append(actual)
            actual = [t]

    bloques.append(actual)

    # =====================================================
    # 🔹 RTL NARRATIVO (CONTROL DE ESTILO)
    # =====================================================

    salida = "LINDEROS TÉCNICOS\n\n"

    orden = df_p["PUNTO"].tolist()
    card_actual = None

    for bloque in bloques:

        card = bloque[0]["CARD"]

        if card != card_actual:
            salida += f"POR EL {card}:\n\n"
            card_actual = card

        p_ini = bloque[0]["INI"]
        p_fin = bloque[-1]["FIN"]

        i1 = orden.index(p_ini)
        i2 = orden.index(p_fin)

        # -------- RUTA --------
        if i2 > i1:
            ruta = orden[i1:i2]
        else:
            ruta = orden[i1:] + orden[:i2]

        # -------- INTERMEDIOS --------
        if i2 < i1:
            intermedios = orden[i1+1:] + orden[:i2]
        else:
            intermedios = orden[i1+1:i2]

        tipo = "recta" if len(intermedios) == 0 else "quebrada"

        # -------- TEXTO INTERMEDIO --------
        texto_int = ""

        if len(intermedios) == 1:
            p = intermedios[0]
            N, E = coords[p]
            texto_int = f"pasando por el punto de coordenadas punto {p} N= {f(N)} m, E= {f(E)} m, "

        elif len(intermedios) > 1:
            texto_int = "pasando por los puntos de coordenadas "
            for p in intermedios:
                N, E = coords[p]
                texto_int += f"punto {p} N= {f(N)} m, E= {f(E)} m, "
            texto_int = texto_int.rstrip(", ") + ", "

        # -------- DISTANCIA --------
        dist = sum(df_l.iloc[orden.index(p)]["LONGITUD"] for p in ruta)
        dist = f(dist)

        N_ini, E_ini = coords[p_ini]
        N_fin, E_fin = coords[p_fin]

        sentido = bloque[0]["SENTIDO"]

        texto = (
            f"Inicia en el punto {p_ini} con coordenadas planas N= {f(N_ini)} m, E= {f(E_ini)} m; "
            f"en línea {tipo}, en sentido {sentido}, "
        )

        if texto_int:
            texto += texto_int

        texto += (
            f"en una distancia de {dist} m, hasta encontrar el punto número {p_fin} "
            f"de coordenadas planas N= {f(N_fin)} m, E= {f(E_fin)} m"
        )

        fila = bloque[-1]

        texto += f"; colinda con {fila['COL']}"

        if str(fila["COND"]).upper() == "TRASLAPA":
            texto += f", que traslapa con el Número Predial Nacional {fila['NPN']}, Folio de Matrícula Inmobiliaria {fila['FMI']}, y cuyo titular catastral es {fila['TIT']}."
        elif str(fila["COND"]).upper() == "CORRESPONDE":
            texto += f", que corresponde con el Número Predial Nacional {fila['NPN']}, Folio de Matrícula Inmobiliaria {fila['FMI']}, y cuyo titular catastral es {fila['TIT']}."
        else:
            texto += "."

        salida += texto + "\n\n"

    st.text_area("📄 RESULTADO RTL FINAL", salida, height=600)
