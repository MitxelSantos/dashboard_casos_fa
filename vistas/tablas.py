"""
Vista de tablas detalladas del dashboard de Fiebre Amarilla.
Muestra datos completos de casos confirmados y epizootias en formato tabular.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io

def show(data_filtered, filters, colors):
    """
    Muestra la vista de tablas detalladas.
    
    Args:
        data_filtered (dict): Datos filtrados
        filters (dict): Filtros aplicados
        colors (dict): Colores institucionales
    """
    st.markdown(
        '<h1 style="color: #5A4214; border-bottom: 2px solid #F2A900; padding-bottom: 8px;">📋 Tablas Detalladas</h1>',
        unsafe_allow_html=True,
    )
    
    # Información general
    st.markdown(f"""
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid {colors['primary']}; margin-bottom: 30px;">
        <h3 style="color: {colors['primary']}; margin-top: 0;">Datos Detallados</h3>
        <p>Esta sección presenta los datos completos de casos confirmados y epizootias en formato tabular, 
        permitiendo la exploración detallada y exportación de la información.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Pestañas para casos y epizootias
    tab1, tab2, tab3 = st.tabs(["🦠 Casos Confirmados", "🐒 Epizootias", "📊 Resumen Ejecutivo"])
    
    with tab1:
        show_casos_table(data_filtered, filters, colors)
    
    with tab2:
        show_epizootias_table(data_filtered, filters, colors)
    
    with tab3:
        show_executive_summary(data_filtered, filters, colors)

def show_casos_table(data_filtered, filters, colors):
    """Muestra tabla detallada de casos confirmados."""
    casos = data_filtered["casos"]
    
    st.subheader("🦠 Casos Confirmados - Datos Detallados")
    
    if casos.empty:
        st.info("No hay casos confirmados que coincidan con los filtros seleccionados.")
        return
    
    # Métricas rápidas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Casos",
            value=len(casos),
            delta=None
        )
    
    with col2:
        if 'condicion_final' in casos.columns:
            fallecidos = (casos['condicion_final'] == 'Fallecido').sum()
            st.metric(
                label="Fallecidos", 
                value=fallecidos,
                delta=f"{fallecidos/len(casos)*100:.1f}% letalidad"
            )
        else:
            st.metric(label="Fallecidos", value="N/D")
    
    with col3:
        if 'municipio' in casos.columns:
            municipios_unicos = casos['municipio'].nunique()
            st.metric(
                label="Municipios",
                value=municipios_unicos
            )
        else:
            st.metric(label="Municipios", value="N/D")
    
    with col4:
        if 'edad' in casos.columns:
            edad_promedio = casos['edad'].mean()
            st.metric(
                label="Edad Promedio",
                value=f"{edad_promedio:.1f} años" if not pd.isna(edad_promedio) else "N/D"
            )
        else:
            st.metric(label="Edad Promedio", value="N/D")
    
    # Opciones de visualización
    st.subheader("⚙️ Opciones de Visualización")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Seleccionar columnas a mostrar
        available_columns = [col for col in casos.columns if not col.endswith('_normalizado')]
        default_columns = ['municipio', 'vereda', 'edad', 'sexo', 'eps', 'condicion_final', 'fecha_inicio_sintomas']
        default_columns = [col for col in default_columns if col in available_columns]
        
        selected_columns = st.multiselect(
            "Columnas a mostrar:",
            available_columns,
            default=default_columns,
            key="casos_columns"
        )
    
    with col2:
        # Orden de la tabla
        if selected_columns:
            sort_column = st.selectbox(
                "Ordenar por:",
                selected_columns,
                key="casos_sort"
            )
            
            sort_ascending = st.radio(
                "Orden:",
                ["Ascendente", "Descendente"],
                key="casos_order"
            ) == "Ascendente"
        else:
            sort_column = None
            sort_ascending = True
    
    with col3:
        # Filtros adicionales
        st.write("**Filtros adicionales:**")
        
        # Filtro por condición final
        if 'condicion_final' in casos.columns:
            condiciones_disponibles = ["Todas"] + list(casos['condicion_final'].dropna().unique())
            condicion_filter = st.selectbox(
                "Condición final:",
                condiciones_disponibles,
                key="casos_condicion_filter"
            )
        else:
            condicion_filter = "Todas"
        
        # Filtro por sexo
        if 'sexo' in casos.columns:
            sexos_disponibles = ["Todos"] + list(casos['sexo'].dropna().unique())
            sexo_filter = st.selectbox(
                "Sexo:",
                sexos_disponibles,
                key="casos_sexo_filter"
            )
        else:
            sexo_filter = "Todos"
    
    # Aplicar filtros adicionales
    casos_display = casos.copy()
    
    if condicion_filter != "Todas":
        casos_display = casos_display[casos_display['condicion_final'] == condicion_filter]
    
    if sexo_filter != "Todos":
        casos_display = casos_display[casos_display['sexo'] == sexo_filter]
    
    # Preparar datos para mostrar
    if selected_columns:
        casos_display = casos_display[selected_columns]
        
        # Ordenar si se especificó
        if sort_column and sort_column in casos_display.columns:
            casos_display = casos_display.sort_values(sort_column, ascending=sort_ascending)
    
    # Reemplazar valores faltantes
    casos_display = casos_display.fillna('No disponible')
    
    # Mostrar tabla
    st.subheader(f"📋 Tabla de Casos ({len(casos_display)} registros)")
    
    # Búsqueda en la tabla
    search_term = st.text_input(
        "🔍 Buscar en la tabla:",
        placeholder="Ingrese término de búsqueda...",
        key="casos_search"
    )
    
    if search_term:
        # Filtrar por término de búsqueda
        mask = casos_display.astype(str).apply(
            lambda x: x.str.contains(search_term, case=False, na=False)
        ).any(axis=1)
        casos_display = casos_display[mask]
        st.caption(f"Mostrando {len(casos_display)} resultados para '{search_term}'")
    
    # Mostrar la tabla con formateo
    st.dataframe(
        casos_display,
        use_container_width=True,
        hide_index=True
    )
    
    # Botones de exportación
    st.subheader("📥 Exportar Datos")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Exportar CSV
        csv_data = casos_display.to_csv(index=False)
        st.download_button(
            label="📄 Descargar CSV",
            data=csv_data,
            file_name=f"casos_confirmados_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            key="download_casos_csv"
        )
    
    with col2:
        # Exportar Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            casos_display.to_excel(writer, sheet_name='Casos_Confirmados', index=False)
        
        st.download_button(
            label="📊 Descargar Excel",
            data=buffer.getvalue(),
            file_name=f"casos_confirmados_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_casos_excel"
        )
    
    with col3:
        # Estadísticas rápidas
        if st.button("📈 Mostrar Estadísticas", key="casos_stats"):
            show_casos_statistics(casos_display, colors)

