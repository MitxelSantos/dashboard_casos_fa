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
    st.markdown('<h1 class="main-title">Fiebre Amarilla - Visión General</h1>', unsafe_allow_html=True)

    # Mostrar descripción general con un diseño más atractivo
    st.markdown(
        f"""
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid {colors['primary']}; margin-bottom: 30px;">
            <h3 style="color: {colors['primary']}; margin-top: 0;">¿Qué es la Fiebre Amarilla?</h3>
            <p style="margin-bottom: 5px;">La Fiebre Amarilla es una enfermedad viral aguda transmitida por mosquitos, causada por el virus de la fiebre amarilla.</p>
            <p style="margin-bottom: 5px;">Este dashboard presenta el análisis de casos registrados en Colombia, con enfoque particular en el departamento del Tolima.</p>
            <p>La vigilancia epidemiológica de esta enfermedad es crucial debido a su potencial de causar brotes con alta mortalidad.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Métricas principales
    st.markdown('<h2 style="color: #5A4214; border-bottom: 2px solid #F2A900; padding-bottom: 8px;">Métricas Principales</h2>', unsafe_allow_html=True)

    # Calcular métricas generales
    total_casos = len(data["fiebre"])
    
    # Métricas de letalidad
    letalidad = 0
    fallecidos = 0
    if "con_fin_" in data["fiebre"].columns:
        fallecidos = data["fiebre"][data["fiebre"]["con_fin_"] == 2].shape[0]
        letalidad = (fallecidos / total_casos * 100) if total_casos > 0 else 0
    
    # Casos confirmados
    confirmados = 0
    if "tip_cas_" in data["fiebre"].columns:
        # Contar casos confirmados (tipos 3, 4 y 5)
        confirmados = data["fiebre"][data["fiebre"]["tip_cas_"].isin([3, 4, 5])].shape[0]
    
    # Fecha de última actualización
    fecha_actualizacion = datetime.now().strftime("%Y-%m-%d %H:%M")
    if "fecha_actualizacion" in data["metricas"].columns:
        fecha_actualizacion = data["metricas"]["fecha_actualizacion"].iloc[0]
    
    # Calcular departamento con más casos
    depto_top = "No disponible"
    casos_top_depto = 0
    if "ndep_resi" in data["fiebre"].columns and not data["fiebre"].empty:
        depto_series = data["fiebre"]["ndep_resi"].value_counts()
        if not depto_series.empty:
            depto_top = depto_series.index[0]
            casos_top_depto = depto_series.iloc[0]
    
    # Definir iconos para cada métrica (emojis unicode)
    iconos = {
        "total": "📊",
        "confirmados": "✅",
        "fallecidos": "⚠️",
        "letalidad": "📈",
        "depto": "🌎",
    }
    
    # Crear contenedor para métricas con CSS Grid para mejor disposición
    st.markdown(
        f"""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 30px;">
            <div class="big-metric-container" style="border-top: 5px solid {colors['primary']}">
                <div style="font-size: 2rem; margin-bottom: 5px;">{iconos["total"]}</div>
                <div class="big-metric-title">Total de Casos</div>
                <div class="big-metric-value" style="color: {colors['primary']};">{total_casos:,}</div>
            </div>
            
            <div class="big-metric-container" style="border-top: 5px solid {colors['secondary']}">
                <div style="font-size: 2rem; margin-bottom: 5px;">{iconos["confirmados"]}</div>
                <div class="big-metric-title">Casos Confirmados</div>
                <div class="big-metric-value" style="color: {colors['secondary']};">{confirmados:,}</div>
                <div style="font-size: 0.9rem; color: #666;">{(confirmados/total_casos*100) if total_casos > 0 else 0:.1f}% del total</div>
            </div>
            
            <div class="big-metric-container" style="border-top: 5px solid {colors['danger']}">
                <div style="font-size: 2rem; margin-bottom: 5px;">{iconos["fallecidos"]}</div>
                <div class="big-metric-title">Fallecidos</div>
                <div class="big-metric-value" style="color: {colors['danger']};">{fallecidos:,}</div>
            </div>
            
            <div class="big-metric-container" style="border-top: 5px solid {colors['warning']}">
                <div style="font-size: 2rem; margin-bottom: 5px;">{iconos["letalidad"]}</div>
                <div class="big-metric-title">Tasa de Letalidad</div>
                <div class="big-metric-value" style="color: {colors['warning']};">{letalidad:.2f}%</div>
            </div>
            
            <div class="big-metric-container" style="border-top: 5px solid {colors['accent']}">
                <div style="font-size: 2rem; margin-bottom: 5px;">{iconos["depto"]}</div>
                <div class="big-metric-title">Departamento Más Afectado</div>
                <div class="big-metric-value" style="color: {colors['accent']};">{depto_top}</div>
                <div style="font-size: 0.9rem; color: #666;">{casos_top_depto:,} casos</div>
            </div>
        </div>
        
        <div class="update-info">Última actualización: {fecha_actualizacion}</div>
        """,
        unsafe_allow_html=True
    )

    # Sección de distribución de casos
    st.markdown('<h2 style="color: #5A4214; border-bottom: 2px solid #F2A900; padding-bottom: 8px; margin-top: 40px;">Distribución de Casos</h2>', unsafe_allow_html=True)

    # Organizar los gráficos en dos columnas
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribución por tipo de caso
        if "tip_cas_" in data["fiebre"].columns:
            st.subheader("Distribución por Tipo de Caso")
            
            # Mapeo de códigos a nombres
            tipo_mapping = {
                1: "Sospechoso", 
                2: "Probable", 
                3: "Confirmado por Laboratorio",
                4: "Confirmado por Clínica",
                5: "Confirmado por Nexo Epidemiológico"
            }
            
            # Crear copia del dataframe para la transformación
            df_tipo = data["fiebre"].copy()
            
            # Aplicar mapeo
            df_tipo["tipo_caso_desc"] = df_tipo["tip_cas_"].map(tipo_mapping).fillna("Otro")
            
            # Contar casos por tipo
            tipo_count = df_tipo["tipo_caso_desc"].value_counts().reset_index()
            tipo_count.columns = ["Tipo de Caso", "Cantidad"]
            
            # Crear gráfico con Plotly
            fig = px.bar(
                tipo_count, 
                x="Tipo de Caso", 
                y="Cantidad",
                title="Distribución por Tipo de Caso",
                color_discrete_sequence=[colors["primary"]],
                text="Cantidad"  # Mostrar valores en las barras
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
                    "font": dict(size=16, color="#5A4214")
                },
                xaxis=dict(
                    title=None,
                    tickangle=-45,
                    gridcolor="#f5f5f5"
                ),
                yaxis=dict(
                    title="Número de Casos",
                    gridcolor="#f5f5f5"
                )
            )
            
            # Mostrar gráfico
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No se encontraron datos sobre el tipo de caso.")
    
    with col2:
        # Distribución por condición final
        if "con_fin_" in data["fiebre"].columns:
            st.subheader("Condición Final de los Casos")
            
            # Mapeo de códigos a nombres
            condicion_mapping = {
                1: "Vivo", 
                2: "Fallecido"
            }
            
            # Crear copia del dataframe para la transformación
            df_condicion = data["fiebre"].copy()
            
            # Aplicar mapeo
            df_condicion["condicion_desc"] = df_condicion["con_fin_"].map(condicion_mapping).fillna("No especificado")
            
            # Contar casos por condición
            condicion_count = df_condicion["condicion_desc"].value_counts().reset_index()
            condicion_count.columns = ["Condición Final", "Cantidad"]
            
            # Crear gráfico de pastel con Plotly
            fig = px.pie(
                condicion_count, 
                names="Condición Final", 
                values="Cantidad",
                title="Condición Final de los Casos",
                color_discrete_sequence=[colors["primary"], colors["danger"], colors["accent"]],
                hole=0.4
            )
            
            # Agregar porcentajes en las etiquetas
            fig.update_traces(
                textposition='inside',
                textinfo='percent+label+value',
                textfont_size=12,
                marker=dict(line=dict(color='#FFFFFF', width=2))
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
                    "font": dict(size=16, color="#5A4214")
                },
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.2,
                    xanchor="center",
                    x=0.5
                )
            )
            
            # Mostrar gráfico
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No se encontraron datos sobre la condición final.")

    # Distribución demográfica
    st.markdown('<h2 style="color: #5A4214; border-bottom: 2px solid #F2A900; padding-bottom: 8px; margin-top: 40px;">Distribución Demográfica</h2>', unsafe_allow_html=True)
    
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
                color_discrete_sequence=[colors["primary"], colors["secondary"], colors["accent"]],
                hole=0.4
            )
            
            # Agregar porcentajes en las etiquetas
            fig.update_traces(
                textposition='inside',
                textinfo='percent+label+value',
                textfont_size=12,
                marker=dict(line=dict(color='#FFFFFF', width=2))
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
                    "font": dict(size=16, color="#5A4214")
                },
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.2,
                    xanchor="center",
                    x=0.5
                )
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
                "0-4 años", "5-14 años", "15-19 años", "20-29 años",
                "30-39 años", "40-49 años", "50-59 años", "60-69 años",
                "70-79 años", "80+ años", "No especificado"
            ]
            
            # Contar casos por grupo de edad
            edad_count = df_edad["grupo_edad"].value_counts().reset_index()
            edad_count.columns = ["Grupo de Edad", "Cantidad"]
            
            # Reordenar según el orden definido
            edad_count["Grupo de Edad"] = pd.Categorical(
                edad_count["Grupo de Edad"],
                categories=orden_grupos,
                ordered=True
            )
            edad_count = edad_count.sort_values("Grupo de Edad")
            
            # Crear gráfico de barras con Plotly
            fig = px.bar(
                edad_count, 
                x="Grupo de Edad", 
                y="Cantidad",
                title="Distribución por Grupo de Edad",
                color_discrete_sequence=[colors["secondary"]],
                text="Cantidad"  # Mostrar valores en las barras
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
                    "font": dict(size=16, color="#5A4214")
                },
                xaxis=dict(
                    title=None,
                    tickangle=-45,
                    gridcolor="#f5f5f5"
                ),
                yaxis=dict(
                    title="Número de Casos",
                    gridcolor="#f5f5f5"
                )
            )
            
            # Mostrar gráfico
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No se encontraron datos sobre la edad.")

    # Evolución temporal
    st.markdown('<h2 style="color: #5A4214; border-bottom: 2px solid #F2A900; padding-bottom: 8px; margin-top: 40px;">Evolución Temporal</h2>', unsafe_allow_html=True)
    
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
            title="Evolución Anual de Casos",
            color_discrete_sequence=[colors["primary"]],
            line_shape="spline"  # Curvas suavizadas
        )
        
        # Agregar puntos para mejor visualización
        fig.add_trace(
            go.Scatter(
                x=año_count["Año"],
                y=año_count["Cantidad"],
                mode="markers",
                marker=dict(color=colors["secondary"], size=10),
                name="Casos por año"
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
                "font": dict(size=16, color="#5A4214")
            },
            showlegend=False,
            xaxis=dict(
                title="Año",
                gridcolor="#f5f5f5"
            ),
            yaxis=dict(
                title="Número de Casos",
                gridcolor="#f5f5f5"
            )
        )
        
        # Mostrar gráfico
        st.plotly_chart(fig, use_container_width=True)
        
        # Agregar análisis de tendencia
        if len(año_count) >= 3:
            # Calcular tendencia simple
            primeros_años = año_count.head(3)["Cantidad"].mean()
            últimos_años = año_count.tail(3)["Cantidad"].mean()
            
            cambio = últimos_años - primeros_años
            cambio_porcentual = (cambio / primeros_años * 100) if primeros_años > 0 else 0
            
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
                unsafe_allow_html=True
            )
    else:
        st.warning("No se encontraron datos sobre el año de los casos.")

    # Distribución geográfica resumida
    st.markdown('<h2 style="color: #5A4214; border-bottom: 2px solid #F2A900; padding-bottom: 8px; margin-top: 40px;">Distribución Geográfica</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if "ndep_resi" in data["fiebre"].columns:
            st.subheader("Top 10 Departamentos")
            
            # Contar casos por departamento
            depto_count = data["fiebre"]["ndep_resi"].value_counts().reset_index()
            depto_count.columns = ["Departamento", "Cantidad"]
            depto_count = depto_count.sort_values("Cantidad", ascending=False).head(10)
            
            # Crear gráfico de barras horizontales con Plotly
            fig = px.bar(
                depto_count, 
                y="Departamento", 
                x="Cantidad",
                title="Top 10 Departamentos con más Casos",
                color_discrete_sequence=[colors["primary"]],
                text="Cantidad",
                orientation="h"
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
                    "font": dict(size=16, color="#5A4214")
                },
                xaxis=dict(
                    title="Número de Casos",
                    gridcolor="#f5f5f5"
                ),
                yaxis=dict(
                    title=None,
                    gridcolor="#f5f5f5"
                )
            )
            
            # Mostrar gráfico
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No se encontraron datos sobre departamentos.")
    
    with col2:
        if "nmun_resi" in data["fiebre"].columns:
            st.subheader("Top 10 Municipios")
            
            # Contar casos por municipio
            muni_count = data["fiebre"]["nmun_resi"].value_counts().reset_index()
            muni_count.columns = ["Municipio", "Cantidad"]
            muni_count = muni_count.sort_values("Cantidad", ascending=False).head(10)
            
            # Crear gráfico de barras horizontales con Plotly
            fig = px.bar(
                muni_count, 
                y="Municipio", 
                x="Cantidad",
                title="Top 10 Municipios con más Casos",
                color_discrete_sequence=[colors["secondary"]],
                text="Cantidad",
                orientation="h"
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
                    "font": dict(size=16, color="#5A4214")
                },
                xaxis=dict(
                    title="Número de Casos",
                    gridcolor="#f5f5f5"
                ),
                yaxis=dict(
                    title=None,
                    gridcolor="#f5f5f5"
                )
            )
            
            # Mostrar gráfico
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No se encontraron datos sobre municipios.")

    # Información adicional y enlaces
    st.markdown('<h2 style="color: #5A4214; border-bottom: 2px solid #F2A900; padding-bottom: 8px; margin-top: 40px;">Información Adicional</h2>', unsafe_allow_html=True)
    
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
        unsafe_allow_html=True
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
        unsafe_allow_html=True
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
        unsafe_allow_html=True
    )