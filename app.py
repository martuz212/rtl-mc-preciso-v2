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

    else:
        st.error("⚠️ La tabla de puntos no tiene la columna CONSECUTIVO")
