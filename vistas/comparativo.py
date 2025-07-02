"""
Vista de análisis comparativo del dashboard de Fiebre Amarilla.
Muestra comparaciones y análisis cruzados entre casos confirmados y epizootias.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats

def show(data_filtered, filters, colors):
    """
    Muestra la vista de análisis comparativo.
    
    Args:
        data_filtered (dict): Datos filtrados
        filters (dict): Filtros aplicados
        colors (dict): Colores institucionales
    """
    st.markdown(
        '<h1 style="color: #5A4214; border-bottom: 2px solid #F2A900; padding-bottom: 8px;">📊 Análisis Comparativo</h1>',
        unsafe_allow_html=True,
    )
    
    # Información general
    st.markdown(f"""
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid {colors['primary']}; margin-bottom: 30px;">
        <h3 style="color: {colors['primary']}; margin-top: 0;">Análisis Cruzado</h3>
        <p>Esta sección presenta análisis comparativos entre casos confirmados y epizootias, 
        identificando patrones, correlaciones y relaciones epidemiológicas entre ambos tipos de eventos.</p>
        <p><strong>Objetivo:</strong> Comprender la dinámica de transmisión y los factores de riesgo 
        asociados con la fiebre amarilla en el territorio.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Pestañas para diferentes tipos de análisis
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔄 Comparación General", 
        "📍 Análisis Espacial", 
        "📈 Análisis Estadístico", 
        "🎯 Factores de Riesgo"
    ])
    
    with tab1:
        show_general_comparison(data_filtered, filters, colors)
    
    with tab2:
        show_spatial_analysis(data_filtered, filters, colors)
    
    with tab3:
        show_statistical_analysis(data_filtered, filters, colors)
    
    with tab4:
        show_risk_factors(data_filtered, filters, colors)

def show_general_comparison(data_filtered, filters, colors):
    """Muestra comparación general entre casos y epizootias."""
    st.subheader("🔄 Comparación General")
    
    casos = data_filtered["casos"]
    epizootias = data_filtered["epizootias"]
    
    # Métricas comparativas principales
    show_comparative_metrics(casos, epizootias, colors)
    
    # Comparación temporal básica
    st.subheader("📅 Distribución Temporal Comparativa")
    temporal_comparison = create_temporal_comparison(casos, epizootias)
    
    if not temporal_comparison.empty:
        # Gráfico de comparación temporal
        fig = create_temporal_comparison_chart(temporal_comparison, colors)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        
        # Tabla de resumen temporal
        show_temporal_summary_table(temporal_comparison)
    else:
        st.info("No hay suficientes datos temporales para la comparación.")
    
    # Distribución por resultados/condición
    st.subheader("🎯 Distribución por Resultados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribución de condición final en casos
        if not casos.empty and 'condicion_final' in casos.columns:
            condicion_dist = casos['condicion_final'].value_counts()
            
            fig = px.pie(
                values=condicion_dist.values,
                names=condicion_dist.index,
                title='Condición Final - Casos Confirmados',
                color_discrete_map={
                    'Vivo': colors['success'],
                    'Fallecido': colors['danger']
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de condición final disponibles.")
    
    with col2:
        # Distribución de resultados en epizootias
        if not epizootias.empty and 'descripcion' in epizootias.columns:
            resultado_dist = epizootias['descripcion'].value_counts()
            
            color_map = {
                'POSITIVO FA': colors['danger'],
                'NEGATIVO FA': colors['success'],
                'NO APTA': colors['warning'],
                'EN ESTUDIO': colors['info']
            }
            
            fig = px.pie(
                values=resultado_dist.values,
                names=resultado_dist.index,
                title='Resultados - Epizootias',
                color_discrete_map=color_map
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de resultados de epizootias disponibles.")
    
    # Análisis de co-ocurrencia por municipio
    show_municipality_cooccurrence(casos, epizootias, colors)

def show_spatial_analysis(data_filtered, filters, colors):
    """Muestra análisis espacial comparativo."""
    st.subheader("📍 Análisis Espacial Comparativo")
    
    casos = data_filtered["casos"]
    epizootias = data_filtered["epizootias"]
    
    # Crear datos espaciales combinados
    spatial_data = create_spatial_comparison_data(casos, epizootias)
    
    if spatial_data is None or (hasattr(spatial_data, 'empty') and spatial_data.empty):
        return pd.DataFrame()
    
    # Configuración del análisis
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.subheader("⚙️ Configuración")
        
        # Métrica espacial a analizar
        spatial_metric = st.selectbox(
            "Métrica a analizar:",
            ["Densidad de eventos", "Ratio casos/epizootias", "Índice de riesgo"],
            key="spatial_metric"
        )
        
        # Nivel de agregación
        aggregation_level = st.selectbox(
            "Nivel de agregación:",
            ["Municipio", "Vereda"],
            key="spatial_aggregation"
        )
        
        # Filtro de valores mínimos
        min_events = st.number_input(
            "Eventos mínimos:",
            min_value=0,
            max_value=20,
            value=1,
            key="spatial_min_events"
        )
    
    with col1:
        # Filtrar datos según configuración
        filtered_spatial = filter_spatial_data(spatial_data, aggregation_level, min_events)
        
        # Crear visualización espacial
        if not filtered_spatial.empty:
            fig = create_spatial_comparison_chart(filtered_spatial, spatial_metric, colors)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No hay datos suficientes con los filtros aplicados.")
    
    # Análisis de concentración espacial
    show_spatial_concentration_analysis(spatial_data, colors)
    
    # Tabla de análisis espacial
    show_spatial_analysis_table(spatial_data, aggregation_level)

def show_statistical_analysis(data_filtered, filters, colors):
    """Muestra análisis estadístico avanzado."""
    st.subheader("📈 Análisis Estadístico")
    
    casos = data_filtered["casos"]
    epizootias = data_filtered["epizootias"]
    
    # Crear dataset para análisis estadístico
    stats_data = create_statistical_dataset(casos, epizootias)
    
    if stats_data.empty:
        st.info("No hay suficientes datos para el análisis estadístico.")
        return
    
    # Análisis de correlación
    st.subheader("🔗 Análisis de Correlación")
    correlation_analysis = perform_correlation_analysis(stats_data)
    
    if correlation_analysis is not None and not correlation_analysis.empty:
        show_correlation_results(correlation_analysis, colors)
    
    # Análisis de distribución
    st.subheader("📊 Análisis de Distribuciones")
    
    # Configuración del análisis
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.subheader("⚙️ Configuración")
        
        # Variable a analizar
        available_vars = [col for col in stats_data.columns if stats_data[col].dtype in ['int64', 'float64']]
        
        if available_vars:
            selected_var = st.selectbox(
                "Variable a analizar:",
                available_vars,
                key="distribution_var"
            )
            
            # Tipo de análisis
            analysis_type = st.selectbox(
                "Tipo de análisis:",
                ["Histograma", "Box plot", "Violin plot"],
                key="distribution_type"
            )
            
            # Agrupar por
            group_vars = [col for col in stats_data.columns if stats_data[col].dtype == 'object']
            
            if group_vars:
                group_by = st.selectbox(
                    "Agrupar por:",
                    ["Ninguno"] + group_vars,
                    key="distribution_group"
                )
            else:
                group_by = "Ninguno"
        else:
            selected_var = None
            analysis_type = "Histograma"
            group_by = "Ninguno"
    
    with col1:
        if selected_var:
            # Crear gráfico de distribución
            fig = create_distribution_chart(stats_data, selected_var, analysis_type, group_by, colors)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay variables numéricas disponibles para el análisis.")
    
    # Test estadísticos
    if selected_var and group_by != "Ninguno":
        show_statistical_tests(stats_data, selected_var, group_by, colors)

def show_risk_factors(data_filtered, filters, colors):
    """Muestra análisis de factores de riesgo."""
    st.subheader("🎯 Análisis de Factores de Riesgo")
    
    casos = data_filtered["casos"]
    epizootias = data_filtered["epizootias"]
    
    # Crear análisis de riesgo por municipio
    risk_analysis = create_risk_analysis(casos, epizootias)
    
    if risk_analysis.empty:
        st.info("No hay suficientes datos para el análisis de riesgo.")
        return
    
    # Métricas de riesgo
    st.subheader("📊 Métricas de Riesgo por Municipio")
    
    # Configuración del análisis de riesgo
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.subheader("⚙️ Configuración")
        
        # Métrica de riesgo
        risk_metric = st.selectbox(
            "Métrica de riesgo:",
            ["Índice de riesgo combinado", "Tasa de letalidad", "Tasa de positividad epizootias", "Densidad de casos"],
            key="risk_metric"
        )
        
        # Número de municipios a mostrar
        top_n = st.slider(
            "Top municipios:",
            min_value=5,
            max_value=min(20, len(risk_analysis)),
            value=10,
            key="risk_top_n"
        )
        
        # Incluir solo municipios con casos
        only_with_cases = st.checkbox(
            "Solo municipios con casos",
            value=True,
            key="risk_only_cases"
        )
    
    with col1:
        # Filtrar y mostrar análisis de riesgo
        filtered_risk = filter_risk_analysis(risk_analysis, only_with_cases, top_n)
        
        if not filtered_risk.empty:
            fig = create_risk_analysis_chart(filtered_risk, risk_metric, colors)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No hay datos para mostrar con los filtros aplicados.")
    
    # Clasificación de riesgo
    show_risk_classification(risk_analysis, colors)
    
    # Factores asociados con alta letalidad
    if not casos.empty and 'condicion_final' in casos.columns:
        show_mortality_factors(casos, colors)
    
    # Recomendaciones basadas en riesgo
    show_risk_recommendations(risk_analysis, colors)

def show_comparative_metrics(casos, epizootias, colors):
    """Muestra métricas comparativas principales."""
    st.subheader("📊 Métricas Comparativas")
    
    # Calcular métricas
    total_casos = len(casos)
    total_epizootias = len(epizootias)
    
    fallecidos = 0
    if not casos.empty and 'condicion_final' in casos.columns:
        fallecidos = (casos['condicion_final'] == 'Fallecido').sum()
    
    positivos_fa = 0
    if not epizootias.empty and 'descripcion' in epizootias.columns:
        positivos_fa = (epizootias['descripcion'] == 'POSITIVO FA').sum()
    
    # Métricas derivadas
    letalidad = (fallecidos / total_casos * 100) if total_casos > 0 else 0
    positividad = (positivos_fa / total_epizootias * 100) if total_epizootias > 0 else 0
    ratio_epi_casos = total_epizootias / total_casos if total_casos > 0 else 0
    
    # Mostrar métricas en columnas
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric(
            label="🦠 Casos Confirmados",
            value=total_casos
        )
    
    with col2:
        st.metric(
            label="🐒 Epizootias",
            value=total_epizootias
        )
    
    with col3:
        st.metric(
            label="⚰️ Letalidad",
            value=f"{letalidad:.1f}%"
        )
    
    with col4:
        st.metric(
            label="🔴 Positividad",
            value=f"{positividad:.1f}%"
        )
    
    with col5:
        st.metric(
            label="📊 Ratio Epi/Casos",
            value=f"{ratio_epi_casos:.1f}"
        )
    
    with col6:
        # Índice de alerta (combinado)
        alert_index = calculate_alert_index(letalidad, positividad, ratio_epi_casos)
        st.metric(
            label="🚨 Índice de Alerta",
            value=f"{alert_index:.1f}"
        )

def create_temporal_comparison(casos, epizootias):
    """Crea datos para comparación temporal."""
    temporal_data = []
    
    # Procesar casos por mes
    if not casos.empty and 'fecha_inicio_sintomas' in casos.columns:
        casos_monthly = casos.groupby(casos['fecha_inicio_sintomas'].dt.to_period('M')).size()
        
        for period, count in casos_monthly.items():
            temporal_data.append({
                'periodo': period.to_timestamp(),
                'año': period.year,
                'mes': period.month,
                'casos': count,
                'epizootias': 0
            })
    
    # Procesar epizootias por mes
    if not epizootias.empty and 'fecha_recoleccion' in epizootias.columns:
        epi_monthly = epizootias.groupby(epizootias['fecha_recoleccion'].dt.to_period('M')).size()
        
        for period, count in epi_monthly.items():
            # Buscar si ya existe el período
            existing = next((item for item in temporal_data if item['periodo'] == period.to_timestamp()), None)
            if existing:
                existing['epizootias'] = count
            else:
                temporal_data.append({
                    'periodo': period.to_timestamp(),
                    'año': period.year,
                    'mes': period.month,
                    'casos': 0,
                    'epizootias': count
                })
    
    if temporal_data:
        df = pd.DataFrame(temporal_data)
        return df.sort_values('periodo')
    
    return pd.DataFrame()

def create_temporal_comparison_chart(temporal_data, colors):
    """Crea gráfico de comparación temporal."""
    if not temporal_data:
        return None
    
    # Crear gráfico con ejes duales
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Agregar casos
    fig.add_trace(
        go.Scatter(
            x=temporal_data['periodo'],
            y=temporal_data['casos'],
            mode='lines+markers',
            name='Casos Confirmados',
            line=dict(color=colors['danger'], width=3),
            marker=dict(size=8)
        ),
        secondary_y=False,
    )
    
    # Agregar epizootias
    fig.add_trace(
        go.Scatter(
            x=temporal_data['periodo'],
            y=temporal_data['epizootias'],
            mode='lines+markers',
            name='Epizootias',
            line=dict(color=colors['warning'], width=3),
            marker=dict(size=8)
        ),
        secondary_y=True,
    )
    
    # Configurar ejes
    fig.update_xaxes(title_text="Período")
    fig.update_yaxes(title_text="Casos Confirmados", secondary_y=False, color=colors['danger'])
    fig.update_yaxes(title_text="Epizootias", secondary_y=True, color=colors['warning'])
    
    # Configurar layout
    fig.update_layout(
        title_text="Evolución Temporal: Casos vs Epizootias",
        height=500,
        hovermode='x unified'
    )
    
    return fig

def show_temporal_summary_table(temporal_data):
    """Muestra tabla resumen temporal."""
    if not temporal_data:
        return
    
    # Crear resumen anual
    annual_summary = temporal_data.groupby('año').agg({
        'casos': 'sum',
        'epizootias': 'sum'
    }).reset_index()
    
    annual_summary['Total Eventos'] = annual_summary['casos'] + annual_summary['epizootias']
    annual_summary['Ratio Epi/Casos'] = (annual_summary['epizootias'] / annual_summary['casos']).round(2).fillna(0)
    
    st.subheader("📋 Resumen Anual")
    st.dataframe(
        annual_summary.rename(columns={
            'año': 'Año',
            'casos': 'Casos',
            'epizootias': 'Epizootias'
        }),
        use_container_width=True,
        hide_index=True
    )

def show_municipality_cooccurrence(casos, epizootias, colors):
    """Muestra análisis de co-ocurrencia por municipio."""
    st.subheader("🏘️ Co-ocurrencia por Municipio")
    
    # Crear datos de co-ocurrencia
    cooccurrence_data = create_cooccurrence_data(casos, epizootias)
    
    if cooccurrence_data.empty:
        st.info("No hay datos de co-ocurrencia disponibles.")
        return
    
    # Clasificar municipios
    municipios_casos_solo = cooccurrence_data[
        (cooccurrence_data['casos'] > 0) & (cooccurrence_data['epizootias'] == 0)
    ]
    municipios_epi_solo = cooccurrence_data[
        (cooccurrence_data['casos'] == 0) & (cooccurrence_data['epizootias'] > 0)
    ]
    municipios_ambos = cooccurrence_data[
        (cooccurrence_data['casos'] > 0) & (cooccurrence_data['epizootias'] > 0)
    ]
    
    # Mostrar estadísticas de co-ocurrencia
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="🦠 Solo Casos",
            value=len(municipios_casos_solo),
            help="Municipios con casos confirmados pero sin epizootias"
        )
    
    with col2:
        st.metric(
            label="🐒 Solo Epizootias",
            value=len(municipios_epi_solo),
            help="Municipios con epizootias pero sin casos confirmados"
        )
    
    with col3:
        st.metric(
            label="🔄 Ambos",
            value=len(municipios_ambos),
            help="Municipios con casos confirmados y epizootias"
        )
    
    # Gráfico de dispersión
    if not cooccurrence_data.empty:
        fig = px.scatter(
            cooccurrence_data,
            x='epizootias',
            y='casos',
            hover_name='municipio',
            title='Co-ocurrencia: Casos vs Epizootias por Municipio',
            color='casos',
            size='epizootias',
            color_continuous_scale='Reds'
        )
        
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

def create_cooccurrence_data(casos, epizootias):
    """Crea datos de co-ocurrencia por municipio."""
    cooccurrence_list = []
    
    # Obtener municipios únicos
    municipios_casos = set(casos['municipio_normalizado'].dropna()) if 'municipio_normalizado' in casos.columns else set()
    municipios_epi = set(epizootias['municipio_normalizado'].dropna()) if 'municipio_normalizado' in epizootias.columns else set()
    todos_municipios = municipios_casos.union(municipios_epi)
    
    for municipio in todos_municipios:
        # Contar casos y epizootias
        casos_count = 0
        if 'municipio_normalizado' in casos.columns:
            casos_count = (casos['municipio_normalizado'] == municipio).sum()
        
        epi_count = 0
        if 'municipio_normalizado' in epizootias.columns:
            epi_count = (epizootias['municipio_normalizado'] == municipio).sum()
        
        # Obtener nombre para display
        municipio_display = municipio
        if not casos.empty and 'municipio' in casos.columns:
            municipio_casos = casos[casos['municipio_normalizado'] == municipio]['municipio'].unique()
            if len(municipio_casos) > 0:
                municipio_display = municipio_casos[0]
        elif not epizootias.empty and 'municipio' in epizootias.columns:
            municipio_epi = epizootias[epizootias['municipio_normalizado'] == municipio]['municipio'].unique()
            if len(municipio_epi) > 0:
                municipio_display = municipio_epi[0]
        
        cooccurrence_list.append({
            'municipio': municipio_display,
            'municipio_normalizado': municipio,
            'casos': casos_count,
            'epizootias': epi_count
        })
    
    return pd.DataFrame(cooccurrence_list)

def create_spatial_comparison_data(casos, epizootias):
    """Crea datos para análisis espacial comparativo."""
    spatial_data = []
    
    # Obtener ubicaciones únicas (municipios y veredas)
    locations = get_unique_locations(casos, epizootias)
    
    for municipio in locations['municipios']:
        # Datos a nivel de municipio
        casos_mpio = casos[casos['municipio_normalizado'] == municipio] if 'municipio_normalizado' in casos.columns else pd.DataFrame()
        epi_mpio = epizootias[epizootias['municipio_normalizado'] == municipio] if 'municipio_normalizado' in epizootias.columns else pd.DataFrame()
        
        total_casos = len(casos_mpio)
        total_epi = len(epi_mpio)
        
        # Calcular métricas espaciales
        density_score = calculate_density_score(total_casos, total_epi)
        ratio_score = total_epi / total_casos if total_casos > 0 else 0
        risk_index = calculate_spatial_risk_index(total_casos, total_epi, casos_mpio, epi_mpio)
        
        spatial_data.append({
            'ubicacion': municipio,
            'tipo': 'Municipio',
            'casos': total_casos,
            'epizootias': total_epi,
            'densidad_eventos': density_score,
            'ratio_casos_epi': ratio_score,
            'indice_riesgo': risk_index
        })
        
        # Datos a nivel de vereda si hay suficientes datos
        if municipio in locations['veredas_por_municipio']:
            for vereda in locations['veredas_por_municipio'][municipio]:
                casos_vereda = casos_mpio[casos_mpio['vereda_normalizada'] == vereda] if 'vereda_normalizada' in casos_mpio.columns else pd.DataFrame()
                epi_vereda = epi_mpio[epi_mpio['vereda_normalizada'] == vereda] if 'vereda_normalizada' in epi_mpio.columns else pd.DataFrame()
                
                casos_v = len(casos_vereda)
                epi_v = len(epi_vereda)
                
                if casos_v > 0 or epi_v > 0:  # Solo incluir veredas con eventos
                    density_v = calculate_density_score(casos_v, epi_v)
                    ratio_v = epi_v / casos_v if casos_v > 0 else 0
                    risk_v = calculate_spatial_risk_index(casos_v, epi_v, casos_vereda, epi_vereda)
                    
                    spatial_data.append({
                        'ubicacion': f"{municipio} - {vereda}",
                        'tipo': 'Vereda',
                        'casos': casos_v,
                        'epizootias': epi_v,
                        'densidad_eventos': density_v,
                        'ratio_casos_epi': ratio_v,
                        'indice_riesgo': risk_v
                    })
    
    return pd.DataFrame(spatial_data)

def get_unique_locations(casos, epizootias):
    """Obtiene ubicaciones únicas de ambas fuentes."""
    locations = {
        'municipios': set(),
        'veredas_por_municipio': {}
    }
    
    # Municipios
    if 'municipio_normalizado' in casos.columns:
        locations['municipios'].update(casos['municipio_normalizado'].dropna().unique())
    if 'municipio_normalizado' in epizootias.columns:
        locations['municipios'].update(epizootias['municipio_normalizado'].dropna().unique())
    
    locations['municipios'] = sorted(list(locations['municipios']))
    
    # Veredas por municipio
    for municipio in locations['municipios']:
        veredas = set()
        
        if 'vereda_normalizada' in casos.columns:
            veredas_casos = casos[casos['municipio_normalizado'] == municipio]['vereda_normalizada'].dropna().unique()
            veredas.update(veredas_casos)
        
        if 'vereda_normalizada' in epizootias.columns:
            veredas_epi = epizootias[epizootias['municipio_normalizado'] == municipio]['vereda_normalizada'].dropna().unique()
            veredas.update(veredas_epi)
        
        locations['veredas_por_municipio'][municipio] = sorted(list(veredas))
    
    return locations

def calculate_density_score(casos, epizootias):
    """Calcula puntaje de densidad de eventos."""
    return casos + epizootias

def calculate_spatial_risk_index(casos, epizootias, casos_df, epi_df):
    """Calcula índice de riesgo espacial."""
    base_score = casos * 10 + epizootias * 5
    
    # Ajustar por letalidad si hay datos
    if not casos_df.empty and 'condicion_final' in casos_df.columns:
        fallecidos = (casos_df['condicion_final'] == 'Fallecido').sum()
        if casos > 0:
            letalidad_factor = (fallecidos / casos) * 50
            base_score += letalidad_factor
    
    # Ajustar por positividad de epizootias
    if not epi_df.empty and 'descripcion' in epi_df.columns:
        positivos = (epi_df['descripcion'] == 'POSITIVO FA').sum()
        if epizootias > 0:
            positividad_factor = (positivos / epizootias) * 30
            base_score += positividad_factor
    
    return min(base_score, 1000)  # Limitar a 1000

def filter_spatial_data(spatial_data, aggregation_level, min_events):
    """Filtra datos espaciales según configuración."""
    if spatial_data is None or (hasattr(spatial_data, 'empty') and spatial_data.empty):
        return pd.DataFrame()
    
    # Filtrar por nivel de agregación
    if aggregation_level == "Municipio":
        filtered = spatial_data[spatial_data['tipo'] == 'Municipio']
    else:
        filtered = spatial_data[spatial_data['tipo'] == 'Vereda']
    
    # Filtrar por eventos mínimos
    filtered = filtered[
        (filtered['casos'] + filtered['epizootias']) >= min_events
    ]
    
    return filtered

def create_spatial_comparison_chart(spatial_data, metric, colors):
    """Crea gráfico de comparación espacial."""
    if spatial_data is None or (hasattr(spatial_data, 'empty') and spatial_data.empty):
        return pd.DataFrame()
    
    metric_map = {
        "Densidad de eventos": "densidad_eventos",
        "Ratio casos/epizootias": "ratio_casos_epi", 
        "Índice de riesgo": "indice_riesgo"
    }
    
    y_column = metric_map.get(metric, "densidad_eventos")
    
    # Ordenar por la métrica seleccionada
    spatial_data_sorted = spatial_data.sort_values(y_column, ascending=True).tail(15)
    
    fig = px.bar(
        spatial_data_sorted,
        x=y_column,
        y='ubicacion',
        title=f'{metric} por Ubicación',
        color=y_column,
        color_continuous_scale='Reds',
        orientation='h'
    )
    
    fig.update_layout(
        height=500,
        yaxis={'categoryorder': 'total ascending'}
    )
    
    return fig

def show_spatial_concentration_analysis(spatial_data, colors):
    """Muestra análisis de concentración espacial."""
    if spatial_data is None or (hasattr(spatial_data, 'empty') and spatial_data.empty):
        return pd.DataFrame()
    
    st.subheader("🎯 Concentración Espacial")
    
    # Calcular índices de concentración
    municipios_data = spatial_data[spatial_data['tipo'] == 'Municipio']
    
    if not municipios_data.empty:
        # Concentración de casos
        total_casos = municipios_data['casos'].sum()
        top_5_casos = municipios_data.nlargest(5, 'casos')['casos'].sum()
        concentracion_casos = (top_5_casos / total_casos * 100) if total_casos > 0 else 0
        
        # Concentración de epizootias
        total_epi = municipios_data['epizootias'].sum()
        top_5_epi = municipios_data.nlargest(5, 'epizootias')['epizootias'].sum()
        concentracion_epi = (top_5_epi / total_epi * 100) if total_epi > 0 else 0
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                label="🦠 Concentración Casos (Top 5)",
                value=f"{concentracion_casos:.1f}%",
                help="Porcentaje de casos concentrados en los 5 municipios principales"
            )
        
        with col2:
            st.metric(
                label="🐒 Concentración Epizootias (Top 5)",
                value=f"{concentracion_epi:.1f}%",
                help="Porcentaje de epizootias concentradas en los 5 municipios principales"
            )

def show_spatial_analysis_table(spatial_data, aggregation_level):
    """Muestra tabla de análisis espacial."""
    if spatial_data is None or (hasattr(spatial_data, 'empty') and spatial_data.empty):
        return pd.DataFrame()
    
    st.subheader(f"📋 Tabla de Análisis - {aggregation_level}")
    
    # Filtrar por nivel de agregación
    table_data = spatial_data[spatial_data['tipo'] == aggregation_level].copy()
    
    if not table_data.empty:
        # Formatear datos para tabla
        table_data = table_data.round(2)
        table_data = table_data.rename(columns={
            'ubicacion': 'Ubicación',
            'casos': 'Casos',
            'epizootias': 'Epizootias',
            'densidad_eventos': 'Densidad',
            'ratio_casos_epi': 'Ratio',
            'indice_riesgo': 'Índice Riesgo'
        })
        
        # Ordenar por índice de riesgo
        table_data = table_data.sort_values('Índice Riesgo', ascending=False)
        
        st.dataframe(
            table_data[['Ubicación', 'Casos', 'Epizootias', 'Densidad', 'Ratio', 'Índice Riesgo']],
            use_container_width=True,
            hide_index=True
        )

def create_statistical_dataset(casos, epizootias):
    """Crea dataset para análisis estadístico."""
    # Crear datos agregados por municipio para análisis estadístico
    cooccurrence_data = create_cooccurrence_data(casos, epizootias)
    
    if cooccurrence_data.empty:
        return pd.DataFrame()
    
    # Agregar métricas adicionales
    enhanced_data = cooccurrence_data.copy()
    
    # Calcular métricas derivadas
    enhanced_data['total_eventos'] = enhanced_data['casos'] + enhanced_data['epizootias']
    enhanced_data['ratio_epi_casos'] = (enhanced_data['epizootias'] / enhanced_data['casos']).fillna(0)
    enhanced_data['tiene_casos'] = (enhanced_data['casos'] > 0).astype(int)
    enhanced_data['tiene_epizootias'] = (enhanced_data['epizootias'] > 0).astype(int)
    enhanced_data['tiene_ambos'] = ((enhanced_data['casos'] > 0) & (enhanced_data['epizootias'] > 0)).astype(int)
    
    # Calcular densidad logarítmica (para manejar valores de 0)
    enhanced_data['log_casos'] = np.log1p(enhanced_data['casos'])
    enhanced_data['log_epizootias'] = np.log1p(enhanced_data['epizootias'])
    
    return enhanced_data

def perform_correlation_analysis(stats_data):
    """Realiza análisis de correlación."""
    if stats_data.empty:
        return None
    
    # Seleccionar variables numéricas
    numeric_cols = stats_data.select_dtypes(include=[np.number]).columns
    
    if len(numeric_cols) < 2:
        return None
    
    # Calcular matriz de correlación
    correlation_matrix = stats_data[numeric_cols].corr()
    
    # Encontrar correlaciones más fuertes
    correlations = []
    for i in range(len(numeric_cols)):
        for j in range(i+1, len(numeric_cols)):
            var1 = numeric_cols[i]
            var2 = numeric_cols[j]
            corr_value = correlation_matrix.loc[var1, var2]
            
            if not np.isnan(corr_value):
                correlations.append({
                    'Variable 1': var1,
                    'Variable 2': var2,
                    'Correlación': corr_value,
                    'Fuerza': interpret_correlation_strength(corr_value),
                    'Significativo': abs(corr_value) > 0.3
                })
    
    correlations_df = pd.DataFrame(correlations)
    correlations_df = correlations_df.sort_values('Correlación', key=abs, ascending=False)
    
    return {
        'matrix': correlation_matrix,
        'correlations': correlations_df,
        'numeric_columns': numeric_cols
    }

def interpret_correlation_strength(corr_value):
    """Interpreta la fuerza de correlación."""
    abs_corr = abs(corr_value)
    
    if abs_corr >= 0.8:
        return "Muy fuerte"
    elif abs_corr >= 0.6:
        return "Fuerte"
    elif abs_corr >= 0.4:
        return "Moderada"
    elif abs_corr >= 0.2:
        return "Débil"
    else:
        return "Muy débil"

def show_correlation_results(correlation_analysis, colors):
    """Muestra resultados del análisis de correlación."""
    col1, col2 = st.columns(2)
    
    with col1:
        # Matriz de correlación
        fig = px.imshow(
            correlation_analysis['matrix'],
            title='Matriz de Correlación',
            color_continuous_scale='RdBu',
            aspect='auto'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Tabla de correlaciones significativas
        significant_corr = correlation_analysis['correlations'][
            correlation_analysis['correlations']['Significativo']
        ]
        
        if not significant_corr.empty:
            st.subheader("🔗 Correlaciones Significativas")
            st.dataframe(
                significant_corr[['Variable 1', 'Variable 2', 'Correlación', 'Fuerza']].round(3),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No se encontraron correlaciones significativas.")

def create_distribution_chart(stats_data, variable, chart_type, group_by, colors):
    """Crea gráfico de distribución."""
    if stats_data.empty or variable not in stats_data.columns:
        return None
    
    if chart_type == "Histograma":
        if group_by != "Ninguno" and group_by in stats_data.columns:
            fig = px.histogram(
                stats_data,
                x=variable,
                color=group_by,
                title=f'Distribución de {variable}',
                marginal='box'
            )
        else:
            fig = px.histogram(
                stats_data,
                x=variable,
                title=f'Distribución de {variable}',
                color_discrete_sequence=[colors['primary']]
            )
    
    elif chart_type == "Box plot":
        if group_by != "Ninguno" and group_by in stats_data.columns:
            fig = px.box(
                stats_data,
                y=variable,
                x=group_by,
                title=f'Box Plot de {variable} por {group_by}'
            )
        else:
            fig = px.box(
                stats_data,
                y=variable,
                title=f'Box Plot de {variable}'
            )
    
    elif chart_type == "Violin plot":
        if group_by != "Ninguno" and group_by in stats_data.columns:
            fig = px.violin(
                stats_data,
                y=variable,
                x=group_by,
                title=f'Violin Plot de {variable} por {group_by}'
            )
        else:
            fig = px.violin(
                stats_data,
                y=variable,
                title=f'Violin Plot de {variable}'
            )
    
    fig.update_layout(height=400)
    return fig

def show_statistical_tests(stats_data, variable, group_by, colors):
    """Muestra resultados de tests estadísticos."""
    st.subheader("🧪 Tests Estadísticos")
    
    # Agrupar datos
    groups = []
    group_names = []
    
    for group_value in stats_data[group_by].unique():
        if pd.notna(group_value):
            group_data = stats_data[stats_data[group_by] == group_value][variable].dropna()
            if len(group_data) > 0:
                groups.append(group_data)
                group_names.append(str(group_value))
    
    if len(groups) >= 2:
        # Test de normalidad (Shapiro-Wilk para muestras pequeñas)
        st.write("**Test de Normalidad (Shapiro-Wilk):**")
        
        for i, (group, name) in enumerate(zip(groups, group_names)):
            if len(group) >= 3 and len(group) <= 5000:  # Límites del test
                stat, p_value = stats.shapiro(group)
                is_normal = p_value > 0.05
                st.write(f"- {name}: p-value = {p_value:.4f} {'(Normal)' if is_normal else '(No normal)'}")
        
        # Test de diferencias entre grupos
        if len(groups) == 2:
            # Test t o Mann-Whitney U
            stat_t, p_t = stats.ttest_ind(groups[0], groups[1])
            stat_u, p_u = stats.mannwhitneyu(groups[0], groups[1], alternative='two-sided')
            
            st.write("**Tests de diferencias entre grupos:**")
            st.write(f"- Test t: p-value = {p_t:.4f}")
            st.write(f"- Mann-Whitney U: p-value = {p_u:.4f}")
            
            # Interpretación
            alpha = 0.05
            if p_t < alpha or p_u < alpha:
                st.success("✅ Existe diferencia significativa entre los grupos")
            else:
                st.info("ℹ️ No hay diferencia significativa entre los grupos")
        
        elif len(groups) > 2:
            # ANOVA o Kruskal-Wallis
            stat_f, p_f = stats.f_oneway(*groups)
            stat_kw, p_kw = stats.kruskal(*groups)
            
            st.write("**Tests de diferencias entre múltiples grupos:**")
            st.write(f"- ANOVA: p-value = {p_f:.4f}")
            st.write(f"- Kruskal-Wallis: p-value = {p_kw:.4f}")
            
            # Interpretación
            alpha = 0.05
            if p_f < alpha or p_kw < alpha:
                st.success("✅ Existe diferencia significativa entre los grupos")
            else:
                st.info("ℹ️ No hay diferencia significativa entre los grupos")

def calculate_alert_index(letalidad, positividad, ratio_epi_casos):
    """Calcula índice de alerta combinado."""
    # Normalizar métricas (0-100)
    letalidad_norm = min(letalidad, 100)
    positividad_norm = min(positividad, 100)
    ratio_norm = min(ratio_epi_casos * 10, 100)  # Escalado
    
    # Ponderación: letalidad 50%, positividad 30%, ratio 20%
    alert_index = (letalidad_norm * 0.5) + (positividad_norm * 0.3) + (ratio_norm * 0.2)
    
    return alert_index

def create_risk_analysis(casos, epizootias):
    """Crea análisis de riesgo por municipio."""
    risk_data = []
    
    # Obtener municipios únicos
    cooccurrence_data = create_cooccurrence_data(casos, epizootias)
    
    for _, row in cooccurrence_data.iterrows():
        municipio = row['municipio']
        municipio_norm = row['municipio_normalizado']
        total_casos = row['casos']
        total_epi = row['epizootias']
        
        # Filtrar datos por municipio
        casos_mpio = casos[casos['municipio_normalizado'] == municipio_norm] if 'municipio_normalizado' in casos.columns else pd.DataFrame()
        epi_mpio = epizootias[epizootias['municipio_normalizado'] == municipio_norm] if 'municipio_normalizado' in epizootias.columns else pd.DataFrame()
        
        # Calcular métricas de riesgo
        letalidad = 0
        if not casos_mpio.empty and 'condicion_final' in casos_mpio.columns and total_casos > 0:
            fallecidos = (casos_mpio['condicion_final'] == 'Fallecido').sum()
            letalidad = (fallecidos / total_casos) * 100
        
        positividad_epi = 0
        if not epi_mpio.empty and 'descripcion' in epi_mpio.columns and total_epi > 0:
            positivos = (epi_mpio['descripcion'] == 'POSITIVO FA').sum()
            positividad_epi = (positivos / total_epi) * 100
        
        densidad_casos = total_casos  # Podría normalizarse por población si estuviera disponible
        
        # Índice de riesgo combinado
        indice_riesgo = calculate_combined_risk_index(total_casos, total_epi, letalidad, positividad_epi)
        
        # Clasificación de riesgo
        if indice_riesgo >= 70:
            clasificacion = "Muy Alto"
        elif indice_riesgo >= 50:
            clasificacion = "Alto"
        elif indice_riesgo >= 30:
            clasificacion = "Medio"
        elif indice_riesgo >= 10:
            clasificacion = "Bajo"
        else:
            clasificacion = "Mínimo"
        
        risk_data.append({
            'municipio': municipio,
            'total_casos': total_casos,
            'total_epizootias': total_epi,
            'tasa_letalidad': letalidad,
            'tasa_positividad_epizootias': positividad_epi,
            'densidad_casos': densidad_casos,
            'indice_riesgo_combinado': indice_riesgo,
            'clasificacion_riesgo': clasificacion
        })
    
    return pd.DataFrame(risk_data)

def calculate_combined_risk_index(casos, epizootias, letalidad, positividad):
    """Calcula índice de riesgo combinado."""
    # Componentes del índice
    casos_score = min(casos * 5, 30)  # Máximo 30 puntos
    epi_score = min(epizootias * 2, 20)  # Máximo 20 puntos
    letalidad_score = min(letalidad * 0.5, 25)  # Máximo 25 puntos (50% letalidad)
    positividad_score = min(positividad * 0.25, 25)  # Máximo 25 puntos (100% positividad)
    
    total_score = casos_score + epi_score + letalidad_score + positividad_score
    
    return min(total_score, 100)

def filter_risk_analysis(risk_analysis, only_with_cases, top_n):
    """Filtra análisis de riesgo según configuración."""
    if risk_analysis.empty:
        return pd.DataFrame()
    
    filtered = risk_analysis.copy()
    
    if only_with_cases:
        filtered = filtered[filtered['total_casos'] > 0]
    
    # Tomar top N por índice de riesgo
    filtered = filtered.nlargest(top_n, 'indice_riesgo_combinado')
    
    return filtered

def create_risk_analysis_chart(risk_data, metric, colors):
    """Crea gráfico de análisis de riesgo."""
    if not risk_data:
        return None
    
    metric_map = {
        "Índice de riesgo combinado": "indice_riesgo_combinado",
        "Tasa de letalidad": "tasa_letalidad",
        "Tasa de positividad epizootias": "tasa_positividad_epizootias",
        "Densidad de casos": "densidad_casos"
    }
    
    y_column = metric_map.get(metric, "indice_riesgo_combinado")
    
    fig = px.bar(
        risk_data,
        x=y_column,
        y='municipio',
        title=f'{metric} por Municipio',
        color='clasificacion_riesgo',
        color_discrete_map={
            'Muy Alto': colors['danger'],
            'Alto': '#FF6B35',
            'Medio': colors['warning'],
            'Bajo': colors['info'],
            'Mínimo': colors['success']
        },
        orientation='h'
    )
    
    fig.update_layout(
        height=500,
        yaxis={'categoryorder': 'total ascending'}
    )
    
    return fig

def show_risk_classification(risk_analysis, colors):
    """Muestra clasificación de riesgo."""
    if risk_analysis.empty:
        return
    
    st.subheader("🎯 Clasificación de Riesgo")
    
    # Contar municipios por clasificación
    risk_counts = risk_analysis['clasificacion_riesgo'].value_counts()
    
    # Mostrar distribución
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Gráfico de distribución de riesgo
        fig = px.pie(
            values=risk_counts.values,
            names=risk_counts.index,
            title='Distribución de Municipios por Nivel de Riesgo',
            color_discrete_map={
                'Muy Alto': colors['danger'],
                'Alto': '#FF6B35',
                'Medio': colors['warning'],
                'Bajo': colors['info'],
                'Mínimo': colors['success']
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Tabla de conteos
        st.subheader("📊 Conteo por Nivel")
        risk_table = pd.DataFrame({
            'Nivel de Riesgo': risk_counts.index,
            'Cantidad': risk_counts.values,
            'Porcentaje': (risk_counts.values / risk_counts.sum() * 100).round(1)
        })
        
        st.dataframe(risk_table, use_container_width=True, hide_index=True)

def show_mortality_factors(casos, colors):
    """Muestra factores asociados con mortalidad."""
    st.subheader("⚰️ Factores de Mortalidad")
    
    if casos.empty or 'condicion_final' not in casos.columns:
        st.info("No hay datos de condición final disponibles.")
        return
    
    # Análisis por edad
    if 'edad' in casos.columns:
        mortality_by_age = casos.groupby('condicion_final')['edad'].agg(['mean', 'median', 'std']).round(1)
        
        st.write("**Estadísticas de edad por condición final:**")
        st.dataframe(mortality_by_age, use_container_width=True)
        
        # Gráfico de distribución de edad
        fig = px.box(
            casos,
            x='condicion_final',
            y='edad',
            title='Distribución de Edad por Condición Final',
            color='condicion_final',
            color_discrete_map={
                'Vivo': colors['success'],
                'Fallecido': colors['danger']
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Análisis por sexo
    if 'sexo' in casos.columns:
        mortality_by_sex = pd.crosstab(casos['sexo'], casos['condicion_final'], normalize='index') * 100
        
        st.write("**Tasa de mortalidad por sexo (%):**")
        st.dataframe(mortality_by_sex.round(1), use_container_width=True)

def show_risk_recommendations(risk_analysis, colors):
    """Muestra recomendaciones basadas en el análisis de riesgo."""
    if risk_analysis.empty:
        return
    
    st.subheader("💡 Recomendaciones")
    
    # Identificar municipios de alto riesgo
    alto_riesgo = risk_analysis[
        risk_analysis['clasificacion_riesgo'].isin(['Muy Alto', 'Alto'])
    ]
    
    if not alto_riesgo.empty:
        st.markdown(f"""
        <div style="background-color: #fff3cd; padding: 20px; border-radius: 10px; border-left: 5px solid {colors['warning']}; margin: 20px 0;">
            <h4 style="color: {colors['warning']}; margin-top: 0;">🚨 Municipios Prioritarios</h4>
            <p><strong>Municipios de alto/muy alto riesgo:</strong> {', '.join(alto_riesgo['municipio'].tolist())}</p>
            
            <h5>Recomendaciones específicas:</h5>
            <ul>
                <li><strong>Vigilancia reforzada:</strong> Implementar vigilancia epidemiológica intensiva</li>
                <li><strong>Campaña de vacunación:</strong> Priorizar campañas de vacunación antiamárílica</li>
                <li><strong>Control vectorial:</strong> Intensificar medidas de control de Aedes aegypti</li>
                <li><strong>Educación comunitaria:</strong> Programas de educación sobre prevención</li>
                <li><strong>Fortalecimiento diagnóstico:</strong> Mejorar capacidad diagnóstica local</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Recomendaciones generales
    st.markdown(f"""
    <div style="background-color: #d1ecf1; padding: 20px; border-radius: 10px; border-left: 5px solid {colors['info']}; margin: 20px 0;">
        <h4 style="color: {colors['info']}; margin-top: 0;">📋 Recomendaciones Generales</h4>
        
        <h5>🔍 Vigilancia epidemiológica:</h5>
        <ul>
            <li>Mantener vigilancia activa de epizootias como sistema de alerta temprana</li>
            <li>Fortalecer notificación inmediata de casos sospechosos</li>
            <li>Implementar vigilancia centinela en zonas de riesgo</li>
        </ul>
        
        <h5>🛡️ Prevención y control:</h5>
        <ul>
            <li>Mantener cobertura de vacunación ≥95% en zonas de riesgo</li>
            <li>Implementar control vectorial sostenible</li>
            <li>Educación continua a comunidades en riesgo</li>
        </ul>
        
        <h5>🏥 Atención médica:</h5>
        <ul>
            <li>Capacitar personal de salud en diagnóstico temprano</li>
            <li>Asegurar disponibilidad de pruebas diagnósticas</li>
            <li>Fortalecer red de referencia para casos graves</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)