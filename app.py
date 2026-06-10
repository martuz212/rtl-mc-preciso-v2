import streamlit as st
import pandas as pd
import math

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

def f(v):
    return f"{v:.1f}".replace(".", ",")

# =========================================================
# CARGA
# =========================================================

puntos_file = st.file_uploader("📌 Tabla de puntos", type=["xlsx", "csv"])
lineas_file = st.file_uploader("📐 Tabla de líneas", type=["xlsx", "csv"])

if puntos_file and lineas_file:

    df_p = cargar_archivo(puntos_file)
    df_l = cargar_archivo(lineas_file)

    cons = st.selectbox("🔍 CONSECUTIVO", df_p["CONSECUTIVO"].unique())
    df_p = df_p[df_p["CONSECUTIVO"] == cons]
    df_l = df_l[df_l["CONSECUTIVO"] == cons]

    # =====================================================
    # LIMPIEZA
    # =====================================================

    df_p["ORDEN"] = df_p["ORDEN"].astype(int)
    df_p = df_p.sort_values("ORDEN")

    df_p["NORTE"] = df_p["Y"].str.replace(",", ".").astype(float)
    df_p["ESTE"] = df_p["X"].str.replace(",", ".").astype(float)
    df_p["PUNTO"] = df_p["ORDEN"].astype(str).str.zfill(2)

    df_l["ORDEN"] = df_l["ORDEN"].astype(int)
    df_l = df_l.sort_values("ORDEN")

    df_l["LONGITUD"] = df_l["LONGITUD"].str.replace(",", ".").astype(float)
    df_l["COL"] = df_l["NOM_COLINDANTE"].str.strip()
    df_l["COND"] = df_l["OBSERVACIONES"].str.strip()

    puntos = df_p["PUNTO"].tolist()

    coords = {r["PUNTO"]:(r["NORTE"],r["ESTE"]) for _,r in df_p.iterrows()}

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

        dist = round(math.sqrt((N2-N1)**2 + (E2-E1)**2),1)

        fila = df_l.iloc[i]

        tramos.append({
            "INI":p1,
            "FIN":p2,
            "ANGULO":ang,
            "DIST":dist,
            "CARD":fila["CARDINALDIAD"],
            "COL":fila["COL"],
            "COND":fila["COND"],
            "NPN":fila["NPN_COLINDANTE"],
            "FMI":fila["FMI_COLINDANTE"],
            "TIT":fila["NOMBRE_PREDIO_COL"]
        })

    df_tramos = pd.DataFrame(tramos)

    # =====================================================
    # DETECCIÓN DE QUIEBRES REALES
    # =====================================================

    bloques = []
    actual = [df_tramos.iloc[0]]

    for i in range(1, len(df_tramos)):

        t = df_tramos.iloc[i]
        u = actual[-1]

        delta = abs(t["ANGULO"] - u["ANGULO"])

        if delta > 180:
            delta = 360 - delta

        if (
            t["CARD"] == u["CARD"] and
            t["COL"] == u["COL"] and
            delta < 30   # 🔥 criterio de quiebre real
        ):
            actual.append(t)
        else:
            bloques.append(actual)
            actual = [t]

    bloques.append(actual)

    # =====================================================
    # TABLAS DE VALIDACIÓN
    # =====================================================

    st.subheader("📐 Tramos técnicos")
    st.dataframe(df_tramos)

    info = []

    for i, b in enumerate(bloques,1):
        info.append({
            "LINDERO":i,
            "INI":b[0]["INI"],
            "FIN":b[-1]["FIN"],
            "COL":b[0]["COL"],
            "CARD":b[0]["CARD"]
        })

    st.subheader("📊 Linderos agrupados")
    st.dataframe(pd.DataFrame(info))

    # =====================================================
    # RTL NARRATIVO
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

        i1 = orden.index(p_ini)
        i2 = orden.index(p_fin)

        if i2 > i1:
            ruta = orden[i1:i2]
        else:
            ruta = orden[i1:] + orden[:i2]

        inter = orden[i1+1:i2] if i2 > i1 else orden[i1+1:] + orden[:i2]

        tipo = "recta" if len(inter)==0 else "quebrada"

        txt = ""

        if len(inter)>0:
            txt="pasando por los puntos de coordenadas "
            for p in inter:
                N,E=coords[p]
                txt+=f"punto {p} N= {f(N)} m, E= {f(E)} m, "
            txt=txt.rstrip(", ")+", "

        dist = f(sum(df_l.iloc[orden.index(p)]["LONGITUD"] for p in ruta))

        N1,E1=coords[p_ini]
        N2,E2=coords[p_fin]

        texto = (
            f"Inicia en el punto {p_ini} con coordenadas planas N= {f(N1)} m, E= {f(E1)} m; "
            f"en línea {tipo}, {txt}"
            f"en una distancia de {dist} m, hasta encontrar el punto número {p_fin} "
            f"de coordenadas planas N= {f(N2)} m, E= {f(E2)} m"
        )

        fila = b[-1]

        texto += f"; colinda con {fila['COL']}"

        if fila["COND"].upper() == "TRASLAPA":
            texto += f", que traslapa con el Número Predial Nacional {fila['NPN']}, Folio de Matrícula Inmobiliaria {fila['FMI']}, y cuyo titular catastral es {fila['TIT']}."
        elif fila["COND"].upper() == "CORRESPONDE":
            texto += f", que corresponde con el Número Predial Nacional {fila['NPN']}, Folio de Matrícula Inmobiliaria {fila['FMI']}, y cuyo titular catastral es {fila['TIT']}."
        else:
            texto += "."

        salida += texto + "\n\n"

    st.text_area("📄 RTL FINAL", salida, height=600)
