"""
Vista de análisis epidemiológico.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
import logging

# Configurar logger
logger = logging.getLogger(__name__)

def show(data_filtered, filters, colors):
    """Vista principal de análisis epidemiológico OPTIMIZADA."""
    logger.info("📊 INICIANDO VISTA TABLAS OPTIMIZADA")
    
    # Aplicar CSS estético UNA SOLA VEZ
    apply_tables_css_super_aesthetic(colors)
    
    # Verificar datos filtrados UNA SOLA VEZ
    casos_filtrados = data_filtered["casos"]
    epizootias_filtradas = data_filtered["epizootias"]
    
    if not isinstance(casos_filtrados, pd.DataFrame) or not isinstance(epizootias_filtradas, pd.DataFrame):
        st.error("Error: datos no válidos")
        return
    
    logger.info(f"📊 Datos recibidos: {len(casos_filtrados)} casos, {len(epizootias_filtradas)} epizootias")
    
    # Información de contexto
    active_filters = filters.get("active_filters", [])
    context_info = "datos filtrados" if active_filters else "datos completos del Tolima"
    
    if active_filters:
        st.info(f"📊 Análisis de {context_info}: {' • '.join(active_filters[:2])}")

    # **SECCIONES PRINCIPALES**
    show_executive_summary_optimized(casos_filtrados, epizootias_filtradas, filters, colors)
    show_detailed_tables_optimized(casos_filtrados, epizootias_filtradas, colors)
    show_location_summary_optimized(casos_filtrados, epizootias_filtradas, colors)
    show_visual_analysis_optimized(casos_filtrados, epizootias_filtradas, colors)
    show_export_section_optimized(casos_filtrados, epizootias_filtradas, filters, colors)

# ===== SECCIÓN 1: RESUMEN EJECUTIVO =====

def show_executive_summary_optimized(casos, epizootias, filters, colors):
    """Resumen ejecutivo con métricas principales."""
    from utils.data_processor import calculate_basic_metrics
    
    st.markdown(
        """
        <div class="analysis-section">
            <div class="section-header">📊 Resumen Ejecutivo</div>
        """,
        unsafe_allow_html=True,
    )
    
    # Contexto de filtrado
    active_filters = filters.get("active_filters", [])
    if active_filters:
        filter_context = f"Filtrado por: {' • '.join(active_filters[:2])}"
        if len(active_filters) > 2:
            filter_context += f" • +{len(active_filters)-2} más"
    else:
        filter_context = "Vista completa del Tolima"
    
    st.markdown(
        f"""
        <div class="context-info">
            <strong>📍 Contexto:</strong> {filter_context}<br>
            <strong>📊 Período:</strong> Todos los eventos registrados en el contexto seleccionado
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Calcular métricas UNA SOLA VEZ
    metrics = calculate_basic_metrics(casos, epizootias)
    
    # Mostrar métricas en grid
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🦠 Casos Humanos", metrics["total_casos"])
    with col2:
        st.metric("⚰️ Fallecidos", metrics["fallecidos"], 
                 delta=f"{metrics['letalidad']:.1f}% letalidad")
    with col3:
        st.metric("🐒 Epizootias", metrics["total_epizootias"])
    with col4:
        st.metric("🔴 Positivas", metrics["epizootias_positivas"], 
                 delta=f"{metrics['positividad']:.1f}% positividad")

    # Información de últimos eventos
    create_last_events_info_optimized(metrics, active_filters, colors)
    
    st.markdown("</div>", unsafe_allow_html=True)

