"""
Vista de mapas del dashboard de Fiebre Amarilla.
PLACEHOLDER: Vista vacía preparada para futura implementación con shapefiles.
"""

import streamlit as st


def show(data_filtered, filters, colors):
    """
    Muestra la vista de mapas (placeholder).

    Args:
        data_filtered (dict): Datos filtrados
        filters (dict): Filtros aplicados
        colors (dict): Colores institucionales
    """
    st.markdown(
        '<h1 style="color: #5A4214; border-bottom: 2px solid #F2A900; padding-bottom: 8px;">🗺️ Mapas Geográficos</h1>',
        unsafe_allow_html=True,
    )

    # Información sobre desarrollo futuro
    st.markdown(
        f"""
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid {colors['info']}; margin-bottom: 30px;">
        <h3 style="color: {colors['info']}; margin-top: 0;">🚧 En Desarrollo</h3>
        <p>Esta sección está preparada para mostrar visualizaciones geográficas interactivas del departamento del Tolima.</p>
        <p><strong>Próximamente:</strong></p>
        <ul>
            <li>📍 Mapa del departamento del Tolima con división municipal</li>
            <li>🦠 Distribución geográfica de casos confirmados</li>
            <li>🐒 Ubicación de epizootias reportadas</li>
            <li>🔥 Mapas de calor por densidad de eventos</li>
            <li>📊 Análisis espacial interactivo</li>
        </ul>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Estadísticas geográficas básicas mientras se desarrolla
    casos = data_filtered["casos"]
    epizootias = data_filtered["epizootias"]

    if not casos.empty or not epizootias.empty:
        st.subheader("📊 Estadísticas Geográficas")

        col1, col2, col3 = st.columns(3)

        with col1:
            # Municipios con casos
            municipios_casos = 0
            if not casos.empty and "municipio_normalizado" in casos.columns:
                municipios_casos = casos["municipio_normalizado"].nunique()

            st.metric(
                label="🏛️ Municipios con Casos",
                value=municipios_casos,
                help="Número de municipios que reportan casos confirmados",
            )

        with col2:
            # Municipios con epizootias
            municipios_epi = 0
            if not epizootias.empty and "municipio_normalizado" in epizootias.columns:
                municipios_epi = epizootias["municipio_normalizado"].nunique()

            st.metric(
                label="🐒 Municipios con Epizootias",
                value=municipios_epi,
                help="Número de municipios que reportan epizootias",
            )

        with col3:
            # Veredas afectadas
            veredas_afectadas = set()
            if not casos.empty and "vereda_normalizada" in casos.columns:
                veredas_afectadas.update(casos["vereda_normalizada"].dropna())
            if not epizootias.empty and "vereda_normalizada" in epizootias.columns:
                veredas_afectadas.update(epizootias["vereda_normalizada"].dropna())

            st.metric(
                label="🏘️ Veredas Afectadas",
                value=len(veredas_afectadas),
                help="Número total de veredas con casos o epizootias",
            )

        # Lista de municipios afectados
        st.subheader("📋 Municipios Afectados")

        municipios_todos = set()
        if not casos.empty and "municipio" in casos.columns:
            municipios_todos.update(casos["municipio"].dropna())
        if not epizootias.empty and "municipio" in epizootias.columns:
            municipios_todos.update(epizootias["municipio"].dropna())

        if municipios_todos:
            municipios_lista = sorted(list(municipios_todos))

            # Mostrar en columnas para mejor organización
            num_cols = 3
            cols = st.columns(num_cols)

            for i, municipio in enumerate(municipios_lista):
                col_idx = i % num_cols
                with cols[col_idx]:
                    st.markdown(f"• **{municipio}**")
        else:
            st.info("No hay municipios con datos en los filtros actuales.")

    else:
        st.info(
            "No hay datos disponibles con los filtros actuales para mostrar estadísticas geográficas."
        )

    # Información técnica para desarrolladores
    with st.expander("🔧 Información Técnica (Desarrollo)"):
        st.markdown(
            """
            ### Especificaciones Técnicas Futuras
            
            **Datos Geográficos Requeridos:**
            - Shapefiles del departamento del Tolima
            - División política administrativa (municipios)
            - Coordenadas geográficas de veredas
            
            **Tecnologías a Implementar:**
            - `folium` para mapas interactivos
            - `geopandas` para manipulación de datos geoespaciales
            - `plotly` para mapas de calor y visualizaciones avanzadas
            
            **Funcionalidades Planificadas:**
            - Mapas base con OpenStreetMap o similar
            - Layers diferenciados para casos y epizootias
            - Clustering dinámico por zoom level
            - Popup con información detallada
            - Filtros geográficos interactivos
            - Exportación de mapas en diferentes formatos
            
            **Estructura de Datos Esperada:**
            - Coordenadas lat/lon por municipio y vereda
            - Geometrías poligonales para áreas administrativas
            - Metadatos geográficos adicionales
            """
        )

    # Mensaje motivacional
    st.markdown("---")
    st.markdown(
        f"""
        <div style="
            text-align: center; 
            padding: 20px; 
            background: linear-gradient(135deg, {colors['primary']} 0%, {colors['secondary']} 100%);
            color: white;
            border-radius: 10px;
            margin-top: 20px;
        ">
            <h4 style="margin: 0;">🚀 ¡Próximamente Mapas Interactivos!</h4>
            <p style="margin: 10px 0 0 0;">Visualizaciones geográficas avanzadas para mejor análisis epidemiológico.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
