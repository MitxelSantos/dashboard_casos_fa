"""
Módulo para la vista general del dashboard de Fiebre Amarilla.
Contiene las funciones para generar visualizaciones y métricas clave.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime


def show(data, filters, colors):
    """
    Muestra la página de visión general del dashboard.

    Args:
        data (dict): Diccionario con los dataframes
        filters (dict): Filtros seleccionados
        colors (dict): Colores institucionales
    """
    # Título y descripción
    st.markdown(
        '<h1 class="main-title">Fiebre Amarilla - Visión General</h1>',
        unsafe_allow_html=True,
    )

    # Mostrar descripción general con un diseño más atractivo
    st.markdown(
        f"""
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid {colors['primary']}; margin-bottom: 30px;">
            <h3 style="color: {colors['primary']}; margin-top: 0;">¿Qué es la Fiebre Amarilla?</h3>
            <p style="margin-bottom: 5px;">La Fiebre Amarilla es una enfermedad viral aguda transmitida por mosquitos, causada por el virus de la fiebre amarilla.</p>
            <p style="margin-bottom: 5px;">Este dashboard presenta el análisis de casos probables registrados en el departamento del Tolima y casos notificados en este territorio.</p>
            <p>La vigilancia epidemiológica de esta enfermedad es crucial debido a su potencial de causar brotes con alta mortalidad.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Métricas principales
    st.markdown(
        '<h2 style="color: #5A4214; border-bottom: 2px solid #F2A900; padding-bottom: 8px;">Métricas Principales</h2>',
        unsafe_allow_html=True,
    )

    # Calcular métricas generales
    total_casos = len(data["fiebre"])

    # Inicializar contadores
    fallecidos = 0
    fallecidos_confirmados = 0  # Nuevo: contador de fallecidos confirmados
    recuperados = 0
    casos_confirmados_total = 0  # Total de casos confirmados (incluye fallecidos)
    casos_confirmados_activos = 0  # Casos confirmados que siguen activos

    # Preparar dataframe para análisis
    df_analisis = data["fiebre"].copy()

    # Verificar si existen las columnas necesarias
    has_tipo_caso = "tip_cas_" in df_analisis.columns
    has_condicion_final = "con_fin_" in df_analisis.columns
    has_recuperados = "est_rec_" in df_analisis.columns

    # Definir tipos de casos confirmados (si existe la columna)
    tipos_confirmados = [3, 4, 5]  # Confirmado por lab, clínica o nexo

    # Obtener máscara de casos confirmados
    if has_tipo_caso:
        is_confirmado = df_analisis["tip_cas_"].isin(tipos_confirmados)

        # Total de casos confirmados (independientemente del estado)
        casos_confirmados_total = is_confirmado.sum()
    else:
        # Si no hay columna de tipo de caso, no podemos determinar confirmados
        is_confirmado = pd.Series(False, index=df_analisis.index)

    # Contar fallecidos y estado de los casos
    if has_condicion_final:
        # Fallecidos (todos)
        is_fallecido = df_analisis["con_fin_"] == 2
        fallecidos = is_fallecido.sum()

        # Fallecidos confirmados (intersección)
        is_fallecido_confirmado = is_fallecido & is_confirmado
        fallecidos_confirmados = is_fallecido_confirmado.sum()

        # Casos recuperados (si existe esta información)
        if has_recuperados:
            is_recuperado = df_analisis["est_rec_"] == 1
            recuperados = (
                is_recuperado & is_confirmado
            ).sum()  # Solo contar recuperados confirmados

        # Casos confirmados activos = confirmados - (fallecidos confirmados + recuperados confirmados)
        casos_confirmados_activos = casos_confirmados_total - (
            fallecidos_confirmados + recuperados
        )

    # Calcular tasa de letalidad entre los casos confirmados
    # (fallecidos confirmados / total confirmados)
    letalidad_confirmados = (
        (fallecidos_confirmados / casos_confirmados_total * 100)
        if casos_confirmados_total > 0
        else 0
    )

    # Fecha de última actualización
    fecha_actualizacion = datetime.now().strftime("%Y-%m-%d %H:%M")
    if "fecha_actualizacion" in data["metricas"].columns:
        fecha_actualizacion = data["metricas"]["fecha_actualizacion"].iloc[0]

    # Calcular departamento con más casos
    depto_top = "No disponible"
    casos_top_depto = 0

    # Primero intentamos por departamento de notificación si existe
    if "ndep_notif" in data["fiebre"].columns and not data["fiebre"].empty:
        depto_series = data["fiebre"]["ndep_notif"].value_counts()
        if not depto_series.empty:
            depto_top = depto_series.index[0]
            casos_top_depto = depto_series.iloc[0]
    # Si no existe o no tiene datos, usamos departamento de residencia
    elif "ndep_resi" in data["fiebre"].columns and not data["fiebre"].empty:
        depto_series = data["fiebre"]["ndep_resi"].value_counts()
        if not depto_series.empty:
            depto_top = depto_series.index[0]
            casos_top_depto = depto_series.iloc[0]

    # Definir iconos para cada métrica (emojis unicode)
    iconos = {
        "total": "📊",
        "confirmados": "✅",
        "activos": "🔴",
        "fallecidos": "⚠️",
        "recuperados": "🩺",
        "letalidad": "📈",
        "depto": "🌎",
    }

    # Crear columnas para las métricas (layout responsivo)
    if has_recuperados:
        # Si hay datos de recuperados, usar 7 columnas
        cols = st.columns(7)
    else:
        # Si no hay datos de recuperados, usar 6 columnas
        cols = st.columns(6)

    # Función para crear métrica mejorada
    def create_metric_box(col, title, value, subtext=None, color=None, icon=None):
        """Crea una caja de métrica usando Streamlit nativo"""
        with col:
            # CSS personalizado solo para la caja individual
            st.markdown(
                f"""
                <div style="
                    background-color: white;
                    border-radius: 10px;
                    padding: 20px;
                    text-align: center;
                    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                    border-top: 4px solid {color if color else colors['primary']};
                    height: 140px;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    margin-bottom: 20px;
                    transition: transform 0.3s ease;
                ">
                    <div style="font-size: 1.5rem; margin-bottom: 8px;">{icon if icon else '📊'}</div>
                    <div style="
                        font-size: 0.85rem;
                        font-weight: 600;
                        color: #666;
                        margin-bottom: 8px;
                        line-height: 1.2;
                    ">{title}</div>
                    <div style="
                        font-size: 1.6rem;
                        font-weight: 700;
                        color: {color if color else colors['primary']};
                        margin-bottom: 5px;
                    ">{value}</div>
                    {f'<div style="font-size: 0.7rem; color: #666; line-height: 1.1;">{subtext}</div>' if subtext else ''}
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Crear las métricas usando las columnas
    col_idx = 0

    # Métrica: Total de casos probables
    create_metric_box(
        cols[col_idx],
        "Total Casos Probables",
        f"{total_casos:,}",
        color=colors["primary"],
        icon=iconos["total"],
    )
    col_idx += 1

    # Métrica: Total Confirmados
    create_metric_box(
        cols[col_idx],
        "Total Confirmados",
        f"{casos_confirmados_total:,}",
        f"{(casos_confirmados_total/total_casos*100) if total_casos > 0 else 0:.1f}% del total",
        color=colors["secondary"],
        icon=iconos["confirmados"],
    )
    col_idx += 1

    # Métrica: Confirmados Activos
    create_metric_box(
        cols[col_idx],
        "Confirmados Activos",
        f"{casos_confirmados_activos:,}",
        f"{(casos_confirmados_activos/casos_confirmados_total*100) if casos_confirmados_total > 0 else 0:.1f}% de confirmados",
        color=colors["accent"],
        icon=iconos["activos"],
    )
    col_idx += 1

    # Métrica: Recuperados (si está disponible)
    if has_recuperados:
        create_metric_box(
            cols[col_idx],
            "Recuperados",
            f"{recuperados:,}",
            f"{(recuperados/casos_confirmados_total*100) if casos_confirmados_total > 0 else 0:.1f}% de confirmados",
            color=colors["success"],
            icon=iconos["recuperados"],
        )
        col_idx += 1

    # Métrica: Fallecidos Confirmados
    create_metric_box(
        cols[col_idx],
        "Fallecidos Confirmados",
        f"{fallecidos_confirmados:,}",
        f"{(fallecidos_confirmados/casos_confirmados_total*100) if casos_confirmados_total > 0 else 0:.1f}% de confirmados",
        color=colors["danger"],
        icon=iconos["fallecidos"],
    )
    col_idx += 1

    # Métrica: Tasa de letalidad
    create_metric_box(
        cols[col_idx],
        "Letalidad en Confirmados",
        f"{letalidad_confirmados:.2f}%",
        color=colors["warning"],
        icon=iconos["letalidad"],
    )
    col_idx += 1

    # Métrica: Departamento más afectado
    create_metric_box(
        cols[col_idx],
        "Departamento Más Afectado",
        f"{depto_top}",
        f"{casos_top_depto:,} casos",
        color=colors["primary"],
        icon=iconos["depto"],
    )

    # CSS adicional para responsividad
    st.markdown(
        """
        <style>
        /* Responsividad para pantallas pequeñas */
        @media (max-width: 768px) {
            .stColumns > div > div {
                margin-bottom: 10px !important;
            }
        }
        
        /* Hover effect mejorado */
        div[style*="box-shadow"]:hover {
            transform: translateY(-3px) !important;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Información de actualización
    st.markdown(
        f"<div class='update-info'>Última actualización: {fecha_actualizacion}</div>",
        unsafe_allow_html=True,
    )

    # Aclaración sobre los datos
    st.markdown(
        f"""
        <div style="background-color: #f0f8ff; padding: 10px; border-radius: 5px; border-left: 5px solid #4682b4; margin: 20px 0;">
            <p style="margin: 0; font-size: 0.9rem;"><strong>Nota:</strong> Los datos presentados incluyen casos probables notificados en el Tolima y casos donde el paciente reside en el departamento pero pudo ser notificado en otra región. Utilice los filtros para analizar según necesidades específicas.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sección de distribución de casos
    st.markdown(
        '<h2 style="color: #5A4214; border-bottom: 2px solid #F2A900; padding-bottom: 8px; margin-top: 40px;">Distribución de Casos Probables</h2>',
        unsafe_allow_html=True,
    )

    # Organizar los gráficos en dos columnas
    col1, col2 = st.columns(2)

    with col1:
        # Distribución por tipo de caso
        if has_tipo_caso:
            st.subheader("Distribución por Tipo de Caso Probable")

            # Mapeo de códigos a nombres
            tipo_mapping = {
                1: "Sospechoso",
                2: "Probable",
                3: "Confirmado por Laboratorio",
                4: "Confirmado por Clínica",
                5: "Confirmado por Nexo Epidemiológico",
            }

            # Crear copia del dataframe para la transformación
            df_tipo = data["fiebre"].copy()

            # Aplicar mapeo
            df_tipo["tipo_caso_desc"] = (
                df_tipo["tip_cas_"].map(tipo_mapping).fillna("Otro")
            )

            # Contar casos por tipo
            tipo_count = df_tipo["tipo_caso_desc"].value_counts().reset_index()
            tipo_count.columns = ["Tipo de Caso", "Cantidad"]

            # Crear gráfico con Plotly
            fig = px.bar(
                tipo_count,
                x="Tipo de Caso",
                y="Cantidad",
                title="Distribución por Tipo de Caso Probable",
                color_discrete_sequence=[colors["primary"]],
                text="Cantidad",  # Mostrar valores en las barras
            )

            # Configurar para que los números no se giren
            fig.update_traces(
                textangle=0,  # Mantener texto horizontal
                textposition="outside",  # Texto fuera de las barras
                cliponaxis=False,  # Evitar recorte de texto
            )

            # Mejorar layout
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
                xaxis=dict(title=None, tickangle=-45, gridcolor="#f5f5f5"),
                yaxis=dict(title="Número de Casos Probables", gridcolor="#f5f5f5"),
            )

            # Mostrar gráfico
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No se encontraron datos sobre el tipo de caso.")

    with col2:
        # Distribución por condición final y estado (activo/recuperado/fallecido)
        if has_condicion_final:
            st.subheader("Estado Actual de los Casos")

            # Crear dataframe para análisis de estado
            df_estado = df_analisis.copy()

            # Función para determinar el estado completo de cada caso
            def determinar_estado_completo(row):
                # Si no es un caso confirmado
                if not (row["tip_cas_"] in tipos_confirmados):
                    return "Sospechoso/Probable"

                # Si es un caso confirmado
                if row["con_fin_"] == 2:  # Fallecido
                    return "Fallecido (confirmado)"
                elif has_recuperados and row["est_rec_"] == 1:  # Recuperado
                    return "Recuperado"
                else:  # Activo
                    return "Activo (confirmado)"

            # Aplicar función de estado
            df_estado["Estado"] = df_estado.apply(determinar_estado_completo, axis=1)

            # Contar por estado
            estado_count = df_estado["Estado"].value_counts().reset_index()
            estado_count.columns = ["Estado", "Cantidad"]

            # Crear gráfico de pastel con Plotly
            fig = px.pie(
                estado_count,
                names="Estado",
                values="Cantidad",
                title="Estado Actual de los Casos",
                color_discrete_sequence=[
                    colors["danger"],  # Fallecido
                    colors["success"],  # Recuperado
                    colors["accent"],  # Activo
                    colors["secondary"],  # Sospechoso/Probable
                ],
                hole=0.4,
            )

            # Agregar porcentajes en las etiquetas
            fig.update_traces(
                textposition="inside",
                textinfo="percent+label+value",
                textfont_size=12,
                marker=dict(line=dict(color="#FFFFFF", width=2)),
            )

            # Mejorar layout
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
                legend=dict(
                    orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5
                ),
            )

            # Mostrar gráfico
            st.plotly_chart(fig, use_container_width=True)

            # Añadir explicación clara
            st.info(
                """
                **Nota sobre el estado de los casos:**
                - **Fallecido (confirmado)**: Casos fallecidos que fueron confirmados.
                - **Recuperado**: Casos confirmados que se han recuperado.
                - **Activo (confirmado)**: Casos confirmados que continúan activos.
                - **Sospechoso/Probable**: Casos que no han sido confirmados.
            """
            )
        else:
            st.warning("No se encontraron datos sobre la condición final de los casos.")

    # Distribución demográfica
    st.markdown(
        '<h2 style="color: #5A4214; border-bottom: 2px solid #F2A900; padding-bottom: 8px; margin-top: 40px;">Distribución Demográfica</h2>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        if "sexo_" in data["fiebre"].columns:
            st.subheader("Distribución por Sexo")

            # Contar casos por sexo
            sexo_count = data["fiebre"]["sexo_"].value_counts().reset_index()
            sexo_count.columns = ["Sexo", "Cantidad"]

            # Crear gráfico de pastel con Plotly
            fig = px.pie(
                sexo_count,
                names="Sexo",
                values="Cantidad",
                title="Distribución por Sexo",
                color_discrete_sequence=[
                    colors["primary"],
                    colors["secondary"],
                    colors["accent"],
                ],
                hole=0.4,
            )

            # Agregar porcentajes en las etiquetas
            fig.update_traces(
                textposition="inside",
                textinfo="percent+label+value",
                textfont_size=12,
                marker=dict(line=dict(color="#FFFFFF", width=2)),
            )

            # Mejorar layout
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
                legend=dict(
                    orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5
                ),
            )

            # Mostrar gráfico
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No se encontraron datos sobre el sexo.")

    with col2:
        if "edad_" in data["fiebre"].columns:
            st.subheader("Distribución por Edad")

            # Crear rangos de edad
            def crear_grupo_edad(edad):
                if pd.isna(edad):
                    return "No especificado"
                elif edad < 5:
                    return "0-4 años"
                elif edad < 15:
                    return "5-14 años"
                elif edad < 20:
                    return "15-19 años"
                elif edad < 30:
                    return "20-29 años"
                elif edad < 40:
                    return "30-39 años"
                elif edad < 50:
                    return "40-49 años"
                elif edad < 60:
                    return "50-59 años"
                elif edad < 70:
                    return "60-69 años"
                elif edad < 80:
                    return "70-79 años"
                else:
                    return "80+ años"

            # Aplicar función para crear grupos de edad
            df_edad = data["fiebre"].copy()
            df_edad["grupo_edad"] = df_edad["edad_"].apply(crear_grupo_edad)

            # Orden de los grupos de edad
            orden_grupos = [
                "0-4 años",
                "5-14 años",
                "15-19 años",
                "20-29 años",
                "30-39 años",
                "40-49 años",
                "50-59 años",
                "60-69 años",
                "70-79 años",
                "80+ años",
                "No especificado",
            ]

            # Contar casos por grupo de edad
            edad_count = df_edad["grupo_edad"].value_counts().reset_index()
            edad_count.columns = ["Grupo de Edad", "Cantidad"]

            # Reordenar según el orden definido
            edad_count["Grupo de Edad"] = pd.Categorical(
                edad_count["Grupo de Edad"], categories=orden_grupos, ordered=True
            )
            edad_count = edad_count.sort_values("Grupo de Edad")

            # Crear gráfico de barras con Plotly
            fig = px.bar(
                edad_count,
                x="Grupo de Edad",
                y="Cantidad",
                title="Distribución por Grupo de Edad",
                color_discrete_sequence=[colors["secondary"]],
                text="Cantidad",  # Mostrar valores en las barras
            )

            # Configurar para que los números no se giren
            fig.update_traces(
                textangle=0,  # Mantener texto horizontal
                textposition="outside",  # Texto fuera de las barras
                cliponaxis=False,  # Evitar recorte de texto
            )

            # Mejorar layout
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
                xaxis=dict(title=None, tickangle=-45, gridcolor="#f5f5f5"),
                yaxis=dict(title="Número de Casos", gridcolor="#f5f5f5"),
            )

            # Mostrar gráfico
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No se encontraron datos sobre la edad.")

    # Evolución temporal
    st.markdown(
        '<h2 style="color: #5A4214; border-bottom: 2px solid #F2A900; padding-bottom: 8px; margin-top: 40px;">Evolución Temporal</h2>',
        unsafe_allow_html=True,
    )

    if "año" in data["fiebre"].columns:
        # Agrupar por año
        año_count = data["fiebre"]["año"].value_counts().reset_index()
        año_count.columns = ["Año", "Cantidad"]
        año_count = año_count.sort_values("Año")

        # Crear gráfico de área con Plotly para mayor impacto visual
        fig = px.area(
            año_count,
            x="Año",
            y="Cantidad",
            title="Evolución Anual de Casos Probables",
            color_discrete_sequence=[colors["primary"]],
            line_shape="spline",  # Curvas suavizadas
        )

        # Agregar puntos para mejor visualización
        fig.add_trace(
            go.Scatter(
                x=año_count["Año"],
                y=año_count["Cantidad"],
                mode="markers",
                marker=dict(color=colors["secondary"], size=10),
                name="Casos por año",
            )
        )

        # Mejorar layout
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
            showlegend=False,
            xaxis=dict(title="Año", gridcolor="#f5f5f5"),
            yaxis=dict(title="Número de Casos Probables", gridcolor="#f5f5f5"),
        )

        # Mostrar gráfico
        st.plotly_chart(fig, use_container_width=True)

        # Agregar análisis de tendencia
        if len(año_count) >= 3:
            # Calcular tendencia simple
            primeros_años = año_count.head(3)["Cantidad"].mean()
            últimos_años = año_count.tail(3)["Cantidad"].mean()

            cambio = últimos_años - primeros_años
            cambio_porcentual = (
                (cambio / primeros_años * 100) if primeros_años > 0 else 0
            )

            # Mostrar análisis
            if cambio_porcentual > 10:
                tendencia_color = colors["danger"]
                tendencia_texto = f"Tendencia creciente: Aumento del {cambio_porcentual:.1f}% en los casos"
                tendencia_icon = "⚠️"
            elif cambio_porcentual < -10:
                tendencia_color = colors["success"]
                tendencia_texto = f"Tendencia decreciente: Disminución del {abs(cambio_porcentual):.1f}% en los casos"
                tendencia_icon = "✅"
            else:
                tendencia_color = colors["accent"]
                tendencia_texto = f"Tendencia estable: Variación del {abs(cambio_porcentual):.1f}% en los casos"
                tendencia_icon = "ℹ️"

            st.markdown(
                f"""
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid {tendencia_color}; margin: 20px 0;">
                    <h3 style="color: {tendencia_color}; margin-top: 0;"><span style="font-size: 1.5rem; margin-right: 10px;">{tendencia_icon}</span> Análisis de Tendencia</h3>
                    <p style="margin-bottom: 0;"><strong>{tendencia_texto}</strong> al comparar los promedios de los primeros y últimos períodos del análisis.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.warning("No se encontraron datos sobre el año de los casos.")

    # Analizar casos activos
    st.markdown(
        '<h2 style="color: #5A4214; border-bottom: 2px solid #F2A900; padding-bottom: 8px; margin-top: 40px;">Análisis de Casos Activos</h2>',
        unsafe_allow_html=True,
    )

    # Verificar si podemos obtener datos de casos activos
    if casos_confirmados_activos > 0 and has_tipo_caso and has_condicion_final:
        # Filtrar casos activos
        df_activos = data["fiebre"].copy()

        # Definir casos activos (confirmados y no fallecidos)
        df_activos = df_activos[
            df_activos["tip_cas_"].isin(tipos_confirmados)
            & (df_activos["con_fin_"] != 2)
        ]

        # Si hay columna est_rec_, excluir recuperados
        if has_recuperados:
            df_activos = df_activos[df_activos["est_rec_"] != 1]

        # Información general sobre casos activos
        col1, col2 = st.columns(2)

        with col1:
            # Distribución de casos activos por sexo
            if "sexo_" in df_activos.columns:
                sexo_activos = df_activos["sexo_"].value_counts().reset_index()
                sexo_activos.columns = ["Sexo", "Cantidad"]

                # Gráfico de pastel
                fig = px.pie(
                    sexo_activos,
                    names="Sexo",
                    values="Cantidad",
                    title="Casos Activos por Sexo",
                    color_discrete_sequence=[colors["primary"], colors["secondary"]],
                    hole=0.4,
                )

                # Configurar layout
                fig.update_layout(
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    margin=dict(l=10, r=10, t=40, b=10),
                    title={"y": 0.98, "x": 0.5, "xanchor": "center", "yanchor": "top"},
                    title_font=dict(size=16),
                )

                st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Distribución de casos activos por grupo de edad
            if "edad_" in df_activos.columns:
                # Aplicar función para crear grupos de edad
                df_activos["grupo_edad"] = df_activos["edad_"].apply(crear_grupo_edad)

                # Contar casos por grupo de edad
                edad_activos = df_activos["grupo_edad"].value_counts().reset_index()
                edad_activos.columns = ["Grupo de Edad", "Cantidad"]

                # Reordenar según el orden definido
                orden_grupos = [
                    "0-4 años",
                    "5-14 años",
                    "15-19 años",
                    "20-29 años",
                    "30-39 años",
                    "40-49 años",
                    "50-59 años",
                    "60-69 años",
                    "70-79 años",
                    "80+ años",
                    "No especificado",
                ]
                edad_activos["Grupo de Edad"] = pd.Categorical(
                    edad_activos["Grupo de Edad"], categories=orden_grupos, ordered=True
                )
                edad_activos = edad_activos.sort_values("Grupo de Edad")

                # Crear gráfico de barras
                fig = px.bar(
                    edad_activos,
                    x="Grupo de Edad",
                    y="Cantidad",
                    title="Casos Activos por Grupo de Edad",
                    color_discrete_sequence=[colors["accent"]],
                    text="Cantidad",
                )

                # Configurar para que los números no se giren
                fig.update_traces(textangle=0, textposition="outside", cliponaxis=False)

                # Configurar layout
                fig.update_layout(
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    margin=dict(l=10, r=10, t=40, b=10),
                    title={"y": 0.98, "x": 0.5, "xanchor": "center", "yanchor": "top"},
                    title_font=dict(size=16),
                    xaxis=dict(tickangle=-45),
                )

                st.plotly_chart(fig, use_container_width=True)

        # Mostrar tabla de casos activos por departamento
        if "ndep_resi" in df_activos.columns:
            st.subheader("Distribución Geográfica de Casos Activos")

            # Contar casos activos por departamento
            depto_activos = df_activos["ndep_resi"].value_counts().reset_index()
            depto_activos.columns = ["Departamento", "Casos Activos"]

            # Mostrar tabla de casos activos por departamento
            st.dataframe(
                depto_activos.style.format({"Casos Activos": "{:,}"}),
                use_container_width=True,
            )
    else:
        st.info(
            "No hay casos activos para mostrar o no se cuenta con la información necesaria para identificarlos."
        )

    # Distribución geográfica resumida
    st.markdown(
        '<h2 style="color: #5A4214; border-bottom: 2px solid #F2A900; padding-bottom: 8px; margin-top: 40px;">Distribución Geográfica</h2>',
        unsafe_allow_html=True,
    )

    # Analizar por lugar de notificación vs lugar de residencia
    st.markdown(
        f"""
        <div style="background-color: #f5f5f5; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
            <h3 style="color: {colors['primary']}; margin-top: 0;">Nota sobre Distribución Geográfica</h3>
            <p>El análisis geográfico considera dos aspectos importantes:</p>
            <ul>
                <li><strong>Lugar de residencia</strong>: Donde vive la persona afectada.</li>
                <li><strong>Lugar de notificación</strong>: Donde se reportó el caso al sistema de vigilancia.</li>
            </ul>
            <p style="margin-bottom: 0;">Estos pueden diferir, y es importante considerarlo para la planificación de intervenciones.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    # Determinar qué columnas de ubicación utilizar
    with col1:
        # Mostrar datos por departamento de residencia
        if "ndep_resi" in data["fiebre"].columns:
            st.subheader("Por Departamento de Residencia")

            # Contar casos por departamento
            depto_resi = data["fiebre"]["ndep_resi"].value_counts().reset_index()
            depto_resi.columns = ["Departamento", "Cantidad"]
            depto_resi = depto_resi.sort_values("Cantidad", ascending=False).head(10)

            # Crear gráfico de barras horizontales con Plotly
            fig = px.bar(
                depto_resi,
                y="Departamento",
                x="Cantidad",
                title="Top 10 Departamentos de Residencia",
                color_discrete_sequence=[colors["primary"]],
                text="Cantidad",
                orientation="h",
            )

            # Configurar para que los números no se giren
            fig.update_traces(textangle=0, textposition="outside", cliponaxis=False)

            # Mejorar layout
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
                xaxis=dict(title="Número de Casos Probables", gridcolor="#f5f5f5"),
                yaxis=dict(title=None, gridcolor="#f5f5f5"),
            )

            # Mostrar gráfico
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No se encontraron datos sobre departamentos de residencia.")

    with col2:
        # Mostrar datos por departamento de notificación si existe
        if "ndep_notif" in data["fiebre"].columns:
            st.subheader("Por Departamento de Notificación")

            # Contar casos por departamento de notificación
            depto_not = data["fiebre"]["ndep_notif"].value_counts().reset_index()
            depto_not.columns = ["Departamento", "Cantidad"]
            depto_not = depto_not.sort_values("Cantidad", ascending=False).head(10)

            # Crear gráfico de barras horizontales con Plotly
            fig = px.bar(
                depto_not,
                y="Departamento",
                x="Cantidad",
                title="Top 10 Departamentos de Notificación",
                color_discrete_sequence=[colors["secondary"]],
                text="Cantidad",
                orientation="h",
            )

            # Configurar para que los números no se giren
            fig.update_traces(textangle=0, textposition="outside", cliponaxis=False)

            # Mejorar layout
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
                xaxis=dict(title="Número de Casos Probables", gridcolor="#f5f5f5"),
                yaxis=dict(title=None, gridcolor="#f5f5f5"),
            )

            # Mostrar gráfico
            st.plotly_chart(fig, use_container_width=True)
        elif "nmun_resi" in data["fiebre"].columns:
            # Si no hay departamento de notificación, mostrar municipios de residencia
            st.subheader("Top 10 Municipios")

            # Contar casos por municipio
            muni_count = data["fiebre"]["nmun_resi"].value_counts().reset_index()
            muni_count.columns = ["Municipio", "Cantidad"]
            muni_count = muni_count.sort_values("Cantidad", ascending=False).head(10)

            # Crear gráfico
            fig = px.bar(
                muni_count,
                y="Municipio",
                x="Cantidad",
                title="Top 10 Municipios con más Casos",
                color_discrete_sequence=[colors["secondary"]],
                text="Cantidad",
                orientation="h",
            )

            # Configurar para que los números no se giren
            fig.update_traces(textangle=0, textposition="outside", cliponaxis=False)

            # Mejorar layout
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
                xaxis=dict(title="Número de Casos Probables", gridcolor="#f5f5f5"),
                yaxis=dict(title=None, gridcolor="#f5f5f5"),
            )

            # Mostrar gráfico
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(
                "No se encontraron datos sobre departamentos de notificación o municipios."
            )

    # Información adicional y enlaces
    st.markdown(
        '<h2 style="color: #5A4214; border-bottom: 2px solid #F2A900; padding-bottom: 8px; margin-top: 40px;">Información Adicional</h2>',
        unsafe_allow_html=True,
    )

    # Panel informativo con más información sobre la enfermedad
    st.markdown(
        f"""
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 30px;">
            <h3 style="color: {colors['primary']}; margin-top: 0;">Sobre la Fiebre Amarilla</h3>
            <p><strong>Síntomas:</strong> Fiebre, dolores musculares, náuseas, vómitos, fatiga y en casos graves ictericia, insuficiencia renal y hepática.</p>
            <p><strong>Transmisión:</strong> A través de la picadura de mosquitos infectados, principalmente de los géneros Aedes y Haemagogus.</p>
            <p><strong>Prevención:</strong> La vacunación es la medida de prevención más efectiva. Una sola dosis proporciona inmunidad de por vida.</p>
            <p><strong>Población en riesgo:</strong> Personas que viven o viajan a zonas endémicas, especialmente áreas tropicales y subtropicales.</p>
            <hr style="margin: 15px 0;">
            <p style="font-style: italic; margin-bottom: 0;">Para más información, consulte los lineamientos del Ministerio de Salud y Protección Social.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Pie de página con créditos
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


def create_metric_card(title, value, delta=None, color="#AB0520"):
    """
    Crea una tarjeta de métrica estilizada.

    Args:
        title (str): Título de la métrica
        value (str): Valor de la métrica
        delta (str): Texto de cambio o información adicional
        color (str): Color de la tarjeta
    """
    # CSS personalizado para crear la tarjeta
    st.markdown(
        f"""
        <div style="background-color: white; padding: 15px; border-radius: 5px; border-left: 5px solid {color}; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);">
            <h3 style="color: #333; font-size: 16px; margin-bottom: 5px;">{title}</h3>
            <p style="color: {color}; font-size: 24px; font-weight: bold; margin: 0;">{value}</p>
            {f'<p style="color: #666; font-size: 12px; margin-top: 5px;">{delta}</p>' if delta else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )
