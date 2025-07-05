"""
Vista de seguimiento temporal CORREGIDA del dashboard de Fiebre Amarilla.
CORRECCIONES:
- Eliminado completamente el análisis de riesgo
- Enfoque en información descriptiva y temporal
- Sin términos alarmantes
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def show(data_filtered, filters, colors):
    """
    Muestra la vista de seguimiento temporal SIN análisis de riesgo.

    Args:
        data_filtered (dict): Datos filtrados
        filters (dict): Filtros aplicados
        colors (dict): Colores institucionales
    """
    st.subheader("📈 Seguimiento Temporal")

    casos = data_filtered["casos"]
    epizootias = data_filtered["epizootias"]  # Ya solo son positivas

    if casos.empty and epizootias.empty:
        st.warning("No hay datos disponibles para el seguimiento temporal.")
        return

    # **INFORMACIÓN DESCRIPTIVA sobre las epizootias**
    st.markdown(
        f"""
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 5px solid {colors['primary']}; margin-bottom: 20px;">
            <h4 style="color: {colors['primary']}; margin-top: 0;">🐒 Epizootias como Indicadores de Vigilancia</h4>
            <p>Las epizootias <strong>confirmadas positivas</strong> en primates no humanos representan 
            eventos de circulación viral documentados en el ecosistema.</p>
            <p><strong>Función:</strong> Proporcionan información sobre la presencia del virus en fauna silvestre, 
            complementando la vigilancia epidemiológica.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Crear análisis temporal
    temporal_data = create_temporal_analysis_descriptive(casos, epizootias)

    if temporal_data.empty:
        st.info("No hay suficientes datos temporales para el análisis.")
        return

    # Gráfico temporal principal
    show_temporal_evolution_chart_descriptive(temporal_data, colors)

    # Métricas temporales básicas
    st.markdown("---")
    show_temporal_metrics_descriptive(temporal_data, casos, epizootias, colors)

    # Gráficos adicionales
    st.markdown("---")
    show_additional_charts_descriptive(temporal_data, colors)


def create_temporal_analysis_descriptive(casos, epizootias):
    """
    CORREGIDO: Análisis temporal descriptivo sin análisis de riesgo.
    """
    temporal_data = []

    # Obtener fechas de ambos datasets
    fechas_casos = []
    if not casos.empty and "fecha_inicio_sintomas" in casos.columns:
        fechas_casos = casos["fecha_inicio_sintomas"].dropna().tolist()

    # Ya son todas epizootias positivas
    fechas_epi = []
    if not epizootias.empty and "fecha_recoleccion" in epizootias.columns:
        fechas_epi = epizootias["fecha_recoleccion"].dropna().tolist()

    todas_fechas = fechas_casos + fechas_epi

    if not todas_fechas:
        return pd.DataFrame()

    # Crear rango mensual desde la primera fecha hasta la última
    fecha_min = min(todas_fechas).replace(day=1)
    fecha_max = max(todas_fechas)

    # Generar períodos mensuales
    periodos = pd.date_range(start=fecha_min, end=fecha_max, freq="MS")

    for periodo in periodos:
        fin_periodo = (periodo + pd.DateOffset(months=1)) - pd.DateOffset(days=1)

        # Contar casos en el período
        casos_periodo = 0
        fallecidos_periodo = 0
        if not casos.empty and "fecha_inicio_sintomas" in casos.columns:
            casos_mes = casos[
                (casos["fecha_inicio_sintomas"] >= periodo)
                & (casos["fecha_inicio_sintomas"] <= fin_periodo)
            ]
            casos_periodo = len(casos_mes)

            if "condicion_final" in casos_mes.columns:
                fallecidos_periodo = (casos_mes["condicion_final"] == "Fallecido").sum()
                
        # Epizootias (positivas + en estudio)
        epizootias_periodo = 0
        positivas_periodo = 0
        en_estudio_periodo = 0
        if not epizootias.empty and "fecha_recoleccion" in epizootias.columns:
            epi_mes = epizootias[
                (epizootias["fecha_recoleccion"] >= periodo)
                & (epizootias["fecha_recoleccion"] <= fin_periodo)
            ]
            epizootias_periodo = len(epi_mes)
            
            if "descripcion" in epi_mes.columns:
                positivas_periodo = (epi_mes["descripcion"] == "POSITIVO FA").sum()
                en_estudio_periodo = (epi_mes["descripcion"] == "EN ESTUDIO").sum()

        temporal_data.append(
            {
                "periodo": periodo,
                "año_mes": periodo.strftime("%Y-%m"),
                "casos": casos_periodo,
                "fallecidos": fallecidos_periodo,
                "epizootias": epizootias_periodo,
                "epizootias_positivas": positivas_periodo,  # NUEVO
                "epizootias_en_estudio": en_estudio_periodo,  # NUEVO
                "actividad_total": casos_periodo + epizootias_periodo,
                "categoria_actividad": categorize_activity_level(casos_periodo, epizootias_periodo),
            }
        )

    return pd.DataFrame(temporal_data)