def show_epizootias_table(data_filtered, filters, colors):
    """Muestra tabla detallada de epizootias."""
    epizootias = data_filtered["epizootias"]
    
    st.subheader("🐒 Epizootias - Datos Detallados")
    
    if epizootias.empty:
        st.info("No hay epizootias que coincidan con los filtros seleccionados.")
        return
    
    # Métricas rápidas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Epizootias",
            value=len(epizootias)
        )
    
    with col2:
        if 'descripcion' in epizootias.columns:
            positivos = (epizootias['descripcion'] == 'POSITIVO FA').sum()
            st.metric(
                label="Positivos FA",
                value=positivos,
                delta=f"{positivos/len(epizootias)*100:.1f}% positividad"
            )
        else:
            st.metric(label="Positivos FA", value="N/D")
    
    with col3:
        if 'municipio' in epizootias.columns:
            municipios_unicos = epizootias['municipio'].nunique()
            st.metric(
                label="Municipios",
                value=municipios_unicos
            )
        else:
            st.metric(label="Municipios", value="N/D")
    
    with col4:
        if 'proveniente' in epizootias.columns:
            fuentes_unicas = epizootias['proveniente'].nunique()
            st.metric(
                label="Fuentes",
                value=fuentes_unicas
            )
        else:
            st.metric(label="Fuentes", value="N/D")
    
    # Opciones de visualización
    st.subheader("⚙️ Opciones de Visualización")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Seleccionar columnas a mostrar
        available_columns = [col for col in epizootias.columns if not col.endswith('_normalizado')]
        default_columns = ['municipio', 'vereda', 'fecha_recoleccion', 'proveniente', 'descripcion']
        default_columns = [col for col in default_columns if col in available_columns]
        
        selected_columns = st.multiselect(
            "Columnas a mostrar:",
            available_columns,
            default=default_columns,
            key="epi_columns"
        )
    
    with col2:
        # Orden de la tabla
        if selected_columns:
            sort_column = st.selectbox(
                "Ordenar por:",
                selected_columns,
                key="epi_sort"
            )
            
            sort_ascending = st.radio(
                "Orden:",
                ["Ascendente", "Descendente"],
                key="epi_order"
            ) == "Ascendente"
        else:
            sort_column = None
            sort_ascending = True
    
    with col3:
        # Filtros adicionales
        st.write("**Filtros adicionales:**")
        
        # Filtro por descripción
        if 'descripcion' in epizootias.columns:
            descripciones_disponibles = ["Todas"] + list(epizootias['descripcion'].dropna().unique())
            descripcion_filter = st.selectbox(
                "Resultado:",
                descripciones_disponibles,
                key="epi_descripcion_filter"
            )
        else:
            descripcion_filter = "Todas"
        
        # Filtro por fuente
        if 'proveniente' in epizootias.columns:
            fuentes_disponibles = ["Todas"] + list(epizootias['proveniente'].dropna().unique())
            fuente_filter = st.selectbox(
                "Fuente:",
                fuentes_disponibles,
                key="epi_fuente_filter"
            )
        else:
            fuente_filter = "Todas"
    
    # Aplicar filtros adicionales
    epizootias_display = epizootias.copy()
    
    if descripcion_filter != "Todas":
        epizootias_display = epizootias_display[epizootias_display['descripcion'] == descripcion_filter]
    
    if fuente_filter != "Todas":
        epizootias_display = epizootias_display[epizootias_display['proveniente'] == fuente_filter]
    
    # Preparar datos para mostrar
    if selected_columns:
        epizootias_display = epizootias_display[selected_columns]
        
        # Ordenar si se especificó
        if sort_column and sort_column in epizootias_display.columns:
            epizootias_display = epizootias_display.sort_values(sort_column, ascending=sort_ascending)
    
    # Reemplazar valores faltantes
    epizootias_display = epizootias_display.fillna('No disponible')
    
    # Mostrar tabla
    st.subheader(f"📋 Tabla de Epizootias ({len(epizootias_display)} registros)")
    
    # Búsqueda en la tabla
    search_term = st.text_input(
        "🔍 Buscar en la tabla:",
        placeholder="Ingrese término de búsqueda...",
        key="epi_search"
    )
    
    if search_term:
        # Filtrar por término de búsqueda
        mask = epizootias_display.astype(str).apply(
            lambda x: x.str.contains(search_term, case=False, na=False)
        ).any(axis=1)
        epizootias_display = epizootias_display[mask]
        st.caption(f"Mostrando {len(epizootias_display)} resultados para '{search_term}'")
    
    # Mostrar la tabla con formateo
    st.dataframe(
        epizootias_display,
        use_container_width=True,
        hide_index=True
    )
    
    # Botones de exportación
    st.subheader("📥 Exportar Datos")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Exportar CSV
        csv_data = epizootias_display.to_csv(index=False)
        st.download_button(
            label="📄 Descargar CSV",
            data=csv_data,
            file_name=f"epizootias_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            key="download_epi_csv"
        )
    
    with col2:
        # Exportar Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            epizootias_display.to_excel(writer, sheet_name='Epizootias', index=False)
        
        st.download_button(
            label="📊 Descargar Excel",
            data=buffer.getvalue(),
            file_name=f"epizootias_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_epi_excel"
        )
    
    with col3:
        # Estadísticas rápidas
        if st.button("📈 Mostrar Estadísticas", key="epi_stats"):
            show_epizootias_statistics(epizootias_display, colors)

