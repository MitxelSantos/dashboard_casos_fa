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

logger = logging.getLogger(__name__)

def show(data_filtered, filters, colors):
    """Vista principal de análisis epidemiológico."""
    logger.info("📊 INICIANDO VISTA TABLAS")
    
    # Aplicar CSS
    apply_tables_css_super_aesthetic(colors)
    
    # Verificar datos filtrados
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
    show_location_summary_with_drilldown(casos_filtrados, epizootias_filtradas, filters, colors, data_filtered)  # NUEVA FUNCIÓN
    show_visual_analysis_optimized(casos_filtrados, epizootias_filtradas, colors)
    show_export_section_optimized(casos_filtrados, epizootias_filtradas, filters, colors)

# ===== DRILL-DOWN POR UBICACIÓN =====

def show_location_summary_with_drilldown(casos, epizootias, filters, colors, data_original):
    """Resumen por ubicación con drill-down inteligente."""
    st.markdown(
        """
        <div class="analysis-section">
            <div class="section-header">📈 Resumen por Ubicación</div>
        """,
        unsafe_allow_html=True,
    )

    # Determinar nivel de drill-down según filtros
    current_level = determine_drilldown_level(filters)
    
    if current_level == "departamento":
        show_municipal_summary_table(casos, epizootias, filters, colors, data_original)
    elif current_level == "municipio":
        show_vereda_summary_table(casos, epizootias, filters, colors, data_original)
    elif current_level == "vereda":
        show_vereda_detail_analysis(casos, epizootias, filters, colors)
    elif current_level == "multiple":
        show_multiple_selection_summary(casos, epizootias, filters, colors)
    
    st.markdown("</div>", unsafe_allow_html=True)

def determine_drilldown_level(filters):
    """Determina el nivel de drill-down según los filtros activos."""
    if filters.get("modo") == "multiple":
        return "multiple"
    elif filters.get("vereda_display") and filters.get("vereda_display") != "Todas":
        return "vereda"
    elif filters.get("municipio_display") and filters.get("municipio_display") != "Todos":
        return "municipio"
    else:
        return "departamento"

def show_municipal_summary_table(casos, epizootias, filters, colors, data_original):
    """Tabla resumen municipal (vista departamental)."""
    st.markdown("#### 🏛️ Resumen por Municipio - Tolima")
    
    # Crear resumen municipal
    summary_data = create_municipal_summary_optimized(casos, epizootias, data_original)
    
    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        
        # Ordenar por total de casos + epizootias
        summary_df['actividad_total'] = summary_df['casos'] + summary_df['epizootias']
        summary_df = summary_df.sort_values('actividad_total', ascending=False)
        
        # Preparar para mostrar
        display_df = summary_df.rename(columns={
            'municipio': '📍 Municipio',
            'casos': '🦠 Casos', 
            'fallecidos': '⚰️ Fallecidos',
            'letalidad': '📊 Letalidad %',
            'epizootias': '🐒 Epizootias',
            'epizootias_positivas': '🔴 Positivas',
            'epizootias_en_estudio': '🔵 En Estudio',
            'veredas_afectadas': '🏘️ Veredas',
            'actividad_total': '📈 Total'
        })
        
        # Mostrar tabla con formato
        st.dataframe(
            display_df[[
                '📍 Municipio', '🦠 Casos', '⚰️ Fallecidos', '📊 Letalidad %',
                '🐒 Epizootias', '🔴 Positivas', '🔵 En Estudio', '🏘️ Veredas', '📈 Total'
            ]],
            use_container_width=True,
            height=400,
            hide_index=True
        )
        
        # Estadísticas de la tabla
        show_municipal_table_stats(summary_df, colors)
        
        # Botón de exportación
        create_summary_export_button(display_df, "municipios", filters)
        
    else:
        st.info("📊 No hay datos suficientes para el resumen municipal")

