"""
Vista de línea de tiempo del dashboard de Fiebre Amarilla.
Muestra evolución temporal de casos confirmados vs epizootias.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import calendar

def show(data_filtered, filters, colors):
    """
    Muestra la vista de línea de tiempo.
    
    Args:
        data_filtered (dict): Datos filtrados
        filters (dict): Filtros aplicados
        colors (dict): Colores institucionales
    """
    st.markdown(
        '<h1 style="color: #5A4214; border-bottom: 2px solid #F2A900; padding-bottom: 8px;">📈 Evolución Temporal</h1>',
        unsafe_allow_html=True,
    )
    
    # Información general
    st.markdown(f"""
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid {colors['primary']}; margin-bottom: 30px;">
        <h3 style="color: {colors['primary']}; margin-top: 0;">Análisis Temporal</h3>
        <p>Esta sección presenta la evolución temporal de casos confirmados y epizootias, permitiendo identificar 
        patrones estacionales, brotes y la relación temporal entre la presencia del virus en fauna silvestre y casos humanos.</p>
        <p><strong>Interpretación:</strong> Las epizootias pueden ser indicadores tempranos de circulación viral que 
        preceden a los casos humanos.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Pestañas para diferentes análisis temporales
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Timeline General", 
        "📅 Análisis por Periodos", 
        "🔄 Correlación Temporal", 
        "📈 Tendencias"
    ])
    
    with tab1:
        show_general_timeline(data_filtered, filters, colors)
    
    with tab2:
        show_period_analysis(data_filtered, filters, colors)
    
    with tab3:
        show_temporal_correlation(data_filtered, filters, colors)
    
    with tab4:
        show_trends_analysis(data_filtered, filters, colors)

def show_general_timeline(data_filtered, filters, colors):
    """Muestra timeline general combinando casos y epizootias."""
    st.subheader("📊 Línea de Tiempo General")
    
    casos = data_filtered["casos"]
    epizootias = data_filtered["epizootias"]
    
    # Crear datos de timeline
    timeline_data = create_timeline_data(casos, epizootias)
    
    if timeline_data.empty:
        st.info("No hay datos temporales disponibles para mostrar.")
        return
    
    # Controles de configuración
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        # Rango de fechas
        if not timeline_data.empty:
            min_date = timeline_data['fecha'].min().date()
            max_date = timeline_data['fecha'].max().date()
            
            date_range = st.date_input(
                "📅 Rango de fechas:",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key="timeline_date_range"
            )
        else:
            date_range = None
    
    with col2:
        # Agregación temporal
        aggregation = st.selectbox(
            "📊 Agregación:",
            ["Diario", "Semanal", "Mensual"],
            index=1,  # Default to semanal
            key="timeline_aggregation"
        )
    
    with col3:
        # Tipo de visualización
        chart_type = st.selectbox(
            "📈 Tipo de gráfico:",
            ["Líneas", "Barras", "Área"],
            key="timeline_chart_type"
        )
    
    # Filtrar datos por rango de fechas
    if date_range and len(date_range) == 2:
        start_date, end_date = date_range
        timeline_filtered = timeline_data[
            (timeline_data['fecha'].dt.date >= start_date) & 
            (timeline_data['fecha'].dt.date <= end_date)
        ]
    else:
        timeline_filtered = timeline_data
    
    # Agregar datos según configuración
    timeline_agg = aggregate_timeline_data(timeline_filtered, aggregation)
    
    if timeline_agg.empty:
        st.warning("No hay datos para el rango de fechas seleccionado.")
        return
    
    # Crear gráfico principal
    fig = create_timeline_chart(timeline_agg, chart_type, aggregation, colors)
    
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    
    # Mostrar eventos destacados
    show_timeline_highlights(timeline_filtered, colors)
    
    # Estadísticas del periodo
    show_period_statistics(timeline_agg, colors)

