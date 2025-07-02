"""
Componente de filtros del dashboard - Completamente responsive.
Actualizado para casos confirmados y epizootias con mejor UX en móviles.
"""

import streamlit as st
import pandas as pd
from utils.data_processor import normalize_text

def create_responsive_filters_ui():
    """
    Agrega CSS específico para filtros responsive.
    """
    st.markdown(
        """
        <style>
        /* Filtros responsive */
        .filter-section {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: clamp(0.75rem, 2vw, 1rem);
            margin-bottom: clamp(0.5rem, 2vw, 1rem);
            border-left: 4px solid #7D0F2B;
        }
        
        .filter-header {
            color: #7D0F2B;
            font-size: clamp(1rem, 3vw, 1.1rem);
            font-weight: 600;
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .filter-help {
            font-size: clamp(0.75rem, 2vw, 0.85rem);
            color: #666;
            margin-top: 0.25rem;
            line-height: 1.3;
        }
        
        /* Responsive filter controls */
        .sidebar .stSelectbox > div > div,
        .sidebar .stMultiSelect > div > div,
        .sidebar .stDateInput > div > div {
            font-size: clamp(0.8rem, 2vw, 0.9rem) !important;
        }
        
        .sidebar .stSelectbox label,
        .sidebar .stMultiSelect label,
        .sidebar .stDateInput label,
        .sidebar .stSlider label,
        .sidebar .stCheckbox label {
            font-size: clamp(0.85rem, 2vw, 0.95rem) !important;
            font-weight: 600 !important;
            color: #2c2c2c !important;
        }
        
        /* Reset button styling */
        .reset-filters-btn {
            width: 100% !important;
            background-color: #dc3545 !important;
            color: white !important;
            border: none !important;
            border-radius: 6px !important;
            padding: 0.5rem 1rem !important;
            font-size: clamp(0.8rem, 2vw, 0.9rem) !important;
            font-weight: 600 !important;
            margin: 1rem 0 !important;
            transition: all 0.3s ease !important;
        }
        
        .reset-filters-btn:hover {
            background-color: #c82333 !important;
            transform: translateY(-1px) !important;
        }
        
        /* Active filters display */
        .active-filters {
            background-color: #7D0F2B;
            color: white;
            padding: clamp(0.5rem, 2vw, 0.75rem);
            border-radius: 6px;
            margin: 0.5rem 0;
            font-size: clamp(0.8rem, 2vw, 0.9rem);
            line-height: 1.4;
        }
        
        .active-filters-title {
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        
        .active-filters-list {
            margin-left: 1rem;
        }
        
        /* Mobile optimizations */
        @media (max-width: 768px) {
            .filter-section {
                padding: 0.5rem;
                margin-bottom: 0.75rem;
            }
            
            .sidebar .stSelectbox > div > div,
            .sidebar .stMultiSelect > div > div {
                min-height: 44px !important; /* Touch-friendly */
            }
            
            .sidebar .stButton > button {
                min-height: 44px !important;
                font-size: 0.9rem !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def create_hierarchical_filters(data):
    """
    Crea filtros jerárquicos responsive para municipio y vereda.
    
    Args:
        data (dict): Datos cargados con mapeos
        
    Returns:
        dict: Filtros seleccionados
    """
    # Aplicar CSS responsive
    create_responsive_filters_ui()
    
    # Sección de filtros de ubicación
    st.sidebar.markdown(
        '<div class="filter-section">',
        unsafe_allow_html=True
    )
    
    st.sidebar.markdown(
        '<div class="filter-header">🔍 Filtros de Ubicación</div>',
        unsafe_allow_html=True
    )
    
    # Filtro de municipio con mejor UX
    municipio_options = ["Todos"] + [
        data["municipio_display_map"][norm] for norm in data["municipios_normalizados"]
    ]
    
    municipio_selected = st.sidebar.selectbox(
        "📍 Municipio:",
        municipio_options,
        key="municipio_filter",
        help="Seleccione un municipio específico para filtrar los datos"
    )
    
    # Mostrar información del municipio seleccionado
    if municipio_selected != "Todos":
        st.sidebar.markdown(
            f'<div class="filter-help">📊 Municipio seleccionado: <strong>{municipio_selected}</strong></div>',
            unsafe_allow_html=True
        )
    
    # Determinar municipio normalizado seleccionado
    municipio_norm_selected = None
    if municipio_selected != "Todos":
        for norm, display in data["municipio_display_map"].items():
            if display == municipio_selected:
                municipio_norm_selected = norm
                break
    
    # Filtro de vereda (jerárquico - depende del municipio)
    vereda_options = ["Todas"]
    if municipio_norm_selected and municipio_norm_selected in data["veredas_por_municipio"]:
        veredas_norm = data["veredas_por_municipio"][municipio_norm_selected]
        if municipio_norm_selected in data["vereda_display_map"]:
            vereda_options.extend([
                data["vereda_display_map"][municipio_norm_selected].get(norm, norm) 
                for norm in veredas_norm
            ])
    
    # Deshabilitar vereda si no hay municipio seleccionado
    vereda_disabled = municipio_selected == "Todos"
    
    if vereda_disabled:
        st.sidebar.markdown(
            '<div class="filter-help">💡 Seleccione un municipio para ver sus veredas</div>',
            unsafe_allow_html=True
        )
    
    vereda_selected = st.sidebar.selectbox(
        "🏘️ Vereda:",
        vereda_options,
        key="vereda_filter",
        disabled=vereda_disabled,
        help="Las veredas se actualizan automáticamente según el municipio seleccionado"
    )
    
    # Mostrar información de la vereda seleccionada
    if vereda_selected != "Todas" and not vereda_disabled:
        st.sidebar.markdown(
            f'<div class="filter-help">🏘️ Vereda seleccionada: <strong>{vereda_selected}</strong></div>',
            unsafe_allow_html=True
        )
    
    # Determinar vereda normalizada seleccionada
    vereda_norm_selected = None
    if vereda_selected != "Todas" and municipio_norm_selected:
        if municipio_norm_selected in data["vereda_display_map"]:
            for norm, display in data["vereda_display_map"][municipio_norm_selected].items():
                if display == vereda_selected:
                    vereda_norm_selected = norm
                    break
    
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    
    return {
        "municipio_display": municipio_selected,
        "municipio_normalizado": municipio_norm_selected,
        "vereda_display": vereda_selected,
        "vereda_normalizada": vereda_norm_selected,
    }

def create_content_filters(data):
    """
    Crea filtros de contenido responsive (tipo de datos, fechas, etc.).
    
    Args:
        data (dict): Datos cargados
        
    Returns:
        dict: Filtros de contenido seleccionados
    """
    # Sección de filtros de contenido
    st.sidebar.markdown(
        '<div class="filter-section">',
        unsafe_allow_html=True
    )
    
    st.sidebar.markdown(
        '<div class="filter-header">📊 Filtros de Contenido</div>',
        unsafe_allow_html=True
    )
    
    # Filtro de tipo de datos con mejor descripción
    tipo_datos = st.sidebar.multiselect(
        "📋 Mostrar:",
        ["Casos Confirmados", "Epizootias"],
        default=["Casos Confirmados", "Epizootias"],
        key="tipo_datos_filter",
        help="Seleccione qué tipo de datos mostrar en las visualizaciones"
    )
    
    # Información sobre los tipos seleccionados
    if len(tipo_datos) == 1:
        st.sidebar.markdown(
            f'<div class="filter-help">📋 Mostrando solo: <strong>{tipo_datos[0]}</strong></div>',
            unsafe_allow_html=True
        )
    elif len(tipo_datos) == 2:
        st.sidebar.markdown(
            '<div class="filter-help">📋 Mostrando: <strong>Ambos tipos de datos</strong></div>',
            unsafe_allow_html=True
        )
    elif len(tipo_datos) == 0:
        st.sidebar.warning("⚠️ Seleccione al menos un tipo de datos")
    
    # Filtro de rango de fechas con información contextual
    fechas_disponibles = []
    
    # Recopilar fechas de casos
    if not data["casos"].empty and 'fecha_inicio_sintomas' in data["casos"].columns:
        fechas_casos = data["casos"]['fecha_inicio_sintomas'].dropna()
        fechas_disponibles.extend(fechas_casos.tolist())
    
    # Recopilar fechas de epizootias
    if not data["epizootias"].empty and 'fecha_recoleccion' in data["epizootias"].columns:
        fechas_epi = data["epizootias"]['fecha_recoleccion'].dropna()
        fechas_disponibles.extend(fechas_epi.tolist())
    
    fecha_rango = None
    if fechas_disponibles:
        fecha_min = min(fechas_disponibles)
        fecha_max = max(fechas_disponibles)
        
        # Mostrar información del rango disponible
        st.sidebar.markdown(
            f'<div class="filter-help">📅 Datos disponibles: {fecha_min.strftime("%Y-%m-%d")} a {fecha_max.strftime("%Y-%m-%d")}</div>',
            unsafe_allow_html=True
        )
        
        fecha_rango = st.sidebar.date_input(
            "📅 Rango de Fechas:",
            value=(fecha_min.date(), fecha_max.date()),
            min_value=fecha_min.date(),
            max_value=fecha_max.date(),
            key="fecha_filter",
            help="Seleccione el período temporal de interés"
        )
        
        # Validar rango seleccionado
        if fecha_rango and len(fecha_rango) == 2:
            fecha_inicio, fecha_fin = fecha_rango
            dias_seleccionados = (fecha_fin - fecha_inicio).days + 1
            st.sidebar.markdown(
                f'<div class="filter-help">📊 Período seleccionado: <strong>{dias_seleccionados} días</strong></div>',
                unsafe_allow_html=True
            )
    else:
        st.sidebar.warning("⚠️ No hay fechas disponibles en los datos")
    
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    
    return {
        "tipo_datos": tipo_datos,
        "fecha_rango": fecha_rango
    }

def create_advanced_filters(data):
    """
    Crea filtros avanzados responsive específicos para casos y epizootias.
    
    Args:
        data (dict): Datos cargados
        
    Returns:
        dict: Filtros avanzados seleccionados
    """
    # Sección de filtros avanzados
    st.sidebar.markdown(
        '<div class="filter-section">',
        unsafe_allow_html=True
    )
    
    st.sidebar.markdown(
        '<div class="filter-header">🔧 Filtros Avanzados</div>',
        unsafe_allow_html=True
    )
    
    # Expandir sección de filtros avanzados con mejor organización
    with st.sidebar.expander("🦠 Filtros de Casos", expanded=False):
        # Filtro por condición final
        condicion_filter = "Todas"
        if not data["casos"].empty and 'condicion_final' in data["casos"].columns:
            condiciones_disponibles = ["Todas"] + list(data["casos"]['condicion_final'].dropna().unique())
            condicion_filter = st.selectbox(
                "Condición Final:",
                condiciones_disponibles,
                key="condicion_filter",
                help="Estado final del paciente"
            )
            
            # Información sobre la condición seleccionada
            if condicion_filter != "Todas":
                count = (data["casos"]['condicion_final'] == condicion_filter).sum()
                st.caption(f"📊 {count} casos con condición: {condicion_filter}")
        
        # Filtro por sexo
        sexo_filter = "Todos"
        if not data["casos"].empty and 'sexo' in data["casos"].columns:
            sexos_disponibles = ["Todos"] + list(data["casos"]['sexo'].dropna().unique())
            sexo_filter = st.selectbox(
                "Sexo:",
                sexos_disponibles,
                key="sexo_filter",
                help="Género del paciente"
            )
            
            # Información sobre el sexo seleccionado
            if sexo_filter != "Todos":
                count = (data["casos"]['sexo'] == sexo_filter).sum()
                st.caption(f"📊 {count} casos de sexo: {sexo_filter}")
        
        # Filtro por rango de edad
        edad_rango = None
        if not data["casos"].empty and 'edad' in data["casos"].columns:
            edad_min = int(data["casos"]['edad'].min()) if not data["casos"]['edad'].isna().all() else 0
            edad_max = int(data["casos"]['edad'].max()) if not data["casos"]['edad'].isna().all() else 100
            
            if edad_min < edad_max:
                edad_rango = st.slider(
                    "Rango de Edad:",
                    min_value=edad_min,
                    max_value=edad_max,
                    value=(edad_min, edad_max),
                    key="edad_filter",
                    help="Seleccione el rango de edad de interés"
                )
                
                # Información sobre el rango seleccionado
                if edad_rango:
                    casos_en_rango = data["casos"][
                        (data["casos"]['edad'] >= edad_rango[0]) & 
                        (data["casos"]['edad'] <= edad_rango[1])
                    ].shape[0]
                    st.caption(f"📊 {casos_en_rango} casos en rango {edad_rango[0]}-{edad_rango[1]} años")
    
    with st.sidebar.expander("🐒 Filtros de Epizootias", expanded=False):
        # Filtro por resultado de epizootia
        resultado_filter = "Todos"
        if not data["epizootias"].empty and 'descripcion' in data["epizootias"].columns:
            resultados_disponibles = ["Todos"] + list(data["epizootias"]['descripcion'].dropna().unique())
            resultado_filter = st.selectbox(
                "Resultado:",
                resultados_disponibles,
                key="resultado_filter",
                help="Resultado del análisis de la muestra"
            )
            
            # Información sobre el resultado seleccionado
            if resultado_filter != "Todos":
                count = (data["epizootias"]['descripcion'] == resultado_filter).sum()
                st.caption(f"📊 {count} epizootias con resultado: {resultado_filter}")
        
        # Filtro por fuente de epizootia
        fuente_filter = "Todas"
        if not data["epizootias"].empty and 'proveniente' in data["epizootias"].columns:
            fuentes_disponibles = ["Todas"] + list(data["epizootias"]['proveniente'].dropna().unique())
            fuente_filter = st.selectbox(
                "Fuente:",
                fuentes_disponibles,
                key="fuente_filter",
                help="Origen o fuente de la muestra"
            )
            
            # Información sobre la fuente seleccionada
            if fuente_filter != "Todas":
                count = (data["epizootias"]['proveniente'] == fuente_filter).sum()
                st.caption(f"📊 {count} epizootias de fuente: {fuente_filter[:30]}...")
    
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    
    return {
        "condicion_final": condicion_filter,
        "sexo": sexo_filter,
        "edad_rango": edad_rango,
        "resultado_epizootia": resultado_filter,
        "fuente_epizootia": fuente_filter
    }

def create_filter_summary(filters_location, filters_content, filters_advanced):
    """
    Crea un resumen responsive de los filtros aplicados.
    
    Args:
        filters_location (dict): Filtros de ubicación
        filters_content (dict): Filtros de contenido
        filters_advanced (dict): Filtros avanzados
        
    Returns:
        list: Lista de filtros activos
    """
    active_filters = []
    
    # Filtros de ubicación
    if filters_location["municipio_display"] != "Todos":
        active_filters.append(f"📍 Municipio: {filters_location['municipio_display']}")
    
    if filters_location["vereda_display"] != "Todas":
        active_filters.append(f"🏘️ Vereda: {filters_location['vereda_display']}")
    
    # Filtros de contenido
    if len(filters_content["tipo_datos"]) < 2 and len(filters_content["tipo_datos"]) > 0:
        active_filters.append(f"📋 Datos: {', '.join(filters_content['tipo_datos'])}")
    
    if filters_content["fecha_rango"] and len(filters_content["fecha_rango"]) == 2:
        fecha_inicio, fecha_fin = filters_content["fecha_rango"]
        active_filters.append(f"📅 Período: {fecha_inicio} - {fecha_fin}")
    
    # Filtros avanzados
    if filters_advanced["condicion_final"] != "Todas":
        active_filters.append(f"⚰️ Condición: {filters_advanced['condicion_final']}")
    
    if filters_advanced["sexo"] != "Todos":
        active_filters.append(f"👤 Sexo: {filters_advanced['sexo']}")
    
    if filters_advanced["edad_rango"]:
        edad_min, edad_max = filters_advanced["edad_rango"]
        active_filters.append(f"🎂 Edad: {edad_min}-{edad_max} años")
    
    if filters_advanced["resultado_epizootia"] != "Todos":
        resultado_short = filters_advanced["resultado_epizootia"][:20] + "..." if len(filters_advanced["resultado_epizootia"]) > 20 else filters_advanced["resultado_epizootia"]
        active_filters.append(f"🔬 Resultado: {resultado_short}")
    
    if filters_advanced["fuente_epizootia"] != "Todas":
        fuente_short = filters_advanced["fuente_epizootia"][:20] + "..." if len(filters_advanced["fuente_epizootia"]) > 20 else filters_advanced["fuente_epizootia"]
        active_filters.append(f"📋 Fuente: {fuente_short}")
    
    return active_filters

def show_active_filters_sidebar(active_filters):
    """
    Muestra los filtros activos en la barra lateral de manera responsive.
    
    Args:
        active_filters (list): Lista de filtros activos
    """
    if not active_filters:
        return
    
    st.sidebar.markdown("---")
    
    # Título con contador
    filter_count = len(active_filters)
    st.sidebar.markdown(
        f"""
        <div class="active-filters">
            <div class="active-filters-title">
                🔍 Filtros Activos ({filter_count})
            </div>
            <div class="active-filters-list">
        """,
        unsafe_allow_html=True
    )
    
    # Mostrar filtros de manera compacta
    for filter_desc in active_filters:
        st.sidebar.markdown(f"• {filter_desc}")
    
    st.sidebar.markdown(
        """
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def apply_all_filters(data, filters_location, filters_content, filters_advanced):
    """
    Aplica todos los filtros a los datos de manera eficiente.
    
    Args:
        data (dict): Datos originales
        filters_location (dict): Filtros de ubicación
        filters_content (dict): Filtros de contenido  
        filters_advanced (dict): Filtros avanzados
        
    Returns:
        dict: Datos filtrados
    """
    casos_filtrados = data["casos"].copy()
    epizootias_filtradas = data["epizootias"].copy()
    
    # =============== APLICAR FILTROS DE UBICACIÓN ===============
    if filters_location["municipio_normalizado"]:
        municipio_norm = filters_location["municipio_normalizado"]
        
        if 'municipio_normalizado' in casos_filtrados.columns:
            casos_filtrados = casos_filtrados[
                casos_filtrados["municipio_normalizado"] == municipio_norm
            ]
        
        if 'municipio_normalizado' in epizootias_filtradas.columns:
            epizootias_filtradas = epizootias_filtradas[
                epizootias_filtradas["municipio_normalizado"] == municipio_norm
            ]
    
    if filters_location["vereda_normalizada"]:
        vereda_norm = filters_location["vereda_normalizada"]
        
        if 'vereda_normalizada' in casos_filtrados.columns:
            casos_filtrados = casos_filtrados[
                casos_filtrados["vereda_normalizada"] == vereda_norm
            ]
        
        if 'vereda_normalizada' in epizootias_filtradas.columns:
            epizootias_filtradas = epizootias_filtradas[
                epizootias_filtradas["vereda_normalizada"] == vereda_norm
            ]
    
    # =============== APLICAR FILTROS DE CONTENIDO ===============
    if filters_content["fecha_rango"] and len(filters_content["fecha_rango"]) == 2:
        fecha_inicio, fecha_fin = filters_content["fecha_rango"]
        fecha_inicio = pd.Timestamp(fecha_inicio)
        fecha_fin = pd.Timestamp(fecha_fin)
        
        # Filtrar casos por fecha de inicio de síntomas
        if 'fecha_inicio_sintomas' in casos_filtrados.columns:
            casos_filtrados = casos_filtrados[
                (casos_filtrados['fecha_inicio_sintomas'] >= fecha_inicio) &
                (casos_filtrados['fecha_inicio_sintomas'] <= fecha_fin)
            ]
        
        # Filtrar epizootias por fecha de recolección
        if 'fecha_recoleccion' in epizootias_filtradas.columns:
            epizootias_filtradas = epizootias_filtradas[
                (epizootias_filtradas['fecha_recoleccion'] >= fecha_inicio) &
                (epizootias_filtradas['fecha_recoleccion'] <= fecha_fin)
            ]
    
    # =============== APLICAR FILTROS AVANZADOS PARA CASOS ===============
    if filters_advanced["condicion_final"] != "Todas":
        if 'condicion_final' in casos_filtrados.columns:
            casos_filtrados = casos_filtrados[
                casos_filtrados['condicion_final'] == filters_advanced["condicion_final"]
            ]
    
    if filters_advanced["sexo"] != "Todos":
        if 'sexo' in casos_filtrados.columns:
            casos_filtrados = casos_filtrados[
                casos_filtrados['sexo'] == filters_advanced["sexo"]
            ]
    
    if filters_advanced["edad_rango"]:
        edad_min, edad_max = filters_advanced["edad_rango"]
        if 'edad' in casos_filtrados.columns:
            casos_filtrados = casos_filtrados[
                (casos_filtrados['edad'] >= edad_min) &
                (casos_filtrados['edad'] <= edad_max)
            ]
    
    # =============== APLICAR FILTROS AVANZADOS PARA EPIZOOTIAS ===============
    if filters_advanced["resultado_epizootia"] != "Todos":
        if 'descripcion' in epizootias_filtradas.columns:
            epizootias_filtradas = epizootias_filtradas[
                epizootias_filtradas['descripcion'] == filters_advanced["resultado_epizootia"]
            ]
    
    if filters_advanced["fuente_epizootia"] != "Todas":
        if 'proveniente' in epizootias_filtradas.columns:
            epizootias_filtradas = epizootias_filtradas[
                epizootias_filtradas['proveniente'] == filters_advanced["fuente_epizootia"]
            ]
    
    # Retornar datos filtrados con metadatos preservados
    return {
        "casos": casos_filtrados,
        "epizootias": epizootias_filtradas,
        **{k: v for k, v in data.items() if k not in ["casos", "epizootias"]}
    }

def reset_all_filters():
    """
    Resetea todos los filtros a sus valores por defecto.
    """
    # Lista de todas las claves de filtros
    filter_keys = [
        "municipio_filter",
        "vereda_filter", 
        "tipo_datos_filter",
        "fecha_filter",
        "condicion_filter",
        "sexo_filter",
        "edad_filter",
        "resultado_filter",
        "fuente_filter"
    ]
    
    # Resetear cada filtro en session_state
    for key in filter_keys:
        if key in st.session_state:
            if key == "tipo_datos_filter":
                st.session_state[key] = ["Casos Confirmados", "Epizootias"]
            elif key in ["municipio_filter", "condicion_filter", "sexo_filter", "resultado_filter", "fuente_filter"]:
                st.session_state[key] = "Todos" if key not in ["vereda_filter"] else "Todas"
            elif key == "vereda_filter":
                st.session_state[key] = "Todas"

def create_filter_export_options(data_filtered):
    """
    Crea opciones responsive para exportar datos filtrados.
    
    Args:
        data_filtered (dict): Datos filtrados
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        '<div class="filter-header">📥 Exportar Datos Filtrados</div>',
        unsafe_allow_html=True
    )
    
    # Información sobre los datos filtrados
    casos_count = len(data_filtered["casos"])
    epi_count = len(data_filtered["epizootias"])
    
    st.sidebar.markdown(
        f"""
        <div class="filter-help">
            📊 Datos filtrados:<br>
            • Casos: {casos_count}<br>
            • Epizootias: {epi_count}
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Crear columnas responsive para botones
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        # Botón para descargar casos filtrados
        if not data_filtered["casos"].empty:
            casos_csv = data_filtered["casos"].to_csv(index=False)
            st.download_button(
                label="🦠 Casos",
                data=casos_csv,
                file_name=f"casos_filtrados_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                key="download_casos_filtered",
                help="Descargar casos filtrados como CSV"
            )
        else:
            st.button(
                "🦠 Casos",
                disabled=True,
                help="No hay casos para exportar"
            )
    
    with col2:
        # Botón para descargar epizootias filtradas
        if not data_filtered["epizootias"].empty:
            epi_csv = data_filtered["epizootias"].to_csv(index=False)
            st.download_button(
                label="🐒 Epizootias",
                data=epi_csv,
                file_name=f"epizootias_filtradas_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                key="download_epi_filtered",
                help="Descargar epizootias filtradas como CSV"
            )
        else:
            st.button(
                "🐒 Epizootias",
                disabled=True,
                help="No hay epizootias para exportar"
            )

def show_filter_info():
    """
    Muestra información responsive sobre cómo usar los filtros.
    """
    with st.sidebar.expander("ℹ️ Información sobre Filtros"):
        st.markdown(
            """
            **🔍 Filtros Jerárquicos:**
            - Seleccione primero un municipio
            - Las veredas se actualizarán automáticamente
            - "Todos/Todas" muestra datos sin filtrar
            
            **📅 Filtros de Fecha:**
            - Incluye ambas fechas límite
            - Casos: fecha de inicio de síntomas
            - Epizootias: fecha de recolección
            
            **🔧 Filtros Avanzados:**
            - Permiten análisis más específicos
            - Se combinan con otros filtros
            - Use "Todos" para incluir todos los valores
            
            **💡 Consejos:**
            - Los filtros se aplican automáticamente
            - Use "Restablecer Filtros" para limpiar
            - La exportación respeta los filtros activos
            """,
            help="Información detallada sobre el uso de filtros"
        )

def create_complete_filter_system(data):
    """
    Crea el sistema completo de filtros responsive.
    
    Args:
        data (dict): Datos cargados
        
    Returns:
        dict: Todos los filtros aplicados y datos filtrados
    """
    # Crear diferentes tipos de filtros
    filters_location = create_hierarchical_filters(data)
    filters_content = create_content_filters(data)
    filters_advanced = create_advanced_filters(data)
    
    # Crear resumen de filtros activos
    active_filters = create_filter_summary(filters_location, filters_content, filters_advanced)
    
    # Mostrar filtros activos en sidebar
    show_active_filters_sidebar(active_filters)
    
    # Botón para resetear filtros con estilo responsive
    st.sidebar.markdown("---")
    col1, col2 = st.sidebar.columns([2, 1])
    
    with col1:
        if st.button("🔄 Restablecer Filtros", key="reset_all_filters", help="Limpiar todos los filtros aplicados"):
            reset_all_filters()
            st.rerun()
    
    with col2:
        # Contador de filtros activos
        filter_count = len(active_filters)
        if filter_count > 0:
            st.markdown(
                f"""
                <div style="
                    background-color: #7D0F2B; 
                    color: white; 
                    padding: 0.25rem 0.5rem; 
                    border-radius: 12px; 
                    text-align: center; 
                    font-size: 0.8rem; 
                    font-weight: 600;
                ">
                    {filter_count}
                </div>
                """,
                unsafe_allow_html=True
            )
    
    # Aplicar todos los filtros
    data_filtered = apply_all_filters(data, filters_location, filters_content, filters_advanced)
    
    # Mostrar opciones de exportación
    create_filter_export_options(data_filtered)
    
    # Mostrar información sobre filtros
    show_filter_info()
    
    # Combinar todos los filtros en un solo diccionario
    all_filters = {
        **filters_location,
        **filters_content,
        **filters_advanced,
        "active_filters": active_filters
    }
    
    return {
        "filters": all_filters,
        "data_filtered": data_filtered
    }