def show_vereda_summary_table(casos, epizootias, filters, colors, data_original):
    """Tabla resumen de veredas (vista municipal)."""
    municipio_actual = filters.get("municipio_display", "")
    
    st.markdown(f"#### 🏘️ Resumen por Vereda - {municipio_actual}")
    
    # Crear resumen de veredas para el municipio específico
    summary_data = create_vereda_summary_optimized(casos, epizootias, municipio_actual, data_original)
    
    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        
        # Ordenar por actividad total
        summary_df['actividad_total'] = summary_df['casos'] + summary_df['epizootias']
        summary_df = summary_df.sort_values('actividad_total', ascending=False)
        
        # Preparar para mostrar
        display_df = summary_df.rename(columns={
            'vereda': '🏘️ Vereda',
            'casos': '🦠 Casos',
            'fallecidos': '⚰️ Fallecidos', 
            'letalidad': '📊 Letalidad %',
            'epizootias': '🐒 Epizootias',
            'epizootias_positivas': '🔴 Positivas',
            'epizootias_en_estudio': '🔵 En Estudio',
            'actividad_total': '📈 Total',
            'ultima_actividad': '📅 Última Actividad'
        })
        
        # Mostrar tabla
        st.dataframe(
            display_df[[
                '🏘️ Vereda', '🦠 Casos', '⚰️ Fallecidos', '📊 Letalidad %',
                '🐒 Epizootias', '🔴 Positivas', '🔵 En Estudio', '📈 Total', '📅 Última Actividad'
            ]],
            use_container_width=True,
            height=400,
            hide_index=True
        )
        
        # Estadísticas de veredas
        show_vereda_table_stats(summary_df, municipio_actual, colors)
        
        # Botón de exportación
        create_summary_export_button(display_df, f"veredas_{municipio_actual}", filters)
        
        # Navegación: Botón para volver a vista departamental
        if st.button("🏛️ Volver a Vista Departamental", key="back_to_dept_view"):
            st.session_state['municipio_filter'] = 'Todos'
            st.session_state['vereda_filter'] = 'Todas'
            st.rerun()
        
    else:
        st.info(f"📊 No hay veredas con datos para {municipio_actual}")
        
        # Mostrar lista de veredas disponibles para el municipio
        show_available_veredas_for_municipio(municipio_actual, data_original, colors)

def show_vereda_detail_analysis(casos, epizootias, filters, colors):
    """Análisis detallado de vereda específica (detalle temporal)."""
    vereda_actual = filters.get("vereda_display", "")
    municipio_actual = filters.get("municipio_display", "")
    
    st.markdown(f"#### 📍 Análisis Detallado - {vereda_actual}, {municipio_actual}")
    
    # Análisis temporal de la vereda específica
    create_vereda_temporal_analysis(casos, epizootias, vereda_actual, municipio_actual, colors)
    
    # Métricas específicas de la vereda
    create_vereda_specific_metrics(casos, epizootias, vereda_actual, municipio_actual, colors)
    
    # Navegación: Botones para volver
    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"🏘️ Volver a {municipio_actual}", key="back_to_mun_view"):
            st.session_state['vereda_filter'] = 'Todas'
            st.rerun()
    with col2:
        if st.button("🏛️ Volver a Vista Departamental", key="back_to_dept_from_vereda"):
            st.session_state['municipio_filter'] = 'Todos'
            st.session_state['vereda_filter'] = 'Todas'
            st.rerun()

def show_multiple_selection_summary(casos, epizootias, filters, colors):
    """Resumen para selección múltiple."""
    municipios_seleccionados = filters.get("municipios_seleccionados", [])
    veredas_seleccionadas = filters.get("veredas_seleccionadas", [])
    
    if municipios_seleccionados and not veredas_seleccionadas:
        # Vista de múltiples municipios
        st.markdown(f"#### 🗂️ Resumen Múltiple - {len(municipios_seleccionados)} Municipios")
        
        summary_data = []
        for municipio in municipios_seleccionados:
            municipio_summary = create_single_municipio_summary(casos, epizootias, municipio)
            if municipio_summary:
                summary_data.append(municipio_summary)
        
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            summary_df['actividad_total'] = summary_df['casos'] + summary_df['epizootias']
            summary_df = summary_df.sort_values('actividad_total', ascending=False)
            
            display_df = summary_df.rename(columns={
                'municipio': '📍 Municipio',
                'casos': '🦠 Casos',
                'epizootias': '🐒 Epizootias',
                'actividad_total': '📈 Total'
            })
            
            st.dataframe(display_df, use_container_width=True, height=300, hide_index=True)
            
            # Totales agregados
            show_multiple_selection_totals(summary_df, colors)
    
    elif veredas_seleccionadas:
        # Vista de múltiples veredas
        st.markdown(f"#### 🗂️ Resumen Múltiple - {len(veredas_seleccionadas)} Veredas")
        
        summary_data = []
        for vereda in veredas_seleccionadas:
            # Encontrar municipio de la vereda
            municipio_vereda = find_municipio_for_vereda(vereda, municipios_seleccionados, casos, epizootias)
            vereda_summary = create_single_vereda_summary(casos, epizootias, vereda, municipio_vereda)
            if vereda_summary:
                summary_data.append(vereda_summary)
        
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            summary_df['actividad_total'] = summary_df['casos'] + summary_df['epizootias']
            summary_df = summary_df.sort_values('actividad_total', ascending=False)
            
            display_df = summary_df.rename(columns={
                'vereda': '🏘️ Vereda',
                'municipio': '📍 Municipio',
                'casos': '🦠 Casos',
                'epizootias': '🐒 Epizootias',
                'actividad_total': '📈 Total'
            })
            
            st.dataframe(display_df, use_container_width=True, height=300, hide_index=True)
            
            # Totales agregados
            show_multiple_selection_totals(summary_df, colors)

