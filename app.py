import streamlit as st
import pandas as pd

st.set_page_config(page_title="RTL–MC PRECISO V2", layout="wide")

st.title("🧭 RTL–MC PRECISO V2")

st.markdown("### 1️⃣ Carga de información")

# ------------------ CARGA ------------------
puntos_file = st.file_uploader("📌 Cargar tabla de puntos", type=["xlsx", "csv"])
lineas_file = st.file_uploader("📐 Cargar tabla de líneas", type=["xlsx", "csv"])

# ------------------ FUNCIÓN ------------------
def cargar_archivo(file):
    if file.name.endswith(".xlsx"):
        df = pd.read_excel(file, dtype=str)
    else:
        df = pd.read_csv(file, dtype=str)

    df.columns = df.columns.str.strip()
    return df

# ------------------ PROCESO PRINCIPAL ------------------
if puntos_file and lineas_file:

    df_p = cargar_archivo(puntos_file)
    df_l = cargar_archivo(lineas_file)

    # ------------------ SELECCIÓN ------------------
    if "CONSECUTIVO" in df_p.columns:

        consecutivos = df_p["CONSECUTIVO"].unique()

        cons_sel = st.selectbox(
            "🔍 Selecciona el polígono (CONSECUTIVO)",
            consecutivos
        )

        st.success(f"✅ Polígono seleccionado: {cons_sel}")

        # ------------------ FILTRADO ------------------
        df_p_filtrado = df_p[df_p["CONSECUTIVO"] == cons_sel]
        df_l_filtrado = df_l[df_l["CONSECUTIVO"] == cons_sel]

        # ------------------ LIMPIEZA ------------------
        st.markdown("### 🧹 Limpieza y preparación de datos")

        df_p_clean = df_p_filtrado.copy()
        df_l_clean = df_l_filtrado.copy()

        # ---------- PUNTOS ----------
        df_p_clean["ORDEN"] = df_p_clean["ORDEN"].astype(int)
        df_p_clean = df_p_clean.sort_values("ORDEN")

        df_p_clean["NORTE"] = df_p_clean["Y"].astype(str).str.replace(",", ".").astype(float)
        df_p_clean["ESTE"] = df_p_clean["X"].astype(str).str.replace(",", ".").astype(float)

        df_p_clean["PUNTO"] = df_p_clean["ORDEN"].astype(str).str.zfill(2)

        # ---------- LINEAS ----------
        df_l_clean["ORDEN"] = df_l_clean["ORDEN"].astype(int)
        df_l_clean = df_l_clean.sort_values("ORDEN")

        df_l_clean["LONGITUD"] = df_l_clean["LONGITUD"].astype(str).str.replace(",", ".").astype(float)

        df_l_clean["COLINDANTE"] = df_l_clean["NOM_COLINDANTE"].str.strip()
        df_l_clean["CONDICION"] = df_l_clean["OBSERVACIONES"].str.strip()
        df_l_clean["TITULAR"] = df_l_clean["NOMBRE_PREDIO_COL"].str.strip()

        # ------------------ VALIDACIÓN ------------------
        st.subheader("🔍 Validación básica")

        st.write(f"Total puntos: {len(df_p_clean)}")
        st.write(f"Total tramos: {len(df_l_clean)}")

        if len(df_p_clean) != len(df_l_clean):
            st.warning("⚠️ El número de puntos y tramos no coincide")
        else:
            st.success("✅ Puntos y tramos coinciden correctamente")

        # ------------------ VISUALIZACIÓN ------------------
        st.subheader(f"📌 Puntos limpios (CONSECUTIVO {cons_sel})")
        st.dataframe(df_p_clean[["PUNTO", "NORTE", "ESTE"]])

        st.subheader(f"📐 Líneas limpias (CONSECUTIVO {cons_sel})")
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

# -------------------- FASE 3: TRAMOS Y SENTIDOS --------------------

st.markdown("### 🧭 Construcción geométrica")

import math

# 🔹 Lista de puntos ordenados
puntos_lista = df_p_clean["PUNTO"].tolist()

# 🔹 Diccionario de coordenadas
coords = {
    row["PUNTO"]: (row["NORTE"], row["ESTE"])
    for _, row in df_p_clean.iterrows()
}

tramos = []
errores = []

for i in range(len(puntos_lista)):

    p1 = puntos_lista[i]
    p2 = puntos_lista[(i + 1) % len(puntos_lista)]  # cierre automático

    N1, E1 = coords[p1]
    N2, E2 = coords[p2]

    # 🔹 Distancia calculada
    dist_calc = math.sqrt((N2 - N1)**2 + (E2 - E1)**2)

    # 🔹 Distancia tabla
    dist_tabla = df_l_clean.iloc[i]["LONGITUD"]

    # 🔹 Diferencia
    dif = abs(dist_calc - dist_tabla)

    estado = "✅ OK" if dif < 1 else "❌ ERROR"

    # 🔹 Calcular sentido
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

    fila_linea = df_l_clean.iloc[i]

    tramos.append({
        "PUNTO_INI": p1,
        "PUNTO_FIN": p2,
        "DIST_CALCULADA": round(dist_calc, 2),
        "DIST_TABLA": dist_tabla,
        "DIFERENCIA": round(dif, 2),
        "ESTADO": estado,
        "SENTIDO": sentido,
        "CARDINALIDAD": fila_linea["CARDINALDIAD"],
        "COLINDANTE": fila_linea["COLINDANTE"]
    })

    if estado == "❌ ERROR":
        errores.append(tramos[-1])

# -------------------- RESULTADOS --------------------

df_tramos = pd.DataFrame(tramos)

st.subheader("📐 Tramos calculados")
st.dataframe(df_tramos)

# -------------------- VALIDADOR --------------------

if errores:
    st.subheader("🚨 Errores de distancia")
    st.dataframe(pd.DataFrame(errores))
else:
    st.success("✅ Todas las distancias coinciden correctamente")

    else:
        st.error("⚠️ La tabla de puntos no tiene la columna CONSECUTIVO")
