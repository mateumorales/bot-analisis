import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import anthropic
import io

st.set_page_config(page_title="Bot de Análisis de Datos", page_icon="📊", layout="wide")

st.title("📊 Bot de Análisis de Datos con IA")
st.markdown("Sube tu archivo Excel o CSV y hazme preguntas sobre tus datos.")

# API Key
api_key = st.sidebar.text_input("🔑 Introduce tu API Key de Claude", type="password")

st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ Instrucciones")
st.sidebar.markdown("1. Introduce tu API Key\n2. Sube tu archivo\n3. Explora los gráficos\n4. Haz preguntas sobre tus datos")

# Subir archivo
archivo = st.file_uploader("📁 Sube tu archivo Excel o CSV", type=["csv", "xlsx", "xls"])

if archivo:
    if archivo.name.endswith(".csv"):
        df = pd.read_csv(archivo)
    else:
        df = pd.read_excel(archivo)

    # DETECCIÓN DE ERRORES
    st.subheader("🔍 Diagnóstico de calidad de datos")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total filas", df.shape[0])
    col2.metric("Total columnas", df.shape[1])
    col3.metric("Valores vacíos", df.isnull().sum().sum())
    col4.metric("Filas duplicadas", df.duplicated().sum())

    errores = []
    if df.isnull().sum().sum() > 0:
        cols_vacias = df.columns[df.isnull().any()].tolist()
        errores.append(f"⚠️ Columnas con valores vacíos: {', '.join(cols_vacias)}")
    if df.duplicated().sum() > 0:
        errores.append(f"⚠️ Hay {df.duplicated().sum()} filas duplicadas")
    if errores:
        for e in errores:
            st.warning(e)
    else:
        st.success("✅ No se detectaron problemas en los datos")

    st.markdown("---")

    # VISTA PREVIA
    st.subheader("👀 Vista previa de los datos")
    st.dataframe(df.head(10))

    st.subheader("📋 Resumen estadístico")
    st.dataframe(df.describe())

    st.markdown("---")

    # GRÁFICOS
    columnas_numericas = df.select_dtypes(include="number").columns.tolist()
    columnas_todas = df.columns.tolist()

    if columnas_numericas:
        st.subheader("📈 Gráficos interactivos")
        tipo = st.selectbox("Tipo de gráfico", ["Barras", "Líneas", "Dispersión", "Histograma", "Pastel", "Caja (Boxplot)"])

        if tipo in ["Barras", "Líneas", "Dispersión"]:
            col_x = st.selectbox("Eje X", columnas_todas)
            col_y = st.selectbox("Eje Y", columnas_numericas)
            if tipo == "Barras":
                fig = px.bar(df, x=col_x, y=col_y, title=f"{col_y} por {col_x}")
            elif tipo == "Líneas":
                fig = px.line(df, x=col_x, y=col_y, title=f"{col_y} por {col_x}")
            else:
                fig = px.scatter(df, x=col_x, y=col_y, title=f"{col_y} vs {col_x}")
        elif tipo == "Histograma":
            col_y = st.selectbox("Columna", columnas_numericas)
            fig = px.histogram(df, x=col_y, title=f"Distribución de {col_y}")
        elif tipo == "Pastel":
            col_x = st.selectbox("Categoría", columnas_todas)
            col_y = st.selectbox("Valor", columnas_numericas)
            fig = px.pie(df, names=col_x, values=col_y, title=f"{col_y} por {col_x}")
        else:
            col_y = st.selectbox("Columna", columnas_numericas)
            fig = px.box(df, y=col_y, title=f"Distribución de {col_y}")

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # EXPORTAR
    st.subheader("💾 Exportar resultados")
    col1, col2 = st.columns(2)

    with col1:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Datos", index=False)
            df.describe().to_excel(writer, sheet_name="Resumen estadístico")
        st.download_button(
            label="📥 Descargar Excel con resumen",
            data=buffer.getvalue(),
            file_name="analisis_datos.xlsx",
            mime="application/vnd.ms-excel"
        )

    with col2:
        csv_export = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Descargar CSV limpio",
            data=csv_export,
            file_name="datos_limpios.csv",
            mime="text/csv"
        )

    st.markdown("---")

    # CHAT CON IA
    st.subheader("💬 Pregúntame sobre tus datos")
    pregunta = st.text_input("Escribe tu pregunta aquí...")

    if pregunta and api_key:
        with st.spinner("Analizando..."):
            resumen = df.describe().to_string()
            columnas = ", ".join(df.columns.tolist())
            muestra = df.head(5).to_string()
            vacios = df.isnull().sum().to_string()

            cliente = anthropic.Anthropic(api_key=api_key)
            mensaje = cliente.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": f"""Eres un experto en análisis de datos.
                    El usuario tiene un dataset con las columnas: {columnas}
                    Resumen estadístico: {resumen}
                    Muestra de datos: {muestra}
                    Valores vacíos por columna: {vacios}
                    Pregunta del usuario: {pregunta}
                    Responde en español de forma clara y concisa."""
                }]
            )
            st.success(mensaje.content[0].text)
    elif pregunta and not api_key:
        st.warning("⚠️ Introduce tu API Key de Claude en el panel izquierdo.")