# ===== FUNCIONES DE CREACIÓN DE RESÚMENES =====

def create_municipal_summary_optimized(casos, epizootias, data_original):
    """Crea resumen municipal."""
    summary_data = []
    
    # Lista completa de municipios del Tolima (desde configuración)
    municipios_tolima = get_all_tolima_municipios(data_original)
    
    def normalize_name(name):
        return str(name).upper().strip() if pd.notna(name) else ""
    
    for municipio in municipios_tolima:
        municipio_norm = normalize_name(municipio)
        
        # Casos en este municipio
        casos_municipio = pd.DataFrame()
        if not casos.empty and "municipio" in casos.columns:
            casos_municipio = casos[casos["municipio"].apply(normalize_name) == municipio_norm]
        
        # Epizootias en este municipio
        epi_municipio = pd.DataFrame()
        if not epizootias.empty and "municipio" in epizootias.columns:
            epi_municipio = epizootias[epizootias["municipio"].apply(normalize_name) == municipio_norm]
        
        # Cálculos
        total_casos = len(casos_municipio)
        total_epizootias = len(epi_municipio)
        
        fallecidos = 0
        if not casos_municipio.empty and "condicion_final" in casos_municipio.columns:
            fallecidos = (casos_municipio["condicion_final"] == "Fallecido").sum()
            vivos = (casos_municipio["condicion_final"] == "Vivo").sum()
        
        letalidad = (fallecidos / total_casos * 100) if total_casos > 0 else 0
        
        positivas = 0
        en_estudio = 0
        if not epi_municipio.empty and "descripcion" in epi_municipio.columns:
            positivas = (epi_municipio["descripcion"] == "POSITIVO FA").sum()
            en_estudio = (epi_municipio["descripcion"] == "EN ESTUDIO").sum()
        
        # Contar veredas afectadas
        veredas_afectadas = set()
        if not casos_municipio.empty and "vereda" in casos_municipio.columns:
            veredas_afectadas.update(casos_municipio["vereda"].dropna())
        if not epi_municipio.empty and "vereda" in epi_municipio.columns:
            veredas_afectadas.update(epi_municipio["vereda"].dropna())
        
        # Agregar solo si hay actividad O si queremos mostrar todos los municipios
        actividad_total = total_casos + total_epizootias
        if actividad_total > 0 or True:  # Cambiar a True para mostrar todos
            summary_data.append({
                "municipio": municipio,
                "casos": total_casos,
                "fallecidos": fallecidos,
                "letalidad": round(letalidad, 1),
                "epizootias": total_epizootias,
                "epizootias_positivas": positivas,
                "epizootias_en_estudio": en_estudio,
                "veredas_afectadas": len(veredas_afectadas),
                "tiene_datos": actividad_total > 0
            })
    
    return summary_data

def create_vereda_summary_optimized(casos, epizootias, municipio_actual, data_original):
    """Crea resumen de veredas para un municipio específico."""
    summary_data = []
    
    def normalize_name(name):
        return str(name).upper().strip() if pd.notna(name) else ""
    
    municipio_norm = normalize_name(municipio_actual)
    
    # Obtener las veredas del municipio
    todas_las_veredas = get_all_veredas_for_municipio(municipio_actual, data_original)
    
    for vereda in todas_las_veredas:
        vereda_norm = normalize_name(vereda)
        
        # Casos en esta vereda del municipio específico
        casos_vereda = pd.DataFrame()
        if not casos.empty and "vereda" in casos.columns and "municipio" in casos.columns:
            casos_vereda = casos[
                (casos["vereda"].apply(normalize_name) == vereda_norm) &
                (casos["municipio"].apply(normalize_name) == municipio_norm)
            ]
        
        # Epizootias en esta vereda del municipio específico
        epi_vereda = pd.DataFrame()
        if not epizootias.empty and "vereda" in epizootias.columns and "municipio" in epizootias.columns:
            epi_vereda = epizootias[
                (epizootias["vereda"].apply(normalize_name) == vereda_norm) &
                (epizootias["municipio"].apply(normalize_name) == municipio_norm)
            ]
        
        # Cálculos
        total_casos = len(casos_vereda)
        total_epizootias = len(epi_vereda)
        
        fallecidos = 0
        if not casos_vereda.empty and "condicion_final" in casos_vereda.columns:
            fallecidos = (casos_vereda["condicion_final"] == "Fallecido").sum()
        
        letalidad = (fallecidos / total_casos * 100) if total_casos > 0 else 0
        
        positivas = 0
        en_estudio = 0
        if not epi_vereda.empty and "descripcion" in epi_vereda.columns:
            positivas = (epi_vereda["descripcion"] == "POSITIVO FA").sum()
            en_estudio = (epi_vereda["descripcion"] == "EN ESTUDIO").sum()
        
        # Última actividad
        ultima_actividad = get_ultima_actividad_vereda(casos_vereda, epi_vereda)
        
        # Agregar vereda (mostrar todas, incluso sin datos)
        summary_data.append({
            "vereda": vereda,
            "casos": total_casos,
            "fallecidos": fallecidos,
            "letalidad": round(letalidad, 1),
            "epizootias": total_epizootias,
            "epizootias_positivas": positivas,
            "epizootias_en_estudio": en_estudio,
            "ultima_actividad": ultima_actividad,
            "tiene_datos": (total_casos + total_epizootias) > 0
        })
    
    return summary_data