def show_period_analysis(data_filtered, filters, colors):
    """Muestra análisis detallado por periodos."""
    st.subheader("📅 Análisis por Periodos")
    
    casos = data_filtered["casos"]
    epizootias = data_filtered["epizootias"]
    
    # Crear datos temporales
    timeline_data = create_timeline_data(casos, epizootias)
    
    if timeline_data.empty:
        st.info("No hay datos temporales disponibles.")
        return
    
    # Análisis por año
    st.subheader("📊 Análisis Anual")
    yearly_analysis = create_yearly_analysis(timeline_data)
    
    if not yearly_analysis.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de casos por año
            fig_casos = px.bar(
                yearly_analysis,
                x='año',
                y='casos',
                title='Casos Confirmados por Año',
                color='casos',
                color_continuous_scale='Reds'
            )
            fig_casos.update_layout(height=400)
            st.plotly_chart(fig_casos, use_container_width=True)
        
        with col2:
            # Gráfico de epizootias por año
            fig_epi = px.bar(
                yearly_analysis,
                x='año',
                y='epizootias',
                title='Epizootias por Año',
                color='epizootias',
                color_continuous_scale='Oranges'
            )
            fig_epi.update_layout(height=400)
            st.plotly_chart(fig_epi, use_container_width=True)
        
        # Tabla de resumen anual
        st.subheader("📋 Resumen Anual")
        yearly_display = yearly_analysis.copy()
        yearly_display['Total Eventos'] = yearly_display['casos'] + yearly_display['epizootias']
        yearly_display = yearly_display.rename(columns={
            'año': 'Año',
            'casos': 'Casos',
            'epizootias': 'Epizootias'
        })
        
        st.dataframe(yearly_display, use_container_width=True, hide_index=True)
    
    # Análisis estacional
    st.subheader("🌀 Análisis Estacional")
    seasonal_analysis = create_seasonal_analysis(timeline_data)
    
    if not seasonal_analysis.empty:
        fig_seasonal = create_seasonal_chart(seasonal_analysis, colors)
        if fig_seasonal:
            st.plotly_chart(fig_seasonal, use_container_width=True)
        
        # Interpretación estacional
        show_seasonal_interpretation(seasonal_analysis, colors)

def show_temporal_correlation(data_filtered, filters, colors):
    """Muestra análisis de correlación temporal entre casos y epizootias."""
    st.subheader("🔄 Correlación Temporal")
    
    casos = data_filtered["casos"]
    epizootias = data_filtered["epizootias"]
    
    # Crear series temporales
    casos_ts, epi_ts = create_time_series(casos, epizootias)
    
    if casos_ts.empty and epi_ts.empty:
        st.info("No hay suficientes datos temporales para el análisis de correlación.")
        return
    
    # Combinar series temporales
    combined_ts = combine_time_series(casos_ts, epi_ts)
    
    if combined_ts.empty:
        st.warning("No se pudieron combinar las series temporales.")
        return
    
    # Análisis de correlación cruzada
    st.subheader("📊 Correlación Cruzada")
    
    # Configuración del análisis
    col1, col2 = st.columns([3, 1])
    
    with col2:
        # Configuraciones
        max_lag = st.slider(
            "Desfase máximo (días):",
            min_value=1,
            max_value=90,
            value=30,
            key="correlation_max_lag"
        )
        
        smoothing = st.checkbox(
            "Suavizar series",
            value=True,
            key="correlation_smoothing"
        )
        
        if smoothing:
            window_size = st.slider(
                "Ventana de suavizado:",
                min_value=3,
                max_value=21,
                value=7,
                key="correlation_window"
            )
        else:
            window_size = 1
    
    with col1:
        # Calcular y mostrar correlación cruzada
        cross_corr = calculate_cross_correlation(combined_ts, max_lag, window_size if smoothing else 1)
        
        if not cross_corr.empty:
            fig_corr = create_correlation_chart(cross_corr, colors)
            if fig_corr:
                st.plotly_chart(fig_corr, use_container_width=True)
        
        # Mostrar series temporales originales
        fig_ts = create_time_series_chart(combined_ts, colors, smoothing, window_size)
        if fig_ts:
            st.plotly_chart(fig_ts, use_container_width=True)
    
    # Interpretación de resultados
    show_correlation_interpretation(cross_corr, colors)

def show_trends_analysis(data_filtered, filters, colors):
    """Muestra análisis de tendencias y proyecciones."""
    st.subheader("📈 Análisis de Tendencias")
    
    casos = data_filtered["casos"]
    epizootias = data_filtered["epizootias"]
    
    # Crear datos mensuales para análisis de tendencias
    monthly_data = create_monthly_trends_data(casos, epizootias)
    
    if monthly_data is None or (hasattr(monthly_data, 'empty') and monthly_data.empty):
        st.info("No hay suficientes datos para el análisis de tendencias.")
        return
    
    # Análisis de tendencias
    col1, col2 = st.columns(2)
    
    with col1:
        # Tendencia de casos
        st.subheader("🦠 Tendencia de Casos")
        
        casos_trend = calculate_trend(monthly_data, 'casos')
        
        fig_casos_trend = px.scatter(
            monthly_data,
            x='fecha',
            y='casos',
            title='Tendencia de Casos Confirmados',
            # trendline='ols'  # Deshabilitado para evitar conflicto scipy/statsmodels,
            color_discrete_sequence=[colors['danger']]
        )
        
        # Agregar línea de tendencia manual si es necesario
        fig_casos_trend.update_layout(height=400)
        st.plotly_chart(fig_casos_trend, use_container_width=True)
        
        # Mostrar estadísticas de tendencia
        if casos_trend:
            show_trend_statistics("Casos", casos_trend, colors)
    
    with col2:
        # Tendencia de epizootias
        st.subheader("🐒 Tendencia de Epizootias")
        
        epi_trend = calculate_trend(monthly_data, 'epizootias')
        
        fig_epi_trend = px.scatter(
            monthly_data,
            x='fecha',
            y='epizootias',
            title='Tendencia de Epizootias',
            # trendline='ols'  # Deshabilitado para evitar conflicto scipy/statsmodels,
            color_discrete_sequence=[colors['warning']]
        )
        
        fig_epi_trend.update_layout(height=400)
        st.plotly_chart(fig_epi_trend, use_container_width=True)
        
        # Mostrar estadísticas de tendencia
        if epi_trend:
            show_trend_statistics("Epizootias", epi_trend, colors)
    
    # Análisis de ciclicidad
    st.subheader("🔄 Análisis de Patrones Cíclicos")
    cyclical_analysis = analyze_cyclical_patterns(monthly_data)
    
    if cyclical_analysis is not None and not cyclical_analysis.empty:
        show_cyclical_analysis(cyclical_analysis, colors)
    
    # Proyecciones simples
    show_simple_projections(monthly_data, colors)