def create_last_events_info_optimized(metrics, active_filters, colors):
    """Información de últimos eventos optimizada."""
    col1, col2 = st.columns(2)
    
    filter_suffix = " (en área filtrada)" if active_filters else ""
    
    with col1:
        ultimo_caso = metrics["ultimo_caso"]
        if ultimo_caso["existe"]:
            fecha_str = ultimo_caso["fecha"].strftime('%d/%m/%Y') if ultimo_caso["fecha"] else 'Sin fecha'
            st.markdown(
                f"""
                <div class="event-info-card caso-card">
                    <strong>🦠 Último Caso{filter_suffix}:</strong><br>
                    📍 {ultimo_caso["ubicacion"]}<br>
                    📅 {fecha_str}<br>
                    ⏱️ Hace {ultimo_caso["tiempo_transcurrido"]}
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class="event-info-card no-data-card">
                    <strong>🦠 Último Caso:</strong><br>
                    📭 Sin casos registrados{filter_suffix}
                </div>
                """,
                unsafe_allow_html=True,
            )
    
    with col2:
        ultima_epizootia = metrics["ultima_epizootia_positiva"]
        if ultima_epizootia["existe"]:
            fecha_str = ultima_epizootia["fecha"].strftime('%d/%m/%Y') if ultima_epizootia["fecha"] else 'Sin fecha'
            st.markdown(
                f"""
                <div class="event-info-card epizootia-card">
                    <strong>🔴 Última Epizootia Positiva{filter_suffix}:</strong><br>
                    📍 {ultima_epizootia["ubicacion"]}<br>
                    📅 {fecha_str}<br>
                    ⏱️ Hace {ultima_epizootia["tiempo_transcurrido"]}
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class="event-info-card no-data-card">
                    <strong>🔴 Última Epizootia Positiva:</strong><br>
                    📭 Sin epizootias positivas{filter_suffix}
                </div>
                """,
                unsafe_allow_html=True,
            )

# ===== SECCIÓN 2: TABLAS DETALLADAS =====