def create_single_municipio_summary(casos, epizootias, municipio):
    """Crea resumen para un municipio específico."""
    def normalize_name(name):
        return str(name).upper().strip() if pd.notna(name) else ""
    
    municipio_norm = normalize_name(municipio)
    
    # Filtrar por municipio
    casos_mun = casos[casos["municipio"].apply(normalize_name) == municipio_norm] if not casos.empty and "municipio" in casos.columns else pd.DataFrame()
    epi_mun = epizootias[epizootias["municipio"].apply(normalize_name) == municipio_norm] if not epizootias.empty and "municipio" in epizootias.columns else pd.DataFrame()
    
    return {
        "municipio": municipio,
        "casos": len(casos_mun),
        "epizootias": len(epi_mun)
    }

def create_single_vereda_summary(casos, epizootias, vereda, municipio):
    """Crea resumen para una vereda específica."""
    def normalize_name(name):
        return str(name).upper().strip() if pd.notna(name) else ""
    
    vereda_norm = normalize_name(vereda)
    municipio_norm = normalize_name(municipio) if municipio else ""
    
    # Filtrar por vereda y municipio
    casos_ver = pd.DataFrame()
    epi_ver = pd.DataFrame()
    
    if not casos.empty and "vereda" in casos.columns:
        if municipio:
            casos_ver = casos[
                (casos["vereda"].apply(normalize_name) == vereda_norm) &
                (casos["municipio"].apply(normalize_name) == municipio_norm)
            ]
        else:
            casos_ver = casos[casos["vereda"].apply(normalize_name) == vereda_norm]
    
    if not epizootias.empty and "vereda" in epizootias.columns:
        if municipio:
            epi_ver = epizootias[
                (epizootias["vereda"].apply(normalize_name) == vereda_norm) &
                (epizootias["municipio"].apply(normalize_name) == municipio_norm)
            ]
        else:
            epi_ver = epizootias[epizootias["vereda"].apply(normalize_name) == vereda_norm]
    
    return {
        "vereda": vereda,
        "municipio": municipio or "N/A",
        "casos": len(casos_ver),
        "epizootias": len(epi_ver)
    }

# ===== FUNCIONES DE APOYO =====

def get_all_tolima_municipios(data_original):
    """Obtiene la lista completa de municipios del Tolima."""
    # Intentar obtener desde los datos originales
    municipios_from_data = set()
    
    if "municipios_normalizados" in data_original:
        municipios_from_data.update(data_original["municipios_normalizados"])
    
    # Lista fija de municipios del Tolima (backup)
    municipios_tolima_completos = [
        "IBAGUE", "ALPUJARRA", "ALVARADO", "AMBALEMA", "ANZOATEGUI",
        "ARMERO", "ATACO", "CAJAMARCA", "CARMEN DE APICALA", "CASABIANCA",
        "CHAPARRAL", "COELLO", "COYAIMA", "CUNDAY", "DOLORES",
        "ESPINAL", "FALAN", "FLANDES", "FRESNO", "GUAMO",
        "HERVEO", "HONDA", "ICONONZO", "LERIDA", "LIBANO",
        "MARIQUITA", "MELGAR", "MURILLO", "NATAGAIMA", "ORTEGA",
        "PALOCABILDO", "PIEDRAS", "PLANADAS", "PRADO", "PURIFICACION",
        "RIOBLANCO", "RONCESVALLES", "ROVIRA", "SALDAÑA", "SAN ANTONIO",
        "SAN LUIS", "SANTA ISABEL", "SUAREZ", "VALLE DE SAN JUAN",
        "VENADILLO", "VILLAHERMOSA", "VILLARRICA"
    ]
    
    # Combinar y retornar lista completa
    todos_municipios = sorted(set(list(municipios_from_data) + municipios_tolima_completos))
    
    logger.info(f"📍 Lista completa: {len(todos_municipios)} municipios del Tolima")
    return todos_municipios