def create_timeline_data(casos, epizootias):
    """Crea datos de timeline combinando casos y epizootias."""
    timeline_events = []
    
    # Agregar casos
    if not casos.empty and 'fecha_inicio_sintomas' in casos.columns:
        for _, row in casos.iterrows():
            if pd.notna(row['fecha_inicio_sintomas']):
                timeline_events.append({
                    'fecha': row['fecha_inicio_sintomas'],
                    'tipo': 'Caso Confirmado',
                    'municipio': row.get('municipio', 'N/D'),
                    'vereda': row.get('vereda', 'N/D'),
                    'condicion': row.get('condicion_final', 'N/D'),
                    'edad': row.get('edad', 'N/D'),
                    'sexo': row.get('sexo', 'N/D'),
                    'cantidad': 1
                })
    
    # Agregar epizootias
    if not epizootias.empty and 'fecha_recoleccion' in epizootias.columns:
        for _, row in epizootias.iterrows():
            if pd.notna(row['fecha_recoleccion']):
                timeline_events.append({
                    'fecha': row['fecha_recoleccion'],
                    'tipo': 'Epizootia',
                    'municipio': row.get('municipio', 'N/D'),
                    'vereda': row.get('vereda', 'N/D'),
                    'resultado': row.get('descripcion', 'N/D'),
                    'fuente': row.get('proveniente', 'N/D'),
                    'cantidad': 1
                })
    
    if timeline_events:
        df = pd.DataFrame(timeline_events)
        df['fecha'] = pd.to_datetime(df['fecha'])
        return df.sort_values('fecha')
    
    return pd.DataFrame()

def aggregate_timeline_data(timeline_data, aggregation):
    """Agrega datos de timeline según el periodo especificado."""
    if timeline_data.empty:
        return pd.DataFrame()
    
    # Definir frecuencia de agregación
    freq_map = {
        'Diario': 'D',
        'Semanal': 'W',
        'Mensual': 'MS'
    }
    
    freq = freq_map.get(aggregation, 'W')
    
    # Agrupar por fecha y tipo
    timeline_data['fecha_periodo'] = timeline_data['fecha'].dt.to_period(freq).dt.to_timestamp()
    
    agg_data = timeline_data.groupby(['fecha_periodo', 'tipo']).agg({
        'cantidad': 'sum',
        'municipio': 'nunique'
    }).reset_index()
    
    agg_data.columns = ['fecha', 'tipo', 'cantidad', 'municipios_afectados']
    
    return agg_data