def show_detailed_tables_optimized(casos, epizootias, colors):
    """Tablas detalladas tipo Excel optimizadas."""
    st.markdown(
        """
        <div class="analysis-section">
            <div class="section-header">📊 Tablas Detalladas</div>
        """,
        unsafe_allow_html=True,
    )

    # Preparar datos para mostrar UNA SOLA VEZ
    casos_display = prepare_data_for_display(casos, "casos")
    epizootias_display = prepare_data_for_display(epizootias, "epizootias")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 🦠 Casos Humanos")
        if not casos_display.empty:
            # Filtros rápidos
            casos_filtered = apply_quick_filters(casos_display, "casos")
            
            st.markdown(
                f"""
                <div class="table-info">
                    📋 Mostrando {len(casos_filtered)} de {len(casos_display)} registros
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            st.dataframe(casos_filtered, use_container_width=True, height=500, hide_index=True)
        else:
            st.info("📭 No hay casos para mostrar")

    with col2:
        st.markdown("### 🐒 Epizootias")
        if not epizootias_display.empty:
            # Filtros rápidos
            epizootias_filtered = apply_quick_filters(epizootias_display, "epizootias")
            
            # Desglose por tipo
            positivas = len(epizootias_filtered[epizootias_filtered["Resultado"] == "POSITIVO FA"]) if "Resultado" in epizootias_filtered.columns else 0
            en_estudio = len(epizootias_filtered[epizootias_filtered["Resultado"] == "EN ESTUDIO"]) if "Resultado" in epizootias_filtered.columns else 0
            
            st.markdown(
                f"""
                <div class="table-info">
                    📋 {positivas} positivas • {en_estudio} en estudio • {len(epizootias_filtered)} total
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            st.dataframe(epizootias_filtered, use_container_width=True, height=500, hide_index=True)
        else:
            st.info("📭 No hay epizootias para mostrar")

    st.markdown("</div>", unsafe_allow_html=True)

# ===== SECCIÓN 3: RESUMEN POR UBICACIÓN =====

def show_location_summary_optimized(casos, epizootias, colors):
    """Resumen por ubicación optimizado."""
    st.markdown(
        """
        <div class="analysis-section">
            <div class="section-header">📈 Resumen por Ubicación</div>
        """,
        unsafe_allow_html=True,
    )

    summary_data = create_location_summary_optimized(casos, epizootias)
    
    if summary_data:
        summary_df = create_summary_dataframe(summary_data)
        
        st.dataframe(summary_df, use_container_width=True, height=400, hide_index=True)
        
        # Estadísticas generales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🏛️ Ubicaciones", len(summary_data))
        with col2:
            ubicaciones_con_casos = len([m for m in summary_data if m["casos"] > 0])
            st.metric("🦠 Con Casos", ubicaciones_con_casos)
        with col3:
            ubicaciones_con_epizootias = len([m for m in summary_data if m["epizootias"] > 0])
            st.metric("🐒 Con Epizootias", ubicaciones_con_epizootias)
        with col4:
            ubicaciones_mixtas = len([m for m in summary_data if m["casos"] > 0 and m["epizootias"] > 0])
            st.metric("🔄 Ambos", ubicaciones_mixtas)
    else:
        st.info("📊 No hay datos suficientes para el resumen por ubicación")

    st.markdown("</div>", unsafe_allow_html=True)

# ===== SECCIÓN 4: ANÁLISIS VISUAL =====

def show_visual_analysis_optimized(casos, epizootias, colors):
    """Análisis visual optimizado."""
    st.markdown(
        """
        <div class="analysis-section">
            <div class="section-header">📊 Análisis Visual</div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🦠 Distribución de Casos")
        create_casos_chart_optimized(casos, colors)

    with col2:
        st.markdown("#### 🐒 Distribución de Epizootias") 
        create_epizootias_chart_optimized(epizootias, colors)

    st.markdown("</div>", unsafe_allow_html=True)

# ===== SECCIÓN 5: EXPORTACIÓN =====

def show_export_section_optimized(casos, epizootias, filters, colors):
    """Sección de exportación optimizada."""
    st.markdown(
        """
        <div class="analysis-section">
            <div class="section-header">📥 Exportación de Datos</div>
        """,
        unsafe_allow_html=True,
    )

    # Información de contexto
    active_filters = filters.get("active_filters", [])
    filter_info = "datos completos del Tolima" if not active_filters else f"datos filtrados por: {' • '.join(active_filters[:2])}"

    st.markdown(
        f"""
        <div class="export-info">
            <div class="export-title">📊 Datos Listos para Exportar ({filter_info})</div>
            <strong>Casos humanos:</strong> {len(casos)} registros<br>
            <strong>Epizootias:</strong> {len(epizootias)} registros<br>
            <strong>Incluye:</strong> Solo los datos que pasaron los filtros aplicados
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Botones de exportación
    create_export_buttons_optimized(casos, epizootias, filters, active_filters)
    
    st.markdown("</div>", unsafe_allow_html=True)

# ===== FUNCIONES DE APOYO OPTIMIZADAS =====

def prepare_data_for_display(data, data_type):
    """Prepara datos para vista detallada optimizada."""
    if data.empty:
        return pd.DataFrame()

    data_display = data.copy()
    
    if data_type == "casos":
        # Formatear fechas
        if "fecha_inicio_sintomas" in data_display.columns:
            data_display["fecha_inicio_sintomas"] = data_display["fecha_inicio_sintomas"].dt.strftime('%d/%m/%Y')
        
        # Renombrar columnas
        rename_map = {
            'municipio': 'Municipio', 'vereda': 'Vereda', 'fecha_inicio_sintomas': 'Fecha Inicio',
            'edad': 'Edad', 'sexo': 'Sexo', 'condicion_final': 'Condición Final', 'eps': 'EPS'
        }
    else:  # epizootias
        # Formatear fechas
        if "fecha_recoleccion" in data_display.columns:
            data_display["fecha_recoleccion"] = data_display["fecha_recoleccion"].dt.strftime('%d/%m/%Y')
        
        # Simplificar proveniente
        if "proveniente" in data_display.columns:
            data_display["proveniente"] = data_display["proveniente"].apply(
                lambda x: "Vigilancia Comunitaria" if "VIGILANCIA COMUNITARIA" in str(x) 
                else "Incautación/Rescate" if "INCAUTACIÓN" in str(x)
                else str(x)[:50] + "..." if len(str(x)) > 50 else str(x)
            )
        
        rename_map = {
            'municipio': 'Municipio', 'vereda': 'Vereda', 'fecha_recoleccion': 'Fecha Recolección',
            'descripcion': 'Resultado', 'proveniente': 'Fuente'
        }
    
    # Aplicar renombrado
    existing_renames = {k: v for k, v in rename_map.items() if k in data_display.columns}
    data_display = data_display.rename(columns=existing_renames)
    
    return data_display

def apply_quick_filters(data_display, data_type):
    """Aplica filtros rápidos dentro de tablas."""
    if data_display.empty:
        return data_display

    if data_type == "casos":
        # Filtros para casos
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if "Sexo" in data_display.columns:
                sexo_options = ["Todos"] + sorted(data_display["Sexo"].dropna().unique().tolist())
                sexo_filter = st.selectbox("🚻 Sexo:", sexo_options, key="sexo_filter_opt")
        
        with col2:
            if "Condición Final" in data_display.columns:
                condicion_options = ["Todas"] + sorted(data_display["Condición Final"].dropna().unique().tolist())
                condicion_filter = st.selectbox("⚰️ Condición:", condicion_options, key="condicion_filter_opt")
        
        with col3:
            if "Municipio" in data_display.columns:
                municipio_options = ["Todos"] + sorted(data_display["Municipio"].dropna().unique().tolist())
                municipio_filter = st.selectbox("📍 Municipio:", municipio_options, key="municipio_filter_opt")
        
        # Aplicar filtros
        filtered_data = data_display.copy()
        if 'sexo_filter' in locals() and sexo_filter != "Todos" and "Sexo" in filtered_data.columns:
            filtered_data = filtered_data[filtered_data["Sexo"] == sexo_filter]
        if 'condicion_filter' in locals() and condicion_filter != "Todas" and "Condición Final" in filtered_data.columns:
            filtered_data = filtered_data[filtered_data["Condición Final"] == condicion_filter]
        if 'municipio_filter' in locals() and municipio_filter != "Todos" and "Municipio" in filtered_data.columns:
            filtered_data = filtered_data[filtered_data["Municipio"] == municipio_filter]
        
        return filtered_data
    
    else:  # epizootias
        col1, col2 = st.columns(2)
        
        with col1:
            if "Resultado" in data_display.columns:
                resultado_options = ["Todos"] + sorted(data_display["Resultado"].dropna().unique().tolist())
                resultado_filter = st.selectbox("🔬 Resultado:", resultado_options, key="resultado_filter_opt")
        
        with col2:
            if "Fuente" in data_display.columns:
                fuente_options = ["Todas"] + sorted(data_display["Fuente"].dropna().unique().tolist())
                fuente_filter = st.selectbox("📋 Fuente:", fuente_options, key="fuente_filter_opt")
        
        # Aplicar filtros
        filtered_data = data_display.copy()
        if 'resultado_filter' in locals() and resultado_filter != "Todos" and "Resultado" in filtered_data.columns:
            filtered_data = filtered_data[filtered_data["Resultado"] == resultado_filter]
        if 'fuente_filter' in locals() and fuente_filter != "Todas" and "Fuente" in filtered_data.columns:
            filtered_data = filtered_data[filtered_data["Fuente"] == fuente_filter]
        
        return filtered_data

def create_location_summary_optimized(casos, epizootias):
    """Crea resumen por ubicación optimizado."""
    summary_data = []
    
    # Obtener ubicaciones únicas
    ubicaciones = set()
    if not casos.empty and "municipio" in casos.columns:
        ubicaciones.update(casos["municipio"].dropna())
    if not epizootias.empty and "municipio" in epizootias.columns:
        ubicaciones.update(epizootias["municipio"].dropna())
    
    for ubicacion in sorted(ubicaciones):
        # Casos en esta ubicación
        casos_ubi = casos[casos["municipio"] == ubicacion] if not casos.empty and "municipio" in casos.columns else pd.DataFrame()
        epi_ubi = epizootias[epizootias["municipio"] == ubicacion] if not epizootias.empty and "municipio" in epizootias.columns else pd.DataFrame()
        
        casos_count = len(casos_ubi)
        epi_count = len(epi_ubi)
        
        if casos_count > 0 or epi_count > 0:
            # Cálculos adicionales
            fallecidos = (casos_ubi["condicion_final"] == "Fallecido").sum() if not casos_ubi.empty and "condicion_final" in casos_ubi.columns else 0
            letalidad = (fallecidos / casos_count * 100) if casos_count > 0 else 0
            
            positivas = (epi_ubi["descripcion"] == "POSITIVO FA").sum() if not epi_ubi.empty and "descripcion" in epi_ubi.columns else 0
            en_estudio = (epi_ubi["descripcion"] == "EN ESTUDIO").sum() if not epi_ubi.empty and "descripcion" in epi_ubi.columns else 0
            
            categoria = "Mixto" if casos_count > 0 and epi_count > 0 else "Solo Casos" if casos_count > 0 else "Solo Epizootias"
            
            summary_data.append({
                "municipio": ubicacion, "casos": casos_count, "fallecidos": fallecidos,
                "letalidad": round(letalidad, 1), "epizootias": epi_count,
                "positivas": positivas, "en_estudio": en_estudio, "categoria": categoria
            })
    
    return summary_data

def create_summary_dataframe(summary_data):
    """Crea DataFrame estético para resumen."""
    summary_data_sorted = sorted(summary_data, key=lambda x: x["casos"], reverse=True)
    summary_df = pd.DataFrame(summary_data_sorted)
    
    return summary_df.rename(columns={
        'municipio': '📍 Ubicación', 'casos': '🦠 Casos', 'fallecidos': '⚰️ Fallecidos',
        'letalidad': '📊 Letalidad %', 'epizootias': '🐒 Epizootias', 'positivas': '🔴 Positivas',
        'en_estudio': '🔵 En Estudio', 'categoria': '🏷️ Tipo'
    })

def create_casos_chart_optimized(casos, colors):
    """Gráfico de casos optimizado."""
    if casos.empty:
        st.info("Sin casos para graficar")
        return
    
    if "municipio" in casos.columns:
        municipio_counts = casos["municipio"].value_counts().head(10)
        
        if not municipio_counts.empty:
            fig = px.bar(
                x=municipio_counts.values, y=municipio_counts.index, orientation="h",
                title="Top 10 Ubicaciones", labels={"x": "Casos", "y": "Ubicación"},
                color=municipio_counts.values, color_continuous_scale="Reds"
            )
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

def create_epizootias_chart_optimized(epizootias, colors):
    """Gráfico de epizootias optimizado."""
    if epizootias.empty:
        st.info("Sin epizootias para graficar")
        return
    
    if "descripcion" in epizootias.columns:
        resultado_counts = epizootias["descripcion"].value_counts()
        
        if not resultado_counts.empty:
            fig = px.pie(
                values=resultado_counts.values, names=resultado_counts.index,
                title="Distribución por Resultado",
                color_discrete_map={"POSITIVO FA": colors["danger"], "EN ESTUDIO": colors["info"]}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

def create_export_buttons_optimized(casos, epizootias, filters, active_filters):
    """Botones de exportación optimizados."""
    col1, col2, col3, col4 = st.columns(4)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    filter_suffix = "_filtrado" if active_filters else "_completo"

    with col1:
        if not casos.empty or not epizootias.empty:
            excel_data = create_excel_export_optimized(casos, epizootias, filters)
            st.download_button(
                label="📊 Excel Completo", data=excel_data,
                file_name=f"fiebre_amarilla{filter_suffix}_{timestamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    with col2:
        if not casos.empty:
            casos_display = prepare_data_for_display(casos, "casos")
            casos_csv = casos_display.to_csv(index=False)
            st.download_button(
                label="🦠 Casos CSV", data=casos_csv,
                file_name=f"casos{filter_suffix}_{timestamp}.csv",
                mime="text/csv", use_container_width=True
            )

    with col3:
        if not epizootias.empty:
            epizootias_display = prepare_data_for_display(epizootias, "epizootias")
            epizootias_csv = epizootias_display.to_csv(index=False)
            st.download_button(
                label="🐒 Epizootias CSV", data=epizootias_csv,
                file_name=f"epizootias{filter_suffix}_{timestamp}.csv",
                mime="text/csv", use_container_width=True
            )

    with col4:
        summary_data = create_location_summary_optimized(casos, epizootias)
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            summary_csv = summary_df.to_csv(index=False)
            st.download_button(
                label="📈 Resumen CSV", data=summary_csv,
                file_name=f"resumen{filter_suffix}_{timestamp}.csv",
                mime="text/csv", use_container_width=True
            )

def create_excel_export_optimized(casos, epizootias, filters):
    """Crea exportación Excel optimizada."""
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Hojas principales
        if not casos.empty:
            casos_export = prepare_data_for_display(casos, "casos")
            casos_export.to_excel(writer, sheet_name='Casos', index=False)
        
        if not epizootias.empty:
            epizootias_export = prepare_data_for_display(epizootias, "epizootias")
            epizootias_export.to_excel(writer, sheet_name='Epizootias', index=False)
        
        # Resumen
        summary_data = create_location_summary_optimized(casos, epizootias)
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Resumen', index=False)
        
        # Metadatos
        metadata = create_metadata_optimized(casos, epizootias, filters)
        metadata.to_excel(writer, sheet_name='Metadatos', index=False)
    
    buffer.seek(0)
    return buffer.getvalue()

def create_metadata_optimized(casos, epizootias, filters):
    """Crea metadatos optimizados."""
    active_filters = filters.get("active_filters", [])
    
    metadata_rows = [
        {"Campo": "Fecha Exportación", "Valor": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        {"Campo": "Tipo Exportación", "Valor": "Datos Filtrados" if active_filters else "Datos Completos"},
        {"Campo": "Total Casos", "Valor": len(casos)},
        {"Campo": "Total Epizootias", "Valor": len(epizootias)},
        {"Campo": "Dashboard Versión", "Valor": "4.0-OPTIMIZADO"}
    ]
    
    if active_filters:
        metadata_rows.append({"Campo": "Filtros Aplicados", "Valor": " • ".join(active_filters)})
    
    return pd.DataFrame(metadata_rows)

# ===== CSS SÚPER ESTÉTICO =====

def apply_tables_css_super_aesthetic(colors):
    """CSS súper estético para tablas aplicado UNA SOLA VEZ."""
    st.markdown(
        f"""
        <style>
        /* =============== CORRECCIÓN SCROLL INFINITO =============== */
        .main .block-container {{
            max-height: calc(100vh - 100px) !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
        }}
        
        .stDataFrame > div {{
            max-height: 400px !important;
            overflow-y: auto !important;
        }}
        
        .js-plotly-plot {{
            max-height: 500px !important;
            overflow: hidden !important;
        }}
        
        /* =============== SECCIONES PRINCIPALES =============== */
        .analysis-section {{
            background: linear-gradient(135deg, white 0%, #fafafa 100%) !important;
            border-radius: 20px !important;
            padding: 30px !important;
            margin: 25px 0 !important;
            box-shadow: 0 12px 40px rgba(0,0,0,0.12) !important;
            border-left: 6px solid {colors['primary']} !important;
            position: relative !important;
            overflow: hidden !important;
        }}

        .analysis-section::before {{
            content: '' !important;
            position: absolute !important;
            top: 0 !important;
            right: 0 !important;
            width: 100px !important;
            height: 100px !important;
            background: radial-gradient(circle, {colors['secondary']}40, transparent) !important;
            border-radius: 50% !important;
            transform: translate(50%, -50%) !important;
        }}

        .section-header {{
            color: {colors['primary']} !important;
            font-size: 1.6rem !important;
            font-weight: 800 !important;
            margin-bottom: 25px !important;
            display: flex !important;
            align-items: center !important;
            gap: 15px !important;
            padding-bottom: 15px !important;
            border-bottom: 3px solid {colors['secondary']} !important;
            position: relative !important;
            z-index: 2 !important;
        }}

        .section-header::after {{
            content: '' !important;
            position: absolute !important;
            bottom: -3px !important;
            left: 0 !important;
            width: 60px !important;
            height: 3px !important;
            background: {colors['accent']} !important;
            border-radius: 3px !important;
        }}

        /* =============== TARJETAS DE INFORMACIÓN =============== */
        .context-info {{
            background: linear-gradient(135deg, {colors['light']}, #ffffff) !important;
            border-radius: 15px !important;
            padding: 20px !important;
            margin: 20px 0 !important;
            border-left: 5px solid {colors['info']} !important;
            font-size: 0.95rem !important;
            line-height: 1.6 !important;
            box-shadow: 0 6px 20px rgba(0,0,0,0.08) !important;
        }}

        .event-info-card {{
            background: linear-gradient(135deg, #f8fafc, #ffffff) !important;
            border-radius: 16px !important;
            padding: 20px !important;
            margin: 15px 0 !important;
            font-size: 0.95rem !important;
            line-height: 1.5 !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08) !important;
            border: 2px solid transparent !important;
        }}

        .event-info-card:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 25px rgba(0,0,0,0.12) !important;
        }}

        .caso-card {{
            border-left: 5px solid {colors['danger']} !important;
            background: linear-gradient(135deg, #fef2f2, #ffffff) !important;
        }}

        .caso-card:hover {{
            border-color: {colors['danger']} !important;
        }}

        .epizootia-card {{
            border-left: 5px solid {colors['warning']} !important;
            background: linear-gradient(135deg, #fffbeb, #ffffff) !important;
        }}

        .epizootia-card:hover {{
            border-color: {colors['warning']} !important;
        }}

        .no-data-card {{
            border-left: 5px solid {colors['info']} !important;
            background: linear-gradient(135deg, #f0f9ff, #ffffff) !important;
            opacity: 0.8 !important;
        }}

        /* =============== TABLAS SÚPER ESTÉTICAS =============== */
        .table-info {{
            background: linear-gradient(45deg, {colors['info']}, {colors['primary']}) !important;
            color: white !important;
            padding: 12px 20px !important;
            border-radius: 25px !important;
            margin: 15px 0 !important;
            text-align: center !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
        }}

        .export-info {{
            background: linear-gradient(135deg, {colors['light']}, #ffffff) !important;
            border-radius: 15px !important;
            padding: 20px !important;
            margin: 20px 0 !important;
            border-left: 5px solid {colors['success']} !important;
            font-size: 0.95rem !important;
            line-height: 1.5 !important;
            box-shadow: 0 6px 20px rgba(0,0,0,0.08) !important;
        }}

        .export-title {{
            color: {colors['primary']} !important;
            font-weight: 700 !important;
            margin-bottom: 12px !important;
            font-size: 1.1rem !important;
        }}

        /* =============== FORMULARIOS ESTÉTICOS =============== */
        .stSelectbox > div > div {{
            border-radius: 10px !important;
            border: 2px solid #e2e8f0 !important;
            transition: all 0.3s ease !important;
        }}

        .stSelectbox > div > div:focus-within {{
            border-color: {colors['primary']} !important;
            box-shadow: 0 0 0 3px {colors['primary']}20 !important;
        }}

        .stSelectbox label {{
            color: {colors['primary']} !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
        }}

        /* =============== BOTONES MEJORADOS =============== */
        .stDownloadButton > button {{
            background: linear-gradient(135deg, {colors['primary']}, {colors['accent']}) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 12px 20px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
        }}

        .stDownloadButton > button:hover {{
            background: linear-gradient(135deg, {colors['accent']}, {colors['primary']}) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(0,0,0,0.3) !important;
        }}

        .stDownloadButton > button:disabled {{
            background: #cbd5e0 !important;
            cursor: not-allowed !important;
            transform: none !important;
        }}

        /* =============== DATAFRAMES ESTÉTICOS =============== */
        .stDataFrame {{
            border-radius: 12px !important;
            overflow: hidden !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08) !important;
        }}

        .stDataFrame [data-testid="stDataFrameResizable"] {{
            border: 1px solid #e2e8f0 !important;
            border-radius: 12px !important;
        }}

        /* =============== MÉTRICAS NATIVAS MEJORADAS =============== */
        [data-testid="metric-container"] {{
            background: linear-gradient(135deg, white, #f8fafc) !important;
            border-radius: 12px !important;
            padding: 20px !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08) !important;
            border-left: 4px solid {colors['primary']} !important;
            transition: all 0.3s ease !important;
        }}

        [data-testid="metric-container"]:hover {{
            transform: translateY(-3px) !important;
            box-shadow: 0 8px 25px rgba(0,0,0,0.12) !important;
        }}

        /* =============== RESPONSIVE =============== */
        @media (max-width: 768px) {{
            .analysis-section {{
                padding: 20px !important;
                margin: 15px 0 !important;
            }}

            .section-header {{
                font-size: 1.3rem !important;
            }}

            .event-info-card {{
                padding: 15px !important;
            }}

            .stColumns > div {{
                gap: 0.5rem !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )