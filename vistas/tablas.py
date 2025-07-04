"""
Vista de información principal SIMPLIFICADA del dashboard de Fiebre Amarilla.
NUEVA: Solo gráficos, análisis y tablas (SIN tarjetas métricas)
Las tarjetas fueron trasladadas a la vista de mapas.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
from utils.data_processor import prepare_dataframe_for_display


def show(data_filtered, filters, colors):
    """
    NUEVA: Vista simplificada SOLO con gráficos, análisis y tablas.
    Las tarjetas métricas fueron trasladadas a la vista de mapas.

    Args:
        data_filtered (dict): Datos filtrados
        filters (dict): Filtros aplicados
        colors (dict): Colores institucionales
    """
    casos = data_filtered["casos"]
    epizootias = data_filtered["epizootias"]

    # **NUEVO TÍTULO**: Aclarar que las métricas están en mapas
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {colors['info']}, {colors['secondary']});
            color: white;
            padding: 15px 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        ">
            <h2 style="margin: 0; font-size: 1.5rem;">📊 Análisis Epidemiológico Detallado</h2>
            <p style="margin: 5px 0 0 0; opacity: 0.9; font-size: 0.9rem;">
                💡 <strong>Tip:</strong> Las métricas y tarjetas informativas están en la pestaña "🗺️ Mapas Interactivos"
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # **SECCIÓN 1**: Análisis epidemiológico (SIN tarjetas métricas)
    show_epidemiological_analysis_charts(casos, epizootias, colors, filters)

    st.markdown("---")
    
    # **SECCIÓN 2**: Distribución geográfica mejorada
    show_enhanced_geographic_analysis(casos, epizootias, colors, filters)
    
    st.markdown("---")
    
    # **SECCIÓN 3**: Tablas de datos detalladas
    show_detailed_data_tables(casos, epizootias, colors)
    
    st.markdown("---")
    
    # **SECCIÓN 4**: Exportación de datos completa
    show_advanced_export_section(casos, epizootias)


def show_epidemiological_analysis_charts(casos, epizootias, colors, filters):
    """
    NUEVO: Análisis epidemiológico enfocado en gráficos y visualizaciones.
    """
    st.subheader("📈 Análisis Epidemiológico")
    
    # **SUBSECCIÓN A**: Casos Humanos - Análisis demográfico
    st.markdown("### 🦠 Casos Humanos - Análisis Demográfico")
    
    if not casos.empty:
        # Primera fila: Análisis por sexo y edad
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**📊 Distribución por Sexo**")
            if "sexo" in casos.columns:
                sexo_dist = casos["sexo"].value_counts()
                if not sexo_dist.empty:
                    fig_sexo = px.pie(
                        values=sexo_dist.values,
                        names=sexo_dist.index,
                        title="Casos por Género",
                        color_discrete_map={
                            "Masculino": colors["info"],
                            "Femenino": colors["secondary"],
                        },
                        hole=0.4  # Donut chart
                    )
                    fig_sexo.update_layout(height=350)
                    fig_sexo.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_sexo, use_container_width=True)
                else:
                    st.info("No hay datos de sexo disponibles")
            else:
                st.info("No hay datos de sexo en los casos")

        with col2:
            st.markdown("**📈 Distribución por Grupos de Edad**")
            if "edad" in casos.columns:
                casos_edad = casos.dropna(subset=["edad"]).copy()
                
                if not casos_edad.empty:
                    # Crear grupos de edad más detallados
                    casos_edad["grupo_edad"] = pd.cut(
                        casos_edad["edad"], 
                        bins=[0, 10, 20, 30, 40, 50, 60, 70, 80, 100], 
                        labels=["0-10", "11-20", "21-30", "31-40", "41-50", "51-60", "61-70", "71-80", "80+"],
                        include_lowest=True
                    )
                    
                    edad_counts = casos_edad["grupo_edad"].value_counts().sort_index()
                    
                    if not edad_counts.empty:
                        fig_edad = px.bar(
                            x=edad_counts.index,
                            y=edad_counts.values,
                            title="Casos por Grupo de Edad",
                            labels={"x": "Grupo de Edad", "y": "Número de Casos"},
                            color=edad_counts.values,
                            color_continuous_scale="Reds",
                        )
                        fig_edad.update_layout(height=350, showlegend=False)
                        st.plotly_chart(fig_edad, use_container_width=True)
                    else:
                        st.info("No hay datos suficientes para grupos de edad")
                else:
                    st.info("No hay datos de edad disponibles")
            else:
                st.info("No hay datos de edad en los casos")

        # Segunda fila: Análisis avanzado
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**⚰️ Análisis de Letalidad por Edad y Sexo**")
            if "condicion_final" in casos.columns and "edad" in casos.columns and "sexo" in casos.columns:
                casos_completos = casos.dropna(subset=["condicion_final", "edad", "sexo"]).copy()
                
                if not casos_completos.empty:
                    casos_completos["grupo_edad"] = pd.cut(
                        casos_completos["edad"], 
                        bins=[0, 20, 40, 60, 100], 
                        labels=["0-20", "21-40", "41-60", "60+"],
                        include_lowest=True
                    )
                    
                    # Calcular letalidad por grupo de edad y sexo
                    letalidad_data = casos_completos.groupby(["grupo_edad", "sexo", "condicion_final"]).size().reset_index(name="count")
                    
                    if not letalidad_data.empty:
                        fig_letalidad = px.sunburst(
                            letalidad_data,
                            path=["grupo_edad", "sexo", "condicion_final"],
                            values="count",
                            title="Letalidad por Edad y Sexo",
                            color="count",
                            color_continuous_scale="RdYlBu_r"
                        )
                        fig_letalidad.update_layout(height=350)
                        st.plotly_chart(fig_letalidad, use_container_width=True)
                    else:
                        st.info("Datos insuficientes para análisis de letalidad")
                else:
                    st.info("Datos incompletos para análisis de letalidad")
            else:
                st.info("Faltan datos de condición final, edad o sexo")

        with col2:
            st.markdown("**📅 Evolución Temporal de Casos**")
            if "fecha_inicio_sintomas" in casos.columns:
                casos_fecha = casos.dropna(subset=["fecha_inicio_sintomas"]).copy()
                
                if not casos_fecha.empty:
                    # Agrupar por mes
                    casos_fecha["año_mes"] = casos_fecha["fecha_inicio_sintomas"].dt.to_period("M")
                    casos_temporal = casos_fecha.groupby("año_mes").size().reset_index(name="casos")
                    casos_temporal["fecha"] = casos_temporal["año_mes"].dt.to_timestamp()
                    
                    if not casos_temporal.empty:
                        fig_temporal = px.line(
                            casos_temporal,
                            x="fecha",
                            y="casos",
                            title="Casos por Mes",
                            labels={"fecha": "Fecha", "casos": "Número de Casos"},
                            markers=True
                        )
                        fig_temporal.update_traces(line=dict(color=colors["danger"], width=3))
                        fig_temporal.update_layout(height=350)
                        st.plotly_chart(fig_temporal, use_container_width=True)
                    else:
                        st.info("No hay datos temporales suficientes")
                else:
                    st.info("No hay fechas de casos disponibles")
            else:
                st.info("No hay datos de fechas en los casos")

    else:
        st.info("⚠️ No hay casos disponibles para analizar con los filtros actuales")

    # **SUBSECCIÓN B**: Epizootias - Análisis de fuentes y distribución
    st.markdown("---")
    st.markdown("### 🐒 Epizootias - Análisis de Vigilancia")
    
    if not epizootias.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📋 Análisis de Fuentes de Epizootias**")
            if "proveniente" in epizootias.columns:
                fuente_dist = epizootias["proveniente"].value_counts()

                # Simplificar nombres de fuentes
                fuente_dist_simplified = {}
                for fuente, count in fuente_dist.items():
                    if "VIGILANCIA COMUNITARIA" in str(fuente):
                        fuente_dist_simplified["Vigilancia Comunitaria"] = fuente_dist_simplified.get("Vigilancia Comunitaria", 0) + count
                    elif "INCAUTACIÓN" in str(fuente):
                        fuente_dist_simplified["Incautación/Rescate"] = fuente_dist_simplified.get("Incautación/Rescate", 0) + count
                    else:
                        fuente_simplified = str(fuente)[:25] + "..." if len(str(fuente)) > 25 else str(fuente)
                        fuente_dist_simplified[fuente_simplified] = fuente_dist_simplified.get(fuente_simplified, 0) + count

                if fuente_dist_simplified:
                    fig_fuente = px.bar(
                        x=list(fuente_dist_simplified.values()),
                        y=list(fuente_dist_simplified.keys()),
                        orientation="h",
                        title="Epizootias por Fuente",
                        labels={"x": "Número de Epizootias", "y": "Fuente"},
                        color=list(fuente_dist_simplified.values()),
                        color_continuous_scale="Oranges",
                    )
                    fig_fuente.update_layout(height=350, showlegend=False)
                    st.plotly_chart(fig_fuente, use_container_width=True)
                else:
                    st.info("No hay datos de fuentes disponibles")
            else:
                st.info("No hay datos de fuentes en las epizootias")

        with col2:
            st.markdown("**📅 Evolución Temporal de Epizootias**")
            if "fecha_recoleccion" in epizootias.columns:
                epi_fecha = epizootias.dropna(subset=["fecha_recoleccion"]).copy()
                
                if not epi_fecha.empty:
                    # Agrupar por mes
                    epi_fecha["año_mes"] = epi_fecha["fecha_recoleccion"].dt.to_period("M")
                    epi_temporal = epi_fecha.groupby("año_mes").size().reset_index(name="epizootias")
                    epi_temporal["fecha"] = epi_temporal["año_mes"].dt.to_timestamp()
                    
                    if not epi_temporal.empty:
                        fig_epi_temporal = px.area(
                            epi_temporal,
                            x="fecha",
                            y="epizootias",
                            title="Epizootias por Mes",
                            labels={"fecha": "Fecha", "epizootias": "Número de Epizootias"},
                        )
                        fig_epi_temporal.update_traces(fill='tonexty', fillcolor=f'rgba(247, 148, 29, 0.3)', line=dict(color=colors["warning"], width=3))
                        fig_epi_temporal.update_layout(height=350)
                        st.plotly_chart(fig_epi_temporal, use_container_width=True)
                    else:
                        st.info("No hay datos temporales suficientes")
                else:
                    st.info("No hay fechas de epizootias disponibles")
            else:
                st.info("No hay datos de fechas en las epizootias")

    else:
        st.info("⚠️ No hay epizootias disponibles para analizar con los filtros actuales")


def show_enhanced_geographic_analysis(casos, epizootias, colors, filters):
    """
    NUEVO: Análisis geográfico mejorado sin métricas básicas.
    """
    st.subheader("🗺️ Análisis Geográfico Avanzado")
    
    municipio_filtrado = filters.get("municipio_normalizado")
    
    if municipio_filtrado:
        st.markdown(f"### 🏘️ Análisis Detallado de {filters.get('municipio_display', 'Municipio')}")
        show_municipal_detailed_analysis(casos, epizootias, municipio_filtrado, colors)
    else:
        st.markdown("### 🏛️ Análisis Departamental por Municipios")
        show_departmental_detailed_analysis(casos, epizootias, colors)


def show_municipal_detailed_analysis(casos, epizootias, municipio_normalizado, colors):
    """
    NUEVO: Análisis detallado a nivel municipal.
    """
    # Filtrar datos por municipio
    casos_municipio = casos[casos["municipio_normalizado"] == municipio_normalizado] if not casos.empty else pd.DataFrame()
    epizootias_municipio = epizootias[epizootias["municipio_normalizado"] == municipio_normalizado] if not epizootias.empty else pd.DataFrame()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📊 Distribución por Veredas - Casos**")
        if not casos_municipio.empty and "vereda" in casos_municipio.columns:
            vereda_casos = casos_municipio["vereda"].value_counts().head(10)
            
            if not vereda_casos.empty:
                fig_vereda_casos = px.bar(
                    x=vereda_casos.values,
                    y=vereda_casos.index,
                    orientation="h",
                    title="Top 10 Veredas con Casos",
                    labels={"x": "Número de Casos", "y": "Vereda"},
                    color=vereda_casos.values,
                    color_continuous_scale="Reds",
                )
                fig_vereda_casos.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig_vereda_casos, use_container_width=True)
            else:
                st.info("No hay casos en veredas para mostrar")
        else:
            st.info("No hay datos de casos por vereda")
    
    with col2:
        st.markdown("**📊 Distribución por Veredas - Epizootias**")
        if not epizootias_municipio.empty and "vereda" in epizootias_municipio.columns:
            vereda_epi = epizootias_municipio["vereda"].value_counts().head(10)
            
            if not vereda_epi.empty:
                fig_vereda_epi = px.bar(
                    x=vereda_epi.values,
                    y=vereda_epi.index,
                    orientation="h",
                    title="Top 10 Veredas con Epizootias",
                    labels={"x": "Número de Epizootias", "y": "Vereda"},
                    color=vereda_epi.values,
                    color_continuous_scale="Oranges",
                )
                fig_vereda_epi.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig_vereda_epi, use_container_width=True)
            else:
                st.info("No hay epizootias en veredas para mostrar")
        else:
            st.info("No hay datos de epizootias por vereda")

    # Análisis combinado por veredas
    st.markdown("**🔗 Análisis Combinado por Veredas**")
    create_combined_vereda_analysis(casos_municipio, epizootias_municipio, colors)


def show_departmental_detailed_analysis(casos, epizootias, colors):
    """
    NUEVO: Análisis detallado a nivel departamental.
    """
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📊 Ranking de Municipios - Casos**")
        if not casos.empty and "municipio" in casos.columns:
            municipio_casos = casos["municipio"].value_counts().head(15)
            
            if not municipio_casos.empty:
                fig_mpio_casos = px.bar(
                    x=municipio_casos.values,
                    y=municipio_casos.index,
                    orientation="h",
                    title="Top 15 Municipios con Casos",
                    labels={"x": "Número de Casos", "y": "Municipio"},
                    color=municipio_casos.values,
                    color_continuous_scale="Reds",
                )
                fig_mpio_casos.update_layout(height=500, showlegend=False)
                st.plotly_chart(fig_mpio_casos, use_container_width=True)
            else:
                st.info("No hay casos por municipio para mostrar")
        else:
            st.info("No hay datos de casos por municipio")
    
    with col2:
        st.markdown("**📊 Ranking de Municipios - Epizootias**")
        if not epizootias.empty and "municipio" in epizootias.columns:
            municipio_epi = epizootias["municipio"].value_counts().head(15)
            
            if not municipio_epi.empty:
                fig_mpio_epi = px.bar(
                    x=municipio_epi.values,
                    y=municipio_epi.index,
                    orientation="h",
                    title="Top 15 Municipios con Epizootias",
                    labels={"x": "Número de Epizootias", "y": "Municipio"},
                    color=municipio_epi.values,
                    color_continuous_scale="Oranges",
                )
                fig_mpio_epi.update_layout(height=500, showlegend=False)
                st.plotly_chart(fig_mpio_epi, use_container_width=True)
            else:
                st.info("No hay epizootias por municipio para mostrar")
        else:
            st.info("No hay datos de epizootias por municipio")

    # Análisis combinado por municipios
    st.markdown("**🔗 Análisis Combinado por Municipios**")
    create_combined_municipio_analysis(casos, epizootias, colors)


def create_combined_vereda_analysis(casos, epizootias, colors):
    """
    NUEVO: Análisis combinado de casos y epizootias por vereda.
    """
    # Crear dataset combinado por vereda
    combined_data = []
    
    # Obtener todas las veredas únicas
    veredas_casos = set(casos["vereda"].dropna()) if not casos.empty and "vereda" in casos.columns else set()
    veredas_epi = set(epizootias["vereda"].dropna()) if not epizootias.empty and "vereda" in epizootias.columns else set()
    todas_veredas = veredas_casos.union(veredas_epi)
    
    for vereda in todas_veredas:
        casos_count = len(casos[casos["vereda"] == vereda]) if not casos.empty and "vereda" in casos.columns else 0
        epi_count = len(epizootias[epizootias["vereda"] == vereda]) if not epizootias.empty and "vereda" in epizootias.columns else 0
        total_actividad = casos_count + epi_count
        
        if total_actividad > 0:  # Solo incluir veredas con actividad
            combined_data.append({
                "Vereda": vereda,
                "Casos": casos_count,
                "Epizootias": epi_count,
                "Total": total_actividad
            })
    
    if combined_data:
        df_combined = pd.DataFrame(combined_data).sort_values("Total", ascending=True).tail(10)
        
        # Gráfico de barras apiladas
        fig_combined = go.Figure()
        
        fig_combined.add_trace(go.Bar(
            x=df_combined["Casos"],
            y=df_combined["Vereda"],
            name="Casos Humanos",
            orientation="h",
            marker_color=colors["danger"],
            opacity=0.8
        ))
        
        fig_combined.add_trace(go.Bar(
            x=df_combined["Epizootias"],
            y=df_combined["Vereda"],
            name="Epizootias",
            orientation="h",
            marker_color=colors["warning"],
            opacity=0.8
        ))
        
        fig_combined.update_layout(
            title="Top 10 Veredas - Actividad Combinada",
            xaxis_title="Número de Eventos",
            yaxis_title="Vereda",
            barmode="stack",
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02)
        )
        
        st.plotly_chart(fig_combined, use_container_width=True)
    else:
        st.info("No hay datos combinados para mostrar")


def create_combined_municipio_analysis(casos, epizootias, colors):
    """
    NUEVO: Análisis combinado de casos y epizootias por municipio.
    """
    # Crear dataset combinado por municipio
    combined_data = []
    
    # Obtener todos los municipios únicos
    municipios_casos = set(casos["municipio"].dropna()) if not casos.empty and "municipio" in casos.columns else set()
    municipios_epi = set(epizootias["municipio"].dropna()) if not epizootias.empty and "municipio" in epizootias.columns else set()
    todos_municipios = municipios_casos.union(municipios_epi)
    
    for municipio in todos_municipios:
        casos_count = len(casos[casos["municipio"] == municipio]) if not casos.empty and "municipio" in casos.columns else 0
        epi_count = len(epizootias[epizootias["municipio"] == municipio]) if not epizootias.empty and "municipio" in epizootias.columns else 0
        total_actividad = casos_count + epi_count
        
        if total_actividad > 0:  # Solo incluir municipios con actividad
            combined_data.append({
                "Municipio": municipio,
                "Casos": casos_count,
                "Epizootias": epi_count,
                "Total": total_actividad
            })
    
    if combined_data:
        df_combined = pd.DataFrame(combined_data).sort_values("Total", ascending=False).head(10)
        
        # Gráfico de dispersión con tamaños
        fig_scatter = px.scatter(
            df_combined,
            x="Casos",
            y="Epizootias",
            size="Total",
            color="Total",
            hover_name="Municipio",
            title="Correlación Casos vs Epizootias por Municipio",
            labels={"Casos": "Número de Casos Humanos", "Epizootias": "Número de Epizootias"},
            color_continuous_scale="RdYlOrRd",
            size_max=60
        )
        
        fig_scatter.update_layout(height=400)
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Tabla resumida
        st.markdown("**📋 Top 10 Municipios - Resumen**")
        st.dataframe(
            df_combined[["Municipio", "Casos", "Epizootias", "Total"]].reset_index(drop=True),
            use_container_width=True,
            height=300
        )
    else:
        st.info("No hay datos combinados para mostrar")


def show_detailed_data_tables(casos, epizootias, colors):
    """
    NUEVO: Tablas de datos detalladas y mejoradas.
    """
    st.subheader("📋 Datos Detallados")
    
    # Preparar datos para mostrar (con todas las columnas relevantes)
    casos_display = prepare_enhanced_casos_display(casos) if not casos.empty else pd.DataFrame()
    epizootias_display = prepare_enhanced_epizootias_display(epizootias) if not epizootias.empty else pd.DataFrame()
    
    # Pestañas para las tablas
    tab1, tab2, tab3 = st.tabs(["🦠 Casos Humanos", "🐒 Epizootias", "📊 Resumen Comparativo"])
    
    with tab1:
        st.markdown("#### 🦠 Casos Humanos Detallados")
        if not casos_display.empty:
            # Filtros para la tabla de casos
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if "sexo" in casos_display.columns:
                    sexo_filter = st.selectbox("Filtrar por Sexo:", ["Todos"] + list(casos_display["sexo"].dropna().unique()))
                    if sexo_filter != "Todos":
                        casos_display = casos_display[casos_display["sexo"] == sexo_filter]
            
            with col2:
                if "condicion_final" in casos_display.columns:
                    condicion_filter = st.selectbox("Filtrar por Condición:", ["Todas"] + list(casos_display["condicion_final"].dropna().unique()))
                    if condicion_filter != "Todas":
                        casos_display = casos_display[casos_display["condicion_final"] == condicion_filter]
            
            with col3:
                if "municipio" in casos_display.columns:
                    municipio_filter = st.selectbox("Filtrar por Municipio:", ["Todos"] + list(casos_display["municipio"].dropna().unique()))
                    if municipio_filter != "Todos":
                        casos_display = casos_display[casos_display["municipio"] == municipio_filter]
            
            st.dataframe(casos_display, use_container_width=True, height=500)
            st.caption(f"📊 Mostrando {len(casos_display)} casos de {len(casos)} totales")
            
        else:
            st.info("No hay casos para mostrar con los filtros actuales")
    
    with tab2:
        st.markdown("#### 🐒 Epizootias Detalladas")
        if not epizootias_display.empty:
            # Filtros para la tabla de epizootias
            col1, col2 = st.columns(2)
            
            with col1:
                if "proveniente" in epizootias_display.columns:
                    fuente_filter = st.selectbox("Filtrar por Fuente:", ["Todas"] + list(epizootias_display["proveniente"].dropna().unique()))
                    if fuente_filter != "Todas":
                        epizootias_display = epizootias_display[epizootias_display["proveniente"] == fuente_filter]
            
            with col2:
                if "municipio" in epizootias_display.columns:
                    municipio_epi_filter = st.selectbox("Filtrar por Municipio:", ["Todos"] + list(epizootias_display["municipio"].dropna().unique()), key="municipio_epi")
                    if municipio_epi_filter != "Todos":
                        epizootias_display = epizootias_display[epizootias_display["municipio"] == municipio_epi_filter]
            
            st.dataframe(epizootias_display, use_container_width=True, height=500)
            st.caption(f"📊 Mostrando {len(epizootias_display)} epizootias de {len(epizootias)} totales")
            
        else:
            st.info("No hay epizootias para mostrar con los filtros actuales")
    
    with tab3:
        st.markdown("#### 📊 Resumen Comparativo")
        create_comparative_summary_table(casos, epizootias, colors)


def prepare_enhanced_casos_display(casos):
    """
    NUEVO: Prepara datos de casos con columnas mejoradas para visualización.
    """
    if casos.empty:
        return casos
    
    # Seleccionar y ordenar columnas relevantes
    columnas_importantes = [
        'municipio', 'vereda', 'fecha_inicio_sintomas', 'edad', 'sexo', 
        'condicion_final', 'eps'
    ]
    
    columnas_existentes = [col for col in columnas_importantes if col in casos.columns]
    casos_display = casos[columnas_existentes].copy()
    
    # Formatear fechas
    if 'fecha_inicio_sintomas' in casos_display.columns:
        casos_display['fecha_inicio_sintomas'] = casos_display['fecha_inicio_sintomas'].dt.strftime('%d/%m/%Y')
    
    # Renombrar columnas para mejor visualización
    rename_map = {
        'municipio': 'Municipio',
        'vereda': 'Vereda',
        'fecha_inicio_sintomas': 'Fecha Inicio',
        'edad': 'Edad',
        'sexo': 'Sexo',
        'condicion_final': 'Condición Final',
        'eps': 'EPS'
    }
    
    casos_display = casos_display.rename(columns=rename_map)
    
    return casos_display


def prepare_enhanced_epizootias_display(epizootias):
    """
    NUEVO: Prepara datos de epizootias con columnas mejoradas para visualización.
    """
    if epizootias.empty:
        return epizootias
    
    # Seleccionar y ordenar columnas relevantes
    columnas_importantes = [
        'municipio', 'vereda', 'fecha_recoleccion', 'descripcion', 'proveniente'
    ]
    
    columnas_existentes = [col for col in columnas_importantes if col in epizootias.columns]
    epi_display = epizootias[columnas_existentes].copy()
    
    # Formatear fechas
    if 'fecha_recoleccion' in epi_display.columns:
        epi_display['fecha_recoleccion'] = epi_display['fecha_recoleccion'].dt.strftime('%d/%m/%Y')
    
    # Simplificar fuentes
    if 'proveniente' in epi_display.columns:
        epi_display['proveniente'] = epi_display['proveniente'].apply(lambda x: 
            "Vigilancia Comunitaria" if "VIGILANCIA COMUNITARIA" in str(x) 
            else "Incautación/Rescate" if "INCAUTACIÓN" in str(x)
            else str(x)[:30] + "..." if len(str(x)) > 30 else str(x)
        )
    
    # Renombrar columnas para mejor visualización
    rename_map = {
        'municipio': 'Municipio',
        'vereda': 'Vereda',
        'fecha_recoleccion': 'Fecha Recolección',
        'descripcion': 'Resultado',
        'proveniente': 'Fuente'
    }
    
    epi_display = epi_display.rename(columns=rename_map)
    
    return epi_display


def create_comparative_summary_table(casos, epizootias, colors):
    """
    NUEVO: Crea tabla de resumen comparativo entre casos y epizootias.
    """
    summary_data = []
    
    # Obtener ubicaciones únicas
    ubicaciones = set()
    if not casos.empty and "municipio" in casos.columns:
        ubicaciones.update(casos["municipio"].dropna())
    if not epizootias.empty and "municipio" in epizootias.columns:
        ubicaciones.update(epizootias["municipio"].dropna())
    
    for ubicacion in sorted(ubicaciones):
        casos_ubi = casos[casos["municipio"] == ubicacion] if not casos.empty and "municipio" in casos.columns else pd.DataFrame()
        epi_ubi = epizootias[epizootias["municipio"] == ubicacion] if not epizootias.empty and "municipio" in epizootias.columns else pd.DataFrame()
        
        casos_count = len(casos_ubi)
        epi_count = len(epi_ubi)
        
        if casos_count > 0 or epi_count > 0:
            fallecidos = (casos_ubi["condicion_final"] == "Fallecido").sum() if not casos_ubi.empty and "condicion_final" in casos_ubi.columns else 0
            letalidad = (fallecidos / casos_count * 100) if casos_count > 0 else 0
            
            summary_data.append({
                "Municipio": ubicacion,
                "Casos Humanos": casos_count,
                "Fallecidos": fallecidos,
                "Letalidad (%)": f"{letalidad:.1f}%",
                "Epizootias": epi_count,
                "Total Eventos": casos_count + epi_count,
                "Riesgo": "Alto" if (casos_count + epi_count) > 10 else "Medio" if (casos_count + epi_count) > 3 else "Bajo"
            })
    
    if summary_data:
        df_summary = pd.DataFrame(summary_data)
        df_summary = df_summary.sort_values("Total Eventos", ascending=False)
        
        # Aplicar colores según nivel de riesgo
        def highlight_risk(row):
            if row["Riesgo"] == "Alto":
                return ['background-color: #ffebee'] * len(row)
            elif row["Riesgo"] == "Medio":
                return ['background-color: #fff3e0'] * len(row)
            else:
                return ['background-color: #e8f5e8'] * len(row)
        
        styled_df = df_summary.style.apply(highlight_risk, axis=1)
        
        st.dataframe(styled_df, use_container_width=True, height=400)
        
        # Estadísticas del resumen
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Municipios Analizados", len(df_summary))
        
        with col2:
            total_casos = df_summary["Casos Humanos"].sum()
            total_epi = df_summary["Epizootias"].sum()
            st.metric("Actividad Total", total_casos + total_epi)
        
        with col3:
            riesgo_alto = len(df_summary[df_summary["Riesgo"] == "Alto"])
            st.metric("Municipios Alto Riesgo", riesgo_alto)
        
    else:
        st.info("No hay datos suficientes para el resumen comparativo")


def show_advanced_export_section(casos, epizootias):
    """
    NUEVO: Sección de exportación avanzada con múltiples formatos.
    """
    st.subheader("📥 Exportación Avanzada de Datos")
    
    casos_count = len(casos)
    epi_count = len(epizootias)
    
    # Información sobre exportación
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #e3f2fd, #bbdefb);
            padding: 20px;
            border-radius: 12px;
            border-left: 5px solid #2196f3;
            margin-bottom: 20px;
        ">
            <h4 style="color: #1976d2; margin-top: 0;">📊 Datos Disponibles para Exportación</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                <div>
                    <strong>🦠 Casos confirmados:</strong> {casos_count} registros<br>
                    <strong>🐒 Epizootias:</strong> {epi_count} registros
                </div>
                <div>
                    <strong>📅 Período:</strong> Según filtros aplicados<br>
                    <strong>📍 Ubicación:</strong> Según filtros geográficos
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Opciones de exportación en columnas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("**📊 Excel Completo**")
        if not casos.empty or not epizootias.empty:
            excel_data = create_advanced_excel_export(casos, epizootias)
            st.download_button(
                label="📊 Excel Avanzado",
                data=excel_data,
                file_name=f"fiebre_amarilla_avanzado_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Excel con múltiples hojas y análisis",
                use_container_width=True
            )
        else:
            st.button("📊 Excel Avanzado", disabled=True, help="No hay datos")
    
    with col2:
        st.markdown("**🦠 Casos CSV**")
        if not casos.empty:
            casos_enhanced = prepare_enhanced_casos_display(casos)
            casos_csv = casos_enhanced.to_csv(index=False)
            st.download_button(
                label="🦠 Casos Detallados",
                data=casos_csv,
                file_name=f"casos_detallados_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                help="Casos con formato mejorado",
                use_container_width=True
            )
        else:
            st.button("🦠 Casos Detallados", disabled=True, help="No hay casos")
    
    with col3:
        st.markdown("**🐒 Epizootias CSV**")
        if not epizootias.empty:
            epi_enhanced = prepare_enhanced_epizootias_display(epizootias)
            epi_csv = epi_enhanced.to_csv(index=False)
            st.download_button(
                label="🐒 Epizootias",
                data=epi_csv,
                file_name=f"epizootias_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                help="Epizootias con formato mejorado",
                use_container_width=True
            )
        else:
            st.button("🐒 Epizootias", disabled=True, help="No hay epizootias")
    
    with col4:
        st.markdown("**📊 Resumen CSV**")
        if not casos.empty or not epizootias.empty:
            summary_data = create_summary_for_export(casos, epizootias)
            if summary_data is not None:
                summary_csv = summary_data.to_csv(index=False)
                st.download_button(
                    label="📊 Resumen",
                    data=summary_csv,
                    file_name=f"resumen_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    help="Resumen ejecutivo",
                    use_container_width=True
                )
            else:
                st.button("📊 Resumen", disabled=True, help="Sin datos para resumen")
        else:
            st.button("📊 Resumen", disabled=True, help="No hay datos")


def create_advanced_excel_export(casos, epizootias):
    """
    NUEVO: Crea archivo Excel avanzado con múltiples hojas y análisis.
    """
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Hoja 1: Casos detallados
        if not casos.empty:
            casos_enhanced = prepare_enhanced_casos_display(casos)
            casos_enhanced.to_excel(writer, sheet_name='Casos_Detallados', index=False)
        
        # Hoja 2: Epizootias detalladas
        if not epizootias.empty:
            epi_enhanced = prepare_enhanced_epizootias_display(epizootias)
            epi_enhanced.to_excel(writer, sheet_name='Epizootias_Detalladas', index=False)
        
        # Hoja 3: Resumen ejecutivo
        summary_data = create_summary_for_export(casos, epizootias)
        if summary_data is not None:
            summary_data.to_excel(writer, sheet_name='Resumen_Ejecutivo', index=False)
        
        # Hoja 4: Análisis temporal
        temporal_analysis = create_temporal_analysis_for_export(casos, epizootias)
        if temporal_analysis is not None:
            temporal_analysis.to_excel(writer, sheet_name='Analisis_Temporal', index=False)
        
        # Hoja 5: Metadatos
        metadata = create_metadata_for_export(casos, epizootias)
        metadata.to_excel(writer, sheet_name='Metadatos', index=False)
    
    buffer.seek(0)
    return buffer.getvalue()


def create_summary_for_export(casos, epizootias):
    """
    NUEVO: Crea resumen ejecutivo para exportación.
    """
    try:
        summary_rows = []
        
        # Métricas generales
        summary_rows.append({
            "Categoría": "GENERAL",
            "Indicador": "Total Casos Confirmados",
            "Valor": len(casos),
            "Observaciones": "Casos humanos confirmados de fiebre amarilla"
        })
        
        summary_rows.append({
            "Categoría": "GENERAL",
            "Indicador": "Total Epizootias",
            "Valor": len(epizootias),
            "Observaciones": "Epizootias confirmadas positivas"
        })
        
        # Métricas de letalidad
        if not casos.empty and "condicion_final" in casos.columns:
            fallecidos = (casos["condicion_final"] == "Fallecido").sum()
            letalidad = (fallecidos / len(casos) * 100) if len(casos) > 0 else 0
            
            summary_rows.append({
                "Categoría": "LETALIDAD",
                "Indicador": "Fallecidos",
                "Valor": fallecidos,
                "Observaciones": f"Letalidad: {letalidad:.1f}%"
            })
        
        # Métricas geográficas
        municipios_casos = casos["municipio"].nunique() if not casos.empty and "municipio" in casos.columns else 0
        municipios_epi = epizootias["municipio"].nunique() if not epizootias.empty and "municipio" in epizootias.columns else 0
        
        summary_rows.append({
            "Categoría": "GEOGRÁFICO",
            "Indicador": "Municipios con Casos",
            "Valor": municipios_casos,
            "Observaciones": "Municipios afectados por casos humanos"
        })
        
        summary_rows.append({
            "Categoría": "GEOGRÁFICO",
            "Indicador": "Municipios con Epizootias",
            "Valor": municipios_epi,
            "Observaciones": "Municipios con epizootias confirmadas"
        })
        
        # Metadata de exportación
        summary_rows.append({
            "Categoría": "METADATA",
            "Indicador": "Fecha de Exportación",
            "Valor": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Observaciones": "Fecha y hora de generación del reporte"
        })
        
        return pd.DataFrame(summary_rows)
    
    except Exception:
        return None


def create_temporal_analysis_for_export(casos, epizootias):
    """
    NUEVO: Crea análisis temporal para exportación.
    """
    try:
        temporal_rows = []
        
        # Análisis por mes - casos
        if not casos.empty and "fecha_inicio_sintomas" in casos.columns:
            casos_temporal = casos.dropna(subset=["fecha_inicio_sintomas"]).copy()
            casos_temporal["año_mes"] = casos_temporal["fecha_inicio_sintomas"].dt.to_period("M")
            casos_mensual = casos_temporal.groupby("año_mes").size()
            
            for periodo, count in casos_mensual.items():
                temporal_rows.append({
                    "Período": str(periodo),
                    "Tipo": "Casos Humanos",
                    "Cantidad": count,
                    "Observaciones": f"Casos humanos en {periodo}"
                })
        
        # Análisis por mes - epizootias
        if not epizootias.empty and "fecha_recoleccion" in epizootias.columns:
            epi_temporal = epizootias.dropna(subset=["fecha_recoleccion"]).copy()
            epi_temporal["año_mes"] = epi_temporal["fecha_recoleccion"].dt.to_period("M")
            epi_mensual = epi_temporal.groupby("año_mes").size()
            
            for periodo, count in epi_mensual.items():
                temporal_rows.append({
                    "Período": str(periodo),
                    "Tipo": "Epizootias",
                    "Cantidad": count,
                    "Observaciones": f"Epizootias confirmadas en {periodo}"
                })
        
        if temporal_rows:
            return pd.DataFrame(temporal_rows).sort_values("Período")
        else:
            return None
    
    except Exception:
        return None


def create_metadata_for_export(casos, epizootias):
    """
    NUEVO: Crea metadatos para exportación.
    """
    metadata_rows = []
    
    # Información del dataset de casos
    metadata_rows.append({
        "Categoría": "CASOS",
        "Campo": "Total Registros",
        "Valor": len(casos),
        "Descripción": "Número total de casos en el dataset"
    })
    
    if not casos.empty:
        metadata_rows.append({
            "Categoría": "CASOS",
            "Campo": "Columnas Disponibles",
            "Valor": len(casos.columns),
            "Descripción": ", ".join(casos.columns.tolist())
        })
    
    # Información del dataset de epizootias
    metadata_rows.append({
        "Categoría": "EPIZOOTIAS",
        "Campo": "Total Registros",
        "Valor": len(epizootias),
        "Descripción": "Número total de epizootias en el dataset"
    })
    
    if not epizootias.empty:
        metadata_rows.append({
            "Categoría": "EPIZOOTIAS",
            "Campo": "Columnas Disponibles",
            "Valor": len(epizootias.columns),
            "Descripción": ", ".join(epizootias.columns.tolist())
        })
    
    # Información del reporte
    metadata_rows.append({
        "Categoría": "REPORTE",
        "Campo": "Dashboard Versión",
        "Valor": "3.0",
        "Descripción": "Versión del dashboard de Fiebre Amarilla"
    })
    
    metadata_rows.append({
        "Categoría": "REPORTE",
        "Campo": "Generado",
        "Valor": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Descripción": "Fecha y hora de generación del reporte"
    })
    
    return pd.DataFrame(metadata_rows)