def categorize_activity_level(casos, epizootias):
    """
    CORREGIDO: Categorización descriptiva sin análisis de riesgo.
    """
    actividad_total = casos + epizootias
    
    if actividad_total == 0:
        return "Sin actividad"
    elif actividad_total <= 2:
        return "Actividad baja"
    elif actividad_total <= 5:
        return "Actividad moderada"
    else:
        return "Actividad alta"


def show_temporal_evolution_chart_descriptive(temporal_data, colors):
    """
    CORREGIDO: Gráfico de evolución temporal descriptivo.
    """
    st.subheader("📊 Evolución Temporal: Casos vs Epizootias")

    # Crear gráfico con doble eje Y
    fig = make_subplots(
        specs=[[{"secondary_y": True}]],
        subplot_titles=["Seguimiento de Eventos Confirmados"],
    )

    # Línea de casos humanos (eje principal)
    fig.add_trace(
        go.Scatter(
            x=temporal_data["periodo"],
            y=temporal_data["casos"],
            mode="lines+markers",
            name="Casos Humanos",
            line=dict(color=colors["danger"], width=4),
            marker=dict(size=8, symbol="circle"),
            hovertemplate="<b>Casos Humanos</b><br>Fecha: %{x}<br>Casos: %{y}<extra></extra>",
        ),
        secondary_y=False,
    )

    # Línea de epizootias (eje secundario)
    fig.add_trace(
        go.Scatter(
            x=temporal_data["periodo"],
            y=temporal_data["epizootias"],
            mode="lines+markers",
            name="Epizootias",
            line=dict(color=colors["warning"], width=4, dash="dot"),
            marker=dict(size=8, symbol="diamond"),
            hovertemplate="<b>Epizootias</b><br>Fecha: %{x}<br>Epizootias: %{y}<extra></extra>",
        ),
        secondary_y=True,
    )

    # Línea de actividad total combinada
    fig.add_trace(
        go.Scatter(
            x=temporal_data["periodo"],
            y=temporal_data["actividad_total"],
            mode="lines",
            name="Actividad Total",
            line=dict(color=colors["primary"], width=2, dash="dash"),
            opacity=0.7,
            hovertemplate="<b>Actividad Total</b><br>Fecha: %{x}<br>Total: %{y}<extra></extra>",
        ),
        secondary_y=False,
    )

    # Actualizar títulos de ejes
    fig.update_xaxes(title_text="Período")
    fig.update_yaxes(
        title_text="<b>Casos Humanos & Actividad Total</b>", secondary_y=False, color=colors["danger"]
    )
    fig.update_yaxes(
        title_text="<b>Epizootias</b>",
        secondary_y=True,
        color=colors["warning"],
    )

    # Configurar layout
    fig.update_layout(
        height=500,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(248,249,250,0.8)",
        title=dict(
            text="Casos humanos vs Epizootias confirmadas - Seguimiento temporal",
            x=0.5,
            font=dict(size=14),
        ),
    )

    st.plotly_chart(fig, use_container_width=True)


def show_temporal_metrics_descriptive(temporal_data, casos, epizootias, colors):
    """
    CORREGIDO: Métricas temporales descriptivas sin análisis de riesgo.
    """
    st.subheader("📊 Métricas Temporales")

    col1, col2, col3, col4 = st.columns(4)

    # Totales por período
    periodos_con_casos = (temporal_data["casos"] > 0).sum()
    periodos_con_epizootias = (temporal_data["epizootias"] > 0).sum()
    total_periodos = len(temporal_data)

    # Picos máximos
    max_casos_mes = temporal_data["casos"].max()
    max_epizootias_mes = temporal_data["epizootias"].max()

    with col1:
        st.metric(
            label="Períodos con Casos",
            value=f"{periodos_con_casos}",
            delta=f"de {total_periodos} meses",
            help="Meses con al menos un caso humano",
        )

    with col2:
        st.metric(
            label="Períodos con Epizootias",
            value=f"{periodos_con_epizootias}",
            delta=f"de {total_periodos} meses",
            help="Meses con al menos una epizootia (positiva o en estudio)",
        )

    with col3:
        st.metric(
            label="Pico Máximo Casos",
            value=f"{max_casos_mes}",
            help="Mayor número de casos en un mes",
        )

    with col4:
        st.metric(
            label="Pico Máximo Epizootias",
            value=f"{max_epizootias_mes}",
            help="Mayor número de epizootias en un mes",
        )

    # Métricas adicionales descriptivas
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Períodos con ambos eventos
        periodos_ambos = ((temporal_data["casos"] > 0) & (temporal_data["epizootias"] > 0)).sum()
        st.metric(
            label="Períodos con Ambos",
            value=f"{periodos_ambos}",
            delta=f"{(periodos_ambos/total_periodos*100):.1f}%" if total_periodos > 0 else "0%",
            help="Meses con casos humanos Y epizootias"
        )
        
    with col2:
        # Desglose de epizootias si hay datos disponibles
        if "epizootias_positivas" in temporal_data.columns:
            total_positivas = temporal_data["epizootias_positivas"].sum()
            total_en_estudio = temporal_data["epizootias_en_estudio"].sum()
            st.metric(
                label="Positivas/En Estudio",
                value=f"{total_positivas}/{total_en_estudio}",
                help="Total epizootias positivas vs en estudio en el período"
            )
        else:
            actividad_promedio = temporal_data["actividad_total"].mean()
            st.metric(
                label="Actividad Promedio",
                value=f"{actividad_promedio:.1f}",
                help="Promedio de eventos por mes"
            )
    
    with col3:
        # Distribución de actividad
        periodos_activos = (temporal_data["actividad_total"] > 0).sum()
        st.metric(
            label="Períodos Activos",
            value=f"{periodos_activos}",
            delta=f"{(periodos_activos/total_periodos*100):.1f}%" if total_periodos > 0 else "0%",
            help="Meses con al menos un evento"
        )


