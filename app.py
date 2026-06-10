import streamlit as st
import pandas as pd

st.set_page_config(page_title="RTL–MC PRECISO V2", layout="wide")

st.title("🧭 RTL–MC PRECISO V2")

st.markdown("### 1️⃣ Carga de información")

# ------------------ CARGA ------------------
puntos_file = st.file_uploader("📌 Cargar tabla de puntos", type=["xlsx", "csv"])
lineas_file = st.file_uploader("📐 Cargar tabla de líneas", type=["xlsx", "csv"])

# ------------------ FUNCIÓN CARGA ------------------
def cargar_archivo(file):
    if file.name.endswith(".xlsx"):
        df = pd.read_excel(file, dtype=str)  # 🔥 fuerza todo a texto
    else:
        df = pd.read_csv(file, dtype=str)

    # 🔥 limpieza básica nombres columnas
    df.columns = df.columns.str.strip()

    return df

# ------------------ PROCESO ------------------

if puntos_file:
    df_p = cargar_archivo(puntos_file)

    st.subheader("📌 Tabla de puntos (vista)")
    st.dataframe(df_p.head())

if lineas_file:
    df_l = cargar_archivo(lineas_file)

    st.subheader("📐 Tabla de líneas (vista)")
    st.dataframe(df_l.head())

# ------------------ SELECCIÓN CONSECUTIVO ------------------
if puntos_file:

    df_p = cargar_archivo(puntos_file)

    if "CONSECUTIVO" in df_p.columns:

        consecutivos = df_p["CONSECUTIVO"].unique()

        cons_sel = st.selectbox(
            "🔍 Selecciona el polígono (CONSECUTIVO)",
            consecutivos
        )

        st.success(f"✅ Polígono seleccionado: {cons_sel}")

        # 🔥 Mostrar cuántos registros tiene ese polígono
        total = df_p[df_p["CONSECUTIVO"] == cons_sel].shape[0]

        st.info(f"📊 Número de puntos del polígono: {total}")

    else:
        st.error("⚠️ No se encontró la columna CONSECUTIVO en la tabla de puntos")
