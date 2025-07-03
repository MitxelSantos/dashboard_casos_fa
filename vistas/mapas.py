"""
Vista de mapas del dashboard de Fiebre Amarilla - IMPLEMENTACIÓN COMPLETA.
Maneja columnas truncadas de shapefiles y rutas actualizadas.
Reemplaza el contenido actual de vistas/mapas.py
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

# Importaciones opcionales para mapas
try:
    import geopandas as gpd
    import folium
    from streamlit_folium import st_folium
    MAPS_AVAILABLE = True
except ImportError:
    MAPS_AVAILABLE = False

# Rutas de shapefiles procesados (ACTUALIZADA)
PROCESSED_DIR = Path("C:/Users/Miguel Santos/Desktop/Tolima-Veredas/processed")


def show(data_filtered, filters, colors):
    """
    Muestra la vista de mapas completa con shapefiles del Tolima.

    Args:
        data_filtered (dict): Datos filtrados
        filters (dict): Filtros aplicados
        colors (dict): Colores institucionales
    """
    st.markdown(
        '<h1 style="color: #5A4214; border-bottom: 2px solid #F2A900; padding-bottom: 8px;">🗺️ Mapas Geográficos</h1>',
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
    geo_data = load_geographic_data()
    
    if not geo_data:
        show_geographic_data_error()
        return

    # Crear interfaz de mapas
    create_maps_interface(data_filtered, filters, colors, geo_data)


def check_shapefiles_availability():
    """
    Verifica si los shapefiles procesados están disponibles.
    """
    municipios_path = PROCESSED_DIR / "tolima_municipios.shp"
    veredas_path = PROCESSED_DIR / "tolima_veredas.shp"
    
    return municipios_path.exists() or veredas_path.exists()


def load_geographic_data():
    """
    Carga los datos geográficos procesados con manejo de columnas truncadas.
    """
    geo_data = {}
    
    try:
        # Cargar municipios
        municipios_path = PROCESSED_DIR / "tolima_municipios.shp"
        if municipios_path.exists():
            geo_data['municipios'] = gpd.read_file(municipios_path)
            st.success(f"✅ Municipios cargados: {len(geo_data['municipios'])} registros")
            
            # Debug: mostrar columnas disponibles
            st.info(f"📋 Columnas municipios: {list(geo_data['municipios'].columns)}")
        
        # Cargar veredas
        veredas_path = PROCESSED_DIR / "tolima_veredas.shp"
        if veredas_path.exists():
            geo_data['veredas'] = gpd.read_file(veredas_path)
            st.success(f"✅ Veredas cargadas: {len(geo_data['veredas'])} registros")
            
            # Debug: mostrar columnas disponibles
            st.info(f"📋 Columnas veredas: {list(geo_data['veredas'].columns)}")
        
        # Cargar límite departamental
        limite_path = PROCESSED_DIR / "tolima_limite.shp"
        if limite_path.exists():
            geo_data['limite'] = gpd.read_file(limite_path)
            st.success(f"✅ Límite departamental cargado")
        
        return geo_data
        
    except Exception as e:
        st.error(f"❌ Error cargando datos geográficos: {str(e)}")
        return None


def create_maps_interface(data_filtered, filters, colors, geo_data):
    """
    Crea la interfaz principal de mapas.
    """
    casos = data_filtered["casos"]
    epizootias = data_filtered["epizootias"]
    
    # Métricas geográficas rápidas
    show_geographic_metrics(casos, epizootias, geo_data, colors)
    
    st.markdown("---")
    
    # Selector de tipo de mapa
    map_type = st.selectbox(
        "🗺️ Tipo de Mapa:",
        ["Vista General", "Casos por Municipio", "Epizootias por Municipio", "Veredas Detalladas"],
        help="Seleccione el tipo de visualización geográfica"
    )
    
    # Crear mapa según selección
    if map_type == "Vista General":
        create_overview_map(geo_data, colors)
    elif map_type == "Casos por Municipio":
        create_casos_choropleth(casos, geo_data, colors)
    elif map_type == "Epizootias por Municipio":
        create_epizootias_choropleth(epizootias, geo_data, colors)
    elif map_type == "Veredas Detalladas":
        create_veredas_map(casos, epizootias, geo_data, colors, filters)


def show_geographic_metrics(casos, epizootias, geo_data, colors):
    """
    Muestra métricas geográficas rápidas.
    """
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        municipios_disponibles = len(geo_data.get('municipios', []))
        st.metric("🏛️ Municipios", municipios_disponibles, help="Municipios en shapefile")
    
    with col2:
        veredas_disponibles = len(geo_data.get('veredas', []))
        st.metric("🏘️ Veredas", veredas_disponibles, help="Veredas en shapefile")
    
    with col3:
        municipios_con_casos = 0
        if not casos.empty and "municipio_normalizado" in casos.columns:
            municipios_con_casos = casos["municipio_normalizado"].nunique()
        st.metric("🦠 Municipios c/Casos", municipios_con_casos, help="Municipios con casos")
    
    with col4:
        municipios_con_epi = 0
        if not epizootias.empty and "municipio_normalizado" in epizootias.columns:
            municipios_con_epi = epizootias["municipio_normalizado"].nunique()
        st.metric("🐒 Municipios c/Epizootias", municipios_con_epi, help="Municipios con epizootias")


def create_overview_map(geo_data, colors):
    """
    Crea mapa general del Tolima.
    """
    st.subheader("🗺️ Vista General del Tolima")
    
    if 'municipios' not in geo_data:
        st.error("No se pudo cargar el shapefile de municipios")
        return
    
    municipios = geo_data['municipios']
    
    # Calcular centro del mapa
    center_lat = municipios.geometry.centroid.y.mean()
    center_lon = municipios.geometry.centroid.x.mean()
    
    # Crear mapa con Folium
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=8,
        tiles='OpenStreetMap'
    )
    
    # Agregar municipios (usando MpNombre que existe en el shapefile original)
    folium.GeoJson(
        municipios,
        style_function=lambda x: {
            'fillColor': colors['primary'],
            'color': 'white',
            'weight': 2,
            'fillOpacity': 0.3,
        },
        popup=folium.GeoJsonPopup(fields=['MpNombre'], aliases=['Municipio:']),
        tooltip=folium.GeoJsonTooltip(fields=['MpNombre'], aliases=['Municipio:'])
    ).add_to(m)
    
    # Agregar límite departamental si existe
    if 'limite' in geo_data:
        folium.GeoJson(
            geo_data['limite'],
            style_function=lambda x: {
                'fillColor': 'none',
                'color': colors['secondary'],
                'weight': 4,
                'opacity': 0.8,
            }
        ).add_to(m)
    
    # Mostrar mapa
    st_folium(m, width=700, height=500)


def create_casos_choropleth(casos, geo_data, colors):
    """
    Crea mapa coroplético de casos por municipio con columnas corregidas.
    """
    st.subheader("🦠 Casos por Municipio")
    
    if 'municipios' not in geo_data:
        st.error("No se pudo cargar el shapefile de municipios")
        return
    
    if casos.empty:
        st.info("No hay casos para mostrar en el mapa")
        return
    
    municipios = geo_data['municipios'].copy()
    
    # Contar casos por municipio normalizado
    casos_por_municipio = casos.groupby('municipio_normalizado').size().reset_index(name='casos')
    
    # Normalizar nombres del shapefile para hacer merge
    # Usar la columna MpNombre original del shapefile
    if 'MpNombre' in municipios.columns:
        municipios['municipio_normalizado_shp'] = municipios['MpNombre'].apply(normalize_for_merge)
    elif 'municipi_1' in municipios.columns:
        # Si la columna fue truncada, usarla
        municipios['municipio_normalizado_shp'] = municipios['municipi_1']
    else:
        st.error("No se encontró columna de municipio en el shapefile")
        return
    
    # Merge con datos de casos
    municipios_con_casos = municipios.merge(
        casos_por_municipio,
        left_on='municipio_normalizado_shp',
        right_on='municipio_normalizado',
        how='left'
    ).fillna(0)
    
    # Información sobre el merge
    municipios_con_datos = (municipios_con_casos['casos'] > 0).sum()
    st.info(f"📊 {municipios_con_datos} de {len(municipios)} municipios tienen casos registrados")
    
    # Debug: mostrar algunos nombres para comparación
    with st.expander("🔍 Debug: Nombres para comparación"):
        st.write("**Municipios en shapefile (primeros 5):**")
        st.write(list(municipios['municipio_normalizado_shp'].head()))
        st.write("**Municipios en datos de casos (primeros 5):**")
        st.write(list(casos_por_municipio['municipio_normalizado'].head()))
    
    # Crear mapa coroplético
    if municipios_con_datos > 0:
        create_choropleth_map(municipios_con_casos, 'casos', colors['danger'], 'Casos')
    else:
        st.warning("⚠️ No se pudieron vincular los casos con los municipios del shapefile")
        show_name_comparison(casos, municipios, 'municipio')


def create_epizootias_choropleth(epizootias, geo_data, colors):
    """
    Crea mapa coroplético de epizootias por municipio.
    """
    st.subheader("🐒 Epizootias por Municipio")
    
    if 'municipios' not in geo_data:
        st.error("No se pudo cargar el shapefile de municipios")
        return
    
    if epizootias.empty:
        st.info("No hay epizootias para mostrar en el mapa")
        return
    
    municipios = geo_data['municipios'].copy()
    
    # Contar epizootias por municipio
    epi_por_municipio = epizootias.groupby('municipio_normalizado').size().reset_index(name='epizootias')
    
    # Preparar datos igual que casos
    if 'MpNombre' in municipios.columns:
        municipios['municipio_normalizado_shp'] = municipios['MpNombre'].apply(normalize_for_merge)
    elif 'municipi_1' in municipios.columns:
        municipios['municipio_normalizado_shp'] = municipios['municipi_1']
    else:
        st.error("No se encontró columna de municipio en el shapefile")
        return
    
    # Merge
    municipios_con_epi = municipios.merge(
        epi_por_municipio,
        left_on='municipio_normalizado_shp',
        right_on='municipio_normalizado',
        how='left'
    ).fillna(0)
    
    # Crear mapa
    municipios_con_datos = (municipios_con_epi['epizootias'] > 0).sum()
    st.info(f"📊 {municipios_con_datos} de {len(municipios)} municipios tienen epizootias registradas")
    
    if municipios_con_datos > 0:
        create_choropleth_map(municipios_con_epi, 'epizootias', colors['warning'], 'Epizootias')
    else:
        st.warning("⚠️ No se pudieron vincular las epizootias con los municipios del shapefile")
        show_name_comparison(epizootias, municipios, 'municipio')


def create_veredas_map(casos, epizootias, geo_data, colors, filters):
    """
    Crea mapa detallado de veredas con columnas corregidas.
    """
    st.subheader("🏘️ Mapa Detallado de Veredas")
    
    if 'veredas' not in geo_data:
        st.error("No se pudo cargar el shapefile de veredas")
        return
    
    veredas = geo_data['veredas'].copy()
    
    # Filtrar por municipio si está seleccionado
    municipio_filtrado = filters.get("municipio_normalizado")
    if municipio_filtrado:
        # Usar la columna correcta para municipios en veredas
        if 'NOMB_MPIO' in veredas.columns:
            veredas['municipio_normalizado_shp'] = veredas['NOMB_MPIO'].apply(normalize_for_merge)
        elif 'municipi_1' in veredas.columns:
            veredas['municipio_normalizado_shp'] = veredas['municipi_1']
        else:
            st.error("No se encontró columna de municipio en veredas")
            return
            
        veredas_filtradas = veredas[veredas['municipio_normalizado_shp'] == municipio_filtrado]
        
        if len(veredas_filtradas) == 0:
            st.warning(f"No se encontraron veredas para {filters.get('municipio_display', 'el municipio seleccionado')}")
            return
        
        st.info(f"📍 Mostrando {len(veredas_filtradas)} veredas de {filters.get('municipio_display', 'municipio')}")
    else:
        veredas_filtradas = veredas
        st.info(f"📍 Mostrando todas las veredas del Tolima ({len(veredas_filtradas)} veredas)")
    
    # Crear mapa de veredas
    center_lat = veredas_filtradas.geometry.centroid.y.mean()
    center_lon = veredas_filtradas.geometry.centroid.x.mean()
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10 if municipio_filtrado else 8
    )
    
    # Agregar veredas (usar columnas originales)
    popup_fields = []
    tooltip_fields = []
    
    if 'NOMBRE_VER' in veredas_filtradas.columns:
        popup_fields.append('NOMBRE_VER')
        tooltip_fields.append('NOMBRE_VER')
    if 'NOMB_MPIO' in veredas_filtradas.columns:
        popup_fields.append('NOMB_MPIO')
    
    folium.GeoJson(
        veredas_filtradas,
        style_function=lambda x: {
            'fillColor': colors['info'],
            'color': 'white',
            'weight': 1,
            'fillOpacity': 0.5,
        },
        popup=folium.GeoJsonPopup(fields=popup_fields, aliases=['Vereda:', 'Municipio:'][:len(popup_fields)]),
        tooltip=folium.GeoJsonTooltip(fields=tooltip_fields, aliases=['Vereda:'][:len(tooltip_fields)])
    ).add_to(m)
    
    # Mostrar mapa
    st_folium(m, width=700, height=500)


def create_choropleth_map(gdf, value_column, color, label):
    """
    Crea un mapa coroplético genérico.
    """
    # Calcular centro
    center_lat = gdf.geometry.centroid.y.mean()
    center_lon = gdf.geometry.centroid.x.mean()
    
    # Crear mapa
    m = folium.Map(location=[center_lat, center_lon], zoom_start=8)
    
    # Determinar escala de colores
    max_value = gdf[value_column].max()
    
    if max_value > 0:
        # Usar el campo MpNombre para choropleth
        name_field = 'MpNombre' if 'MpNombre' in gdf.columns else 'MpCodigo'
        
        # Crear choropleth
        folium.Choropleth(
            geo_data=gdf,
            data=gdf,
            columns=[name_field, value_column],
            key_on=f'feature.properties.{name_field}',
            fill_color='Reds' if 'casos' in value_column.lower() else 'Oranges',
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name=f'{label} por Municipio'
        ).add_to(m)
        
        # Agregar tooltips
        folium.GeoJson(
            gdf,
            style_function=lambda x: {'fillOpacity': 0, 'color': 'transparent'},
            tooltip=folium.GeoJsonTooltip(
                fields=[name_field, value_column],
                aliases=['Municipio:', f'{label}:'],
                sticky=True
            )
        ).add_to(m)
    
    # Mostrar mapa
    st_folium(m, width=700, height=500)
    
    # Mostrar estadísticas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(f"Total {label}", int(gdf[value_column].sum()))
    with col2:
        st.metric(f"Máximo {label}", int(gdf[value_column].max()))
    with col3:
        municipios_afectados = (gdf[value_column] > 0).sum()
        st.metric("Municipios Afectados", municipios_afectados)


def normalize_for_merge(name):
    """
    Normaliza nombres para hacer merge con datos del dashboard.
    """
    from utils.data_processor import normalize_text
    return normalize_text(str(name)) if pd.notna(name) else ""


def show_name_comparison(data_df, geo_df, location_type):
    """
    Muestra comparación de nombres para debugging.
    """
    with st.expander(f"🔍 Comparación de Nombres de {location_type.title()}s"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Nombres en Dashboard ({location_type}s):**")
            if location_type == 'municipio':
                dashboard_names = sorted(data_df['municipio_normalizado'].unique()[:10])
            else:
                dashboard_names = sorted(data_df['vereda_normalizada'].unique()[:10])
            
            for name in dashboard_names:
                st.write(f"- {name}")
        
        with col2:
            st.write(f"**Nombres en Shapefile ({location_type}s):**")
            if location_type == 'municipio':
                if 'MpNombre' in geo_df.columns:
                    shp_names = sorted(geo_df['MpNombre'].unique()[:10])
                elif 'municipi_1' in geo_df.columns:
                    shp_names = sorted(geo_df['municipi_1'].unique()[:10])
                else:
                    shp_names = ["No encontrado"]
            else:
                if 'NOMBRE_VER' in geo_df.columns:
                    shp_names = sorted(geo_df['NOMBRE_VER'].unique()[:10])
                elif 'vereda_nor' in geo_df.columns:
                    shp_names = sorted(geo_df['vereda_nor'].unique()[:10])
                else:
                    shp_names = ["No encontrado"]
            
            for name in shp_names:
                st.write(f"- {name}")


def show_maps_not_available():
    """
    Muestra mensaje cuando las librerías de mapas no están disponibles.
    """
    st.markdown(
        f"""
    <div style="background-color: #fff3cd; padding: 20px; border-radius: 10px; border-left: 5px solid #ffc107; margin-bottom: 30px;">
        <h3 style="color: #856404; margin-top: 0;">⚠️ Librerías de Mapas No Instaladas</h3>
        <p>Para usar la funcionalidad de mapas, instale las dependencias necesarias:</p>
        <pre style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; font-family: monospace;">
pip install geopandas folium streamlit-folium
        </pre>
    </div>
    """,
        unsafe_allow_html=True,
    )


def show_shapefiles_setup_instructions():
    """
    Muestra instrucciones para configurar shapefiles.
    """
    st.markdown(
        f"""
    <div style="background-color: #d1ecf1; padding: 20px; border-radius: 10px; border-left: 5px solid #bee5eb; margin-bottom: 30px;">
        <h3 style="color: #0c5460; margin-top: 0;">🗺️ Configuración de Shapefiles</h3>
        <p>Para usar los mapas, ejecute primero el script de preparación:</p>
        <pre style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; font-family: monospace;">
python prepare_tolima_shapefiles.py
        </pre>
        <p>✅ Los shapefiles ya fueron procesados. Archivos esperados en:</p>
        <code>C:/Users/Miguel Santos/Desktop/Tolima-Veredas/processed/</code>
    </div>
    """,
        unsafe_allow_html=True,
    )


def show_geographic_data_error():
    """
    Muestra mensaje de error al cargar datos geográficos.
    """
    st.error("❌ Error al cargar datos geográficos")
    st.info("Verifique que los shapefiles procesados estén en la carpeta correcta")