def show_additional_charts_descriptive(temporal_data, colors):
    """
    CORREGIDO: Gráficos adicionales descriptivos sin análisis de riesgo.
    """
    st.subheader("📈 Análisis Temporal Adicional")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de barras apiladas
        if not temporal_data.empty:
            fig_bars = go.Figure()
            
            # Barras de casos
            fig_bars.add_trace(go.Bar(
                x=temporal_data["año_mes"],
                y=temporal_data["casos"],
                name="Casos Humanos",
                marker_color=colors["danger"],
                opacity=0.8
            ))
            
            # Barras de epizootias
            fig_bars.add_trace(go.Bar(
                x=temporal_data["año_mes"],
                y=temporal_data["epizootias"],
                name="Epizootias",
                marker_color=colors["warning"],
                opacity=0.8
            ))
            
            # Barras de epizootias positivas
            fig_bars.add_trace(go.Bar(
                x=temporal_data["año_mes"],
                y=temporal_data["epizootias_positivas"] if "epizootias_positivas" in temporal_data.columns else temporal_data["epizootias"],
                name="Epizootias Positivas",
                marker_color=colors["danger"],
                opacity=0.8
            ))

            # Barras de epizootias en estudio (si hay datos)
            if "epizootias_en_estudio" in temporal_data.columns:
                fig_bars.add_trace(go.Bar(
                    x=temporal_data["año_mes"],
                    y=temporal_data["epizootias_en_estudio"],
                    name="En Estudio",
                    marker_color=colors["info"],
                    opacity=0.8
                ))
            
            fig_bars.update_layout(
                title="Distribución Mensual - Eventos Confirmados",
                xaxis_title="Mes",
                yaxis_title="Número de Eventos",
                height=400,
                barmode='group'
            )
            
            st.plotly_chart(fig_bars, use_container_width=True)
    
    with col2:
        # Gráfico de nivel de actividad (SIN riesgo)
        if not temporal_data.empty:
            # Crear mapeo de colores para niveles de actividad
            activity_colors = {
                "Sin actividad": colors["info"],
                "Actividad baja": colors["success"],
                "Actividad moderada": colors["warning"],
                "Actividad alta": colors["primary"]
            }
            
            # Crear gráfico de barras de actividad
            fig_activity = px.bar(
                temporal_data,
                x="periodo",
                y="actividad_total",
                color="categoria_actividad",
                title="Nivel de Actividad por Período",
                color_discrete_map=activity_colors,
                labels={
                    "actividad_total": "Actividad Total",
                    "periodo": "Período",
                    "categoria_actividad": "Nivel de Actividad"
                }
            )
            
            fig_activity.update_layout(height=400)
            st.plotly_chart(fig_activity, use_container_width=True)

    # Tabla resumen mensual
    st.subheader("📋 Resumen Mensual")
    
    if not temporal_data.empty:
        # Incluir desglose de epizootias si está disponible
        if "epizootias_positivas" in temporal_data.columns:
            resumen_tabla = temporal_data[["año_mes", "casos", "fallecidos", "epizootias_positivas", "epizootias_en_estudio", "epizootias", "categoria_actividad"]].copy()
            resumen_tabla.columns = ["Mes", "Casos", "Fallecidos", "Positivas", "En Estudio", "Total Epizootias", "Nivel de Actividad"]
        else:
            resumen_tabla = temporal_data[["año_mes", "casos", "fallecidos", "epizootias", "actividad_total", "categoria_actividad"]].copy()
            resumen_tabla.columns = ["Mes", "Casos", "Fallecidos", "Epizootias", "Actividad Total", "Nivel de Actividad"]
        # Ordenar por mes descendente
        resumen_tabla = resumen_tabla.sort_values("Mes", ascending=False)
        
        st.dataframe(resumen_tabla, use_container_width=True, height=300)
        
        # Opción de descarga
        csv_temporal = resumen_tabla.to_csv(index=False)
        st.download_button(
            label="📄 Descargar Análisis Temporal",
            data=csv_temporal,
            file_name=f"analisis_temporal_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
        )

    # **INTERPRETACIÓN DESCRIPTIVA**
    st.markdown("---")
    st.markdown(
        f"""
        <div style="background-color: #e8f4fd; padding: 15px; border-radius: 8px; border-left: 5px solid {colors['info']};">
            <h5 style="color: {colors['info']}; margin-top: 0;">💡 Interpretación para Vigilancia Epidemiológica</h5>
            <p><strong>Función de las Epizootias:</strong> Las epizootias positivas confirman la presencia del virus, 
            mientras que las "en estudio" representan muestras en proceso de análisis laboratorial que contribuyen 
            al sistema de vigilancia epidemiológica temprana.</p>
            <p><strong>Seguimiento Temporal:</strong> El análisis permite observar:</p>
            <ul style="margin-left: 20px;">
                <li>📊 Patrones estacionales de actividad</li>
                <li>📈 Tendencias en la detección de eventos</li>
                <li>🔄 Correlaciones temporales entre casos y epizootias</li>
                <li>📅 Distribución cronológica de eventos</li>
            </ul>
            <p><strong>Interpretación Temporal:</strong> Los períodos con actividad documentada 
            proporcionan información sobre la dinámica de transmisión del virus.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Correlación entre eventos (SIN análisis de riesgo)
    if not temporal_data.empty and len(temporal_data) > 1:
        correlacion = temporal_data["casos"].corr(temporal_data["epizootias"])
        
        st.markdown("---")
        st.markdown("### 🔗 Análisis de Correlación")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.metric(
                label="Correlación Casos-Epizootias",
                value=f"{correlacion:.3f}",
                help="Correlación temporal entre casos humanos y epizootias (-1 a 1)"
            )
        
        with col2:
            # Interpretación descriptiva de la correlación
            if correlacion > 0.7:
                interpretacion = "🔴 Correlación muy alta - Patrones temporales similares"
                color_corr = colors["danger"]
            elif correlacion > 0.4:
                interpretacion = "🟡 Correlación moderada - Cierta sincronía temporal"
                color_corr = colors["warning"]
            elif correlacion > 0.1:
                interpretacion = "🟢 Correlación baja - Patrones temporales diferentes"
                color_corr = colors["success"]
            else:
                interpretacion = "🔵 Sin correlación temporal aparente"
                color_corr = colors["info"]
            
            st.markdown(
                f"""
                <div style="background: {color_corr}; color: white; padding: 10px; border-radius: 6px; font-weight: 600;">
                    {interpretacion}
                </div>
                """,
                unsafe_allow_html=True
            )

    # **ESTADÍSTICAS ADICIONALES DESCRIPTIVAS**
    st.markdown("---")
    st.markdown("### 📊 Estadísticas Descriptivas")
    
    if not temporal_data.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Período más activo
            max_activity_idx = temporal_data["actividad_total"].idxmax()
            max_activity_period = temporal_data.loc[max_activity_idx, "año_mes"]
            max_activity_value = temporal_data.loc[max_activity_idx, "actividad_total"]
            
            st.metric(
                label="Período Más Activo",
                value=max_activity_period,
                delta=f"{max_activity_value} eventos",
                help="Mes con mayor actividad registrada"
            )
        
        with col2:
            # Duración del seguimiento
            fecha_inicio = temporal_data["periodo"].min()
            fecha_fin = temporal_data["periodo"].max()
            duracion_meses = len(temporal_data)
            
            st.metric(
                label="Duración Seguimiento",
                value=f"{duracion_meses} meses",
                delta=f"{fecha_inicio.strftime('%m/%Y')} - {fecha_fin.strftime('%m/%Y')}",
                help="Período total de seguimiento"
            )
        
        with col3:
            # Proporción de casos vs epizootias
            total_casos_periodo = temporal_data["casos"].sum()
            total_epi_periodo = temporal_data["epizootias"].sum()
            
            if total_casos_periodo + total_epi_periodo > 0:
                prop_casos = (total_casos_periodo / (total_casos_periodo + total_epi_periodo)) * 100
                st.metric(
                    label="Proporción Casos",
                    value=f"{prop_casos:.1f}%",
                    delta=f"{total_casos_periodo} casos",
                    help="Porcentaje de eventos que son casos humanos"
                )
            else:
                st.metric("Proporción Casos", "0%")
        
        with col4:
            # Continuidad del seguimiento
            periodos_consecutivos = calculate_consecutive_periods(temporal_data)
            st.metric(
                label="Mayor Secuencia Activa",
                value=f"{periodos_consecutivos} meses",
                help="Mayor número de meses consecutivos con actividad"
            )


def calculate_consecutive_periods(temporal_data):
    """
    NUEVO: Calcula el mayor número de períodos consecutivos con actividad.
    """
    if temporal_data.empty:
        return 0
    
    max_consecutive = 0
    current_consecutive = 0
    
    for _, row in temporal_data.iterrows():
        if row["actividad_total"] > 0:
            current_consecutive += 1
            max_consecutive = max(max_consecutive, current_consecutive)
        else:
            current_consecutive = 0
    
    return max_consecutive