def show_executive_summary(data_filtered, filters, colors):
    """Muestra resumen ejecutivo combinado."""
    st.subheader("📊 Resumen Ejecutivo")
    
    casos = data_filtered["casos"]
    epizootias = data_filtered["epizootias"]
    
    # Crear resumen combinado
    summary_data = []
    
    # Obtener municipios únicos
    municipios_casos = set(casos['municipio_normalizado'].dropna()) if 'municipio_normalizado' in casos.columns else set()
    municipios_epi = set(epizootias['municipio_normalizado'].dropna()) if 'municipio_normalizado' in epizootias.columns else set()
    todos_municipios = sorted(municipios_casos.union(municipios_epi))
    
    for municipio in todos_municipios:
        # Datos del municipio
        casos_mpio = casos[casos['municipio_normalizado'] == municipio] if 'municipio_normalizado' in casos.columns else pd.DataFrame()
        epi_mpio = epizootias[epizootias['municipio_normalizado'] == municipio] if 'municipio_normalizado' in epizootias.columns else pd.DataFrame()
        
        # Métricas
        total_casos = len(casos_mpio)
        total_epizootias = len(epi_mpio)
        
        fallecidos = 0
        if not casos_mpio.empty and 'condicion_final' in casos_mpio.columns:
            fallecidos = (casos_mpio['condicion_final'] == 'Fallecido').sum()
        
        positivos_fa = 0
        if not epi_mpio.empty and 'descripcion' in epi_mpio.columns:
            positivos_fa = (epi_mpio['descripcion'] == 'POSITIVO FA').sum()
        
        # Obtener nombre original del municipio para display
        municipio_display = municipio
        if not casos_mpio.empty and 'municipio' in casos_mpio.columns:
            municipio_display = casos_mpio['municipio'].iloc[0]
        elif not epi_mpio.empty and 'municipio' in epi_mpio.columns:
            municipio_display = epi_mpio['municipio'].iloc[0]
        
        summary_data.append({
            'Municipio': municipio_display,
            'Casos Confirmados': total_casos,
            'Fallecidos': fallecidos,
            'Letalidad (%)': round(fallecidos / total_casos * 100, 1) if total_casos > 0 else 0,
            'Total Epizootias': total_epizootias,
            'Positivos FA': positivos_fa,
            'Positividad (%)': round(positivos_fa / total_epizootias * 100, 1) if total_epizootias > 0 else 0,
            'Riesgo': 'Alto' if (total_casos > 5 or positivos_fa > 3) else 'Medio' if (total_casos > 0 or positivos_fa > 0) else 'Bajo'
        })
    
    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        summary_df = summary_df.sort_values('Casos Confirmados', ascending=False)
        
        # Mostrar tabla de resumen
        st.dataframe(
            summary_df.style.format({
                'Letalidad (%)': '{:.1f}%',
                'Positividad (%)': '{:.1f}%'
            }).background_gradient(
                subset=['Casos Confirmados', 'Total Epizootias'], 
                cmap='Reds'
            ),
            use_container_width=True,
            hide_index=True
        )
        
        # Gráficos de resumen
        col1, col2 = st.columns(2)
        
        with col1:
            # Top municipios por casos
            top_casos = summary_df.head(10)
            fig_casos = px.bar(
                top_casos,
                x='Casos Confirmados',
                y='Municipio',
                title='Top 10 Municipios por Casos Confirmados',
                color='Casos Confirmados',
                color_continuous_scale='Reds',
                orientation='h'
            )
            fig_casos.update_layout(height=400)
            st.plotly_chart(fig_casos, use_container_width=True)
        
        with col2:
            # Top municipios por epizootias
            top_epi = summary_df.nlargest(10, 'Total Epizootias')
            fig_epi = px.bar(
                top_epi,
                x='Total Epizootias',
                y='Municipio',
                title='Top 10 Municipios por Epizootias',
                color='Positivos FA',
                color_continuous_scale='Oranges',
                orientation='h'
            )
            fig_epi.update_layout(height=400)
            st.plotly_chart(fig_epi, use_container_width=True)
        
        # Exportar resumen
        st.subheader("📥 Exportar Resumen Ejecutivo")
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv_data = summary_df.to_csv(index=False)
            st.download_button(
                label="📄 Descargar Resumen CSV",
                data=csv_data,
                file_name=f"resumen_ejecutivo_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                key="download_summary_csv"
            )
        
        with col2:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                summary_df.to_excel(writer, sheet_name='Resumen_Ejecutivo', index=False)
            
            st.download_button(
                label="📊 Descargar Resumen Excel",
                data=buffer.getvalue(),
                file_name=f"resumen_ejecutivo_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_summary_excel"
            )
    else:
        st.info("No hay datos disponibles para generar el resumen ejecutivo.")

