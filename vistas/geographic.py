"""
Módulo para la vista de distribución geográfica del dashboard de Fiebre Amarilla.
Contiene funciones para visualización y análisis de distribución por ubicación.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging

# Configurar logger
logger = logging.getLogger("FiebreAmarilla-Dashboard")


def show(data, filters, colors):
    """
    Muestra la página de distribución geográfica del dashboard.

    Args:
        data (dict): Diccionario con los dataframes
        filters (dict): Filtros seleccionados
        colors (dict): Colores institucionales
    """
    # Título y descripción
    st.markdown(
        '<h1 class="main-title">Distribución Geográfica</h1>', unsafe_allow_html=True
    )

    # Mostrar descripción general con un diseño más atractivo
    st.markdown(
        f"""
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid {colors['primary']}; margin-bottom: 30px;">
            <h3 style="color: {colors['primary']}; margin-top: 0;">Análisis Geográfico</h3>
            <p>Esta sección muestra la distribución geográfica de los casos de fiebre amarilla, 
            distinguiendo entre <strong>lugar de residencia</strong> de los pacientes y 
            <strong>lugar de notificación</strong> de los casos al sistema de vigilancia.</p>
            <p>Esta distinción es importante para entender el origen y la distribución de la enfermedad, 
            así como para planificar intervenciones adecuadas en cada territorio.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Verificar si tenemos las columnas necesarias para el análisis
    has_residencia = (
        "ndep_resi" in data["fiebre"].columns and "nmun_resi" in data["fiebre"].columns
    )
    has_notificacion = (
        "ndep_not" in data["fiebre"].columns and "nmun_not" in data["fiebre"].columns
    )

    if not (has_residencia or has_notificacion):
        st.error(
            "No se encontraron datos de ubicación (residencia o notificación) en el conjunto de datos."
        )
        return

    # Sección 1: Comparativa de Departamentos (Residencia vs Notificación)
    st.markdown(
        '<h2 style="color: #5A4214; border-bottom: 2px solid #F2A900; padding-bottom: 8px;">Comparativa de Casos por Departamento</h2>',
        unsafe_allow_html=True,
    )

    if has_residencia and has_notificacion:
        # Preparar datos para la comparativa
        df_resi = data["fiebre"]["ndep_resi"].value_counts().reset_index()
        df_resi.columns = ["Departamento", "Casos por Residencia"]

        df_noti = data["fiebre"]["ndep_not"].value_counts().reset_index()
        df_noti.columns = ["Departamento", "Casos por Notificación"]

        # Unir los dataframes para comparar
        df_comparativa = pd.merge(
            df_resi, df_noti, on="Departamento", how="outer"
        ).fillna(0)

        # Calcular la diferencia
        df_comparativa["Diferencia"] = (
            df_comparativa["Casos por Notificación"]
            - df_comparativa["Casos por Residencia"]
        )

        # Ordenar por mayor número de casos (suma de ambos)
        df_comparativa["Total"] = (
            df_comparativa["Casos por Residencia"]
            + df_comparativa["Casos por Notificación"]
        )
        df_comparativa = df_comparativa.sort_values("Total", ascending=False).drop(
            columns=["Total"]
        )

        # Mostrar las primeras filas (top departamentos)
        top_n = min(10, len(df_comparativa))
        df_top = df_comparativa.head(top_n)

        # Crear gráfico de barras agrupadas
        fig = go.Figure()

        # Añadir barras para residencia
        fig.add_trace(
            go.Bar(
                y=df_top["Departamento"],
                x=df_top["Casos por Residencia"],
                name="Residencia",
                orientation="h",
                marker_color=colors["primary"],
                text=df_top["Casos por Residencia"].astype(int),
                textposition="auto",
            )
        )

        # Añadir barras para notificación
        fig.add_trace(
            go.Bar(
                y=df_top["Departamento"],
                x=df_top["Casos por Notificación"],
                name="Notificación",
                orientation="h",
                marker_color=colors["secondary"],
                text=df_top["Casos por Notificación"].astype(int),
                textposition="auto",
            )
        )

        # Actualizar layout
        fig.update_layout(
            title=f"Top {top_n} Departamentos: Casos por Residencia vs Notificación",
            title_font=dict(size=16, color="#5A4214"),
            xaxis_title="Número de Casos",
            barmode="group",
            height=500,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=10, r=10, t=60, b=10),
        )

        # Mostrar gráfico
        st.plotly_chart(fig, use_container_width=True)

        # Añadir explicación
        st.markdown(
            f"""
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h4 style="color: {colors['primary']}; margin-top: 0;">¿Qué significa esta comparativa?</h4>
                <ul>
                    <li><strong>Casos por Residencia</strong>: Número de pacientes que viven en cada departamento.</li>
                    <li><strong>Casos por Notificación</strong>: Número de casos reportados en cada departamento.</li>
                </ul>
                <p>Las diferencias pueden indicar desplazamiento de pacientes para atención médica o disponibilidad de servicios de salud.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Crear tabla interactiva con todos los departamentos
        st.subheader("Tabla Comparativa Completa")

        # Formatear para mostrar enteros
        df_comparativa_display = df_comparativa.copy()
        for col in ["Casos por Residencia", "Casos por Notificación"]:
            df_comparativa_display[col] = df_comparativa_display[col].astype(int)

        # Añadir columna de color para la diferencia
        def color_diferencia(val):
            if val > 0:
                return f'color: {colors["success"]}'
            elif val < 0:
                return f'color: {colors["danger"]}'
            else:
                return ""

        # Mostrar tabla estilizada
        st.dataframe(
            df_comparativa_display.style.format(
                {"Diferencia": "{:+d}"}
            ).applymap(  # Mostrar signo en diferencia
                color_diferencia, subset=["Diferencia"]
            ),
            use_container_width=True,
        )

        # Añadir visualización de flujo (gráfico de sankey o similar)
        st.subheader("Análisis de Flujo entre Departamentos")

        # Crear dataframe con casos que tienen diferente departamento de residencia y notificación
        df_flujo = data["fiebre"][["ndep_resi", "ndep_not"]].copy()
        df_flujo = df_flujo.dropna()  # Eliminar filas con valores faltantes

        # Filtrar solo los que tienen diferente departamento
        df_flujo = df_flujo[df_flujo["ndep_resi"] != df_flujo["ndep_not"]]

        if not df_flujo.empty:
            # Contar frecuencias de flujos
            flujo_count = (
                df_flujo.groupby(["ndep_resi", "ndep_not"]).size().reset_index()
            )
            flujo_count.columns = ["Origen", "Destino", "Cantidad"]

            # Ordenar por cantidad
            flujo_count = flujo_count.sort_values("Cantidad", ascending=False)

            # Mostrar top flujos
            top_flujos = min(10, len(flujo_count))

            # Crear gráfico de barras para los flujos principales
            fig = px.bar(
                flujo_count.head(top_flujos),
                x="Cantidad",
                y="Origen",
                color="Destino",
                title=f"Top {top_flujos} Flujos entre Departamentos",
                orientation="h",
                text="Cantidad",
                color_discrete_sequence=px.colors.qualitative.Set3,
            )

            # Actualizar layout
            fig.update_layout(
                title_font=dict(size=16, color="#5A4214"),
                plot_bgcolor="white",
                paper_bgcolor="white",
                margin=dict(l=10, r=10, t=60, b=10),
            )

            # Mostrar gráfico
            st.plotly_chart(fig, use_container_width=True)

            # Explicación
            st.markdown(
                f"""
                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p>Este gráfico muestra los principales flujos de casos entre departamentos de residencia (origen) 
                    y departamentos de notificación (destino). Indica los patrones de movimiento o derivación de pacientes.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Tabla de flujos
            with st.expander("Ver tabla completa de flujos entre departamentos"):
                st.dataframe(flujo_count, use_container_width=True)
        else:
            st.info(
                "No se encontraron casos con diferente departamento de residencia y notificación."
            )

    elif has_residencia:
        # Solo tenemos datos de residencia
        st.warning(
            "Solo hay datos disponibles de lugar de residencia. No se puede realizar la comparativa con lugar de notificación."
        )
        show_departamentos_chart(data, colors, "ndep_resi", "Residencia")

    elif has_notificacion:
        # Solo tenemos datos de notificación
        st.warning(
            "Solo hay datos disponibles de lugar de notificación. No se puede realizar la comparativa con lugar de residencia."
        )
        show_departamentos_chart(data, colors, "ndep_not", "Notificación")

    # Sección 2: Análisis por Municipio
    st.markdown(
        '<h2 style="color: #5A4214; border-bottom: 2px solid #F2A900; padding-bottom: 8px; margin-top: 40px;">Análisis por Municipio</h2>',
        unsafe_allow_html=True,
    )

    # Selector de tipo de ubicación
    location_options = []
    if has_residencia:
        location_options.append("Lugar de Residencia")
    if has_notificacion:
        location_options.append("Lugar de Notificación")

    if location_options:
        location_type = st.radio(
            "Seleccione tipo de ubicación a analizar:",
            location_options,
            horizontal=True,
        )

        # Determinar columnas a usar
        if location_type == "Lugar de Residencia":
            depto_col = "ndep_resi"
            muni_col = "nmun_resi"
        else:  # Lugar de Notificación
            depto_col = "ndep_not"
            muni_col = "nmun_not"

        # Verificar que existan datos para estas columnas
        if depto_col in data["fiebre"].columns and muni_col in data["fiebre"].columns:
            # Obtener lista de departamentos con casos
            departamentos = sorted(data["fiebre"][depto_col].dropna().unique().tolist())

            if departamentos:
                # Selector de departamento
                selected_depto = st.selectbox(
                    f"Seleccione un departamento para ver sus municipios ({location_type}):",
                    ["Todos"] + departamentos,
                )

                # Filtrar por departamento seleccionado
                if selected_depto != "Todos":
                    df_filtrado = data["fiebre"][
                        data["fiebre"][depto_col] == selected_depto
                    ]
                    title_suffix = f" en {selected_depto}"
                else:
                    df_filtrado = data["fiebre"]
                    title_suffix = ""

                # Contar casos por municipio
                muni_count = df_filtrado[muni_col].value_counts().reset_index()
                muni_count.columns = ["Municipio", "Cantidad"]

                # Ordenar por cantidad descendente
                muni_count = muni_count.sort_values("Cantidad", ascending=False)

                # Mostrar top municipios
                top_n = min(15, len(muni_count))
                top_munis = muni_count.head(top_n)

                # Crear gráfico de barras
                fig = px.bar(
                    top_munis,
                    y="Municipio",
                    x="Cantidad",
                    title=f"Top {top_n} Municipios{title_suffix} ({location_type})",
                    color_discrete_sequence=[
                        (
                            colors["primary"]
                            if location_type == "Lugar de Residencia"
                            else colors["secondary"]
                        )
                    ],
                    text="Cantidad",
                    orientation="h",
                )

                # Configurar diseño
                fig.update_layout(
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    margin=dict(l=10, r=10, t=60, b=10),
                    title_font=dict(size=16, color="#5A4214"),
                    yaxis=dict(title=""),
                    xaxis=dict(title="Número de Casos"),
                )

                # Mostrar gráfico
                st.plotly_chart(fig, use_container_width=True)

                # Mostrar tabla completa con paginación si hay muchos municipios
                if len(muni_count) > top_n:
                    st.subheader(f"Tabla Completa de Municipios{title_suffix}")

                    # Añadir opción para mostrar más municipios
                    num_rows = st.slider(
                        "Número de municipios a mostrar",
                        min_value=top_n,
                        max_value=min(100, len(muni_count)),
                        value=20,
                        step=5,
                    )

                    # Mostrar tabla
                    st.dataframe(muni_count.head(num_rows), use_container_width=True)
            else:
                st.warning(
                    f"No hay datos de departamentos disponibles para {location_type}."
                )
        else:
            st.warning(
                f"No se encontraron columnas necesarias para análisis por municipio ({muni_col})."
            )

    # Sección 3: Análisis por Tipo de Zona
    st.markdown(
        '<h2 style="color: #5A4214; border-bottom: 2px solid #F2A900; padding-bottom: 8px; margin-top: 40px;">Análisis por Tipo de Zona</h2>',
        unsafe_allow_html=True,
    )

    if "tip_zona" in data["fiebre"].columns:
        # Mapeo de códigos a descripciones
        zona_mapping = {
            1: "Cabecera Municipal",
            2: "Centro Poblado",
            3: "Rural Disperso",
        }

        # Contar casos por tipo de zona
        zona_count = data["fiebre"]["tip_zona"].value_counts().reset_index()
        zona_count.columns = ["Código Zona", "Cantidad"]

        # Aplicar mapeo
        zona_count["Tipo de Zona"] = (
            zona_count["Código Zona"].map(zona_mapping).fillna("No especificado")
        )

        # Crear gráfico de pastel
        fig = px.pie(
            zona_count,
            names="Tipo de Zona",
            values="Cantidad",
            title="Distribución de Casos por Tipo de Zona",
            color_discrete_sequence=[
                colors["primary"],
                colors["secondary"],
                colors["accent"],
            ],
            hole=0.4,
        )

        # Mejorar presentación
        fig.update_traces(
            textposition="inside",
            textinfo="percent+label+value",
            textfont_size=12,
            marker=dict(line=dict(color="#FFFFFF", width=2)),
        )

        # Configurar diseño
        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=10, r=10, t=60, b=10),
            title_font=dict(size=16, color="#5A4214"),
            legend=dict(
                orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5
            ),
        )

        # Mostrar gráfico
        st.plotly_chart(fig, use_container_width=True)

        # Mostrar tabla
        st.dataframe(zona_count[["Tipo de Zona", "Cantidad"]], use_container_width=True)

        # Análisis cruzado: zona vs condición final
        if "con_fin_" in data["fiebre"].columns:
            st.subheader("Relación entre Tipo de Zona y Condición Final")

            # Crear tabla cruzada
            zona_fin = pd.crosstab(
                data["fiebre"]["tip_zona"].map(zona_mapping),
                data["fiebre"]["con_fin_"].map({1: "Vivo", 2: "Fallecido"}),
                margins=True,
                margins_name="Total",
            )

            # Mostrar tabla
            st.dataframe(zona_fin, use_container_width=True)

            # Cálculo de letalidad por zona
            st.subheader("Letalidad por Tipo de Zona")

            # Preparar datos
            letalidad_zona = []

            for zona, desc in zona_mapping.items():
                # Filtrar casos de esta zona
                casos_zona = data["fiebre"][data["fiebre"]["tip_zona"] == zona]

                # Contar casos y fallecidos
                total = len(casos_zona)
                fallecidos = casos_zona[casos_zona["con_fin_"] == 2].shape[0]

                # Calcular letalidad
                letalidad = (fallecidos / total * 100) if total > 0 else 0

                letalidad_zona.append(
                    {
                        "Tipo de Zona": desc,
                        "Total Casos": total,
                        "Fallecidos": fallecidos,
                        "Letalidad (%)": letalidad,
                    }
                )

            # Crear dataframe y gráfico
            df_letalidad = pd.DataFrame(letalidad_zona)

            # Mostrar gráfico de barras
            fig = px.bar(
                df_letalidad,
                x="Tipo de Zona",
                y="Letalidad (%)",
                title="Tasa de Letalidad por Tipo de Zona",
                color_discrete_sequence=[colors["danger"]],
                text_auto=".1f",
            )

            # Configurar diseño
            fig.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                margin=dict(l=10, r=10, t=60, b=10),
                title_font=dict(size=16, color="#5A4214"),
            )

            # Mostrar gráfico
            st.plotly_chart(fig, use_container_width=True)

            # Explicación
            st.markdown(
                f"""
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h4 style="color: {colors['primary']}; margin-top: 0;">Interpretación</h4>
                    <p>La letalidad por tipo de zona puede reflejar diferencias en:</p>
                    <ul>
                        <li>Acceso a servicios de salud</li>
                        <li>Tiempo hasta la atención médica</li>
                        <li>Condiciones de vida y factores de riesgo</li>
                        <li>Sistemas de notificación y seguimiento de casos</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.warning("No se encontraron datos sobre el tipo de zona en el archivo.")

    # Información de contextualización
    st.markdown(
        '<h2 style="color: #5A4214; border-bottom: 2px solid #F2A900; padding-bottom: 8px; margin-top: 40px;">Consideraciones Importantes</h2>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 30px;">
            <h4 style="color: {colors['primary']}; margin-top: 0;">¿Por qué es importante la distinción entre lugar de residencia y notificación?</h4>
            <ul>
                <li><strong>Planificación de intervenciones</strong>: Las acciones preventivas deben enfocarse en los lugares de residencia, donde ocurre la transmisión.</li>
                <li><strong>Asignación de recursos</strong>: Los servicios de atención deben fortalecerse en los lugares de notificación que reciben casos.</li>
                <li><strong>Movilidad de pacientes</strong>: Permite entender patrones de desplazamiento para atención médica.</li>
                <li><strong>Vigilancia epidemiológica</strong>: Identificar discrepancias ayuda a mejorar los sistemas de vigilancia y notificación.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Pie de página con créditos y fecha de actualización
    fecha_actualizacion = "No disponible"
    if "fecha_actualizacion" in data["metricas"].columns:
        fecha_actualizacion = data["metricas"]["fecha_actualizacion"].iloc[0]

    st.markdown(
        f"""
        <div style="text-align: center; margin-top: 50px; padding-top: 20px; border-top: 1px solid #e0e0e0;">
            <p style="color: #666; font-size: 0.9rem;">
                Dashboard desarrollado para la Secretaría de Salud del Tolima | Datos actualizados al {fecha_actualizacion}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_departamentos_chart(data, colors, depto_column="ndep_resi", tipo="Residencia"):
    """
    Muestra un gráfico de barras con la distribución por departamento.

    Args:
        data (dict): Diccionario con los dataframes
        colors (dict): Colores institucionales
        depto_column (str): Nombre de la columna a utilizar para departamentos
        tipo (str): Tipo de ubicación (Residencia/Notificación)
    """
    # Contar casos por departamento
    depto_count = data["fiebre"][depto_column].value_counts().reset_index()
    depto_count.columns = ["Departamento", "Cantidad"]
    total_casos = depto_count["Cantidad"].sum()

    # Calcular porcentaje
    depto_count["Porcentaje"] = depto_count["Cantidad"] / total_casos * 100

    # Ordenar por cantidad descendente
    depto_count = depto_count.sort_values("Cantidad", ascending=False)

    # Crear gráfico de barras con Plotly
    fig = px.bar(
        depto_count.head(15),
        y="Departamento",
        x="Cantidad",
        title=f"Top 15 Departamentos por {tipo}",
        color_discrete_sequence=[
            colors["primary"] if tipo == "Residencia" else colors["secondary"]
        ],
        text="Cantidad",
        orientation="h",
    )

    # Configurar diseño
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=10, t=40, b=10),
        title={
            "y": 0.98,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": dict(size=16, color="#5A4214"),
        },
        yaxis=dict(title=""),
        xaxis=dict(title="Número de Casos"),
    )

    # Mostrar gráfico
    st.plotly_chart(fig, use_container_width=True)

    # Mostrar tabla completa
    st.subheader(f"Tabla de Casos por Departamento ({tipo})")
    st.dataframe(
        depto_count.rename(
            columns={"Cantidad": "Casos", "Porcentaje": "Porcentaje (%)"}
        ).style.format({"Porcentaje (%)": "{:.2f}%"}),
        use_container_width=True,
    )
