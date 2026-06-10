import streamlit as st
import pandas as pd

st.set_page_config(page_title="RTL–MC PRECISO V2", layout="wide")

st.title("🧭 RTL–MC PRECISO V2")

st.markdown("### 1️⃣ Carga de información")

# ------------------ CARGA ------------------
puntos_file = st.file_uploader("📌 Cargar tabla de puntos", type=["xlsx", "csv"])
lineas_file = st.file_uploader("📐 Cargar tabla de líneas", type=["xlsx", "csv"])

# ------------------ FUNCION ------------------
def cargar_archivo(file):
    if file.name.endswith(".xlsx"):
        return pd.read_excel(file)
    else:
        return pd.read_csv(file)

# ------------------ MOSTRAR ------------------
if puntos_file:
    df_p = cargar_archivo(puntos_file)
    st.subheader("Tabla de puntos")
    st.dataframe(df_p.head())

if lineas_file:
    df_l = cargar_archivo(lineas_file)
    st.subheader("Tabla de líneas")
    st.dataframe(df_l.head())

# ------------------ SELECCIÓN ------------------
if puntos_file:
    df_p = cargar_archivo(puntos_file)

    if "CONSECUTIVO" in df_p.columns:
        consecutivos = df_p["CONSECUTIVO"].unique()
        cons_sel = st.selectbox("Selecciona el polígono (CONSECUTIVO)", consecutivos)

        st.success(f"Polígono seleccionado: {cons_sel}")
