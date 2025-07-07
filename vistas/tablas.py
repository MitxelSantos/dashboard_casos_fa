"""
Vista de análisis epidemiológico ACTUALIZADA del dashboard de Fiebre Amarilla.
NUEVAS FUNCIONALIDADES:
- Tablas detalladas estilo Excel con todas las columnas
- Tablas resumen estéticamente mejoradas
- Manejo de epizootias positivas + en estudio
- Información de último caso/epizootia con tiempo transcurrido
- Sin pestañas anidadas - interfaz simplificada
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
from utils.data_processor import (
    prepare_dataframe_for_display,
    get_latest_case_info,
    calculate_basic_metrics
)


def show(data_filtered, filters, colors):
    """
    Vista de análisis epidemiológico con tablas detalladas y estéticas.
    """
    casos = data_filtered["casos"]
    epizootias = data_filtered["epizootias"]  # Ya contiene positivas + en estudio

    # CSS para tablas mejoradas
    apply_enhanced_tables_css(colors)

    # Sección 2: Tablas detalladas tipo Excel
    show_detailed_excel_tables(casos, epizootias, colors)

    # Sección 3: Tabla resumen estética
    show_aesthetic_summary_table_FIXED(casos, epizootias, colors)

    # Sección 4: Análisis visual simplificado
    show_simplified_visual_analysis(casos, epizootias, colors)

    # Sección 5: Exportación avanzada
    show_comprehensive_export_section(casos, epizootias, colors)


def apply_enhanced_tables_css(colors):
    """CSS mejorado para tablas estéticas."""
    st.markdown(
        f"""
        <style>
        /* Estilos para secciones principales */
        .analysis-section {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin: 20px 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            border-left: 5px solid {colors['primary']};
        }}

        .section-header {{
            color: {colors['primary']};
            font-size: 1.4rem;
            font-weight: 700;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 12px;
            padding-bottom: 10px;
            border-bottom: 2px solid {colors['secondary']};
        }}

        /* Tabla resumen estética */
        .aesthetic-table {{
            width: 100%;
            border-collapse: collapse;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin: 20px 0;
        }}

        .aesthetic-table th {{
            background: linear-gradient(135deg, {colors['primary']}, {colors['accent']});
            color: white;
            padding: 15px 12px;
            text-align: left;
            font-weight: 600;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .aesthetic-table td {{
            padding: 12px;
            border-bottom: 1px solid #e9ecef;
            font-size: 0.9rem;
            transition: background-color 0.3s ease;
        }}

        .aesthetic-table tr:hover td {{
            background-color: #f8f9fa;
        }}

        .aesthetic-table tr:last-child td {{
            border-bottom: none;
        }}

        /* Estilos para métricas rápidas */
        .quick-metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}

        .quick-metric {{
            background: linear-gradient(135deg, #f8f9fa, white);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border-left: 4px solid {colors['info']};
            box-shadow: 0 3px 10px rgba(0,0,0,0.05);
            transition: transform 0.3s ease;
        }}

        .quick-metric:hover {{
            transform: translateY(-3px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.1);
        }}

        .quick-metric-value {{
            font-size: 2rem;
            font-weight: 700;
            color: {colors['primary']};
            margin-bottom: 8px;
        }}

        .quick-metric-label {{
            color: #666;
            font-weight: 500;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        /* Indicadores de color por tipo */
        .municipio-casos {{ border-left-color: {colors['danger']} !important; }}
        .municipio-epizootias {{ border-left-color: {colors['warning']} !important; }}
        .municipio-mixto {{ border-left-color: {colors['primary']} !important; }}
        .municipio-sin-datos {{ border-left-color: #cccccc !important; }}

        /* Tablas de datos responsivas */
        .data-table-container {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            overflow-x: auto;
            margin: 20px 0;
        }}

        .data-table-container h4 {{
            color: {colors['primary']};
            margin-bottom: 15px;
            font-size: 1.2rem;
            font-weight: 600;
        }}

        /* Botones de filtro */
        .filter-chips {{
            display: flex;
            gap: 10px;
            margin: 15px 0;
            flex-wrap: wrap;
        }}

        .filter-chip {{
            background: {colors['light']};
            color: {colors['primary']};
            padding: 8px 15px;
            border-radius: 20px;
            border: 1px solid {colors['secondary']};
            font-size: 0.8rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
        }}

        .filter-chip:hover {{
            background: {colors['secondary']};
            color: white;
            transform: translateY(-1px);
        }}

        /* Información contextual */
        .info-box {{
            background: linear-gradient(135deg, {colors['light']}, #ffffff);
            border-radius: 10px;
            padding: 15px;
            margin: 15px 0;
            border-left: 4px solid {colors['info']};
            font-size: 0.9rem;
            line-height: 1.5;
        }}

        .info-box-title {{
            color: {colors['primary']};
            font-weight: 600;
            margin-bottom: 8px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def show_detailed_excel_tables(casos, epizootias, colors):
    """Tablas detalladas tipo Excel con todas las columnas."""
    st.markdown(
        """
        <div class="analysis-section">
            <div class="section-header">
                📊 Tablas Detalladas
            </div>
        """,
        unsafe_allow_html=True,
    )

    # Preparar datos para mostrar
    casos_display = prepare_casos_for_detailed_view(casos)
    epizootias_display = prepare_epizootias_for_detailed_view(epizootias)

    # Crear dos columnas para las tablas
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 🦠 Casos Humanos Detallados")
        if not casos_display.empty:
            # Filtros rápidos para casos
            create_quick_filters_casos(casos_display)
            
            # Aplicar filtros si están activos
            casos_filtrados = apply_table_filters_casos(casos_display)
            
            st.markdown(
                f"""
                <div class="data-table-container">
                    <h4>📋 Todos los casos ({len(casos_filtrados)} registros)</h4>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            # Mostrar tabla con scroll
            st.dataframe(
                casos_filtrados,
                use_container_width=True,
                height=500,
                hide_index=True
            )
            
            # Información adicional
            st.caption(f"💡 Mostrando {len(casos_filtrados)} de {len(casos_display)} casos totales")
            
        else:
            st.info("📭 No hay casos para mostrar con los filtros actuales")

    with col2:
        st.markdown("### 🐒 Epizootias Detalladas")
        if not epizootias_display.empty:
            # Filtros rápidos para epizootias
            create_quick_filters_epizootias(epizootias_display)
            
            # Aplicar filtros si están activos
            epizootias_filtradas = apply_table_filters_epizootias(epizootias_display)
            
            st.markdown(
                f"""
                <div class="data-table-container">
                    <h4>📋 Todas las epizootias ({len(epizootias_filtradas)} registros)</h4>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            # Mostrar tabla con scroll
            st.dataframe(
                epizootias_filtradas,
                use_container_width=True,
                height=500,
                hide_index=True
            )
            
            # Desglose por tipo
            if "Resultado" in epizootias_filtradas.columns:
                positivas = len(epizootias_filtradas[epizootias_filtradas["Resultado"] == "POSITIVO FA"])
                en_estudio = len(epizootias_filtradas[epizootias_filtradas["Resultado"] == "EN ESTUDIO"])
                st.caption(f"💡 {positivas} positivas • {en_estudio} en estudio • {len(epizootias_filtradas)} total")
            else:
                st.caption(f"💡 Mostrando {len(epizootias_filtradas)} de {len(epizootias_display)} epizootias totales")
                
        else:
            st.info("📭 No hay epizootias para mostrar con los filtros actuales")

    st.markdown("</div>", unsafe_allow_html=True)

def show_aesthetic_summary_table_FIXED(casos_filtrados, epizootias_filtradas, colors):
    """
    CORREGIDO para vistas/tablas.py - Usa datos filtrados garantizados.
    Reemplazar la función original por esta versión.
    """
    from utils.data_processor import verify_filtered_data_usage
    
    # VERIFICACIÓN: Asegurar que se usan datos filtrados
    verify_filtered_data_usage(casos_filtrados, "show_aesthetic_summary_table - casos")
    verify_filtered_data_usage(epizootias_filtradas, "show_aesthetic_summary_table - epizootias")
    
    st.markdown(
        """
        <div class="analysis-section">
            <div class="section-header">
                📈 Resumen por Ubicación (Datos Filtrados)
            </div>
        """,
        unsafe_allow_html=True,
    )

    # Crear resumen por municipios CON DATOS FILTRADOS
    summary_data = create_location_summary_FIXED(casos_filtrados, epizootias_filtradas)
    
    if summary_data:
        # Mostrar como DataFrame estético
        summary_df = create_aesthetic_summary_html_FIXED(summary_data, colors)
        if isinstance(summary_df, pd.DataFrame):
            st.dataframe(
                summary_df,
                use_container_width=True,
                height=400,
                hide_index=True
            )
        else:
            st.info("No hay datos suficientes para el resumen")
        
        # Estadísticas generales del resumen DE DATOS FILTRADOS
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_municipios = len(summary_data)
            st.metric("🏛️ Municipios", total_municipios)
        
        with col2:
            municipios_con_casos = len([m for m in summary_data if m["casos"] > 0])
            st.metric("🦠 Con Casos", municipios_con_casos)
        
        with col3:
            municipios_con_epizootias = len([m for m in summary_data if m["epizootias"] > 0])
            st.metric("🐒 Con Epizootias", municipios_con_epizootias)
        
        with col4:
            municipios_mixtos = len([m for m in summary_data if m["casos"] > 0 and m["epizootias"] > 0])
            st.metric("🔄 Ambos", municipios_mixtos)
    else:
        st.info("📊 No hay datos suficientes para crear el resumen por ubicación con los filtros aplicados")

    st.markdown("</div>", unsafe_allow_html=True)

def show_simplified_visual_analysis(casos, epizootias, colors):
    """Análisis visual simplificado sin pestañas anidadas."""
    st.markdown(
        """
        <div class="analysis-section">
            <div class="section-header">
                📊 Análisis Visual
            </div>
        """,
        unsafe_allow_html=True,
    )

    # Solo 2 gráficos principales - uno para casos, uno para epizootias
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🦠 Distribución de Casos")
        if not casos.empty:
            create_casos_distribution_chart(casos, colors)
        else:
            st.info("Sin datos de casos para graficar")

    with col2:
        st.markdown("#### 🐒 Distribución de Epizootias")
        if not epizootias.empty:
            create_epizootias_distribution_chart(epizootias, colors)
        else:
            st.info("Sin datos de epizootias para graficar")

    st.markdown("</div>", unsafe_allow_html=True)


def show_comprehensive_export_section(casos, epizootias, colors):
    """Sección de exportación completa y mejorada."""
    st.markdown(
        """
        <div class="analysis-section">
            <div class="section-header">
                📥 Exportación de Datos
            </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="info-box">
            <div class="info-box-title">📊 Datos Listos para Exportar</div>
            <strong>Casos humanos:</strong> {len(casos)} registros<br>
            <strong>Epizootias:</strong> {len(epizootias)} registros ({len(epizootias[epizootias["descripcion"] == "POSITIVO FA"]) if not epizootias.empty and "descripcion" in epizootias.columns else 0} positivas + {len(epizootias[epizootias["descripcion"] == "EN ESTUDIO"]) if not epizootias.empty and "descripcion" in epizootias.columns else 0} en estudio)<br>
            <strong>Incluye:</strong> Todas las columnas disponibles + resumen ejecutivo
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Botones de exportación mejorados
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if not casos.empty or not epizootias.empty:
            excel_data = create_comprehensive_excel_export(casos, epizootias)
            st.download_button(
                label="📊 Excel Completo",
                data=excel_data,
                file_name=f"fiebre_amarilla_completo_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Excel con todas las hojas y análisis",
                use_container_width=True
            )
        else:
            st.button("📊 Excel Completo", disabled=True, help="Sin datos")

    with col2:
        if not casos.empty:
            casos_csv = prepare_casos_for_detailed_view(casos).to_csv(index=False)
            st.download_button(
                label="🦠 Casos CSV",
                data=casos_csv,
                file_name=f"casos_detallados_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                help="Casos con todas las columnas",
                use_container_width=True
            )
        else:
            st.button("🦠 Casos CSV", disabled=True, help="Sin casos")

    with col3:
        if not epizootias.empty:
            epizootias_csv = prepare_epizootias_for_detailed_view(epizootias).to_csv(index=False)
            st.download_button(
                label="🐒 Epizootias CSV",
                data=epizootias_csv,
                file_name=f"epizootias_detalladas_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                help="Epizootias con todas las columnas",
                use_container_width=True
            )
        else:
            st.button("🐒 Epizootias CSV", disabled=True, help="Sin epizootias")

    with col4:
        summary_data = create_location_summary_FIXED(casos, epizootias)
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            summary_csv = summary_df.to_csv(index=False)
            st.download_button(
                label="📈 Resumen CSV",
                data=summary_csv,
                file_name=f"resumen_ubicacion_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                help="Resumen por ubicación",
                use_container_width=True
            )
        else:
            st.button("📈 Resumen CSV", disabled=True, help="Sin datos para resumen")

    st.markdown("</div>", unsafe_allow_html=True)


# === FUNCIONES DE APOYO ===

def prepare_casos_for_detailed_view(casos):
    """Prepara casos para vista detallada con todas las columnas."""
    if casos.empty:
        return pd.DataFrame()

    casos_display = casos.copy()
    
    # Formatear fechas
    if "fecha_inicio_sintomas" in casos_display.columns:
        casos_display["fecha_inicio_sintomas"] = casos_display["fecha_inicio_sintomas"].dt.strftime('%d/%m/%Y')
    
    # Renombrar columnas para mejor legibilidad
    rename_map = {
        'municipio': 'Municipio',
        'vereda': 'Vereda',
        'fecha_inicio_sintomas': 'Fecha Inicio Síntomas',
        'edad': 'Edad',
        'sexo': 'Sexo',
        'condicion_final': 'Condición Final',
        'eps': 'EPS'
    }
    
    # Solo renombrar columnas que existen
    existing_renames = {k: v for k, v in rename_map.items() if k in casos_display.columns}
    casos_display = casos_display.rename(columns=existing_renames)
    
    return casos_display


def prepare_epizootias_for_detailed_view(epizootias):
    """Prepara epizootias para vista detallada con todas las columnas."""
    if epizootias.empty:
        return pd.DataFrame()

    epi_display = epizootias.copy()
    
    # Formatear fechas
    if "fecha_recoleccion" in epi_display.columns:
        epi_display["fecha_recoleccion"] = epi_display["fecha_recoleccion"].dt.strftime('%d/%m/%Y')
    
    # Simplificar texto de proveniente
    if "proveniente" in epi_display.columns:
        epi_display["proveniente"] = epi_display["proveniente"].apply(
            lambda x: "Vigilancia Comunitaria" if "VIGILANCIA COMUNITARIA" in str(x) 
            else "Incautación/Rescate" if "INCAUTACIÓN" in str(x)
            else str(x)[:50] + "..." if len(str(x)) > 50 else str(x)
        )
    
    # Renombrar columnas
    rename_map = {
        'municipio': 'Municipio',
        'vereda': 'Vereda',
        'fecha_recoleccion': 'Fecha Recolección',
        'descripcion': 'Resultado',
        'proveniente': 'Fuente'
    }
    
    existing_renames = {k: v for k, v in rename_map.items() if k in epi_display.columns}
    epi_display = epi_display.rename(columns=existing_renames)
    
    return epi_display


def create_quick_filters_casos(casos_display):
    """Crea filtros rápidos para la tabla de casos."""
    if casos_display.empty:
        return

    # Filtros en una sola fila
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if "Sexo" in casos_display.columns:
            sexo_options = ["Todos"] + sorted(casos_display["Sexo"].dropna().unique().tolist())
            sexo_filter = st.selectbox("🚻 Filtrar por Sexo:", sexo_options, key="sexo_filter_table")
            st.session_state["casos_sexo_filter"] = sexo_filter
    
    with col2:
        if "Condición Final" in casos_display.columns:
            condicion_options = ["Todas"] + sorted(casos_display["Condición Final"].dropna().unique().tolist())
            condicion_filter = st.selectbox("⚰️ Condición:", condicion_options, key="condicion_filter_table")
            st.session_state["casos_condicion_filter"] = condicion_filter
    
    with col3:
        if "Municipio" in casos_display.columns:
            municipio_options = ["Todos"] + sorted(casos_display["Municipio"].dropna().unique().tolist())
            municipio_filter = st.selectbox("📍 Municipio:", municipio_options, key="municipio_filter_table")
            st.session_state["casos_municipio_filter"] = municipio_filter


def create_quick_filters_epizootias(epizootias_display):
    """Crea filtros rápidos para la tabla de epizootias."""
    if epizootias_display.empty:
        return

    col1, col2 = st.columns(2)
    
    with col1:
        if "Resultado" in epizootias_display.columns:
            resultado_options = ["Todos"] + sorted(epizootias_display["Resultado"].dropna().unique().tolist())
            resultado_filter = st.selectbox("🔬 Resultado:", resultado_options, key="resultado_filter_table")
            st.session_state["epi_resultado_filter"] = resultado_filter
    
    with col2:
        if "Fuente" in epizootias_display.columns:
            fuente_options = ["Todas"] + sorted(epizootias_display["Fuente"].dropna().unique().tolist())
            fuente_filter = st.selectbox("📋 Fuente:", fuente_options, key="fuente_filter_table")
            st.session_state["epi_fuente_filter"] = fuente_filter


def apply_table_filters_casos(casos_display):
    """Aplica filtros a la tabla de casos."""
    if casos_display.empty:
        return casos_display

    casos_filtrados = casos_display.copy()
    
    # Aplicar filtro de sexo
    sexo_filter = st.session_state.get("casos_sexo_filter", "Todos")
    if sexo_filter != "Todos" and "Sexo" in casos_filtrados.columns:
        casos_filtrados = casos_filtrados[casos_filtrados["Sexo"] == sexo_filter]
    
    # Aplicar filtro de condición
    condicion_filter = st.session_state.get("casos_condicion_filter", "Todas")
    if condicion_filter != "Todas" and "Condición Final" in casos_filtrados.columns:
        casos_filtrados = casos_filtrados[casos_filtrados["Condición Final"] == condicion_filter]
    
    # Aplicar filtro de municipio
    municipio_filter = st.session_state.get("casos_municipio_filter", "Todos")
    if municipio_filter != "Todos" and "Municipio" in casos_filtrados.columns:
        casos_filtrados = casos_filtrados[casos_filtrados["Municipio"] == municipio_filter]
    
    return casos_filtrados


def apply_table_filters_epizootias(epizootias_display):
    """Aplica filtros a la tabla de epizootias."""
    if epizootias_display.empty:
        return epizootias_display

    epi_filtradas = epizootias_display.copy()
    
    # Aplicar filtro de resultado
    resultado_filter = st.session_state.get("epi_resultado_filter", "Todos")
    if resultado_filter != "Todos" and "Resultado" in epi_filtradas.columns:
        epi_filtradas = epi_filtradas[epi_filtradas["Resultado"] == resultado_filter]
    
    # Aplicar filtro de fuente
    fuente_filter = st.session_state.get("epi_fuente_filter", "Todas")
    if fuente_filter != "Todas" and "Fuente" in epi_filtradas.columns:
        epi_filtradas = epi_filtradas[epi_filtradas["Fuente"] == fuente_filter]
    
    return epi_filtradas

def create_location_summary_FIXED(casos_filtrados, epizootias_filtradas):
    """
    CORREGIDO: Crea resumen de ubicación usando DATOS FILTRADOS garantizados.
    """
    from utils.data_processor import verify_filtered_data_usage
    
    # VERIFICACIÓN adicional
    verify_filtered_data_usage(casos_filtrados, "create_location_summary - casos")
    verify_filtered_data_usage(epizootias_filtradas, "create_location_summary - epizootias")
    
    summary_data = []
    
    # Obtener todas las ubicaciones únicas DE LOS DATOS FILTRADOS
    ubicaciones = set()
    if not casos_filtrados.empty and "municipio" in casos_filtrados.columns:
        ubicaciones.update(casos_filtrados["municipio"].dropna())
    if not epizootias_filtradas.empty and "municipio" in epizootias_filtradas.columns:
        ubicaciones.update(epizootias_filtradas["municipio"].dropna())
    
    for ubicacion in sorted(ubicaciones):
        # Casos en esta ubicación DE LOS DATOS FILTRADOS
        casos_ubi = casos_filtrados[casos_filtrados["municipio"] == ubicacion] if not casos_filtrados.empty and "municipio" in casos_filtrados.columns else pd.DataFrame()
        epi_ubi = epizootias_filtradas[epizootias_filtradas["municipio"] == ubicacion] if not epizootias_filtradas.empty and "municipio" in epizootias_filtradas.columns else pd.DataFrame()
        
        casos_count = len(casos_ubi)
        epi_count = len(epi_ubi)
        
        if casos_count > 0 or epi_count > 0:
            # Cálculos adicionales DE DATOS FILTRADOS
            fallecidos = 0
            if not casos_ubi.empty and "condicion_final" in casos_ubi.columns:
                fallecidos = (casos_ubi["condicion_final"] == "Fallecido").sum()
            
            letalidad = (fallecidos / casos_count * 100) if casos_count > 0 else 0
            
            # Desglose de epizootias DE DATOS FILTRADOS
            positivas = 0
            en_estudio = 0
            if not epi_ubi.empty and "descripcion" in epi_ubi.columns:
                positivas = (epi_ubi["descripcion"] == "POSITIVO FA").sum()
                en_estudio = (epi_ubi["descripcion"] == "EN ESTUDIO").sum()
            
            # Determinar categoría
            if casos_count > 0 and epi_count > 0:
                categoria = "Mixto"
            elif casos_count > 0:
                categoria = "Solo Casos"
            else:
                categoria = "Solo Epizootias"
            
            summary_data.append({
                "municipio": ubicacion,
                "casos": casos_count,
                "fallecidos": fallecidos,
                "letalidad": round(letalidad, 1),
                "epizootias": epi_count,
                "positivas": positivas,
                "en_estudio": en_estudio,
                "categoria": categoria
            })
    
    return summary_data

def create_aesthetic_summary_html_FIXED(summary_data, colors):
    """
    CORREGIDO: Crea DataFrame estético para la tabla resumen usando datos filtrados.
    """
    if not summary_data:
        return None
    
    # Ordenar por casos descendente
    summary_data_sorted = sorted(summary_data, key=lambda x: x["casos"], reverse=True)
    
    # USAR DATAFRAME CON INDICACIÓN DE FILTRADO
    summary_df = pd.DataFrame(summary_data_sorted)
    
    # Renombrar columnas para mejor visualización
    summary_df = summary_df.rename(columns={
        'municipio': '📍 Municipio',
        'casos': '🦠 Casos (Filtrados)', 
        'fallecidos': '⚰️ Fallecidos (Filtrados)',
        'letalidad': '📊 Letalidad % (Filtrados)',
        'epizootias': '🐒 Epizootias (Filtradas)',
        'positivas': '🔴 Positivas (Filtradas)',
        'en_estudio': '🔵 En Estudio (Filtradas)',
        'categoria': '🏷️ Tipo'
    })
    
    return summary_df

def create_casos_distribution_chart(casos, colors):
    """Crea gráfico de distribución de casos simplificado."""
    if casos.empty:
        return
    
    # Gráfico por municipio (top 10)
    if "municipio" in casos.columns:
        municipio_counts = casos["municipio"].value_counts().head(10)
        
        if not municipio_counts.empty:
            fig = px.bar(
                x=municipio_counts.values,
                y=municipio_counts.index,
                orientation="h",
                title="Top 10 Municipios",
                labels={"x": "Casos", "y": "Municipio"},
                color=municipio_counts.values,
                color_continuous_scale="Reds"
            )
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos suficientes para el gráfico")
    else:
        st.info("No hay datos de municipio disponibles")


def create_epizootias_distribution_chart(epizootias, colors):
    """Crea gráfico de distribución de epizootias simplificado."""
    if epizootias.empty:
        return
    
    # Gráfico por resultado
    if "descripcion" in epizootias.columns:
        resultado_counts = epizootias["descripcion"].value_counts()
        
        if not resultado_counts.empty:
            fig = px.pie(
                values=resultado_counts.values,
                names=resultado_counts.index,
                title="Distribución por Resultado",
                color_discrete_map={
                    "POSITIVO FA": colors["danger"],
                    "EN ESTUDIO": colors["info"]
                }
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos suficientes para el gráfico")
    else:
        st.info("No hay datos de resultado disponibles")


def create_comprehensive_excel_export(casos, epizootias):
    """Crea exportación Excel completa."""
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Hoja 1: Casos detallados
        if not casos.empty:
            casos_export = prepare_casos_for_detailed_view(casos)
            casos_export.to_excel(writer, sheet_name='Casos_Detallados', index=False)
        
        # Hoja 2: Epizootias detalladas
        if not epizootias.empty:
            epizootias_export = prepare_epizootias_for_detailed_view(epizootias)
            epizootias_export.to_excel(writer, sheet_name='Epizootias_Detalladas', index=False)
        
        # Hoja 3: Resumen por ubicación
        summary_data = create_location_summary_FIXED(casos, epizootias)
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Resumen_Ubicacion', index=False)
        
        # Hoja 4: Metadatos
        metadata = create_export_metadata(casos, epizootias)
        metadata.to_excel(writer, sheet_name='Metadatos', index=False)
    
    buffer.seek(0)
    return buffer.getvalue()


def create_export_metadata(casos, epizootias):
    """Crea metadatos para la exportación."""
    metadata_rows = []
    
    metadata_rows.append({
        "Campo": "Fecha de Exportación",
        "Valor": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Descripción": "Fecha y hora de generación del archivo"
    })
    
    metadata_rows.append({
        "Campo": "Total Casos",
        "Valor": len(casos),
        "Descripción": "Número total de casos humanos incluidos"
    })
    
    metadata_rows.append({
        "Campo": "Total Epizootias",
        "Valor": len(epizootias),
        "Descripción": "Número total de epizootias incluidas (positivas + en estudio)"
    })
    
    if not epizootias.empty and "descripcion" in epizootias.columns:
        positivas = len(epizootias[epizootias["descripcion"] == "POSITIVO FA"])
        en_estudio = len(epizootias[epizootias["descripcion"] == "EN ESTUDIO"])
        
        metadata_rows.append({
            "Campo": "Epizootias Positivas",
            "Valor": positivas,
            "Descripción": "Epizootias confirmadas positivas para fiebre amarilla"
        })
        
        metadata_rows.append({
            "Campo": "Epizootias En Estudio",
            "Valor": en_estudio,
            "Descripción": "Epizootias con resultado en proceso de análisis"
        })
    
    metadata_rows.append({
        "Campo": "Dashboard Versión",
        "Valor": "3.2",
        "Descripción": "Versión del dashboard de Fiebre Amarilla"
    })
    
    return pd.DataFrame(metadata_rows)