import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="RTL–MC PRECISO V2", layout="wide")
st.title("🧭 RTL–MC PRECISO V2")

st.markdown("### 1️⃣ Carga de información")

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

def f1(x):
    return round(x, 1)

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
    consecutivos = df_p["CONSECUTIVO"].unique()

    cons_sel = st.selectbox("🔍 CONSECUTIVO", consecutivos)
    st.success(f"✅ Polígono seleccionado: {cons_sel}")

    df_p = df_p[df_p["CONSECUTIVO"] == cons_sel]
    df_l = df_l[df_l["CONSECUTIVO"] == cons_sel]

    # =====================================================
    # 🔹 FASE 2 — LIMPIEZA
    # =====================================================

    st.markdown("### 🧹 Limpieza")

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

    st.subheader("📌 Puntos")
    st.dataframe(df_p[["PUNTO", "NORTE", "ESTE"]])

    st.subheader("📐 Líneas")
    st.dataframe(df_l[[
        "ORDEN","LONGITUD","CARDINALDIAD",
        "COLINDANTE","COND","NPN_COLINDANTE","FMI_COLINDANTE"
    ]])

    # =====================================================
    # 🔹 FASE 3 — GEOMETRÍA
    # =====================================================

    st.markdown("### 🧭 Tramos y validación")

    puntos = df_p["PUNTO"].tolist()

    coords = {
        r["PUNTO"]: (r["NORTE"], r["ESTE"])
        for _, r in df_p.iterrows()
    }

    tramos = []
    errores = []

    for i in range(len(puntos)):

        p1 = puntos[i]
        p2 = puntos[(i + 1) % len(puntos)]

        N1, E1 = coords[p1]
        N2, E2 = coords[p2]

        dist_calc = f1(math.sqrt((N2-N1)**2 + (E2-E1)**2))
        dist_tab = df_l.iloc[i]["LONGITUD"]

        dif = f1(abs(dist_calc - dist_tab))
        estado = "✅ OK" if dif == 0 else "❌ ERROR"

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

        tramo = {
            "INI": p1,
            "FIN": p2,
            "DIST_CALC": dist_calc,
            "DIST_TAB": dist_tab,
            "DIF": dif,
            "ESTADO": estado,
            "SENTIDO": sentido,
            "CARD": fila["CARDINALDIAD"],
            "COL": fila["COLINDANTE"]
        }

        tramos.append(tramo)

        if estado == "❌ ERROR":
            errores.append(tramo)

    df_tramos = pd.DataFrame(tramos)

    st.subheader("📐 Tramos")
    st.dataframe(df_tramos)

    if errores:
        st.subheader("🚨 Errores")
        st.dataframe(pd.DataFrame(errores))
    else:
        st.success("✅ Validación OK")

# =====================================================
# 🔹 FASE 4 — RTL NARRATIVO COMPLETO
# =====================================================

st.markdown("### 🧾 RTL Narrativo")

salida = "LINDEROS TÉCNICOS\n\n"

# 🔹 base
orden = df_p["PUNTO"].tolist()

tabla = df_l.to_dict("records")

bloques = []
actual = [df_tramos.iloc[0]]

# -------- AGRUPACIÓN --------
for i in range(1, len(df_tramos)):
    t = df_tramos.iloc[i]
    u = actual[-1]

    if (
        t["CARD"] == u["CARD"] and
        t["COL"] == u["COL"] and
        t["SENTIDO"] == u["SENTIDO"]
    ):
        actual.append(t)
    else:
        bloques.append(actual)
        actual = [t]

bloques.append(actual)

card_actual = None

# -------- FORMATEO --------
def f(v):
    return f"{v:.1f}".replace(".", ",")

for bloque in bloques:

    card = bloque[0]["CARD"]

    # -------- ENCABEZADO CARDINAL --------
    if card != card_actual:

        salida += f"POR EL {card}:\n\n"
        card_actual = card

    salida += "LINDERO:\n"

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

    texto_int = ""

    if len(intermedios) == 1:
        p2 = intermedios[0]
        N2, E2 = coords[p2]
        texto_int = f"pasando por el punto de coordenadas punto {p2} N= {f(N2)} m, E= {f(E2)} m, "

    elif len(intermedios) > 1:
        texto_int = "pasando por los puntos de coordenadas "
        for p2 in intermedios:
            N2, E2 = coords[p2]
            texto_int += f"punto {p2} N= {f(N2)} m, E= {f(E2)} m, "
        texto_int = texto_int.rstrip(", ") + ", "

    # -------- DISTANCIA TOTAL --------
    dist = 0
    for p in ruta:
        idx = orden.index(p)
        dist += tabla[idx]["LONGITUD"]

    dist = f(dist)

    # -------- PUNTOS --------
    N_ini, E_ini = coords[p_ini]
    N_fin, E_fin = coords[p_fin]

    sentido = bloque[0]["SENTIDO"]

    # -------- REDACCIÓN --------
    texto_lindero = (
        f"Inicia en el punto {p_ini} con coordenadas planas N= {f(N_ini)} m, E= {f(E_ini)} m; "
        f"en línea {tipo} en sentido {sentido}, {texto_int}"
        f"en una distancia de {dist} m, hasta encontrar el punto número {p_fin} de coordenadas planas "
        f"N= {f(N_fin)} m, E= {f(E_fin)} m"
    )

    # -------- COLINDANTE FINAL --------
    fila_final = tabla[orden.index(bloque[-1]["INI"])]

    col = bloque[-1]["COL"]
    cond = fila_final["OBSERVACIONES"]
    npn = fila_final["NPN_COLINDANTE"]
    fmi = fila_final["FMI_COLINDANTE"]
    tit = fila_final["NOMBRE_PREDIO_COL"]

    texto_lindero = texto_lindero.rstrip(".") + f"; colindando con {col}"

    if str(cond).upper() == "TRASLAPA":
        texto_lindero += f", que traslapa con el Número Predial Nacional {npn}, Folio de Matrícula Inmobiliaria {fmi}, y cuyo titular catastral es {tit}."
    elif str(cond).upper() == "CORRESPONDE":
        texto_lindero += f", que corresponde con el Número Predial Nacional {npn}, Folio de Matrícula Inmobiliaria {fmi}, y cuyo titular catastral es {tit}."
    else:
        texto_lindero += "."

    salida += texto_lindero + "\n\n"

# -------- MOSTRAR --------
st.text_area("📄 RESULTADO RTL COMPLETO", salida, height=600)
