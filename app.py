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

    # 🔍 Validar columna CONSECUTIVO
    if "CONSECUTIVO" in df_p.columns:

        consecutivos = df_p["CONSECUTIVO"].unique()

        cons_sel = st.selectbox(
            "🔍 Selecciona el polígono (CONSECUTIVO)",
            consecutivos
        )

        st.success(f"✅ Polígono seleccionado: {cons_sel}")

        # ✅ FILTRAR
        df_p_filtrado = df_p[df_p["CONSECUTIVO"] == cons_sel]
        df_l_filtrado = df_l[df_l["CONSECUTIVO"] == cons_sel]

        # ✅ MOSTRAR RESULTADOS FILTRADOS
        st.subheader(f"📌 Tabla de puntos (CONSECUTIVO {cons_sel})")
        st.dataframe(df_p_filtrado)

        st.subheader(f"📐 Tabla de líneas (CONSECUTIVO {cons_sel})")
        st.dataframe(df_l_filtrado)

        # Información adicional
        st.info(f"📊 Total puntos: {len(df_p_filtrado)}")
        st.info(f"📐 Total tramos: {len(df_l_filtrado)}")

    else:
        st.error("⚠️ La tabla de puntos no tiene la columna CONSECUTIVO")
