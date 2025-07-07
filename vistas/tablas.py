"""
Vista de análisis epidemiológico CORREGIDA del dashboard de Fiebre Amarilla.
CORRECCIÓN CRÍTICA:
- TODAS las funciones garantizan uso de datos filtrados recibidos
- Verificación explícita en cada función
- Eliminación completa de accesos a datos originales
- Logging detallado para debugging
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
import logging

# Configurar logging
logger = logging.getLogger(__name__)

def show(data_filtered, filters, colors):
    """
    Vista de análisis epidemiológico CORREGIDA - GARANTIZA USO DE DATOS FILTRADOS.
    
    Args:
        data_filtered (dict): DATOS YA FILTRADOS por el sistema principal
        filters (dict): Filtros aplicados (para información)
        colors (dict): Colores institucionales
    """
    logger.info("📊 INICIANDO VISTA TABLAS CON DATOS FILTRADOS")
    
    # **VERIFICACIÓN CRÍTICA INICIAL**
    casos_filtrados = data_filtered["casos"]
    epizootias_filtradas = data_filtered["epizootias"]
    
    # **LOG DE VERIFICACIÓN**
    logger.info(f"📊 Vista tablas recibió: {len(casos_filtrados)} casos filtrados, {len(epizootias_filtradas)} epizootias filtradas")
    
    # **VERIFICAR QUE SON DATAFRAMES VÁLIDOS**
    if not isinstance(casos_filtrados, pd.DataFrame):
        logger.error(f"❌ casos_filtrados no es DataFrame: {type(casos_filtrados)}")
        st.error("Error: datos de casos no válidos")
        return
    
    if not isinstance(epizootias_filtradas, pd.DataFrame):
        logger.error(f"❌ epizootias_filtradas no es DataFrame: {type(epizootias_filtradas)}")
        st.error("Error: datos de epizootias no válidos")
        return
    
    # **MOSTRAR DEBUG INFO SI HAY FILTROS ACTIVOS**
    active_filters = filters.get("active_filters", [])
    if active_filters:
        st.info(f"📊 Análisis de datos filtrados: {' • '.join(active_filters[:2])}")
        logger.info(f"📊 Mostrando análisis con filtros: {active_filters}")
    else:
        st.info("📊 Análisis de datos completos del Tolima")
        logger.info("📊 Mostrando análisis sin filtros (datos completos)")

    # CSS para tablas mejoradas
    apply_enhanced_tables_css(colors)

    # **SECCIÓN 1: Métricas principales con datos filtrados**
    show_filtered_metrics_summary(casos_filtrados, epizootias_filtradas, filters, colors)

    # **SECCIÓN 2: Tablas detalladas tipo Excel con datos filtrados**
    show_detailed_excel_tables_VERIFIED(casos_filtrados, epizootias_filtradas, colors)

    # **SECCIÓN 3: Tabla resumen estética con datos filtrados**
    show_aesthetic_summary_table_GUARANTEED_FILTERED(casos_filtrados, epizootias_filtradas, colors)

    # **SECCIÓN 4: Análisis visual simplificado con datos filtrados**
    show_simplified_visual_analysis_VERIFIED(casos_filtrados, epizootias_filtradas, colors)

    # **SECCIÓN 5: Exportación avanzada con datos filtrados**
    show_comprehensive_export_section_VERIFIED(casos_filtrados, epizootias_filtradas, filters, colors)

def show_filtered_metrics_summary(casos_filtrados, epizootias_filtradas, filters, colors):
    """
    NUEVA: Sección de métricas principales usando datos filtrados verificados.
    """
    logger.info(f"📊 Calculando métricas con datos filtrados: {len(casos_filtrados)} casos, {len(epizootias_filtradas)} epizootias")
    
    # Importar funciones de cálculo que garantizan uso de datos filtrados
    from utils.data_processor import calculate_basic_metrics, verify_filtered_data_usage
    
    # **VERIFICACIÓN EXPLÍCITA**
    verify_filtered_data_usage(casos_filtrados, "show_filtered_metrics_summary - casos")
    verify_filtered_data_usage(epizootias_filtradas, "show_filtered_metrics_summary - epizootias")
    
    # **CALCULAR MÉTRICAS CON DATOS FILTRADOS VERIFICADOS**
    metrics = calculate_basic_metrics(casos_filtrados, epizootias_filtradas)
    
    st.markdown(
        """
        <div class="analysis-section">
            <div class="section-header">
                📊 Resumen Ejecutivo (Datos Filtrados)
            </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Información del contexto de filtrado
    active_filters = filters.get("active_filters", [])
    if active_filters:
        filter_context = f"Filtrado por: {' • '.join(active_filters[:2])}"
        if len(active_filters) > 2:
            filter_context += f" • +{len(active_filters)-2} más"
    else:
        filter_context = "Vista completa del Tolima"
    
    st.markdown(
        f"""
        <div style="background: {colors['light']}; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 4px solid {colors['info']};">
            <strong>📍 Contexto:</strong> {filter_context}<br>
            <strong>📊 Período:</strong> Incluye todos los eventos registrados en el contexto seleccionado
        </div>
        """,
        unsafe_allow_html=True,
    )

    # **MÉTRICAS PRINCIPALES CON DATOS FILTRADOS**
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🦠 Casos Humanos",
            value=metrics["total_casos"],
            help=f"Total de casos confirmados{' en el área filtrada' if active_filters else ' en el Tolima'}"
        )
    
    with col2:
        st.metric(
            label="⚰️ Fallecidos",
            value=metrics["fallecidos"],
            delta=f"{metrics['letalidad']:.1f}% letalidad",
            help="Número de fallecidos y tasa de letalidad"
        )
    
    with col3:
        st.metric(
            label="🐒 Epizootias",
            value=metrics["total_epizootias"],
            help="Total de epizootias (positivas + en estudio)"
        )
    
    with col4:
        st.metric(
            label="🔴 Positivas",
            value=metrics["epizootias_positivas"],
            delta=f"{metrics['positividad']:.1f}% positividad",
            help="Epizootias confirmadas positivas para fiebre amarilla"
        )

    # **INFORMACIÓN DEL ÚLTIMO EVENTO CON DATOS FILTRADOS**
    col1, col2 = st.columns(2)
    
    with col1:
        ultimo_caso = metrics["ultimo_caso"]
        if ultimo_caso["existe"]:
            st.markdown(
                f"""
                <div style="background: #ffe6e6; padding: 15px; border-radius: 10px; border-left: 4px solid {colors['danger']};">
                    <strong>🦠 Último Caso{' (en área filtrada)' if active_filters else ''}:</strong><br>
                    📍 {ultimo_caso["ubicacion"]}<br>
                    📅 {ultimo_caso["fecha"].strftime('%d/%m/%Y') if ultimo_caso["fecha"] else 'Sin fecha'}<br>
                    ⏱️ Hace {ultimo_caso["tiempo_transcurrido"]}
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div style="background: #f0f8ff; padding: 15px; border-radius: 10px; border-left: 4px solid {colors['info']};">
                    <strong>🦠 Último Caso:</strong><br>
                    📭 Sin casos registrados{' en el área filtrada' if active_filters else ''}
                </div>
                """,
                unsafe_allow_html=True,
            )
    
    with col2:
        ultima_epizootia = metrics["ultima_epizootia_positiva"]
        if ultima_epizootia["existe"]:
            st.markdown(
                f"""
                <div style="background: #fff3e0; padding: 15px; border-radius: 10px; border-left: 4px solid {colors['warning']};">
                    <strong>🔴 Última Epizootia Positiva{' (en área filtrada)' if active_filters else ''}:</strong><br>
                    📍 {ultima_epizootia["ubicacion"]}<br>
                    📅 {ultima_epizootia["fecha"].strftime('%d/%m/%Y') if ultima_epizootia["fecha"] else 'Sin fecha'}<br>
                    ⏱️ Hace {ultima_epizootia["tiempo_transcurrido"]}
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div style="background: #f0f8ff; padding: 15px; border-radius: 10px; border-left: 4px solid {colors['info']};">
                    <strong>🔴 Última Epizootia Positiva:</strong><br>
                    📭 Sin epizootias positivas{' en el área filtrada' if active_filters else ''}
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)

def show_detailed_excel_tables_VERIFIED(casos_filtrados, epizootias_filtradas, colors):
    """
    CORREGIDO: Tablas detalladas tipo Excel que GARANTIZAN uso de datos filtrados.
    """
    logger.info(f"📋 Preparando tablas detalladas con datos filtrados: {len(casos_filtrados)} casos, {len(epizootias_filtradas)} epizootias")
    
    # **VERIFICACIÓN EXPLÍCITA**
    from utils.data_processor import verify_filtered_data_usage
    verify_filtered_data_usage(casos_filtrados, "show_detailed_excel_tables - casos")
    verify_filtered_data_usage(epizootias_filtradas, "show_detailed_excel_tables - epizootias")
    
    st.markdown(
        """
        <div class="analysis-section">
            <div class="section-header">
                📊 Tablas Detalladas (Datos Filtrados)
            </div>
        """,
        unsafe_allow_html=True,
    )

    # **PREPARAR DATOS PARA MOSTRAR CON VERIFICACIÓN**
    casos_display = prepare_casos_for_detailed_view_VERIFIED(casos_filtrados)
    epizootias_display = prepare_epizootias_for_detailed_view_VERIFIED(epizootias_filtradas)

    # Crear dos columnas para las tablas
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 🦠 Casos Humanos Detallados (Filtrados)")
        if not casos_display.empty:
            # Filtros rápidos para casos DENTRO de los datos ya filtrados
            create_quick_filters_casos_VERIFIED(casos_display)
            
            # Aplicar filtros adicionales SI están activos
            casos_sub_filtrados = apply_table_filters_casos_VERIFIED(casos_display)
            
            st.markdown(
                f"""
                <div class="data-table-container">
                    <h4>📋 Casos filtrados ({len(casos_sub_filtrados)} de {len(casos_display)} registros)</h4>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            # Mostrar tabla con scroll
            st.dataframe(
                casos_sub_filtrados,
                use_container_width=True,
                height=500,
                hide_index=True
            )
            
            # Información adicional
            st.caption(f"💡 Mostrando {len(casos_sub_filtrados)} casos de los {len(casos_display)} disponibles después del filtrado principal")
            
        else:
            st.info("📭 No hay casos para mostrar con los filtros aplicados")

    with col2:
        st.markdown("### 🐒 Epizootias Detalladas (Filtradas)")
        if not epizootias_display.empty:
            # Filtros rápidos para epizootias DENTRO de los datos ya filtrados
            create_quick_filters_epizootias_VERIFIED(epizootias_display)
            
            # Aplicar filtros adicionales SI están activos
            epizootias_sub_filtradas = apply_table_filters_epizootias_VERIFIED(epizootias_display)
            
            st.markdown(
                f"""
                <div class="data-table-container">
                    <h4>📋 Epizootias filtradas ({len(epizootias_sub_filtradas)} de {len(epizootias_display)} registros)</h4>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            # Mostrar tabla con scroll
            st.dataframe(
                epizootias_sub_filtradas,
                use_container_width=True,
                height=500,
                hide_index=True
            )
            
            # Desglose por tipo
            if "Resultado" in epizootias_sub_filtradas.columns:
                positivas = len(epizootias_sub_filtradas[epizootias_sub_filtradas["Resultado"] == "POSITIVO FA"])
                en_estudio = len(epizootias_sub_filtradas[epizootias_sub_filtradas["Resultado"] == "EN ESTUDIO"])
                st.caption(f"💡 {positivas} positivas • {en_estudio} en estudio • {len(epizootias_sub_filtradas)} total mostradas")
            else:
                st.caption(f"💡 Mostrando {len(epizootias_sub_filtradas)} epizootias de las {len(epizootias_display)} disponibles")
                
        else:
            st.info("📭 No hay epizootias para mostrar con los filtros aplicados")

    st.markdown("</div>", unsafe_allow_html=True)

def show_aesthetic_summary_table_GUARANTEED_FILTERED(casos_filtrados, epizootias_filtradas, colors):
    """
    CORREGIDO: Resumen por ubicación que GARANTIZA uso de datos filtrados.
    """
    logger.info(f"📈 Creando resumen estético con datos filtrados: {len(casos_filtrados)} casos, {len(epizootias_filtradas)} epizootias")
    
    # **VERIFICACIÓN EXPLÍCITA**
    from utils.data_processor import verify_filtered_data_usage
    verify_filtered_data_usage(casos_filtrados, "show_aesthetic_summary_table - casos")
    verify_filtered_data_usage(epizootias_filtradas, "show_aesthetic_summary_table - epizootias")
    
    st.markdown(
        """
        <div class="analysis-section">
            <div class="section-header">
                📈 Resumen por Ubicación (Datos Filtrados Garantizados)
            </div>
        """,
        unsafe_allow_html=True,
    )

    # **CREAR RESUMEN CON DATOS FILTRADOS VERIFICADOS**
    summary_data = create_location_summary_GUARANTEED_FILTERED(casos_filtrados, epizootias_filtradas)
    
    if summary_data:
        # Mostrar como DataFrame estético
        summary_df = create_aesthetic_summary_dataframe(summary_data, colors)
        
        if isinstance(summary_df, pd.DataFrame) and not summary_df.empty:
            st.dataframe(
                summary_df,
                use_container_width=True,
                height=400,
                hide_index=True
            )
            
            # Estadísticas generales del resumen DE DATOS FILTRADOS
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_ubicaciones = len(summary_data)
                st.metric("🏛️ Ubicaciones", total_ubicaciones, help="Ubicaciones con datos en el contexto filtrado")
            
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
            st.info("📊 No hay suficientes datos para crear el resumen por ubicación")
    else:
        st.info("📊 No hay datos suficientes para crear el resumen por ubicación con los filtros aplicados")

    st.markdown("</div>", unsafe_allow_html=True)

def show_simplified_visual_analysis_VERIFIED(casos_filtrados, epizootias_filtradas, colors):
    """
    CORREGIDO: Análisis visual que GARANTIZA uso de datos filtrados.
    """
    logger.info(f"📊 Creando gráficos con datos filtrados: {len(casos_filtrados)} casos, {len(epizootias_filtradas)} epizootias")
    
    # **VERIFICACIÓN EXPLÍCITA**
    from utils.data_processor import verify_filtered_data_usage
    verify_filtered_data_usage(casos_filtrados, "show_simplified_visual_analysis - casos")
    verify_filtered_data_usage(epizootias_filtradas, "show_simplified_visual_analysis - epizootias")
    
    st.markdown(
        """
        <div class="analysis-section">
            <div class="section-header">
                📊 Análisis Visual (Datos Filtrados)
            </div>
        """,
        unsafe_allow_html=True,
    )

    # Solo 2 gráficos principales - uno para casos, uno para epizootias
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🦠 Distribución de Casos (Filtrados)")
        if not casos_filtrados.empty:
            create_casos_distribution_chart_VERIFIED(casos_filtrados, colors)
        else:
            st.info("Sin datos de casos para graficar en el contexto filtrado")

    with col2:
        st.markdown("#### 🐒 Distribución de Epizootias (Filtradas)")
        if not epizootias_filtradas.empty:
            create_epizootias_distribution_chart_VERIFIED(epizootias_filtradas, colors)
        else:
            st.info("Sin datos de epizootias para graficar en el contexto filtrado")

    st.markdown("</div>", unsafe_allow_html=True)

def show_comprehensive_export_section_VERIFIED(casos_filtrados, epizootias_filtradas, filters, colors):
    """
    CORREGIDO: Sección de exportación que GARANTIZA uso de datos filtrados.
    """
    logger.info(f"📥 Preparando exportación con datos filtrados: {len(casos_filtrados)} casos, {len(epizootias_filtradas)} epizootias")
    
    # **VERIFICACIÓN EXPLÍCITA**
    from utils.data_processor import verify_filtered_data_usage
    verify_filtered_data_usage(casos_filtrados, "show_comprehensive_export_section - casos")
    verify_filtered_data_usage(epizootias_filtradas, "show_comprehensive_export_section - epizootias")
    
    st.markdown(
        """
        <div class="analysis-section">
            <div class="section-header">
                📥 Exportación de Datos Filtrados
            </div>
        """,
        unsafe_allow_html=True,
    )

    # Información de contexto de filtrado
    active_filters = filters.get("active_filters", [])
    filter_info = "datos completos del Tolima"
    if active_filters:
        filter_info = f"datos filtrados por: {' • '.join(active_filters[:2])}"
        if len(active_filters) > 2:
            filter_info += f" • +{len(active_filters)-2} más"

    st.markdown(
        f"""
        <div class="info-box">
            <div class="info-box-title">📊 Datos Listos para Exportar ({filter_info})</div>
            <strong>Casos humanos:</strong> {len(casos_filtrados)} registros filtrados<br>
            <strong>Epizootias:</strong> {len(epizootias_filtradas)} registros filtrados ({len(epizootias_filtradas[epizootias_filtradas["descripcion"] == "POSITIVO FA"]) if not epizootias_filtradas.empty and "descripcion" in epizootias_filtradas.columns else 0} positivas + {len(epizootias_filtradas[epizootias_filtradas["descripcion"] == "EN ESTUDIO"]) if not epizootias_filtradas.empty and "descripcion" in epizootias_filtradas.columns else 0} en estudio)<br>
            <strong>Incluye:</strong> Solo los datos que pasan los filtros aplicados + análisis contextual
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Botones de exportación mejorados
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if not casos_filtrados.empty or not epizootias_filtradas.empty:
            excel_data = create_comprehensive_excel_export_VERIFIED(casos_filtrados, epizootias_filtradas, filters)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            filter_suffix = "_filtrado" if active_filters else "_completo"
            
            st.download_button(
                label="📊 Excel Filtrado",
                data=excel_data,
                file_name=f"fiebre_amarilla{filter_suffix}_{timestamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Excel con datos filtrados y análisis contextual",
                use_container_width=True
            )
        else:
            st.button("📊 Excel Filtrado", disabled=True, help="Sin datos filtrados")

    with col2:
        if not casos_filtrados.empty:
            casos_display = prepare_casos_for_detailed_view_VERIFIED(casos_filtrados)
            casos_csv = casos_display.to_csv(index=False)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            
            st.download_button(
                label="🦠 Casos CSV",
                data=casos_csv,
                file_name=f"casos_filtrados_{timestamp}.csv",
                mime="text/csv",
                help="Casos filtrados con todas las columnas",
                use_container_width=True
            )
        else:
            st.button("🦠 Casos CSV", disabled=True, help="Sin casos filtrados")

    with col3:
        if not epizootias_filtradas.empty:
            epizootias_display = prepare_epizootias_for_detailed_view_VERIFIED(epizootias_filtradas)
            epizootias_csv = epizootias_display.to_csv(index=False)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            
            st.download_button(
                label="🐒 Epizootias CSV",
                data=epizootias_csv,
                file_name=f"epizootias_filtradas_{timestamp}.csv",
                mime="text/csv",
                help="Epizootias filtradas con todas las columnas",
                use_container_width=True
            )
        else:
            st.button("🐒 Epizootias CSV", disabled=True, help="Sin epizootias filtradas")

    with col4:
        summary_data = create_location_summary_GUARANTEED_FILTERED(casos_filtrados, epizootias_filtradas)
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            summary_csv = summary_df.to_csv(index=False)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            
            st.download_button(
                label="📈 Resumen CSV",
                data=summary_csv,
                file_name=f"resumen_filtrado_{timestamp}.csv",
                mime="text/csv",
                help="Resumen por ubicación de datos filtrados",
                use_container_width=True
            )
        else:
            st.button("📈 Resumen CSV", disabled=True, help="Sin datos filtrados para resumen")

    st.markdown("</div>", unsafe_allow_html=True)

# === FUNCIONES DE APOYO CORREGIDAS ===

def prepare_casos_for_detailed_view_VERIFIED(casos_filtrados):
    """
    CORREGIDO: Prepara casos para vista detallada GARANTIZANDO datos filtrados.
    """
    logger.info(f"🔧 Preparando {len(casos_filtrados)} casos filtrados para vista detallada")
    
    if casos_filtrados.empty:
        logger.info("📭 Sin casos filtrados para procesar")
        return pd.DataFrame()

    casos_display = casos_filtrados.copy()
    
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
    
    logger.info(f"✅ Casos preparados: {len(casos_display)} registros con columnas {list(casos_display.columns)}")
    return casos_display

def prepare_epizootias_for_detailed_view_VERIFIED(epizootias_filtradas):
    """
    CORREGIDO: Prepara epizootias para vista detallada GARANTIZANDO datos filtrados.
    """
    logger.info(f"🔧 Preparando {len(epizootias_filtradas)} epizootias filtradas para vista detallada")
    
    if epizootias_filtradas.empty:
        logger.info("📭 Sin epizootias filtradas para procesar")
        return pd.DataFrame()

    epi_display = epizootias_filtradas.copy()
    
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
    
    logger.info(f"✅ Epizootias preparadas: {len(epi_display)} registros con columnas {list(epi_display.columns)}")
    return epi_display

def create_location_summary_GUARANTEED_FILTERED(casos_filtrados, epizootias_filtradas):
    """
    CORREGIDO: Crea resumen de ubicación GARANTIZANDO uso de datos filtrados.
    """
    logger.info(f"📈 Creando resumen por ubicación con datos filtrados: {len(casos_filtrados)} casos, {len(epizootias_filtradas)} epizootias")
    
    # **VERIFICACIÓN EXPLÍCITA**
    from utils.data_processor import verify_filtered_data_usage
    verify_filtered_data_usage(casos_filtrados, "create_location_summary - casos")
    verify_filtered_data_usage(epizootias_filtradas, "create_location_summary - epizootias")
    
    summary_data = []
    
    # Obtener todas las ubicaciones únicas DE LOS DATOS FILTRADOS
    ubicaciones = set()
    if not casos_filtrados.empty and "municipio" in casos_filtrados.columns:
        ubicaciones.update(casos_filtrados["municipio"].dropna())
    if not epizootias_filtradas.empty and "municipio" in epizootias_filtradas.columns:
        ubicaciones.update(epizootias_filtradas["municipio"].dropna())
    
    logger.info(f"📍 Ubicaciones encontradas en datos filtrados: {len(ubicaciones)} - {sorted(list(ubicaciones))[:5]}")
    
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
    
    logger.info(f"📊 Resumen creado: {len(summary_data)} ubicaciones con datos")
    return summary_data

def create_aesthetic_summary_dataframe(summary_data, colors):
    """
    Crea DataFrame estético para la tabla resumen.
    """
    if not summary_data:
        return None
    
    # Ordenar por casos descendente
    summary_data_sorted = sorted(summary_data, key=lambda x: x["casos"], reverse=True)
    
    # Crear DataFrame
    summary_df = pd.DataFrame(summary_data_sorted)
    
    # Renombrar columnas para mejor visualización
    summary_df = summary_df.rename(columns={
        'municipio': '📍 Ubicación',
        'casos': '🦠 Casos', 
        'fallecidos': '⚰️ Fallecidos',
        'letalidad': '📊 Letalidad %',
        'epizootias': '🐒 Epizootias',
        'positivas': '🔴 Positivas',
        'en_estudio': '🔵 En Estudio',
        'categoria': '🏷️ Tipo'
    })
    
    return summary_df

# === FUNCIONES DE FILTROS ADICIONALES DENTRO DE TABLAS ===

def create_quick_filters_casos_VERIFIED(casos_display):
    """Crea filtros rápidos para la tabla de casos DENTRO de datos ya filtrados."""
    if casos_display.empty:
        return

    # Filtros en una sola fila
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if "Sexo" in casos_display.columns:
            sexo_options = ["Todos"] + sorted(casos_display["Sexo"].dropna().unique().tolist())
            sexo_filter = st.selectbox("🚻 Filtrar por Sexo:", sexo_options, key="sexo_filter_table_verified")
            st.session_state["casos_sexo_filter_verified"] = sexo_filter
    
    with col2:
        if "Condición Final" in casos_display.columns:
            condicion_options = ["Todas"] + sorted(casos_display["Condición Final"].dropna().unique().tolist())
            condicion_filter = st.selectbox("⚰️ Condición:", condicion_options, key="condicion_filter_table_verified")
            st.session_state["casos_condicion_filter_verified"] = condicion_filter
    
    with col3:
        if "Municipio" in casos_display.columns:
            municipio_options = ["Todos"] + sorted(casos_display["Municipio"].dropna().unique().tolist())
            municipio_filter = st.selectbox("📍 Municipio:", municipio_options, key="municipio_filter_table_verified")
            st.session_state["casos_municipio_filter_verified"] = municipio_filter

def create_quick_filters_epizootias_VERIFIED(epizootias_display):
    """Crea filtros rápidos para la tabla de epizootias DENTRO de datos ya filtrados."""
    if epizootias_display.empty:
        return

    col1, col2 = st.columns(2)
    
    with col1:
        if "Resultado" in epizootias_display.columns:
            resultado_options = ["Todos"] + sorted(epizootias_display["Resultado"].dropna().unique().tolist())
            resultado_filter = st.selectbox("🔬 Resultado:", resultado_options, key="resultado_filter_table_verified")
            st.session_state["epi_resultado_filter_verified"] = resultado_filter
    
    with col2:
        if "Fuente" in epizootias_display.columns:
            fuente_options = ["Todas"] + sorted(epizootias_display["Fuente"].dropna().unique().tolist())
            fuente_filter = st.selectbox("📋 Fuente:", fuente_options, key="fuente_filter_table_verified")
            st.session_state["epi_fuente_filter_verified"] = fuente_filter

def apply_table_filters_casos_VERIFIED(casos_display):
    """Aplica filtros adicionales a la tabla de casos."""
    if casos_display.empty:
        return casos_display

    casos_sub_filtrados = casos_display.copy()
    
    # Aplicar filtro de sexo
    sexo_filter = st.session_state.get("casos_sexo_filter_verified", "Todos")
    if sexo_filter != "Todos" and "Sexo" in casos_sub_filtrados.columns:
        casos_sub_filtrados = casos_sub_filtrados[casos_sub_filtrados["Sexo"] == sexo_filter]
    
    # Aplicar filtro de condición
    condicion_filter = st.session_state.get("casos_condicion_filter_verified", "Todas")
    if condicion_filter != "Todas" and "Condición Final" in casos_sub_filtrados.columns:
        casos_sub_filtrados = casos_sub_filtrados[casos_sub_filtrados["Condición Final"] == condicion_filter]
    
    # Aplicar filtro de municipio
    municipio_filter = st.session_state.get("casos_municipio_filter_verified", "Todos")
    if municipio_filter != "Todos" and "Municipio" in casos_sub_filtrados.columns:
        casos_sub_filtrados = casos_sub_filtrados[casos_sub_filtrados["Municipio"] == municipio_filter]
    
    return casos_sub_filtrados

def apply_table_filters_epizootias_VERIFIED(epizootias_display):
    """Aplica filtros adicionales a la tabla de epizootias."""
    if epizootias_display.empty:
        return epizootias_display

    epi_sub_filtradas = epizootias_display.copy()
    
    # Aplicar filtro de resultado
    resultado_filter = st.session_state.get("epi_resultado_filter_verified", "Todos")
    if resultado_filter != "Todos" and "Resultado" in epi_sub_filtradas.columns:
        epi_sub_filtradas = epi_sub_filtradas[epi_sub_filtradas["Resultado"] == resultado_filter]
    
    # Aplicar filtro de fuente
    fuente_filter = st.session_state.get("epi_fuente_filter_verified", "Todas")
    if fuente_filter != "Todas" and "Fuente" in epi_sub_filtradas.columns:
        epi_sub_filtradas = epi_sub_filtradas[epi_sub_filtradas["Fuente"] == fuente_filter]
    
    return epi_sub_filtradas

# === FUNCIONES DE GRÁFICOS CORREGIDAS ===

def create_casos_distribution_chart_VERIFIED(casos_filtrados, colors):
    """Crea gráfico de distribución de casos GARANTIZANDO datos filtrados."""
    logger.info(f"📊 Creando gráfico de distribución con {len(casos_filtrados)} casos filtrados")
    
    if casos_filtrados.empty:
        st.info("Sin casos filtrados para graficar")
        return
    
    # Gráfico por municipio (top 10 de los datos filtrados)
    if "municipio" in casos_filtrados.columns:
        municipio_counts = casos_filtrados["municipio"].value_counts().head(10)
        
        if not municipio_counts.empty:
            fig = px.bar(
                x=municipio_counts.values,
                y=municipio_counts.index,
                orientation="h",
                title="Top 10 Ubicaciones (Datos Filtrados)",
                labels={"x": "Casos", "y": "Ubicación"},
                color=municipio_counts.values,
                color_continuous_scale="Reds"
            )
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos suficientes para el gráfico")
    else:
        st.info("No hay datos de ubicación disponibles en los datos filtrados")

def create_epizootias_distribution_chart_VERIFIED(epizootias_filtradas, colors):
    """Crea gráfico de distribución de epizootias GARANTIZANDO datos filtrados."""
    logger.info(f"📊 Creando gráfico de epizootias con {len(epizootias_filtradas)} epizootias filtradas")
    
    if epizootias_filtradas.empty:
        st.info("Sin epizootias filtradas para graficar")
        return
    
    # Gráfico por resultado
    if "descripcion" in epizootias_filtradas.columns:
        resultado_counts = epizootias_filtradas["descripcion"].value_counts()
        
        if not resultado_counts.empty:
            fig = px.pie(
                values=resultado_counts.values,
                names=resultado_counts.index,
                title="Distribución por Resultado (Datos Filtrados)",
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
        st.info("No hay datos de resultado disponibles en los datos filtrados")

# === FUNCIONES DE EXPORTACIÓN CORREGIDAS ===

def create_comprehensive_excel_export_VERIFIED(casos_filtrados, epizootias_filtradas, filters):
    """Crea exportación Excel completa CON DATOS FILTRADOS."""
    logger.info(f"📥 Creando exportación Excel con datos filtrados: {len(casos_filtrados)} casos, {len(epizootias_filtradas)} epizootias")
    
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Hoja 1: Casos detallados (filtrados)
        if not casos_filtrados.empty:
            casos_export = prepare_casos_for_detailed_view_VERIFIED(casos_filtrados)
            casos_export.to_excel(writer, sheet_name='Casos_Filtrados', index=False)
        
        # Hoja 2: Epizootias detalladas (filtradas)
        if not epizootias_filtradas.empty:
            epizootias_export = prepare_epizootias_for_detailed_view_VERIFIED(epizootias_filtradas)
            epizootias_export.to_excel(writer, sheet_name='Epizootias_Filtradas', index=False)
        
        # Hoja 3: Resumen por ubicación (de datos filtrados)
        summary_data = create_location_summary_GUARANTEED_FILTERED(casos_filtrados, epizootias_filtradas)
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Resumen_Filtrado', index=False)
        
        # Hoja 4: Metadatos (incluye información de filtrado)
        metadata = create_export_metadata_VERIFIED(casos_filtrados, epizootias_filtradas, filters)
        metadata.to_excel(writer, sheet_name='Metadatos_Filtros', index=False)
    
    buffer.seek(0)
    return buffer.getvalue()

def create_export_metadata_VERIFIED(casos_filtrados, epizootias_filtradas, filters):
    """Crea metadatos para la exportación incluyendo información de filtrado."""
    metadata_rows = []
    
    metadata_rows.append({
        "Campo": "Fecha de Exportación",
        "Valor": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Descripción": "Fecha y hora de generación del archivo"
    })
    
    # Información de filtrado
    active_filters = filters.get("active_filters", [])
    if active_filters:
        metadata_rows.append({
            "Campo": "Filtros Aplicados",
            "Valor": " • ".join(active_filters),
            "Descripción": "Filtros que se aplicaron a los datos"
        })
        
        metadata_rows.append({
            "Campo": "Tipo de Exportación",
            "Valor": "Datos Filtrados",
            "Descripción": "Esta exportación contiene solo los datos que pasaron los filtros"
        })
    else:
        metadata_rows.append({
            "Campo": "Tipo de Exportación",
            "Valor": "Datos Completos",
            "Descripción": "Esta exportación contiene todos los datos del Tolima"
        })
    
    metadata_rows.append({
        "Campo": "Total Casos Incluidos",
        "Valor": len(casos_filtrados),
        "Descripción": "Número total de casos humanos incluidos en esta exportación"
    })
    
    metadata_rows.append({
        "Campo": "Total Epizootias Incluidas",
        "Valor": len(epizootias_filtradas),
        "Descripción": "Número total de epizootias incluidas (positivas + en estudio)"
    })
    
    if not epizootias_filtradas.empty and "descripcion" in epizootias_filtradas.columns:
        positivas = len(epizootias_filtradas[epizootias_filtradas["descripcion"] == "POSITIVO FA"])
        en_estudio = len(epizootias_filtradas[epizootias_filtradas["descripcion"] == "EN ESTUDIO"])
        
        metadata_rows.append({
            "Campo": "Epizootias Positivas Incluidas",
            "Valor": positivas,
            "Descripción": "Epizootias confirmadas positivas para fiebre amarilla en esta exportación"
        })
        
        metadata_rows.append({
            "Campo": "Epizootias En Estudio Incluidas",
            "Valor": en_estudio,
            "Descripción": "Epizootias con resultado en proceso de análisis en esta exportación"
        })
    
    metadata_rows.append({
        "Campo": "Dashboard Versión",
        "Valor": "3.4-FILTROS-CORREGIDOS",
        "Descripción": "Versión del dashboard de Fiebre Amarilla con filtros corregidos"
    })
    
    return pd.DataFrame(metadata_rows)

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
        </style>
        """,
        unsafe_allow_html=True,
    )