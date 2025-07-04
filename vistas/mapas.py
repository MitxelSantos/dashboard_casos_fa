"""
Vista de mapas NUEVA del dashboard de Fiebre Amarilla.
TRASLADADA: TODAS las tarjetas informativas + mapa fijo + interacciones mejoradas
Layout: Columnas lado a lado (mapa | tarjetas informativas)
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime

# Importaciones opcionales para mapas
try:
    import geopandas as gpd
    import folium
    from streamlit_folium import st_folium
    MAPS_AVAILABLE = True
except ImportError:
    MAPS_AVAILABLE = False

# Importaciones del proyecto
from utils.data_processor import normalize_text

# Ruta de shapefiles procesados
PROCESSED_DIR = Path("C:/Users/Miguel Santos/Desktop/Tolima-Veredas/processed")


def show(data_filtered, filters, colors):
    """
    NUEVA: Vista completa de mapas con todas las tarjetas informativas trasladadas.
    Layout: Columnas lado a lado (mapa | tarjetas)
    """
    
    # CSS para la nueva vista
    apply_new_maps_css(colors)
    
    # Título principal
    st.markdown(
        '<h1 class="new-maps-title">🗺️ Mapas Interactivos con Métricas</h1>',
        unsafe_allow_html=True,
    )

    if not MAPS_AVAILABLE:
        show_maps_not_available()
        return

    # Verificar disponibilidad de shapefiles
    if not check_shapefiles_availability():
        show_shapefiles_setup_instructions()
        return

    # Cargar datos geográficos
    geo_data = load_geographic_data_silent()
    
    if not geo_data:
        show_geographic_data_error()
        return

    casos = data_filtered["casos"]
    epizootias = data_filtered["epizootias"]

    # **NUEVO LAYOUT**: División en columnas lado a lado
    col_mapa, col_tarjetas = st.columns([3, 2])  # 60% mapa, 40% tarjetas
    
    with col_mapa:
        st.markdown("### 🗺️ Mapa del Tolima")
        create_fixed_interactive_map_system(casos, epizootias, geo_data, filters, colors, data_filtered)
    
    with col_tarjetas:
        st.markdown("### 📊 Métricas y Datos")
        # **TRASLADADAS**: TODAS las tarjetas informativas de tablas.py
        create_all_metrics_cards_from_tablas(casos, epizootias, filters, colors)


def create_fixed_interactive_map_system(casos, epizootias, geo_data, filters, colors, data_filtered):
    """
    NUEVO: Sistema de mapas fijo con interacciones mejoradas (1 click = popup, 2 clicks = filtrar)
    """
    
    # Determinar nivel de mapa actual
    current_level = determine_map_level(filters)
    
    # Controles de navegación MEJORADOS
    create_enhanced_navigation_controls(current_level, filters, colors)
    
    # Indicador visual del filtrado activo
    show_active_filter_indicator(filters, colors)
    
    # Crear mapa según nivel con CONFIGURACIÓN FIJA
    if current_level == "departamento":
        create_fixed_departmental_map(casos, epizootias, geo_data, colors, data_filtered)
    elif current_level == "municipio":
        create_fixed_municipal_map(casos, epizootias, geo_data, filters, colors, data_filtered)
    elif current_level == "vereda":
        create_fixed_vereda_view(casos, epizootias, geo_data, filters, colors)


def create_enhanced_navigation_controls(current_level, filters, colors):
    """
    NUEVO: Controles de navegación mejorados con indicadores visuales
    """
    
    # Información del nivel actual con diseño mejorado
    level_info = {
        "departamento": {
            "title": "🏛️ Vista Departamental",
            "subtitle": "Tolima completo - Doble clic en municipios para filtrar",
            "color": colors["primary"],
            "icon": "🗺️"
        },
        "municipio": {
            "title": f"🏘️ {filters.get('municipio_display', 'Municipio')}",
            "subtitle": "Vista municipal - Doble clic en veredas para filtrar",
            "color": colors["warning"],
            "icon": "🏛️"
        },
        "vereda": {
            "title": f"📍 {filters.get('vereda_display', 'Vereda')}",
            "subtitle": f"En {filters.get('municipio_display', 'Municipio')}",
            "color": colors["info"],
            "icon": "🏘️"
        }
    }
    
    info = level_info[current_level]
    
    # Banner de nivel actual
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {info['color']}, {colors['secondary']});
            color: white;
            padding: 15px 20px;
            border-radius: 12px;
            margin-bottom: 15px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        ">
            <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 5px;">
                {info['icon']} {info['title']}
            </div>
            <div style="font-size: 0.9rem; opacity: 0.9;">
                {info['subtitle']}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Botones de navegación en fila
    cols = st.columns([1, 1, 1, 1])
    
    with cols[0]:
        if current_level != "departamento":
            if st.button("🏛️ Ver Tolima", key="nav_tolima", use_container_width=True):
                reset_all_location_filters()
                st.rerun()
        else:
            st.markdown(
                f'<div style="background: {colors["success"]}; color: white; padding: 8px; border-radius: 6px; text-align: center; font-size: 0.8rem;">🏛️ Tolima Actual</div>',
                unsafe_allow_html=True
            )
    
    with cols[1]:
        if current_level == "vereda":
            municipio_name = filters.get('municipio_display', 'Municipio')
            if st.button(f"🏘️ Ver {municipio_name[:10]}...", key="nav_municipio", use_container_width=True):
                reset_vereda_filter_only()
                st.rerun()
        elif current_level == "municipio":
            municipio_name = filters.get('municipio_display', 'Municipio')
            st.markdown(
                f'<div style="background: {colors["warning"]}; color: white; padding: 8px; border-radius: 6px; text-align: center; font-size: 0.8rem;">🏘️ {municipio_name[:10]}... Actual</div>',
                unsafe_allow_html=True
            )
    
    with cols[2]:
        if st.button("🔄 Actualizar", key="refresh_map", use_container_width=True):
            st.rerun()
    
    with cols[3]:
        # Botón reset siempre visible
        if st.button("🚫 Reset Filtros", key="reset_all", use_container_width=True):
            reset_all_filters_completely()
            st.rerun()


def show_active_filter_indicator(filters, colors):
    """
    NUEVO: Indicador visual del filtrado activo
    """
    
    active_filters = filters.get("active_filters", [])
    
    if active_filters:
        filters_text = " • ".join(active_filters[:3])  # Máximo 3 filtros
        
        if len(active_filters) > 3:
            filters_text += f" • +{len(active_filters) - 3} más"
        
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(45deg, {colors['danger']}, {colors['warning']});
                color: white;
                padding: 10px 15px;
                border-radius: 25px;
                margin-bottom: 10px;
                text-align: center;
                font-size: 0.85rem;
                font-weight: 600;
                box-shadow: 0 3px 10px rgba(0,0,0,0.2);
                animation: pulse 2s infinite;
            ">
                🎯 FILTROS ACTIVOS: {filters_text}
            </div>
            
            <style>
            @keyframes pulse {{
                0% {{ box-shadow: 0 3px 10px rgba(0,0,0,0.2); }}
                50% {{ box-shadow: 0 5px 15px rgba(0,0,0,0.3); }}
                100% {{ box-shadow: 0 3px 10px rgba(0,0,0,0.2); }}
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )


def create_fixed_departmental_map(casos, epizootias, geo_data, colors, data_filtered):
    """
    NUEVO: Mapa departamental FIJO (sin zoom, sin panning)
    """
    
    if 'municipios' not in geo_data:
        st.error("No se pudo cargar el shapefile de municipios")
        return
    
    municipios = geo_data['municipios'].copy()
    
    # Preparar datos agregados por municipio
    municipios_data = prepare_municipal_data_fixed(casos, epizootias, municipios)
    
    # Obtener límites del Tolima para configuración FIJA
    bounds = municipios.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2
    
    # **CONFIGURACIÓN FIJA**: Sin zoom, sin panning, limitado al Tolima
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=8,
        tiles='CartoDB positron',
        # **NUEVAS CONFIGURACIONES PARA MAPA FIJO**
        zoom_control=False,       # Sin control de zoom
        scrollWheelZoom=False,    # Sin zoom con scroll
        doubleClickZoom=False,    # Sin zoom con doble click
        dragging=False,           # Sin arrastrar/panning
        attributionControl=False, # Sin atribuciones
        max_bounds=True,          # Limitar área navegable
        min_zoom=8,               # Zoom mínimo
        max_zoom=8                # Zoom máximo (igual = fijo)
    )
    
    # **LIMITAR NAVEGACIÓN** al área del Tolima
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
    m.options['maxBounds'] = [[bounds[1] - 0.1, bounds[0] - 0.1], [bounds[3] + 0.1, bounds[2] + 0.1]]
    
    # Agregar municipios con datos y **NUEVAS INTERACCIONES**
    max_casos = municipios_data['casos'].max() if municipios_data['casos'].max() > 0 else 1
    max_epi = municipios_data['epizootias'].max() if municipios_data['epizootias'].max() > 0 else 1
    
    for idx, row in municipios_data.iterrows():
        municipio_name = row['MpNombre']
        casos_count = row['casos']
        fallecidos_count = row['fallecidos']
        epizootias_count = row['epizootias']
        
        # Color según intensidad de datos
        if casos_count > 0 or epizootias_count > 0:
            intensity = min(casos_count / max_casos, 1.0) if max_casos > 0 else 0
            if casos_count > 0:
                fill_color = f"rgba(229, 25, 55, {0.3 + intensity * 0.6})"
                border_color = colors['danger']
            else:
                epi_intensity = min(epizootias_count / max_epi, 1.0) if max_epi > 0 else 0
                fill_color = f"rgba(247, 148, 29, {0.3 + epi_intensity * 0.6})"
                border_color = colors['warning']
        else:
            fill_color = "rgba(200, 200, 200, 0.3)"
            border_color = "#cccccc"
        
        # **NUEVO POPUP MEJORADO** para 1 click
        popup_html = create_enhanced_municipal_popup(municipio_name, casos_count, fallecidos_count, epizootias_count, colors)
        
        # Agregar polígono con **INTERACCIONES MEJORADAS**
        geojson = folium.GeoJson(
            row['geometry'],
            style_function=lambda x, color=fill_color, border=border_color: {
                'fillColor': color,
                'color': border,
                'weight': 2,
                'fillOpacity': 0.7,
                'opacity': 1
            },
            popup=folium.Popup(popup_html, max_width=350),
            tooltip=f"<b>{municipio_name}</b><br>👆 1 clic: Info | 👆👆 2 clics: Filtrar<br>📊 Casos: {casos_count} | 🐒 Epizootias: {epizootias_count}"
        )
        
        geojson.add_to(m)
    
    # **TAMAÑO FIJO** del mapa
    map_data = st_folium(
        m, 
        width=700,      # **TAMAÑO FIJO**
        height=500,     # **TAMAÑO FIJO**
        returned_objects=["last_object_clicked_popup", "last_object_clicked"],
        key="fixed_main_map"
    )
    
    # **NUEVA LÓGICA**: Procesar clics en municipios (1 click = popup, 2 clicks = filtrar)
    handle_municipal_interactions_new(map_data, municipios_data)


def create_enhanced_municipal_popup(municipio, casos, fallecidos, epizootias, colors):
    """
    NUEVO: Popup mejorado con más datos básicos
    """
    letalidad = (fallecidos / casos * 100) if casos > 0 else 0
    actividad_total = casos + epizootias
    
    # Determinar nivel de riesgo
    if actividad_total > 20:
        riesgo = "Alto"
        riesgo_color = colors['danger']
    elif actividad_total > 5:
        riesgo = "Medio"
        riesgo_color = colors['warning']
    else:
        riesgo = "Bajo"
        riesgo_color = colors['success']
    
    return f"""
    <div style="font-family: Arial, sans-serif; width: 320px;">
        <h3 style="color: {colors['primary']}; margin: 0 0 15px 0; border-bottom: 3px solid {colors['secondary']}; padding-bottom: 8px; text-align: center;">
            📍 {municipio}
        </h3>
        
        <!-- Tarjetas de métricas básicas -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px;">
            <div style="background: #ffe6e6; padding: 12px; border-radius: 8px; text-align: center;">
                <div style="font-size: 1.8em; font-weight: bold; color: {colors['danger']};">🦠 {casos}</div>
                <div style="font-size: 0.8em; color: #666; font-weight: 600;">CASOS HUMANOS</div>
            </div>
            <div style="background: #fff3e0; padding: 12px; border-radius: 8px; text-align: center;">
                <div style="font-size: 1.8em; font-weight: bold; color: {colors['warning']};">🐒 {epizootias}</div>
                <div style="font-size: 0.8em; color: #666; font-weight: 600;">EPIZOOTIAS</div>
            </div>
        </div>
        
        <!-- Métricas adicionales -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px;">
            <div style="background: #f0f0f0; padding: 10px; border-radius: 6px; text-align: center;">
                <div style="font-size: 1.3em; font-weight: bold; color: {colors['dark']};">⚰️ {fallecidos}</div>
                <div style="font-size: 0.7em; color: #666;">Fallecidos ({letalidad:.1f}%)</div>
            </div>
            <div style="background: {riesgo_color}; padding: 10px; border-radius: 6px; text-align: center;">
                <div style="font-size: 1.1em; font-weight: bold; color: white;">⚠️ {riesgo}</div>
                <div style="font-size: 0.7em; color: white; opacity: 0.9;">Nivel de Riesgo</div>
            </div>
        </div>
        
        <!-- Actividad total -->
        <div style="background: linear-gradient(135deg, {colors['primary']}, {colors['accent']}); padding: 12px; border-radius: 8px; text-align: center; color: white;">
            <div style="font-size: 1.4em; font-weight: bold;">📊 {actividad_total}</div>
            <div style="font-size: 0.8em; opacity: 0.9;">Actividad Total (Casos + Epizootias)</div>
        </div>
        
        <!-- Instrucciones de interacción -->
        <div style="margin-top: 15px; padding: 10px; background: linear-gradient(135deg, {colors['info']}, {colors['secondary']}); border-radius: 8px; text-align: center; color: white;">
            <strong style="font-size: 0.9em;">👆👆 DOBLE CLIC PARA FILTRAR Y VER VEREDAS</strong>
        </div>
    </div>
    """


def handle_municipal_interactions_new(map_data, municipios_data):
    """
    NUEVO: Maneja interacciones del mapa (1 click vs 2 clicks)
    """
    if not map_data or not map_data.get('last_object_clicked_popup'):
        return
    
    # Detectar doble clic basado en timestamps
    current_time = st.session_state.get('last_click_time', 0)
    import time
    new_time = time.time()
    
    # Si han pasado menos de 0.5 segundos desde el último clic = doble clic
    is_double_click = (new_time - current_time) < 0.5
    
    st.session_state['last_click_time'] = new_time
    
    if is_double_click:
        # **DOBLE CLIC**: Filtrar municipio
        try:
            clicked_data = map_data['last_object_clicked_popup']
            if isinstance(clicked_data, dict) and 'tooltip' in clicked_data:
                tooltip = clicked_data['tooltip']
                import re
                match = re.search(r'<b>(.*?)</b>', tooltip)
                if match:
                    municipio_name = match.group(1)
                    
                    # **FILTRAR AUTOMÁTICAMENTE**
                    st.session_state['municipio_filter'] = municipio_name
                    
                    # Mostrar confirmación visual
                    st.success(f"✅ Filtrado por municipio: **{municipio_name}**")
                    
                    # **ACTUALIZAR INMEDIATAMENTE**
                    st.rerun()
                    
        except Exception as e:
            st.error(f"Error procesando doble clic: {str(e)}")
    # Para 1 clic, el popup se muestra automáticamente por Folium


def create_all_metrics_cards_from_tablas(casos, epizootias, filters, colors):
    """
    **TRASLADADAS**: TODAS las tarjetas informativas de tablas.py
    """
    
    # Calcular todas las métricas
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

    # Métricas geográficas
    municipios_afectados = set()
    if not casos.empty and "municipio_normalizado" in casos.columns:
        municipios_afectados.update(casos["municipio_normalizado"].dropna())
    if not epizootias.empty and "municipio_normalizado" in epizootias.columns:
        municipios_afectados.update(epizootias["municipio_normalizado"].dropna())

    # Fechas importantes Y UBICACIÓN
    ultima_fecha_caso = None
    ultimo_caso_municipio = None
    ultimo_caso_vereda = None
    ultima_fecha_epi = None
    ultima_epi_municipio = None
    ultima_epi_vereda = None

    if not casos.empty and "fecha_inicio_sintomas" in casos.columns:
        fechas_casos = casos["fecha_inicio_sintomas"].dropna()
        if not fechas_casos.empty:
            idx_ultimo = casos[casos["fecha_inicio_sintomas"] == fechas_casos.max()].index[-1]
            ultimo_caso = casos.loc[idx_ultimo]
            
            ultima_fecha_caso = fechas_casos.max()
            ultimo_caso_municipio = ultimo_caso.get("municipio", "No especificado")
            ultimo_caso_vereda = ultimo_caso.get("vereda", "No especificada")

    if not epizootias.empty and "fecha_recoleccion" in epizootias.columns:
        fechas_epi = epizootias["fecha_recoleccion"].dropna()
        if not fechas_epi.empty:
            idx_ultima = epizootias[epizootias["fecha_recoleccion"] == fechas_epi.max()].index[-1]
            ultima_epi = epizootias.loc[idx_ultima]
            
            ultima_fecha_epi = fechas_epi.max()
            ultima_epi_municipio = ultima_epi.get("municipio", "No especificado")
            ultima_epi_vereda = ultima_epi.get("vereda", "No especificada")

    # **SECCIÓN 1: CASOS HUMANOS**
    st.markdown("#### 🦠 Casos Humanos")
    
    # Tarjetas de casos humanos
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            label="Total Casos",
            value=f"{total_casos}",
            help="Casos humanos confirmados"
        )
        
        st.metric(
            label="Fallecidos",
            value=f"{fallecidos}",
            delta=f"Letalidad: {letalidad:.1f}%",
            help="Pacientes fallecidos por fiebre amarilla"
        )
    
    with col2:
        st.metric(
            label="Vivos",
            value=f"{vivos}",
            help="Pacientes que sobrevivieron"
        )
        
        # Último caso con ubicación
        if ultima_fecha_caso:
            dias_ultimo_caso = (datetime.now() - ultima_fecha_caso).days
            fecha_display = ultima_fecha_caso.strftime("%d/%m/%Y")
            
            st.metric(
                label="Último Caso",
                value=fecha_display,
                delta=f"Hace {dias_ultimo_caso} días",
                help=f"📍 {ultimo_caso_municipio} - {ultimo_caso_vereda}"
            )
        else:
            st.metric(
                label="Último Caso",
                value="Sin datos",
                help="No hay fechas de casos disponibles"
            )

    # **SECCIÓN 2: EPIZOOTIAS**
    st.markdown("---")
    st.markdown("#### 🐒 Epizootias")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            label="Epizootias",
            value=f"{total_epizootias}",
            help="Epizootias confirmadas positivas para FA"
        )
        
        # Actividad total
        actividad_total = total_casos + total_epizootias
        st.metric(
            label="Actividad Total",
            value=f"{actividad_total}",
            help="Casos humanos + epizootias confirmadas"
        )
    
    with col2:
        municipios_count = len(municipios_afectados)
        st.metric(
            label="Municipios Afectados",
            value=f"{municipios_count}",
            help="Municipios con eventos confirmados"
        )
        
        # Última epizootia con ubicación
        if ultima_fecha_epi:
            dias_ultima_epi = (datetime.now() - ultima_fecha_epi).days
            fecha_display = ultima_fecha_epi.strftime("%d/%m/%Y")
            
            st.metric(
                label="Última Epizootia",
                value=fecha_display,
                delta=f"Hace {dias_ultima_epi} días",
                help=f"📍 {ultima_epi_municipio} - {ultima_epi_vereda}"
            )
        else:
            st.metric(
                label="Última Epizootia",
                value="Sin datos",
                help="No hay fechas de epizootias disponibles"
            )

    # **SECCIÓN 3: ANÁLISIS DE RIESGO**
    st.markdown("---")
    st.markdown("#### ⚠️ Análisis de Riesgo")
    
    # Calcular nivel de riesgo
    if actividad_total > 20:
        riesgo = "Alto"
        riesgo_color = colors['danger']
        riesgo_delta = "Vigilancia crítica"
    elif actividad_total > 5:
        riesgo = "Medio"
        riesgo_color = colors['warning']
        riesgo_delta = "Vigilancia activa"
    else:
        riesgo = "Bajo"
        riesgo_color = colors['success']
        riesgo_delta = "Vigilancia rutinaria"
    
    # Mostrar nivel de riesgo con color
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {riesgo_color}, white);
            color: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            margin: 10px 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        ">
            <div style="font-size: 2rem; font-weight: bold; margin-bottom: 8px;">
                ⚠️ Nivel {riesgo}
            </div>
            <div style="font-size: 1rem; opacity: 0.9;">
                {riesgo_delta}
            </div>
            <div style="font-size: 0.9rem; margin-top: 8px; opacity: 0.8;">
                Basado en {actividad_total} eventos totales
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # **SECCIÓN 4: INFORMACIÓN CONTEXTUAL**
    ubicacion_actual = get_current_location_info(filters)
    
    if ubicacion_actual != "Tolima":
        st.markdown("---")
        st.markdown("#### 📍 Ubicación Actual")
        
        st.info(f"🎯 **Datos filtrados para:** {ubicacion_actual}")
        
        # Mostrar contexto de filtros activos
        active_filters = filters.get("active_filters", [])
        if active_filters:
            st.markdown("**Filtros activos:**")
            for filter_desc in active_filters[:5]:  # Máximo 5
                st.markdown(f"• {filter_desc}")

    # **SECCIÓN 5: MINI GRÁFICOS PARA MÓVILES**
    st.markdown("---")
    st.markdown("#### 📊 Distribución Rápida")
    
    # Distribución por sexo (gráfico simple)
    if not casos.empty and "sexo" in casos.columns:
        sexo_dist = casos["sexo"].value_counts()
        
        if not sexo_dist.empty:
            col1, col2 = st.columns(2)
            
            for i, (sexo, count) in enumerate(sexo_dist.items()):
                porcentaje = (count / total_casos * 100) if total_casos > 0 else 0
                
                with col1 if i == 0 else col2:
                    st.metric(
                        label=f"👤 {sexo}",
                        value=f"{count}",
                        delta=f"{porcentaje:.1f}%",
                        help=f"Casos en población {sexo.lower()}"
                    )

    # **BOTÓN DE EXPORTACIÓN RÁPIDA**
    st.markdown("---")
    
    if st.button("📥 Exportar Datos Actuales", use_container_width=True):
        # Crear datos de exportación básicos
        export_data = create_quick_export_data(casos, epizootias, filters)
        
        if export_data:
            csv_data = export_data.to_csv(index=False)
            st.download_button(
                label="💾 Descargar CSV",
                data=csv_data,
                file_name=f"datos_mapa_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.warning("No hay datos para exportar con los filtros actuales")


def create_quick_export_data(casos, epizootias, filters):
    """
    NUEVO: Crea datos de exportación rápida desde el mapa
    """
    export_rows = []
    
    # Agregar casos
    for _, caso in casos.iterrows():
        export_rows.append({
            "Tipo": "Caso Humano",
            "Municipio": caso.get("municipio", ""),
            "Vereda": caso.get("vereda", ""),
            "Fecha": caso.get("fecha_inicio_sintomas", ""),
            "Sexo": caso.get("sexo", ""),
            "Edad": caso.get("edad", ""),
            "Condicion": caso.get("condicion_final", ""),
            "Descripcion": "Caso confirmado de fiebre amarilla"
        })
    
    # Agregar epizootias
    for _, epi in epizootias.iterrows():
        export_rows.append({
            "Tipo": "Epizootia",
            "Municipio": epi.get("municipio", ""),
            "Vereda": epi.get("vereda", ""),
            "Fecha": epi.get("fecha_recoleccion", ""),
            "Sexo": "",
            "Edad": "",
            "Condicion": "",
            "Descripcion": epi.get("descripcion", "POSITIVO FA")
        })
    
    if export_rows:
        return pd.DataFrame(export_rows)
    else:
        return None


# =============== FUNCIONES DE APOYO NUEVAS ===============

def reset_all_location_filters():
    """NUEVO: Resetea todos los filtros de ubicación"""
    if "municipio_filter" in st.session_state:
        st.session_state.municipio_filter = "Todos"
    if "vereda_filter" in st.session_state:
        st.session_state.vereda_filter = "Todas"


def reset_vereda_filter_only():
    """NUEVO: Resetea solo el filtro de vereda"""
    if "vereda_filter" in st.session_state:
        st.session_state.vereda_filter = "Todas"


def reset_all_filters_completely():
    """NUEVO: Resetea TODOS los filtros del dashboard"""
    filter_keys = [
        "municipio_filter",
        "vereda_filter", 
        "fecha_filter",
        "condicion_filter",
        "sexo_filter",
        "edad_filter",
        "fuente_filter",
    ]
    
    for key in filter_keys:
        if key in st.session_state:
            if "municipio" in key:
                st.session_state[key] = "Todos"
            elif "vereda" in key:
                st.session_state[key] = "Todas"
            elif key in ["condicion_filter", "sexo_filter", "fuente_filter"]:
                st.session_state[key] = "Todos" if "sexo" in key else "Todas"
            else:
                try:
                    del st.session_state[key]
                except:
                    pass


def apply_new_maps_css(colors):
    """NUEVO: CSS para la nueva vista de mapas"""
    st.markdown(
        f"""
        <style>
        .new-maps-title {{
            color: {colors['primary']};
            font-size: clamp(2rem, 5vw, 2.5rem);
            font-weight: 700;
            text-align: center;
            margin-bottom: 1.5rem;
            padding: 1rem 2rem;
            border-radius: 12px;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-left: 6px solid {colors['secondary']};
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        /* Responsive design para columnas */
        @media (max-width: 768px) {{
            .css-1r6slb0 {{
                flex: 1 1 100% !important;
                margin-bottom: 1rem !important;
            }}
        }}
        
        /* Mejorar métricas en sidebar */
        .sidebar .stMetric {{
            background: white !important;
            padding: 1rem !important;
            border-radius: 8px !important;
            margin-bottom: 0.5rem !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
        }}
        
        /* Botones mejorados */
        .stButton > button {{
            background: linear-gradient(135deg, {colors['primary']}, {colors['accent']}) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
        }}
        
        .stButton > button:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# =============== FUNCIONES EXISTENTES REUTILIZADAS ===============

def determine_map_level(filters):
    """Determina el nivel de zoom del mapa según filtros activos."""
    if filters.get("vereda_normalizada"):
        return "vereda"
    elif filters.get("municipio_normalizado"):
        return "municipio"
    else:
        return "departamento"


def get_current_location_info(filters):
    """Obtiene información de la ubicación actual según filtros."""
    location_parts = []
    
    if filters.get("municipio_display") and filters["municipio_display"] != "Todos":
        location_parts.append(f"{filters['municipio_display']}")
    
    if filters.get("vereda_display") and filters["vereda_display"] != "Todas":
        location_parts.append(f"{filters['vereda_display']}")
    
    if not location_parts:
        return "Tolima"
    
    return " - ".join(location_parts)


def check_shapefiles_availability():
    """Verifica si los shapefiles procesados están disponibles."""
    municipios_path = PROCESSED_DIR / "tolima_municipios.shp"
    veredas_path = PROCESSED_DIR / "tolima_veredas.shp"
    return municipios_path.exists() or veredas_path.exists()


def load_geographic_data_silent():
    """Carga datos geográficos sin mostrar mensajes."""
    geo_data = {}
    
    try:
        # Cargar municipios
        municipios_path = PROCESSED_DIR / "tolima_municipios.shp"
        if municipios_path.exists():
            geo_data['municipios'] = gpd.read_file(municipios_path)
        
        # Cargar veredas
        veredas_path = PROCESSED_DIR / "tolima_veredas.shp"
        if veredas_path.exists():
            geo_data['veredas'] = gpd.read_file(veredas_path)
        
        return geo_data
        
    except Exception as e:
        st.error(f"❌ Error cargando datos geográficos: {str(e)}")
        return None


def prepare_municipal_data_fixed(casos, epizootias, municipios):
    """Prepara datos agregados por municipio."""
    casos_por_municipio = {}
    fallecidos_por_municipio = {}
    
    if not casos.empty and 'municipio_normalizado' in casos.columns:
        casos_counts = casos.groupby('municipio_normalizado').size()
        casos_por_municipio = casos_counts.to_dict()
        
        if 'condicion_final' in casos.columns:
            fallecidos_counts = casos[casos['condicion_final'] == 'Fallecido'].groupby('municipio_normalizado').size()
            fallecidos_por_municipio = fallecidos_counts.to_dict()
    
    epizootias_por_municipio = {}
    if not epizootias.empty and 'municipio_normalizado' in epizootias.columns:
        epi_counts = epizootias.groupby('municipio_normalizado').size()
        epizootias_por_municipio = epi_counts.to_dict()
    
    # Combinar datos con shapefile
    municipios_data = municipios.copy()
    
    municipios_data['casos'] = municipios_data['municipi_1'].map(casos_por_municipio).fillna(0).astype(int)
    municipios_data['fallecidos'] = municipios_data['municipi_1'].map(fallecidos_por_municipio).fillna(0).astype(int)
    municipios_data['epizootias'] = municipios_data['municipi_1'].map(epizootias_por_municipio).fillna(0).astype(int)
    
    return municipios_data


# =============== FUNCIONES DE RESPALDO ===============

def create_fixed_municipal_map(casos, epizootias, geo_data, filters, colors, data_filtered):
    """Placeholder para vista municipal"""
    st.info("🏘️ Vista municipal en desarrollo - funcionalidad similar al departamental")


def create_fixed_vereda_view(casos, epizootias, geo_data, filters, colors):
    """Placeholder para vista de vereda"""
    st.info("📍 Vista de vereda en desarrollo - información detallada")


def show_maps_not_available():
    """Muestra mensaje cuando las librerías de mapas no están disponibles."""
    st.error("⚠️ Librerías de mapas no instaladas. Instale: geopandas folium streamlit-folium")


def show_shapefiles_setup_instructions():
    """Muestra instrucciones para configurar shapefiles."""
    st.error("🗺️ Shapefiles no encontrados en la ruta configurada")


def show_geographic_data_error():
    """Muestra mensaje de error al cargar datos geográficos."""
    st.error("❌ Error al cargar datos geográficos")