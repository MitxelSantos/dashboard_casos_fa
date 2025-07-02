"""
Vista de información principal del dashboard de Fiebre Amarilla.
Simplificada y minimalista para profesionales médicos.
ACTUALIZADA: Múltiples mejoras según especificaciones del usuario.
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
    Muestra la vista de información principal simplificada.

    Args:
        data_filtered (dict): Datos filtrados
        filters (dict): Filtros aplicados
        colors (dict): Colores institucionales
    """
    casos = data_filtered["casos"]
    epizootias = data_filtered["epizootias"]

    # Métricas principales sin colores de alerta
    create_main_metrics(casos, epizootias, colors)

    # Secciones informativas
    st.markdown("---")
    show_all_charts_section(casos, epizootias, colors, filters)

    st.markdown("---")
    show_geographic_summary(casos, epizootias, colors, filters)
    
    st.markdown("---")
    show_filtered_data_tables(casos, epizootias, colors)
    
    st.markdown("---")
    show_consolidated_export_section(casos, epizootias)


def create_main_metrics(casos, epizootias, colors):
    """
    Crea las métricas principales sin alertas de color.
    ACTUALIZADA: Último caso y epizootia con municipio y vereda en misma línea.
    """
    # Calcular métricas básicas
    total_casos = len(casos)
    total_epizootias = len(epizootias)

    # Métricas de casos
    fallecidos = 0
    vivos = 0
    letalidad = 0
    if total_casos > 0 and "condicion_final" in casos.columns:
        fallecidos = (casos["condicion_final"] == "Fallecido").sum()
        vivos = (casos["condicion_final"] == "Vivo").sum()
        letalidad = (fallecidos / total_casos * 100) if total_casos > 0 else 0

    # Métricas de epizootias
    positivos_fa = 0
    positividad = 0
    if total_epizootias > 0 and "descripcion" in epizootias.columns:
        positivos_fa = (epizootias["descripcion"] == "POSITIVO FA").sum()
        positividad = (
            (positivos_fa / total_epizootias * 100) if total_epizootias > 0 else 0
        )

    # Métricas geográficas
    municipios_afectados = set()
    if not casos.empty and "municipio_normalizado" in casos.columns:
        municipios_afectados.update(casos["municipio_normalizado"].dropna())
    if not epizootias.empty and "municipio_normalizado" in epizootias.columns:
        municipios_afectados.update(epizootias["municipio_normalizado"].dropna())

    # Fechas importantes Y UBICACIÓN DEL ÚLTIMO CASO
    ultima_fecha_caso = None
    ultimo_caso_municipio = None
    ultimo_caso_vereda = None
    ultima_fecha_epi_positiva = None
    ultima_epi_municipio = None
    ultima_epi_vereda = None

    if not casos.empty and "fecha_inicio_sintomas" in casos.columns:
        fechas_casos = casos["fecha_inicio_sintomas"].dropna()
        if not fechas_casos.empty:
            # Encontrar el caso más reciente
            idx_ultimo = casos[casos["fecha_inicio_sintomas"] == fechas_casos.max()].index[-1]
            ultimo_caso = casos.loc[idx_ultimo]
            
            ultima_fecha_caso = fechas_casos.max()
            ultimo_caso_municipio = ultimo_caso.get("municipio", "No especificado")
            ultimo_caso_vereda = ultimo_caso.get("vereda", "No especificada")

    if not epizootias.empty and "fecha_recoleccion" in epizootias.columns:
        epi_positivas = epizootias[epizootias["descripcion"] == "POSITIVO FA"]
        if not epi_positivas.empty:
            fechas_positivas = epi_positivas["fecha_recoleccion"].dropna()
            if not fechas_positivas.empty:
                # Encontrar la epizootia positiva más reciente
                idx_ultima = epi_positivas[epi_positivas["fecha_recoleccion"] == fechas_positivas.max()].index[-1]
                ultima_epi = epizootias.loc[idx_ultima]
                
                ultima_fecha_epi_positiva = fechas_positivas.max()
                ultima_epi_municipio = ultima_epi.get("municipio", "No especificado")
                ultima_epi_vereda = ultima_epi.get("vereda", "No especificada")

    # CSS para tarjetas sin alertas
    st.markdown(
        f"""
    <style>
    .metric-card {{
        background: linear-gradient(135deg, white 0%, #f8f9fa 100%);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease;
        margin-bottom: 20px;
        border-top: 4px solid {colors['primary']};
        min-height: 150px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }}
    
    .metric-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    }}
    
    .card-icon {{
        font-size: 2rem;
        margin-bottom: 10px;
    }}
    
    .card-title {{
        font-size: 0.9rem;
        font-weight: 600;
        color: {colors['dark']};
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    .card-value {{
        font-size: 2rem;
        font-weight: 700;
        color: {colors['primary']};
        margin-bottom: 8px;
        line-height: 1;
    }}
    
    .card-subtitle {{
        font-size: 0.85rem;
        color: #666;
        margin: 0;
        line-height: 1.2;
    }}
    
    .card-location {{
        font-size: 0.75rem;
        color: #888;
        margin-top: 4px;
        line-height: 1.1;
    }}
    
    @media (max-width: 768px) {{
        .metric-card {{
            min-height: 120px;
            padding: 15px;
        }}
        
        .card-icon {{
            font-size: 1.5rem;
        }}
        
        .card-value {{
            font-size: 1.5rem;
        }}
    }}
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Primera fila - Casos humanos
    st.subheader("🦠 Casos Humanos")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="card-icon">🦠</div>
            <div class="card-title">Casos Totales</div>
            <div class="card-value">{total_casos}</div>
            <div class="card-subtitle">Confirmados</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="card-icon">💚</div>
            <div class="card-title">Vivos</div>
            <div class="card-value">{vivos}</div>
            <div class="card-subtitle">Pacientes</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="card-icon">⚰️</div>
            <div class="card-title">Fallecidos</div>
            <div class="card-value">{fallecidos}</div>
            <div class="card-subtitle">Letalidad: {letalidad:.1f}%</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col4:
        dias_ultimo_caso = "Sin datos"
        if ultima_fecha_caso:
            dias_ultimo_caso = (datetime.now() - ultima_fecha_caso).days
            fecha_display = ultima_fecha_caso.strftime("%d/%m/%Y")
            dias_display = f"Hace {dias_ultimo_caso} días"
        else:
            fecha_display = "Sin datos"
            dias_display = ""

        # NUEVA: Información de ubicación del último caso EN UNA SOLA LÍNEA
        ubicacion_text = ""
        if ultimo_caso_municipio and ultimo_caso_vereda:
            ubicacion_text = f"📍 {ultimo_caso_municipio} - {ultimo_caso_vereda}"

        st.markdown(
            f"""
        <div class="metric-card">
            <div class="card-icon">📅</div>
            <div class="card-title">Último Caso</div>
            <div class="card-value" style="font-size: 1.2rem;">{fecha_display}</div>
            <div class="card-subtitle">{dias_display}</div>
            <div class="card-location">{ubicacion_text}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Segunda fila - Vigilancia de fauna
    st.subheader("🐒 Vigilancia de Fauna")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="card-icon">🐒</div>
            <div class="card-title">Epizootias Totales</div>
            <div class="card-value">{total_epizootias}</div>
            <div class="card-subtitle">Registradas</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="card-icon">🔴</div>
            <div class="card-title">Positivas FA</div>
            <div class="card-value">{positivos_fa}</div>
            <div class="card-subtitle">{positividad:.1f}% del total</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        municipios_count = len(municipios_afectados)
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="card-icon">🏛️</div>
            <div class="card-title">Municipios</div>
            <div class="card-value">{municipios_count}</div>
            <div class="card-subtitle">Con eventos</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col4:
        dias_ultima_epi = "Sin datos"
        if ultima_fecha_epi_positiva:
            dias_ultima_epi = (datetime.now() - ultima_fecha_epi_positiva).days
            fecha_display = ultima_fecha_epi_positiva.strftime("%d/%m/%Y")
            dias_display = f"Hace {dias_ultima_epi} días"
        else:
            fecha_display = "Sin datos"
            dias_display = ""

        # NUEVA: Información de ubicación de la última epizootia EN UNA SOLA LÍNEA
        ubicacion_epi_text = ""
        if ultima_epi_municipio and ultima_epi_vereda:
            ubicacion_epi_text = f"📍 {ultima_epi_municipio} - {ultima_epi_vereda}"

        st.markdown(
            f"""
        <div class="metric-card">
            <div class="card-icon">🔬</div>
            <div class="card-title">Última Positiva</div>
            <div class="card-value" style="font-size: 1.2rem;">{fecha_display}</div>
            <div class="card-subtitle">{dias_display}</div>
            <div class="card-location">{ubicacion_epi_text}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )


def show_all_charts_section(casos, epizootias, colors, filters):
    """
    NUEVA: Muestra todas las gráficas en una sola sección con separación lógica.
    """
    st.subheader("📊 Análisis Epidemiológico")
    
    # Sección 1: Casos Humanos
    st.markdown("### 🦠 Casos Humanos")
    
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Distribución por Sexo**")
        if not casos.empty and "sexo" in casos.columns:
            sexo_dist = casos["sexo"].value_counts()
            if not sexo_dist.empty:
                fig_sexo = px.pie(
                    values=sexo_dist.values,
                    names=sexo_dist.index,
                    title="",
                    color_discrete_map={
                        "Masculino": colors["info"],
                        "Femenino": colors["secondary"],
                    },
                )
                fig_sexo.update_layout(height=300, showlegend=True)
                st.plotly_chart(fig_sexo, use_container_width=True)
        else:
            st.info("No hay datos de casos disponibles.")

    with col2:
        st.markdown("**Casos por Edad y Sexo**")
        if not casos.empty and "edad" in casos.columns and "sexo" in casos.columns:
            casos_edad = casos.dropna(subset=["edad", "sexo"]).copy()
            
            if not casos_edad.empty:
                casos_edad["grupo_edad"] = pd.cut(
                    casos_edad["edad"], 
                    bins=[0, 10, 20, 30, 40, 50, 60, 70, 80, 100], 
                    labels=["0-10", "11-20", "21-30", "31-40", "41-50", "51-60", "61-70", "71-80", "80+"],
                    include_lowest=True
                )
                
                edad_sexo_counts = casos_edad.groupby(["grupo_edad", "sexo"]).size().reset_index(name="casos")
                
                if not edad_sexo_counts.empty:
                    fig_edad = px.bar(
                        edad_sexo_counts,
                        x="grupo_edad",
                        y="casos",
                        color="sexo",
                        title="",
                        labels={"grupo_edad": "Grupo de Edad", "casos": "Número de Casos"},
                        color_discrete_map={
                            "Masculino": colors["info"],
                            "Femenino": colors["secondary"],
                        },
                    )
                    fig_edad.update_layout(height=300)
                    st.plotly_chart(fig_edad, use_container_width=True)
                else:
                    st.info("No hay datos suficientes para mostrar distribución por edad.")
            else:
                st.info("No hay datos de edad y sexo disponibles.")
        else:
            st.info("No hay datos de edad disponibles.")

    # Segunda fila de casos humanos
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Fallecidos por Edad y Sexo**")
        if not casos.empty and "condicion_final" in casos.columns:
            fallecidos = casos[casos["condicion_final"] == "Fallecido"]
            
            if not fallecidos.empty and "edad" in fallecidos.columns and "sexo" in fallecidos.columns:
                fallecidos_edad = fallecidos.dropna(subset=["edad", "sexo"]).copy()
                
                if not fallecidos_edad.empty:
                    fallecidos_edad["grupo_edad"] = pd.cut(
                        fallecidos_edad["edad"], 
                        bins=[0, 10, 20, 30, 40, 50, 60, 70, 80, 100], 
                        labels=["0-10", "11-20", "21-30", "31-40", "41-50", "51-60", "61-70", "71-80", "80+"],
                        include_lowest=True
                    )
                    
                    fallecidos_counts = fallecidos_edad.groupby(["grupo_edad", "sexo"]).size().reset_index(name="fallecidos")
                    
                    if not fallecidos_counts.empty:
                        fig_fallecidos = px.bar(
                            fallecidos_counts,
                            x="grupo_edad",
                            y="fallecidos",
                            color="sexo",
                            title="",
                            labels={"grupo_edad": "Grupo de Edad", "fallecidos": "Número de Fallecidos"},
                            color_discrete_map={
                                "Masculino": colors["danger"],
                                "Femenino": "#8B0000",
                            },
                        )
                        fig_fallecidos.update_layout(height=300)
                        st.plotly_chart(fig_fallecidos, use_container_width=True)
                    else:
                        st.info("No hay fallecidos para mostrar distribución por edad.")
                else:
                    st.info("No hay datos de edad en fallecidos.")
            else:
                st.info("No hay fallecidos registrados.")
        else:
            st.info("No hay datos de condición final disponibles.")

    with col2:
        # RESPONSIVE: Casos por ubicación según filtros
        municipio_filtrado = filters.get("municipio_normalizado")
        
        if municipio_filtrado:
            st.markdown(f"**Casos por Vereda en {filters.get('municipio_display', 'Municipio')}**")
            
            if not casos.empty and "vereda" in casos.columns:
                vereda_dist = casos["vereda"].value_counts().head(10)
                if not vereda_dist.empty:
                    fig_vereda = px.bar(
                        x=vereda_dist.values,
                        y=vereda_dist.index,
                        orientation="h",
                        title="",
                        labels={"x": "Número de Casos", "y": "Vereda"},
                        color=vereda_dist.values,
                        color_continuous_scale="Reds",
                    )
                    fig_vereda.update_layout(height=300, showlegend=False)
                    st.plotly_chart(fig_vereda, use_container_width=True)
                else:
                    st.info("No hay datos de veredas disponibles.")
            else:
                st.info("No hay datos de casos disponibles.")
        else:
            st.markdown("**Casos por Municipio**")
            
            if not casos.empty and "municipio" in casos.columns:
                municipio_dist = casos["municipio"].value_counts().head(10)
                if not municipio_dist.empty:
                    fig_municipio = px.bar(
                        x=municipio_dist.values,
                        y=municipio_dist.index,
                        orientation="h",
                        title="",
                        labels={"x": "Número de Casos", "y": "Municipio"},
                        color=municipio_dist.values,
                        color_continuous_scale="Reds",
                    )
                    fig_municipio.update_layout(height=300, showlegend=False)
                    st.plotly_chart(fig_municipio, use_container_width=True)
                else:
                    st.info("No hay datos de municipios disponibles.")
            else:
                st.info("No hay datos de casos disponibles.")

    # Sección 2: Epizootias
    st.markdown("### 🐒 Vigilancia de Fauna")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Resultados de Análisis**")
        if not epizootias.empty and "descripcion" in epizootias.columns:
            resultado_dist = epizootias["descripcion"].value_counts()

            color_map = {
                "POSITIVO FA": colors["danger"],
                "NEGATIVO FA": colors["success"],
                "NO APTA": colors["warning"],
                "EN ESTUDIO": colors["info"],
            }

            fig_resultado = px.pie(
                values=resultado_dist.values,
                names=resultado_dist.index,
                title="",
                color_discrete_map=color_map,
            )
            fig_resultado.update_layout(height=300, showlegend=True)
            st.plotly_chart(fig_resultado, use_container_width=True)
        else:
            st.info("No hay datos de epizootias disponibles.")

    with col2:
        # RESPONSIVE: Epizootias por ubicación según filtros
        if municipio_filtrado:
            st.markdown(f"**Epizootias por Vereda en {filters.get('municipio_display', 'Municipio')}**")
            
            if not epizootias.empty and "vereda" in epizootias.columns:
                vereda_dist = epizootias["vereda"].value_counts().head(10)
                if not vereda_dist.empty:
                    fig_vereda = px.bar(
                        x=vereda_dist.values,
                        y=vereda_dist.index,
                        orientation="h",
                        title="",
                        labels={"x": "Número de Epizootias", "y": "Vereda"},
                        color=vereda_dist.values,
                        color_continuous_scale="Oranges",
                    )
                    fig_vereda.update_layout(height=300, showlegend=False)
                    st.plotly_chart(fig_vereda, use_container_width=True)
                else:
                    st.info("No hay datos de veredas disponibles.")
            else:
                st.info("No hay datos de epizootias disponibles.")
        else:
            st.markdown("**Epizootias por Municipio**")
            
            if not epizootias.empty and "municipio" in epizootias.columns:
                municipio_dist = epizootias["municipio"].value_counts().head(10)
                if not municipio_dist.empty:
                    fig_municipio = px.bar(
                        x=municipio_dist.values,
                        y=municipio_dist.index,
                        orientation="h",
                        title="",
                        labels={"x": "Número de Epizootias", "y": "Municipio"},
                        color=municipio_dist.values,
                        color_continuous_scale="Oranges",
                    )
                    fig_municipio.update_layout(height=300, showlegend=False)
                    st.plotly_chart(fig_municipio, use_container_width=True)
                else:
                    st.info("No hay datos de municipios disponibles.")
            else:
                st.info("No hay datos de epizootias disponibles.")


def show_geographic_summary(casos, epizootias, colors, filters):
    """
    Muestra distribución geográfica COMPLETA.
    ACTUALIZADA: Responsive a filtros (municipio vs vereda).
    """
    # RESPONSIVE: Cambiar título y contenido según filtros
    municipio_filtrado = filters.get("municipio_normalizado")
    
    if municipio_filtrado:
        st.subheader(f"🏘️ Distribución por Vereda en {filters.get('municipio_display', 'Municipio')}")
        summary_data = create_vereda_geographic_summary(casos, epizootias, municipio_filtrado)
        location_type = "Vereda"
    else:
        st.subheader("📍 Distribución por Municipio")
        summary_data = create_municipio_geographic_summary(casos, epizootias)
        location_type = "Municipio"

    if summary_data.empty:
        st.info(f"No hay datos geográficos disponibles para {location_type.lower()}s.")
        return

    # Mostrar TODOS los registros
    st.markdown(f"**Resumen de {len(summary_data)} {location_type}s con Actividad**")

    # ACTUALIZADA: Orden de columnas según especificación
    # Vereda/Municipio | Casos | Fallecidos | Total Epi | Epi+
    for i, (_, row) in enumerate(summary_data.iterrows()):
        if i % 2 == 0:
            bg_color = "#f8f9fa"
        else:
            bg_color = "white"

        st.markdown(
            f"""
        <div style="
            background-color: {bg_color};
            padding: 12px;
            border-radius: 6px;
            margin: 4px 0;
            border-left: 4px solid {colors['primary']};
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="flex: 2;">
                    <strong style="color: {colors['primary']}; font-size: 1rem;">
                        {row['Ubicacion']}
                    </strong>
                </div>
                <div style="flex: 3; display: flex; gap: 15px; text-align: center; font-size: 0.9rem;">
                    <div>
                        <div style="font-weight: bold; color: {colors['danger']};">{row['Casos']}</div>
                        <div style="font-size: 0.75rem; color: #666;">Casos</div>
                    </div>
                    <div>
                        <div style="font-weight: bold; color: {colors['dark']};">{row['Fallecidos']}</div>
                        <div style="font-size: 0.75rem; color: #666;">Fallecidos</div>
                    </div>
                    <div>
                        <div style="font-weight: bold; color: {colors['info']};">{row['Total_Epizootias']}</div>
                        <div style="font-size: 0.75rem; color: #666;">Total Epi</div>
                    </div>
                    <div>
                        <div style="font-weight: bold; color: {colors['warning']};">{row['Epizootias_Positivas']}</div>
                        <div style="font-size: 0.75rem; color: #666;">Epi +</div>
                    </div>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Botón de exportación de datos geográficos
    csv_data = summary_data.to_csv(index=False)
    st.download_button(
        label="📄 Exportar Datos por Ubicación",
        data=csv_data,
        file_name=f"distribucion_geografica_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )


def filter_casos_columns(casos_df):
    """
    Filtra las columnas de casos hasta 'Inicio de síntomas' (columna N).
    Solo mantiene las columnas relevantes para la visualización.
    """
    if casos_df.empty:
        return casos_df
    
    # Columnas deseadas hasta "Inicio de síntomas"
    columnas_deseadas = [
        'edad', 'sexo', 'vereda', 'municipio', 'eps', 'condicion_final', 'fecha_inicio_sintomas'
    ]
    
    # También incluir las versiones normalizadas si existen
    columnas_adicionales = [
        'municipio_normalizado', 'vereda_normalizada', 'grupo_edad', 'año_inicio'
    ]
    
    # Filtrar solo las columnas que existen en el dataframe
    columnas_existentes = []
    for col in columnas_deseadas + columnas_adicionales:
        if col in casos_df.columns:
            columnas_existentes.append(col)
    
    return casos_df[columnas_existentes]


def show_filtered_data_tables(casos, epizootias, colors):
    """
    ACTUALIZADA: Solo muestra tablas separadas según especificación.
    CORREGIDA: Limita columnas de casos hasta 'Inicio de síntomas'.
    """
    st.subheader("📋 Datos Filtrados")
    
    # Filtrar columnas de casos hasta "Inicio de síntomas"
    casos_filtered = filter_casos_columns(casos) if not casos.empty else pd.DataFrame()
    
    # Preparar datos para mostrar
    casos_display = prepare_dataframe_for_display(casos_filtered, ["fecha_inicio_sintomas"]) if not casos_filtered.empty else pd.DataFrame()
    epizootias_display = prepare_dataframe_for_display(epizootias, ["fecha_recoleccion"]) if not epizootias.empty else pd.DataFrame()
    
    # Solo tablas separadas
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("**🦠 Casos Confirmados**")
        if not casos_display.empty:
            st.dataframe(casos_display, use_container_width=True, height=400)
            st.caption(f"Total: {len(casos_display)} casos mostrados")
        else:
            st.info("No hay casos que mostrar con los filtros aplicados.")
    
    with col2:
        st.markdown("**🐒 Epizootias**")
        if not epizootias_display.empty:
            st.dataframe(epizootias_display, use_container_width=True, height=400)
            st.caption(f"Total: {len(epizootias_display)} epizootias mostradas")
        else:
            st.info("No hay epizootias que mostrar con los filtros aplicados.")


def show_consolidated_export_section(casos, epizootias):
    """
    NUEVA: Sección consolidada de exportación de datos.
    """
    st.subheader("📥 Exportar Datos")
    
    # Información sobre los datos disponibles
    casos_count = len(casos)
    epi_count = len(epizootias)
    
    st.markdown(
        f"""
        <div style="
            background-color: #e8f4fd;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #4682B4;
            margin-bottom: 20px;
        ">
            <h5 style="color: #4682B4; margin-top: 0;">📊 Datos Disponibles para Exportación</h5>
            <p><strong>• Casos confirmados:</strong> {casos_count} registros</p>
            <p><strong>• Epizootias:</strong> {epi_count} registros</p>
            <p style="margin-bottom: 0;"><strong>• Filtros aplicados:</strong> Los datos exportados reflejan los filtros actualmente seleccionados</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Opciones de exportación
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📊 Excel Completo**")
        if not casos.empty or not epizootias.empty:
            excel_data = create_excel_with_multiple_sheets(casos, epizootias)
            st.download_button(
                label="📊 Descargar Excel",
                data=excel_data,
                file_name=f"fiebre_amarilla_filtrado_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Excel con hojas separadas: Casos, Epizootias y Resumen",
                use_container_width=True
            )
        else:
            st.button("📊 Descargar Excel", disabled=True, help="No hay datos para exportar")
    
    with col2:
        st.markdown("**🦠 Solo Casos**")
        if not casos.empty:
            casos_filtered = filter_casos_columns(casos)
            casos_csv = casos_filtered.to_csv(index=False)
            st.download_button(
                label="🦠 Casos CSV",
                data=casos_csv,
                file_name=f"casos_filtrados_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                help="Solo casos confirmados en formato CSV (hasta columna Inicio de síntomas)",
                use_container_width=True
            )
        else:
            st.button("🦠 Casos CSV", disabled=True, help="No hay casos para exportar")
    
    with col3:
        st.markdown("**🐒 Solo Epizootias**")
        if not epizootias.empty:
            epizootias_csv = epizootias.to_csv(index=False)
            st.download_button(
                label="🐒 Epizootias CSV",
                data=epizootias_csv,
                file_name=f"epizootias_filtradas_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                help="Solo epizootias en formato CSV",
                use_container_width=True
            )
        else:
            st.button("🐒 Epizootias CSV", disabled=True, help="No hay epizootias para exportar")


def create_municipio_geographic_summary(casos, epizootias):
    """
    Crea resumen por municipio.
    """
    municipio_data = []

    # Obtener todos los municipios únicos de ambos datasets
    municipios_casos = set()
    municipios_epi = set()

    if not casos.empty and "municipio" in casos.columns:
        municipios_casos.update(casos["municipio"].dropna())

    if not epizootias.empty and "municipio" in epizootias.columns:
        municipios_epi.update(epizootias["municipio"].dropna())

    todos_municipios = sorted(municipios_casos.union(municipios_epi))

    for municipio in todos_municipios:
        # Contar casos en este municipio
        casos_municipio = 0
        fallecidos_municipio = 0
        if not casos.empty and "municipio" in casos.columns:
            casos_mpio = casos[casos["municipio"] == municipio]
            casos_municipio = len(casos_mpio)

            if "condicion_final" in casos_mpio.columns:
                fallecidos_municipio = (
                    casos_mpio["condicion_final"] == "Fallecido"
                ).sum()

        # Contar epizootias en este municipio
        total_epizootias = 0
        epizootias_positivas = 0
        if not epizootias.empty and "municipio" in epizootias.columns:
            epi_mpio = epizootias[epizootias["municipio"] == municipio]
            total_epizootias = len(epi_mpio)

            if "descripcion" in epi_mpio.columns:
                epizootias_positivas = (epi_mpio["descripcion"] == "POSITIVO FA").sum()

        # Calcular total de eventos (para ordenar)
        total_eventos = casos_municipio + epizootias_positivas

        # Solo incluir municipios con al menos algún evento
        if total_eventos > 0:
            municipio_data.append(
                {
                    "Ubicacion": municipio,
                    "Casos": casos_municipio,
                    "Fallecidos": fallecidos_municipio,
                    "Total_Epizootias": total_epizootias,
                    "Epizootias_Positivas": epizootias_positivas,
                    "Total_Eventos": total_eventos,
                }
            )

    if municipio_data:
        df = pd.DataFrame(municipio_data)
        return df.sort_values("Total_Eventos", ascending=False)

    return pd.DataFrame()


def create_vereda_geographic_summary(casos, epizootias, municipio_normalizado):
    """
    NUEVA: Crea resumen por vereda para un municipio específico.
    """
    vereda_data = []

    # Filtrar datos por municipio normalizado
    casos_municipio = casos[casos["municipio_normalizado"] == municipio_normalizado] if not casos.empty else pd.DataFrame()
    epizootias_municipio = epizootias[epizootias["municipio_normalizado"] == municipio_normalizado] if not epizootias.empty else pd.DataFrame()

    # Obtener todas las veredas únicas del municipio
    veredas_casos = set()
    veredas_epi = set()

    if not casos_municipio.empty and "vereda" in casos_municipio.columns:
        veredas_casos.update(casos_municipio["vereda"].dropna())

    if not epizootias_municipio.empty and "vereda" in epizootias_municipio.columns:
        veredas_epi.update(epizootias_municipio["vereda"].dropna())

    todas_veredas = sorted(veredas_casos.union(veredas_epi))

    for vereda in todas_veredas:
        # Contar casos en esta vereda
        casos_vereda = 0
        fallecidos_vereda = 0
        if not casos_municipio.empty and "vereda" in casos_municipio.columns:
            casos_ver = casos_municipio[casos_municipio["vereda"] == vereda]
            casos_vereda = len(casos_ver)

            if "condicion_final" in casos_ver.columns:
                fallecidos_vereda = (casos_ver["condicion_final"] == "Fallecido").sum()

        # Contar epizootias en esta vereda
        total_epizootias = 0
        epizootias_positivas = 0
        if not epizootias_municipio.empty and "vereda" in epizootias_municipio.columns:
            epi_ver = epizootias_municipio[epizootias_municipio["vereda"] == vereda]
            total_epizootias = len(epi_ver)

            if "descripcion" in epi_ver.columns:
                epizootias_positivas = (epi_ver["descripcion"] == "POSITIVO FA").sum()

        # Calcular total de eventos (para ordenar)
        total_eventos = casos_vereda + epizootias_positivas

        # Solo incluir veredas con al menos algún evento
        if total_eventos > 0:
            vereda_data.append(
                {
                    "Ubicacion": vereda,
                    "Casos": casos_vereda,
                    "Fallecidos": fallecidos_vereda,
                    "Total_Epizootias": total_epizootias,
                    "Epizootias_Positivas": epizootias_positivas,
                    "Total_Eventos": total_eventos,
                }
            )

    if vereda_data:
        df = pd.DataFrame(vereda_data)
        return df.sort_values("Total_Eventos", ascending=False)

    return pd.DataFrame()


def create_excel_with_multiple_sheets(casos, epizootias):
    """
    Crea un archivo Excel con múltiples hojas.
    ACTUALIZADA: Limita columnas de casos hasta 'Inicio de síntomas'.
    """
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Hoja de casos (con columnas filtradas)
        if not casos.empty:
            casos_filtered = filter_casos_columns(casos)
            casos_clean = prepare_dataframe_for_display(casos_filtered, ["fecha_inicio_sintomas"])
            casos_clean.to_excel(writer, sheet_name='Casos_Confirmados', index=False)
        
        # Hoja de epizootias
        if not epizootias.empty:
            epizootias_clean = prepare_dataframe_for_display(epizootias, ["fecha_recoleccion"])
            epizootias_clean.to_excel(writer, sheet_name='Epizootias', index=False)
        
        # Hoja de resumen
        summary_data = create_summary_sheet(casos, epizootias)
        if not summary_data.empty:
            summary_data.to_excel(writer, sheet_name='Resumen', index=False)
    
    buffer.seek(0)
    return buffer.getvalue()


def create_summary_sheet(casos, epizootias):
    """
    Crea una hoja de resumen para el Excel.
    """
    summary_data = []
    
    # Resumen general
    summary_data.append({
        "Indicador": "Total Casos Confirmados",
        "Valor": len(casos),
        "Observaciones": "Casos humanos confirmados de fiebre amarilla"
    })
    
    if not casos.empty and "condicion_final" in casos.columns:
        fallecidos = (casos["condicion_final"] == "Fallecido").sum()
        letalidad = (fallecidos / len(casos) * 100) if len(casos) > 0 else 0
        
        summary_data.append({
            "Indicador": "Fallecidos",
            "Valor": fallecidos,
            "Observaciones": f"Letalidad: {letalidad:.1f}%"
        })
    
    summary_data.append({
        "Indicador": "Total Epizootias",
        "Valor": len(epizootias),
        "Observaciones": "Eventos en fauna silvestre registrados"
    })
    
    if not epizootias.empty and "descripcion" in epizootias.columns:
        positivos = (epizootias["descripcion"] == "POSITIVO FA").sum()
        positividad = (positivos / len(epizootias) * 100) if len(epizootias) > 0 else 0
        
        summary_data.append({
            "Indicador": "Epizootias Positivas",
            "Valor": positivos,
            "Observaciones": f"Positividad: {positividad:.1f}%"
        })
    
    # Fecha de generación
    summary_data.append({
        "Indicador": "Fecha de Generación",
        "Valor": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Observaciones": "Fecha y hora de exportación de datos"
    })
    
    return pd.DataFrame(summary_data)