def show_casos_statistics(casos_display, colors):
    """Muestra estadísticas detalladas de casos."""
    if casos_display.empty:
        st.warning("No hay datos para mostrar estadísticas.")
        return
    
    st.subheader("📈 Estadísticas de Casos Confirmados")
    
    # Estadísticas por columnas numéricas
    numeric_columns = casos_display.select_dtypes(include=[np.number]).columns
    
    if len(numeric_columns) > 0:
        stats_df = casos_display[numeric_columns].describe()
        st.dataframe(stats_df, use_container_width=True)
    
    # Distribuciones por columnas categóricas
    categorical_columns = casos_display.select_dtypes(include=['object']).columns
    
    if len(categorical_columns) > 0:
        st.subheader("📊 Distribuciones")
        
        for col in categorical_columns[:5]:  # Limitar a 5 columnas
            if casos_display[col].nunique() <= 20:  # Solo mostrar si hay pocos valores únicos
                value_counts = casos_display[col].value_counts()
                st.write(f"**{col}:**")
                st.bar_chart(value_counts)

def show_epizootias_statistics(epizootias_display, colors):
    """Muestra estadísticas detalladas de epizootias."""
    if epizootias_display.empty:
        st.warning("No hay datos para mostrar estadísticas.")
        return
    
    st.subheader("📈 Estadísticas de Epizootias")
    
    # Estadísticas por columnas categóricas
    categorical_columns = epizootias_display.select_dtypes(include=['object']).columns
    
    if len(categorical_columns) > 0:
        st.subheader("📊 Distribuciones")
        
        for col in categorical_columns[:5]:  # Limitar a 5 columnas
            if epizootias_display[col].nunique() <= 20:  # Solo mostrar si hay pocos valores únicos
                value_counts = epizootias_display[col].value_counts()
                st.write(f"**{col}:**")
                st.bar_chart(value_counts)