def create_timeline_chart(timeline_agg, chart_type, aggregation, colors):
    """Crea gráfico de timeline según configuración."""
    if timeline_agg.empty:
        return None
    
    # Pivotar datos para gráfico
    pivot_data = timeline_agg.pivot(index='fecha', columns='tipo', values='cantidad').fillna(0)
    pivot_data = pivot_data.reset_index()
    
    title = f"Evolución Temporal ({aggregation})"
    
    if chart_type == "Líneas":
        fig = go.Figure()
        
        if 'Caso Confirmado' in pivot_data.columns:
            fig.add_trace(go.Scatter(
                x=pivot_data['fecha'],
                y=pivot_data['Caso Confirmado'],
                mode='lines+markers',
                name='Casos Confirmados',
                line=dict(color=colors['danger'], width=3),
                marker=dict(size=6)
            ))
        
        if 'Epizootia' in pivot_data.columns:
            fig.add_trace(go.Scatter(
                x=pivot_data['fecha'],
                y=pivot_data['Epizootia'],
                mode='lines+markers',
                name='Epizootias',
                line=dict(color=colors['warning'], width=3),
                marker=dict(size=6),
                yaxis='y2'
            ))
        
        # Configurar ejes duales
        fig.update_layout(
            title=title,
            xaxis_title='Fecha',
            yaxis=dict(title='Casos Confirmados', side='left', color=colors['danger']),
            yaxis2=dict(title='Epizootias', side='right', overlaying='y', color=colors['warning']),
            height=500,
            hovermode='x unified'
        )
    
    elif chart_type == "Barras":
        # Reestructurar datos para barras agrupadas
        melted_data = pivot_data.melt(id_vars=['fecha'], var_name='tipo', value_name='cantidad')
        
        fig = px.bar(
            melted_data,
            x='fecha',
            y='cantidad',
            color='tipo',
            title=title,
            color_discrete_map={
                'Caso Confirmado': colors['danger'],
                'Epizootia': colors['warning']
            },
            barmode='group'
        )
        fig.update_layout(height=500)
    
    elif chart_type == "Área":
        fig = go.Figure()
        
        if 'Caso Confirmado' in pivot_data.columns:
            fig.add_trace(go.Scatter(
                x=pivot_data['fecha'],
                y=pivot_data['Caso Confirmado'],
                fill='tonexty' if 'Epizootia' in pivot_data.columns else 'tozeroy',
                mode='lines',
                name='Casos Confirmados',
                line=dict(color=colors['danger'])
            ))
        
        if 'Epizootia' in pivot_data.columns:
            fig.add_trace(go.Scatter(
                x=pivot_data['fecha'],
                y=pivot_data['Epizootia'],
                fill='tozeroy',
                mode='lines',
                name='Epizootias',
                line=dict(color=colors['warning'])
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title='Fecha',
            yaxis_title='Cantidad',
            height=500
        )
    
    return fig

def create_yearly_analysis(timeline_data):
    """Crea análisis anual de los datos."""
    if timeline_data.empty:
        return pd.DataFrame()
    
    timeline_data['año'] = timeline_data['fecha'].dt.year
    
    yearly_summary = timeline_data.groupby(['año', 'tipo']).agg({
        'cantidad': 'sum'
    }).reset_index()
    
    # Pivotar para tener casos y epizootias como columnas
    yearly_pivot = yearly_summary.pivot(index='año', columns='tipo', values='cantidad').fillna(0)
    yearly_pivot = yearly_pivot.reset_index()
    
    # Renombrar columnas
    column_map = {
        'Caso Confirmado': 'casos',
        'Epizootia': 'epizootias'
    }
    
    for old_name, new_name in column_map.items():
        if old_name in yearly_pivot.columns:
            yearly_pivot = yearly_pivot.rename(columns={old_name: new_name})
        elif new_name not in yearly_pivot.columns:
            yearly_pivot[new_name] = 0
    
    return yearly_pivot

def create_seasonal_analysis(timeline_data):
    """Crea análisis estacional de los datos."""
    if timeline_data.empty:
        return pd.DataFrame()
    
    timeline_data['mes'] = timeline_data['fecha'].dt.month
    timeline_data['nombre_mes'] = timeline_data['fecha'].dt.month_name()
    
    seasonal_summary = timeline_data.groupby(['mes', 'nombre_mes', 'tipo']).agg({
        'cantidad': 'sum'
    }).reset_index()
    
    return seasonal_summary

def create_seasonal_chart(seasonal_data, colors):
    """Crea gráfico estacional."""
    if seasonal_data.empty:
        return None
    
    # Crear gráfico polar para mostrar estacionalidad
    fig = go.Figure()
    
    # Agrupar por tipo
    for tipo in seasonal_data['tipo'].unique():
        tipo_data = seasonal_data[seasonal_data['tipo'] == tipo]
        
        color = colors['danger'] if tipo == 'Caso Confirmado' else colors['warning']
        
        fig.add_trace(go.Scatterpolar(
            r=tipo_data['cantidad'],
            theta=tipo_data['nombre_mes'],
            mode='lines+markers',
            name=tipo,
            line=dict(color=color),
            marker=dict(size=8)
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True),
            angularaxis=dict(direction="clockwise", period=12)
        ),
        title="Distribución Estacional",
        height=500
    )
    
    return fig