def get_all_veredas_for_municipio(municipio, data_original):
    """Obtiene las veredas de un municipio (incluso sin datos)."""
    def normalize_name(name):
        return str(name).upper().strip() if pd.notna(name) else ""
    
    municipio_norm = normalize_name(municipio)
    veredas = set()
    
    # Buscar en casos
    if "casos" in data_original and not data_original["casos"].empty:
        if "vereda" in data_original["casos"].columns and "municipio" in data_original["casos"].columns:
            casos_municipio = data_original["casos"][
                data_original["casos"]["municipio"].apply(normalize_name) == municipio_norm
            ]
            veredas.update(casos_municipio["vereda"].dropna().unique())
    
    # Buscar en epizootias
    if "epizootias" in data_original and not data_original["epizootias"].empty:
        if "vereda" in data_original["epizootias"].columns and "municipio" in data_original["epizootias"].columns:
            epi_municipio = data_original["epizootias"][
                data_original["epizootias"]["municipio"].apply(normalize_name) == municipio_norm
            ]
            veredas.update(epi_municipio["vereda"].dropna().unique())
    
    veredas_lista = sorted([v for v in veredas if v and str(v).strip()])
    
    # Si no hay veredas, agregar placeholder
    if not veredas_lista:
        veredas_lista = [f"{municipio} - CENTRO"]  # Placeholder
    
    logger.info(f"🏘️ {municipio}: {len(veredas_lista)} veredas encontradas")
    return veredas_lista

def get_ultima_actividad_vereda(casos_vereda, epi_vereda):
    """Obtiene la fecha de última actividad en una vereda."""
    fechas = []
    
    if not casos_vereda.empty and "fecha_inicio_sintomas" in casos_vereda.columns:
        fechas.extend(casos_vereda["fecha_inicio_sintomas"].dropna().tolist())
    
    if not epi_vereda.empty and "fecha_notificacion" in epi_vereda.columns:
        fechas.extend(epi_vereda["fecha_notificacion"].dropna().tolist())
    
    if fechas:
        ultima_fecha = max(fechas)
        return ultima_fecha.strftime("%Y-%m-%d")
    else:
        return "Sin actividad"

def find_municipio_for_vereda(vereda, municipios_seleccionados, casos, epizootias):
    """Encuentra el municipio al que pertenece una vereda."""
    def normalize_name(name):
        return str(name).upper().strip() if pd.notna(name) else ""
    
    vereda_norm = normalize_name(vereda)
    
    # Buscar en casos
    if not casos.empty and "vereda" in casos.columns and "municipio" in casos.columns:
        municipio_encontrado = casos[casos["vereda"].apply(normalize_name) == vereda_norm]
        if not municipio_encontrado.empty:
            return municipio_encontrado["municipio"].iloc[0]
    
    # Buscar en epizootias
    if not epizootias.empty and "vereda" in epizootias.columns and "municipio" in epizootias.columns:
        municipio_encontrado = epizootias[epizootias["vereda"].apply(normalize_name) == vereda_norm]
        if not municipio_encontrado.empty:
            return municipio_encontrado["municipio"].iloc[0]
    
    # Si no se encuentra, usar el primer municipio seleccionado como fallback
    return municipios_seleccionados[0] if municipios_seleccionados else "DESCONOCIDO"

# ===== ANÁLISIS TEMPORAL DE VEREDA =====

