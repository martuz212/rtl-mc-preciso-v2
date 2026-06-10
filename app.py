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

# ✅ función de redondeo (1 decimal)
def f1(x):
    return round(x, 1)

# =========================================================
# 🔹 FASE 1 — CARGA
# =========================================================

puntos_file = st.file_uploader("📌 Cargar tabla de puntos", type=["xlsx", "csv"])
lineas_file = st.file_uploader("📐 Cargar tabla de líneas", type=["xlsx", "csv"])

# =========================================================
# 🔹 PROCESO PRINCIPAL
# =========================================================

if puntos_file and lineas_file:

    df_p = cargar_archivo(puntos_file)
    df_l = cargar_archivo(lineas_file)

    # =====================================================
    # 🔹 SELECCIÓN
    # =====================================================

    if "CONSECUTIVO" not in df_p.columns:
        st.error("⚠️ No existe columna CONSECUTIVO")
        st.stop()

    consecutivos = df_p["CONSECUTIVO"].unique()

    cons_sel = st.selectbox(
        "🔍 Selecciona el polígono (CONSECUTIVO)",
        consecutivos
    )

    st.success(f"✅ Polígono seleccionado: {cons_sel}")

    # =====================================================
    # 🔹 FILTRADO
    # =====================================================

    df_p_filtrado = df_p[df_p["CONSECUTIVO"] == cons_sel]
    df_l_filtrado = df_l[df_l["CONSECUTIVO"] == cons_sel]

    # =====================================================
    # 🔹 FASE 2 — LIMPIEZA
    # =====================================================

    st.markdown("### 🧹 Fase 2 — Limpieza")

    df_p_clean = df_p_filtrado.copy()
    df_l_clean = df_l_filtrado.copy()

    # -------- PUNTOS --------
    df_p_clean["ORDEN"] = df_p_clean["ORDEN"].astype(int)
    df_p_clean = df_p_clean.sort_values("ORDEN")

    df_p_clean["NORTE"] = df_p_clean["Y"].str.replace(",", ".").astype(float)
    df_p_clean["ESTE"] = df_p_clean["X"].str.replace(",", ".").astype(float)

    df_p_clean["PUNTO"] = df_p_clean["ORDEN"].astype(str).str.zfill(2)

    # -------- LINEAS --------
    df_l_clean["ORDEN"] = df_l_clean["ORDEN"].astype(int)
    df_l_clean = df_l_clean.sort_values("ORDEN")

    df_l_clean["LONGITUD"] = df_l_clean["LONGITUD"].str.replace(",", ".").astype(float)

    df_l_clean["COLINDANTE"] = df_l_clean["NOM_COLINDANTE"].str.strip()
    df_l_clean["CONDICION"] = df_l_clean["OBSERVACIONES"].str.strip()
    df_l_clean["TITULAR"] = df_l_clean["NOMBRE_PREDIO_COL"].str.strip()

    # -------- VALIDACIÓN --------
    st.write(f"📊 Puntos: {len(df_p_clean)}")
    st.write(f"📐 Tramos: {len(df_l_clean)}")

    if len(df_p_clean) != len(df_l_clean):
        st.warning("⚠️ cantidad no coincide")

    # -------- MOSTRAR --------
    st.subheader("📌 Puntos limpios")
    st.dataframe(df_p_clean[["PUNTO", "NORTE", "ESTE"]])

    st.subheader("📐 Líneas limpias")
    st.dataframe(
        df_l_clean[
            [
                "ORDEN",
                "LONGITUD",
                "CARDINALDIAD",
                "COLINDANTE",
                "CONDICION",
                "TITULAR",
                "NPN_COLINDANTE",
                "FMI_COLINDANTE"
            ]
        ]
    )

    # =====================================================
    # 🔹 FASE 3 — GEOMETRÍA
    # =====================================================

    st.markdown("### 🧭 Fase 3 — Construcción geométrica")

    puntos_lista = df_p_clean["PUNTO"].tolist()

    coords = {
        row["PUNTO"]: (row["NORTE"], row["ESTE"])
        for _, row in df_p_clean.iterrows()
    }

    tramos = []
    errores = []

    for i in range(len(puntos_lista)):

        p1 = puntos_lista[i]
        p2 = puntos_lista[(i + 1) % len(puntos_lista)]

        N1, E1 = coords[p1]
        N2, E2 = coords[p2]

        # -------- DISTANCIA --------
        dist_calc = math.sqrt((N2 - N1)**2 + (E2 - E1)**2)
        dist_calc = f1(dist_calc)

        dist_tabla = df_l_clean.iloc[i]["LONGITUD"]

        dif = abs(dist_calc - dist_tabla)
        dif = f1(dif)

        estado = "✅ OK" if dif == 0 else "❌ ERROR"

        # -------- SENTIDO --------
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

        fila = df_l_clean.iloc[i]

        tramo = {
            "PUNTO_INI": p1,
            "PUNTO_FIN": p2,
            "DIST_CALCULADA": dist_calc,
            "DIST_TABLA": dist_tabla,
            "DIF": dif,
            "ESTADO": estado,
            "SENTIDO": sentido,
            "CARDINALIDAD": fila["CARDINALDIAD"],
            "COLINDANTE": fila["COLINDANTE"]
        }

        tramos.append(tramo)

        if estado == "❌ ERROR":
            errores.append(tramo)

    df_tramos = pd.DataFrame(tramos)

    st.subheader("📐 Tramos calculados")
    st.dataframe(df_tramos)

    # -------- VALIDADOR --------
    if errores:
        st.subheader("🚨 Errores de distancia")
        st.dataframe(pd.DataFrame(errores))
    else:
        st.success("✅ Todas las distancias coinciden")