def show_seasonal_interpretation(seasonal_data, colors):
    """Muestra interpretación del análisis estacional."""
    st.subheader("🔍 Interpretación Estacional")
    
    # Encontrar picos estacionales
    casos_data = seasonal_data[seasonal_data['tipo'] == 'Caso Confirmado']
    epi_data = seasonal_data[seasonal_data['tipo'] == 'Epizootia']
    
    interpretations = []
    
    if not casos_data.empty:
        peak_month_casos = casos_data.loc[casos_data['cantidad'].idxmax(), 'nombre_mes']
        interpretations.append(f"📍 **Pico de casos:** {peak_month_casos}")
    
    if not epi_data.empty:
        peak_month_epi = epi_data.loc[epi_data['cantidad'].idxmax(), 'nombre_mes']
        interpretations.append(f"📍 **Pico de epizootias:** {peak_month_epi}")
    
    if interpretations:
        for interp in interpretations:
            st.markdown(interp)
        
        st.markdown(f"""
        <div style="background-color: #f0f8ff; padding: 15px; border-radius: 5px; border-left: 5px solid {colors['info']}; margin: 15px 0;">
            <p><strong>💡 Consideraciones epidemiológicas:</strong></p>
            <ul>
                <li>Los patrones estacionales pueden relacionarse con factores climáticos y ecológicos</li>
                <li>Las epizootias pueden preceder a los casos humanos en algunas semanas</li>
                <li>La variabilidad estacional ayuda a planificar estrategias de prevención</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

def create_time_series(casos, epizootias):
    """Crea series temporales diarias para análisis de correlación."""
    casos_ts = pd.DataFrame()
    epi_ts = pd.DataFrame()
    
    # Serie temporal de casos
    if not casos.empty and 'fecha_inicio_sintomas' in casos.columns:
        casos_daily = casos.groupby(casos['fecha_inicio_sintomas'].dt.date).size()
        casos_ts = pd.DataFrame({
            'fecha': pd.to_datetime(casos_daily.index),
            'casos': casos_daily.values
        })
    
    # Serie temporal de epizootias
    if not epizootias.empty and 'fecha_recoleccion' in epizootias.columns:
        epi_daily = epizootias.groupby(epizootias['fecha_recoleccion'].dt.date).size()
        epi_ts = pd.DataFrame({
            'fecha': pd.to_datetime(epi_daily.index),
            'epizootias': epi_daily.values
        })
    
    return casos_ts, epi_ts

def combine_time_series(casos_ts, epi_ts):
    """Combina series temporales en un solo DataFrame."""
    if casos_ts.empty and epi_ts.empty:
        return pd.DataFrame()
    
    # Crear rango de fechas completo
    if not casos_ts.empty and not epi_ts.empty:
        min_date = min(casos_ts['fecha'].min(), epi_ts['fecha'].min())
        max_date = max(casos_ts['fecha'].max(), epi_ts['fecha'].max())
    elif not casos_ts.empty:
        min_date = casos_ts['fecha'].min()
        max_date = casos_ts['fecha'].max()
    else:
        min_date = epi_ts['fecha'].min()
        max_date = epi_ts['fecha'].max()
    
    # Crear DataFrame con todas las fechas
    date_range = pd.date_range(start=min_date, end=max_date, freq='D')
    combined = pd.DataFrame({'fecha': date_range})
    
    # Merge con ambas series
    if not casos_ts.empty:
        combined = combined.merge(casos_ts, on='fecha', how='left')
    else:
        combined['casos'] = 0
    
    if not epi_ts.empty:
        combined = combined.merge(epi_ts, on='fecha', how='left')
    else:
        combined['epizootias'] = 0
    
    # Rellenar valores faltantes con 0
    combined = combined.fillna(0)
    
    return combined

def calculate_cross_correlation(combined_ts, max_lag, window_size):
    """Calcula correlación cruzada entre series temporales."""
    if combined_ts.empty or len(combined_ts) < max_lag * 2:
        return pd.DataFrame()
    
    # Suavizar series si se especifica
    casos_series = combined_ts['casos']
    epi_series = combined_ts['epizootias']
    
    if window_size > 1:
        casos_series = casos_series.rolling(window=window_size, center=True).mean()
        epi_series = epi_series.rolling(window=window_size, center=True).mean()
    
    # Calcular correlación cruzada
    correlations = []
    
    for lag in range(-max_lag, max_lag + 1):
        if lag < 0:
            # Epizootias adelantadas
            corr = casos_series.corr(epi_series.shift(-lag))
        else:
            # Casos adelantados
            corr = casos_series.shift(lag).corr(epi_series)
        
        correlations.append({
            'lag': lag,
            'correlation': corr,
            'interpretation': 'Epizootias preceden' if lag < 0 else ('Simultáneo' if lag == 0 else 'Casos preceden')
        })
    
    return pd.DataFrame(correlations).dropna()

def create_correlation_chart(cross_corr, colors):
    """Crea gráfico de correlación cruzada."""
    if cross_corr.empty:
        return None
    
    fig = px.bar(
        cross_corr,
        x='lag',
        y='correlation',
        title='Correlación Cruzada: Casos vs Epizootias',
        color='correlation',
        color_continuous_scale='RdBu',
        color_continuous_midpoint=0
    )
    
    fig.update_layout(
        xaxis_title='Desfase (días)',
        yaxis_title='Correlación',
        height=400
    )
    
    # Agregar línea horizontal en y=0
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    
    return fig

def create_time_series_chart(combined_ts, colors, smoothing, window_size):
    """Crea gráfico de series temporales."""
    if combined_ts.empty:
        return None
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Casos Confirmados', 'Epizootias'),
        vertical_spacing=0.1
    )
    
    # Serie de casos
    casos_data = combined_ts['casos']
    if smoothing and window_size > 1:
        casos_smooth = casos_data.rolling(window=window_size, center=True).mean()
        fig.add_trace(
            go.Scatter(x=combined_ts['fecha'], y=casos_smooth, name='Casos (suavizado)', 
                      line=dict(color=colors['danger'])),
            row=1, col=1
        )
    else:
        fig.add_trace(
            go.Scatter(x=combined_ts['fecha'], y=casos_data, name='Casos', 
                      line=dict(color=colors['danger'])),
            row=1, col=1
        )
    
    # Serie de epizootias
    epi_data = combined_ts['epizootias']
    if smoothing and window_size > 1:
        epi_smooth = epi_data.rolling(window=window_size, center=True).mean()
        fig.add_trace(
            go.Scatter(x=combined_ts['fecha'], y=epi_smooth, name='Epizootias (suavizado)', 
                      line=dict(color=colors['warning'])),
            row=2, col=1
        )
    else:
        fig.add_trace(
            go.Scatter(x=combined_ts['fecha'], y=epi_data, name='Epizootias', 
                      line=dict(color=colors['warning'])),
            row=2, col=1
        )
    
    fig.update_layout(height=600, title_text="Series Temporales")
    
    return fig

def show_correlation_interpretation(cross_corr, colors):
    """Muestra interpretación de la correlación cruzada."""
    if cross_corr.empty:
        return
    
    st.subheader("🔍 Interpretación de Correlación")
    
    # Encontrar correlación máxima
    max_corr_row = cross_corr.loc[cross_corr['correlation'].abs().idxmax()]
    max_corr = max_corr_row['correlation']
    max_lag = max_corr_row['lag']
    
    # Interpretación
    interpretation_text = ""
    
    if abs(max_corr) < 0.3:
        strength = "débil"
        color = colors['info']
    elif abs(max_corr) < 0.6:
        strength = "moderada"
        color = colors['warning']
    else:
        strength = "fuerte"
        color = colors['danger']
    
    if max_lag < 0:
        timing = f"Las epizootias preceden a los casos por {abs(max_lag)} días"
    elif max_lag > 0:
        timing = f"Los casos preceden a las epizootias por {max_lag} días"
    else:
        timing = "Los eventos ocurren simultáneamente"
    
    interpretation_text = f"""
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid {color}; margin: 20px 0;">
        <h4 style="color: {color}; margin-top: 0;">Resultado del Análisis</h4>
        <p><strong>Correlación máxima:</strong> {max_corr:.3f} (correlación {strength})</p>
        <p><strong>Desfase temporal:</strong> {timing}</p>
        <p><strong>Implicación epidemiológica:</strong> {get_epidemiological_implication(max_lag, max_corr)}</p>
    </div>
    """
    
    st.markdown(interpretation_text, unsafe_allow_html=True)

def get_epidemiological_implication(lag, correlation):
    """Obtiene implicación epidemiológica de la correlación."""
    if abs(correlation) < 0.3:
        return "La relación temporal entre epizootias y casos humanos es débil o no concluyente."
    
    if lag < -7:
        return "Las epizootias pueden servir como sistema de alerta temprana para casos humanos."
    elif lag > 7:
        return "Los casos humanos pueden estar asociados con detección posterior de epizootias."
    else:
        return "Existe una relación temporal cercana entre epizootias y casos humanos."

def create_monthly_trends_data(casos, epizootias):
    """Crea datos mensuales para análisis de tendencias."""
    monthly_data = []
    
    # Obtener rango de fechas
    all_dates = []
    
    if not casos.empty and 'fecha_inicio_sintomas' in casos.columns:
        all_dates.extend(casos['fecha_inicio_sintomas'].dropna().tolist())
    
    if not epizootias.empty and 'fecha_recoleccion' in epizootias.columns:
        all_dates.extend(epizootias['fecha_recoleccion'].dropna().tolist())
    
    if not all_dates:
        return pd.DataFrame()
    
    min_date = min(all_dates)
    max_date = max(all_dates)
    
    # Crear rango mensual
    monthly_range = pd.date_range(start=min_date.replace(day=1), end=max_date, freq='MS')
    
    for month_start in monthly_range:
        month_end = (month_start + pd.DateOffset(months=1)) - pd.DateOffset(days=1)
        
        # Contar casos en el mes
        casos_mes = 0
        if not casos.empty and 'fecha_inicio_sintomas' in casos.columns:
            casos_mes = casos[
                (casos['fecha_inicio_sintomas'] >= month_start) & 
                (casos['fecha_inicio_sintomas'] <= month_end)
            ].shape[0]
        
        # Contar epizootias en el mes
        epi_mes = 0
        if not epizootias.empty and 'fecha_recoleccion' in epizootias.columns:
            epi_mes = epizootias[
                (epizootias['fecha_recoleccion'] >= month_start) & 
                (epizootias['fecha_recoleccion'] <= month_end)
            ].shape[0]
        
        monthly_data.append({
            'fecha': month_start,
            'casos': casos_mes,
            'epizootias': epi_mes,
            'año': month_start.year,
            'mes': month_start.month
        })
    
    return pd.DataFrame(monthly_data)

def calculate_trend(monthly_data, column):
    """Calcula estadísticas de tendencia para una columna."""
    if monthly_data.empty or column not in monthly_data.columns:
        return None
    
    # Crear variable temporal numérica
    monthly_data = monthly_data.copy()
    monthly_data['tiempo'] = range(len(monthly_data))
    
    # Calcular correlación con el tiempo
    correlation = monthly_data['tiempo'].corr(monthly_data[column])
    
    # Calcular pendiente simple
    if len(monthly_data) > 1:
        x = monthly_data['tiempo'].values
        y = monthly_data[column].values
        slope = np.polyfit(x, y, 1)[0]
    else:
        slope = 0
    
    return {
        'correlation': correlation,
        'slope': slope,
        'trend_direction': 'Creciente' if slope > 0 else ('Decreciente' if slope < 0 else 'Estable'),
        'strength': 'Fuerte' if abs(correlation) > 0.7 else ('Moderada' if abs(correlation) > 0.4 else 'Débil')
    }

def show_trend_statistics(data_type, trend_stats, colors):
    """Muestra estadísticas de tendencia."""
    if not trend_stats:
        return
    
    color = colors['danger'] if data_type == 'Casos' else colors['warning']
    
    st.markdown(f"""
    <div style="background-color: white; padding: 15px; border-radius: 5px; border-left: 5px solid {color}; margin: 10px 0;">
        <h5 style="color: {color}; margin-top: 0;">Tendencia de {data_type}</h5>
        <p><strong>Dirección:</strong> {trend_stats['trend_direction']}</p>
        <p><strong>Fuerza:</strong> {trend_stats['strength']}</p>
        <p><strong>Correlación temporal:</strong> {trend_stats['correlation']:.3f}</p>
        <p><strong>Pendiente:</strong> {trend_stats['slope']:.3f} eventos/mes</p>
    </div>
    """, unsafe_allow_html=True)

def analyze_cyclical_patterns(monthly_data):
    """Analiza patrones cíclicos en los datos."""
    if monthly_data.empty or len(monthly_data) < 12:
        return pd.DataFrame()
    
    # Análisis básico de ciclicidad por mes del año
    monthly_patterns = monthly_data.groupby('mes').agg({
        'casos': 'mean',
        'epizootias': 'mean'
    }).round(2)
    
    return monthly_patterns

def show_cyclical_analysis(cyclical_data, colors):
    """Muestra análisis de patrones cíclicos."""
    if cyclical_data is None or (hasattr(cyclical_data, "empty") and cyclical_data.empty):
        return
    
    st.markdown("Análisis de patrones mensuales promedio:")
    
    # Crear gráfico de patrones mensuales
    cyclical_data_reset = cyclical_data.reset_index()
    cyclical_data_reset['mes_nombre'] = cyclical_data_reset['mes'].apply(lambda x: calendar.month_name[x])
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=cyclical_data_reset['mes_nombre'],
        y=cyclical_data_reset['casos'],
        mode='lines+markers',
        name='Casos (promedio)',
        line=dict(color=colors['danger'])
    ))
    
    fig.add_trace(go.Scatter(
        x=cyclical_data_reset['mes_nombre'],
        y=cyclical_data_reset['epizootias'],
        mode='lines+markers',
        name='Epizootias (promedio)',
        line=dict(color=colors['warning']),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title='Patrones Mensuales Promedio',
        xaxis_title='Mes',
        yaxis=dict(title='Casos', side='left'),
        yaxis2=dict(title='Epizootias', side='right', overlaying='y'),
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_simple_projections(monthly_data, colors):
    """Muestra proyecciones simples basadas en tendencias."""
    st.subheader("🔮 Proyecciones Simples")
    
    if monthly_data.empty or len(monthly_data) < 6:
        st.info("No hay suficientes datos para realizar proyecciones.")
        return
    
    st.warning("⚠️ Las proyecciones son estimaciones simples basadas en tendencias históricas y no constituyen predicciones epidemiológicas precisas.")
    
    # Proyección simple basada en tendencia lineal
    projection_months = st.slider(
        "Meses a proyectar:",
        min_value=1,
        max_value=12,
        value=6,
        key="projection_months"
    )
    
    # Calcular proyecciones
    casos_projection = calculate_simple_projection(monthly_data, 'casos', projection_months)
    epi_projection = calculate_simple_projection(monthly_data, 'epizootias', projection_months)
    
    if casos_projection is not None or epi_projection is not None:
        # Crear gráfico con proyecciones
        fig = go.Figure()
        
        # Datos históricos
        fig.add_trace(go.Scatter(
            x=monthly_data['fecha'],
            y=monthly_data['casos'],
            mode='lines+markers',
            name='Casos (histórico)',
            line=dict(color=colors['danger'])
        ))
        
        fig.add_trace(go.Scatter(
            x=monthly_data['fecha'],
            y=monthly_data['epizootias'],
            mode='lines+markers',
            name='Epizootias (histórico)',
            line=dict(color=colors['warning']),
            yaxis='y2'
        ))
        
        # Proyecciones
        if casos_projection is not None:
            fig.add_trace(go.Scatter(
                x=casos_projection['fecha'],
                y=casos_projection['casos'],
                mode='lines+markers',
                name='Casos (proyección)',
                line=dict(color=colors['danger'], dash='dash')
            ))
        
        if epi_projection is not None:
            fig.add_trace(go.Scatter(
                x=epi_projection['fecha'],
                y=epi_projection['epizootias'],
                mode='lines+markers',
                name='Epizootias (proyección)',
                line=dict(color=colors['warning'], dash='dash'),
                yaxis='y2'
            ))
        
        fig.update_layout(
            title='Proyecciones Basadas en Tendencia',
            xaxis_title='Fecha',
            yaxis=dict(title='Casos', side='left'),
            yaxis2=dict(title='Epizootias', side='right', overlaying='y'),
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)

def calculate_simple_projection(monthly_data, column, months):
    """Calcula proyección simple basada en tendencia lineal."""
    if monthly_data.empty or column not in monthly_data.columns or len(monthly_data) < 3:
        return None
    
    # Usar últimos 6 meses o todos los datos si hay menos
    recent_data = monthly_data.tail(min(6, len(monthly_data))).copy()
    recent_data['tiempo'] = range(len(recent_data))
    
    # Ajustar tendencia lineal
    if len(recent_data) >= 2:
        coeffs = np.polyfit(recent_data['tiempo'], recent_data[column], 1)
        slope, intercept = coeffs
        
        # Generar proyección
        last_date = monthly_data['fecha'].max()
        projection_dates = pd.date_range(
            start=last_date + pd.DateOffset(months=1),
            periods=months,
            freq='MS'
        )
        
        last_time = len(recent_data) - 1
        projection_values = []
        
        for i in range(months):
            projected_value = max(0, slope * (last_time + i + 1) + intercept)
            projection_values.append(projected_value)
        
        return pd.DataFrame({
            'fecha': projection_dates,
            column: projection_values
        })
    
    return None

def show_timeline_highlights(timeline_data, colors):
    """Muestra eventos destacados en el timeline."""
    if timeline_data.empty:
        return
    
    st.subheader("🎯 Eventos Destacados")
    
    # Encontrar días con múltiples eventos
    daily_events = timeline_data.groupby(timeline_data['fecha'].dt.date).agg({
        'cantidad': 'sum',
        'tipo': lambda x: ', '.join(x.unique()),
        'municipio': lambda x: ', '.join(x.unique()[:3])  # Máximo 3 municipios
    }).reset_index()
    
    # Días con más eventos
    top_days = daily_events.nlargest(5, 'cantidad')
    
    if not top_days.empty:
        st.write("**Días con mayor actividad:**")
        for _, row in top_days.iterrows():
            st.markdown(f"• **{row['fecha']}**: {int(row['cantidad'])} eventos ({row['tipo']}) en {row['municipio']}")

def show_period_statistics(timeline_agg, colors):
    """Muestra estadísticas del periodo analizado."""
    if timeline_agg.empty:
        return
    
    st.subheader("📊 Estadísticas del Periodo")
    
    # Calcular estadísticas básicas
    total_casos = timeline_agg[timeline_agg['tipo'] == 'Caso Confirmado']['cantidad'].sum()
    total_epizootias = timeline_agg[timeline_agg['tipo'] == 'Epizootia']['cantidad'].sum()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Casos", int(total_casos))
    
    with col2:
        st.metric("Total Epizootias", int(total_epizootias))
    
    with col3:
        # Promedio de eventos por periodo
        avg_casos = timeline_agg[timeline_agg['tipo'] == 'Caso Confirmado']['cantidad'].mean()
        st.metric("Promedio Casos/Periodo", f"{avg_casos:.1f}")
    
    with col4:
        # Promedio de epizootias por periodo
        avg_epi = timeline_agg[timeline_agg['tipo'] == 'Epizootia']['cantidad'].mean()
        st.metric("Promedio Epizootias/Periodo", f"{avg_epi:.1f}")