def create_vereda_temporal_analysis(casos, epizootias, vereda, municipio, colors):
    """Crea análisis temporal para una vereda específica."""
    def normalize_name(name):
        return str(name).upper().strip() if pd.notna(name) else ""
    
    vereda_norm = normalize_name(vereda)
    municipio_norm = normalize_name(municipio)
    
    # Filtrar datos de la vereda
    casos_vereda = pd.DataFrame()
    epi_vereda = pd.DataFrame()
    
    if not casos.empty and "vereda" in casos.columns and "municipio" in casos.columns:
        casos_vereda = casos[
            (casos["vereda"].apply(normalize_name) == vereda_norm) &
            (casos["municipio"].apply(normalize_name) == municipio_norm)
        ]
    
    if not epizootias.empty and "vereda" in epizootias.columns and "municipio" in epizootias.columns:
        epi_vereda = epizootias[
            (epizootias["vereda"].apply(normalize_name) == vereda_norm) &
            (epizootias["municipio"].apply(normalize_name) == municipio_norm)
        ]
    
    if casos_vereda.empty and epi_vereda.empty:
        st.info(f"📊 No hay datos temporales para {vereda}")
        return
    
    # Crear línea de tiempo
    st.markdown("##### 📅 Línea de Tiempo")
    
    eventos_timeline = []
    
    # Agregar casos
    if not casos_vereda.empty and "fecha_inicio_sintomas" in casos_vereda.columns:
        for idx, caso in casos_vereda.iterrows():
            if pd.notna(caso["fecha_inicio_sintomas"]):
                eventos_timeline.append({
                    "fecha": caso["fecha_inicio_sintomas"],
                    "tipo": "Caso",
                    "descripcion": f"Caso - {caso.get('sexo', 'N/A')}, {caso.get('edad', 'N/A')} años",
                    "estado": caso.get("condicion_final", "N/A")
                })
    
    # Agregar epizootias
    if not epi_vereda.empty and "fecha_notificacion" in epi_vereda.columns:
        for idx, epi in epi_vereda.iterrows():
            if pd.notna(epi["fecha_notificacion"]):
                eventos_timeline.append({
                    "fecha": epi["fecha_notificacion"],
                    "tipo": "Epizootia",
                    "descripcion": f"Epizootia - {epi.get('descripcion', 'N/A')}",
                    "estado": epi.get("descripcion", "N/A")
                })
    
    if eventos_timeline:
        # Ordenar por fecha
        eventos_timeline.sort(key=lambda x: x["fecha"])
        
        # Mostrar timeline
        for evento in eventos_timeline:
            fecha_str = evento["fecha"].strftime("%Y-%m-%d")
            
            # Color según tipo y estado
            if evento["tipo"] == "Caso":
                color = colors["danger"] if evento["estado"] == "Fallecido" else colors["warning"]
                icon = "⚰️" if evento["estado"] == "Fallecido" else "🦠"
            else:
                color = colors["danger"] if "POSITIVO" in evento["estado"] else colors["info"]
                icon = "🔴" if "POSITIVO" in evento["estado"] else "🔵"
            
            st.markdown(
                f"""
                <div style="
                    border-left: 4px solid {color};
                    padding: 10px;
                    margin: 8px 0;
                    background: #f8f9fa;
                    border-radius: 0 8px 8px 0;
                ">
                    <strong>{icon} {fecha_str}</strong><br>
                    {evento['descripcion']}
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.info("📅 No hay eventos con fechas válidas")

def create_vereda_specific_metrics(casos, epizootias, vereda, municipio, colors):
    """Crea métricas específicas para la vereda."""
    def normalize_name(name):
        return str(name).upper().strip() if pd.notna(name) else ""
    
    vereda_norm = normalize_name(vereda)
    municipio_norm = normalize_name(municipio)
    
    # Filtrar datos
    casos_vereda = pd.DataFrame()
    epi_vereda = pd.DataFrame()
    
    if not casos.empty and "vereda" in casos.columns and "municipio" in casos.columns:
        casos_vereda = casos[
            (casos["vereda"].apply(normalize_name) == vereda_norm) &
            (casos["municipio"].apply(normalize_name) == municipio_norm)
        ]
    
    if not epizootias.empty and "vereda" in epizootias.columns and "municipio" in epizootias.columns:
        epi_vereda = epizootias[
            (epizootias["vereda"].apply(normalize_name) == vereda_norm) &
            (epizootias["municipio"].apply(normalize_name) == municipio_norm)
        ]
    
    # Métricas en columnas
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("🦠 Casos Total", len(casos_vereda))
    
    with col2:
        fallecidos = len(casos_vereda[casos_vereda["condicion_final"] == "Fallecido"]) if not casos_vereda.empty and "condicion_final" in casos_vereda.columns else 0
        st.metric("⚰️ Fallecidos", fallecidos)
    
    with col3:
        st.metric("🐒 Epizootias Total", len(epi_vereda))
    
    with col4:
        positivas = len(epi_vereda[epi_vereda["descripcion"] == "POSITIVO FA"]) if not epi_vereda.empty and "descripcion" in epi_vereda.columns else 0
        st.metric("🔴 Positivas", positivas)
    with col5:
        en_estudio = len(epi_vereda[epi_vereda["descripcion"] == "EN ESTUDIO"]) if not epi_vereda.empty and "descripcion" in epi_vereda.columns else 0
        st.metric("🔵 En Estudio", en_estudio)
    
    # Información adicional
    if not casos_vereda.empty or not epi_vereda.empty:
        st.markdown("##### 📋 Detalles Adicionales")
        
        info_text = []
        
        if not casos_vereda.empty:
            if "sexo" in casos_vereda.columns:
                sexo_dist = casos_vereda["sexo"].value_counts()
                info_text.append(f"**Distribución por sexo:** {dict(sexo_dist)}")
            
            if "edad" in casos_vereda.columns and not casos_vereda["edad"].isna().all():
                edad_promedio = casos_vereda["edad"].mean()
                edad_min = casos_vereda["edad"].min()
                edad_max = casos_vereda["edad"].max()
                info_text.append(f"**Edad:** promedio {edad_promedio:.1f} años (rango {edad_min}-{edad_max})")
        
        if not epi_vereda.empty and "descripcion" in epi_vereda.columns:
            desc_dist = epi_vereda["descripcion"].value_counts()
            info_text.append(f"**Resultados epizootias:** {dict(desc_dist)}")
        
        for info in info_text:
            st.markdown(f"• {info}")

# ===== ESTADÍSTICAS DE TABLAS =====

def show_municipal_table_stats(summary_df, colors):
    """Muestra estadísticas de la tabla municipal."""
    total_municipios = len(summary_df)
    municipios_con_casos = len(summary_df[summary_df['casos'] > 0])
    municipios_con_epizootias = len(summary_df[summary_df['epizootias'] > 0])
    municipios_con_ambos = len(summary_df[(summary_df['casos'] > 0) & (summary_df['epizootias'] > 0)])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🏛️ Total Municipios", total_municipios)
    with col2:
        st.metric("🦠 Con Casos", municipios_con_casos, delta=f"{municipios_con_casos/total_municipios*100:.1f}%")
    with col3:
        st.metric("🐒 Con Epizootias", municipios_con_epizootias, delta=f"{municipios_con_epizootias/total_municipios*100:.1f}%")
    with col4:
        st.metric("🔄 Con Ambos", municipios_con_ambos, delta=f"{municipios_con_ambos/total_municipios*100:.1f}%")

def show_vereda_table_stats(summary_df, municipio, colors):
    """Muestra estadísticas de la tabla de veredas."""
    total_veredas = len(summary_df)
    veredas_con_casos = len(summary_df[summary_df['casos'] > 0])
    veredas_con_epizootias = len(summary_df[summary_df['epizootias'] > 0])
    veredas_con_ambos = len(summary_df[(summary_df['casos'] > 0) & (summary_df['epizootias'] > 0)])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(f"🏘️ Veredas {municipio}", total_veredas)
    with col2:
        st.metric("🦠 Con Casos", veredas_con_casos, delta=f"{veredas_con_casos/total_veredas*100:.1f}%")
    with col3:
        st.metric("🐒 Con Epizootias", veredas_con_epizootias, delta=f"{veredas_con_epizootias/total_veredas*100:.1f}%")
    with col4:
        st.metric("🔄 Con Ambos", veredas_con_ambos, delta=f"{veredas_con_ambos/total_veredas*100:.1f}%")

def show_multiple_selection_totals(summary_df, colors):
    """Muestra totales para selección múltiple."""
    total_casos = summary_df['casos'].sum()
    total_epizootias = summary_df['epizootias'].sum()
    promedio_casos = summary_df['casos'].mean()
    promedio_epizootias = summary_df['epizootias'].mean()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🦠 Total Casos", total_casos)
    with col2:
        st.metric("🐒 Total Epizootias", total_epizootias)
    with col3:
        st.metric("📊 Promedio Casos", f"{promedio_casos:.1f}")
    with col4:
        st.metric("📊 Promedio Epizootias", f"{promedio_epizootias:.1f}")

def show_available_veredas_for_municipio(municipio, data_original, colors):
    """Muestra veredas disponibles cuando no hay datos."""
    veredas_disponibles = get_all_veredas_for_municipio(municipio, data_original)
    
    if veredas_disponibles:
        st.markdown(f"##### 🏘️ Veredas Disponibles en {municipio}")
        
        # Mostrar en formato de lista compacta
        veredas_texto = " • ".join(veredas_disponibles[:10])  # Mostrar solo las primeras 10
        if len(veredas_disponibles) > 10:
            veredas_texto += f" • ... y {len(veredas_disponibles) - 10} más"
        
        st.markdown(
            f"""
            <div style="
                background: {colors['light']};
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid {colors['info']};
                font-size: 0.9rem;
            ">
                <strong>📋 {len(veredas_disponibles)} veredas identificadas:</strong><br>
                {veredas_texto}
            </div>
            """,
            unsafe_allow_html=True
        )

# ===== BOTONES DE EXPORTACIÓN =====

def create_summary_export_button(display_df, context, filters):
    """Crea botón de exportación para resúmenes."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    filter_suffix = "_filtrado" if filters.get("active_filters") else "_completo"
    
    csv_data = display_df.to_csv(index=False)
    
    st.download_button(
        label=f"📥 Exportar Resumen {context.title()}",
        data=csv_data,
        file_name=f"resumen_{context}{filter_suffix}_{timestamp}.csv",
        mime="text/csv",
        use_container_width=True
    )

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

    # Calcular métricas
    metrics = calculate_basic_metrics(casos, epizootias)
    
    # Mostrar métricas en grid
    col1, col2, col3, col4, col5, col6 = st.columns(5)
    
    with col1:
        st.metric("🦠 Casos Humanos", metrics["total_casos"])
    with col2:
        st.metric("⚰️ Fallecidos", metrics["fallecidos"], 
                 delta=f"{metrics['letalidad']:.1f}% letalidad")
    with col3:
        st.metric("🐒 Epizootias", metrics["total_epizootias"])
    with col4:
        st.metric("🔴 Positivas", metrics["epizootias_positivas"], 
                 delta=f"{metrics['positivas_porcentaje']:.1f}% de epizootias")
    with col5:
        st.metric("🔵 En Estudio", metrics["en_estudio"],
                  delta=f"{metrics['en_estudio_porcentaje']:.1f}% de epizootias")

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

# ===== FUNCIONES DE APOYO EXISTENTES (mantener) =====

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
        if "fecha_notificacion" in data_display.columns:
            data_display["fecha_notificacion"] = data_display["fecha_notificacion"].dt.strftime('%d/%m/%Y')
        
        # Simplificar proveniente
        if "proveniente" in data_display.columns:
            data_display["proveniente"] = data_display["proveniente"].apply(
                lambda x: "Vigilancia Comunitaria" if "VIGILANCIA COMUNITARIA" in str(x) 
                else "Incautación/Rescate" if "INCAUTACIÓN" in str(x)
                else str(x)[:50] + "..." if len(str(x)) > 50 else str(x)
            )
        
        rename_map = {
            'municipio': 'Municipio', 'vereda': 'Vereda', 'fecha_notificacion': 'Fecha Notificación',
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
        # Exportar resumen según nivel actual
        current_level = determine_drilldown_level(filters)
        if current_level == "departamento":
            summary_data = create_municipal_summary_optimized(casos, epizootias, {"municipios_normalizados": []})  # Usar datos actuales
        elif current_level == "municipio":
            municipio_actual = filters.get("municipio_display", "")
            summary_data = create_vereda_summary_optimized(casos, epizootias, municipio_actual, {"casos": casos, "epizootias": epizootias})
        else:
            summary_data = []
        
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
        
        # Resumen según nivel
        current_level = determine_drilldown_level(filters)
        if current_level == "departamento":
            summary_data = create_municipal_summary_optimized(casos, epizootias, {"municipios_normalizados": []})
            summary_name = "Resumen_Municipios"
        elif current_level == "municipio":
            municipio_actual = filters.get("municipio_display", "")
            summary_data = create_vereda_summary_optimized(casos, epizootias, municipio_actual, {"casos": casos, "epizootias": epizootias})
            summary_name = f"Resumen_Veredas_{municipio_actual}"
        else:
            summary_data = []
            summary_name = "Sin_Resumen"
        
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name=summary_name[:31], index=False)  # Límite 31 caracteres para nombres de hoja
        
        # Metadatos
        metadata = create_metadata_optimized(casos, epizootias, filters)
        metadata.to_excel(writer, sheet_name='Metadatos', index=False)
    
    buffer.seek(0)
    return buffer.getvalue()

def create_metadata_optimized(casos, epizootias, filters):
    """Crea metadatos optimizados."""
    active_filters = filters.get("active_filters", [])
    current_level = determine_drilldown_level(filters)
    
    metadata_rows = [
        {"Campo": "Fecha Exportación", "Valor": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        {"Campo": "Tipo Exportación", "Valor": "Datos Filtrados" if active_filters else "Datos Completos"},
        {"Campo": "Nivel de Análisis", "Valor": current_level.title()},
        {"Campo": "Total Casos", "Valor": len(casos)},
        {"Campo": "Total Epizootias", "Valor": len(epizootias)},
        {"Campo": "Dashboard Versión", "Valor": "4.0-DRILL-DOWN"}
    ]
    
    if active_filters:
        metadata_rows.append({"Campo": "Filtros Aplicados", "Valor": " • ".join(active_filters)})
    
    if current_level in ["municipio", "vereda"]:
        municipio = filters.get("municipio_display", "")
        metadata_rows.append({"Campo": "Municipio Filtrado", "Valor": municipio})
        
        if current_level == "vereda":
            vereda = filters.get("vereda_display", "")
            metadata_rows.append({"Campo": "Vereda Filtrada", "Valor": vereda})
    
    return pd.DataFrame(metadata_rows)

# ===== CSS SÚPER ESTÉTICO (mantener el existente) =====

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