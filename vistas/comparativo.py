"""
Vista de seguimiento temporal del dashboard de Fiebre Amarilla.
ACTUALIZADA: Solo epizootias positivas en toda la lógica de análisis temporal.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def show(data_filtered, filters, colors):
    """
    Muestra la vista de seguimiento temporal.
    ACTUALIZADA: Solo epizootias positivas en toda la lógica.

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

    # ACTUALIZADA: Información sobre las epizootias positivas como sistema de alerta temprana
    st.markdown(
        f"""
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 5px solid {colors['primary']}; margin-bottom: 20px;">
        <h4 style="color: {colors['primary']}; margin-top: 0;">🔴 Epizootias Positivas como Sistema de Alerta Temprana</h4>
        <p>Las epizootias <strong>positivas</strong> en primates no humanos funcionan como <strong>faros de advertencia directos</strong> 
        que indican circulación activa del virus antes de la aparición de casos humanos.</p>
        <p><strong>Importancia:</strong> Cada epizootia positiva confirma presencia viral en el ecosistema local.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Crear análisis temporal SOLO con epizootias positivas
    temporal_data = create_temporal_analysis_positive_only(casos, epizootias)

    if temporal_data.empty:
        st.info("No hay suficientes datos temporales para el análisis.")
        return

    # Gráfico temporal principal
    show_temporal_evolution_chart_positive_only(temporal_data, colors)

    # Métricas temporales básicas
    st.markdown("---")
    show_temporal_metrics_positive_only(temporal_data, casos, epizootias, colors)

    # Gráficos adicionales
    st.markdown("---")
    show_additional_charts_positive_only(temporal_data, colors)


def create_temporal_analysis_positive_only(casos, epizootias):
    """
    ACTUALIZADA: Análisis temporal considerando solo epizootias positivas.
    """
    temporal_data = []

    # Obtener fechas de ambos datasets
    fechas_casos = []
    if not casos.empty and "fecha_inicio_sintomas" in casos.columns:
        fechas_casos = casos["fecha_inicio_sintomas"].dropna().tolist()

    # CAMBIO: epizootias ya son solo positivas
    fechas_epi_positivas = []
    if not epizootias.empty and "fecha_recoleccion" in epizootias.columns:
        fechas_epi_positivas = epizootias["fecha_recoleccion"].dropna().tolist()

    todas_fechas = fechas_casos + fechas_epi_positivas

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

        # CAMBIO: Solo epizootias positivas (ya filtradas)
        positivas_periodo = 0
        if not epizootias.empty and "fecha_recoleccion" in epizootias.columns:
            epi_mes = epizootias[
                (epizootias["fecha_recoleccion"] >= periodo)
                & (epizootias["fecha_recoleccion"] <= fin_periodo)
            ]
            positivas_periodo = len(epi_mes)  # Ya son solo positivas

        temporal_data.append(
            {
                "periodo": periodo,
                "año_mes": periodo.strftime("%Y-%m"),
                "casos": casos_periodo,
                "fallecidos": fallecidos_periodo,
                "epizootias_positivas": positivas_periodo,
                "actividad_total": casos_periodo + positivas_periodo,
                "riesgo_nivel": calculate_risk_level(casos_periodo, positivas_periodo),
            }
        )

    return pd.DataFrame(temporal_data)


def calculate_risk_level(casos, epi_positivas):
    """
    NUEVA: Calcula nivel de riesgo basado en casos y epizootias positivas.
    """
    actividad_total = casos + epi_positivas
    
    if actividad_total == 0:
        return 0  # Sin riesgo
    elif actividad_total <= 2:
        return 1  # Riesgo bajo
    elif actividad_total <= 5:
        return 2  # Riesgo medio
    else:
        return 3  # Riesgo alto


def show_temporal_evolution_chart_positive_only(temporal_data, colors):
    """
    ACTUALIZADA: Gráfico de evolución temporal considerando solo epizootias positivas.
    """
    st.subheader("📊 Evolución Temporal: Casos vs Epizootias Positivas")

    # Crear gráfico con doble eje Y
    fig = make_subplots(
        specs=[[{"secondary_y": True}]],
        subplot_titles=["Seguimiento de Actividad Viral Confirmada"],
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

    # Línea de epizootias positivas (eje secundario)
    fig.add_trace(
        go.Scatter(
            x=temporal_data["periodo"],
            y=temporal_data["epizootias_positivas"],
            mode="lines+markers",
            name="Epizootias Positivas",
            line=dict(color=colors["warning"], width=4, dash="dot"),
            marker=dict(size=8, symbol="diamond"),
            hovertemplate="<b>Epizootias Positivas</b><br>Fecha: %{x}<br>Positivas: %{y}<extra></extra>",
        ),
        secondary_y=True,
    )

    # NUEVA: Línea de actividad total combinada
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
        title_text="<b>Epizootias Positivas</b>",
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
            text="Casos humanos vs Epizootias positivas confirmadas - Sistema de alerta temprana",
            x=0.5,
            font=dict(size=14),
        ),
    )

    st.plotly_chart(fig, use_container_width=True)


def show_temporal_metrics_positive_only(temporal_data, casos, epizootias, colors):
    """
    ACTUALIZADA: Métricas temporales considerando solo epizootias positivas.
    """
    st.subheader("📊 Métricas Temporales")

    col1, col2, col3, col4 = st.columns(4)

    # Totales por período
    periodos_con_casos = (temporal_data["casos"] > 0).sum()
    periodos_con_positivas = (temporal_data["epizootias_positivas"] > 0).sum()
    total_periodos = len(temporal_data)

    # Picos máximos
    max_casos_mes = temporal_data["casos"].max()
    max_positivas_mes = temporal_data["epizootias_positivas"].max()

    with col1:
        st.metric(
            label="Períodos con Casos",
            value=f"{periodos_con_casos}",
            delta=f"de {total_periodos} meses",
            help="Meses con al menos un caso humano",
        )

    with col2:
        st.metric(
            label="Períodos con Epi+",
            value=f"{periodos_con_positivas}",
            delta=f"de {total_periodos} meses",
            help="Meses con al menos una epizootia positiva",
        )

    with col3:
        st.metric(
            label="Pico Máximo Casos",
            value=f"{max_casos_mes}",
            help="Mayor número de casos en un mes",
        )

    with col4:
        st.metric(
            label="Pico Máximo Epi+",
            value=f"{max_positivas_mes}",
            help="Mayor número de epizootias positivas en un mes",
        )

    # NUEVA: Métricas adicionales de correlación
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Períodos con ambos eventos
        periodos_ambos = ((temporal_data["casos"] > 0) & (temporal_data["epizootias_positivas"] > 0)).sum()
        st.metric(
            label="Períodos con Ambos",
            value=f"{periodos_ambos}",
            delta=f"{(periodos_ambos/total_periodos*100):.1f}%" if total_periodos > 0 else "0%",
            help="Meses con casos humanos Y epizootias positivas"
        )
    
    with col2:
        # Promedio de actividad por período
        actividad_promedio = temporal_data["actividad_total"].mean()
        st.metric(
            label="Actividad Promedio",
            value=f"{actividad_promedio:.1f}",
            help="Promedio de eventos por mes"
        )
    
    with col3:
        # Eficiencia de alerta (epizootias antes de casos)
        alerta_efectiva = calculate_alert_effectiveness(temporal_data)
        st.metric(
            label="Eficiencia Alerta",
            value=f"{alerta_efectiva:.1f}%",
            help="% de casos precedidos por epizootias positivas"
        )


def calculate_alert_effectiveness(temporal_data):
    """
    NUEVA: Calcula la efectividad del sistema de alerta temprana.
    """
    if temporal_data.empty:
        return 0
    
    # Buscar casos precedidos por epizootias positivas en los últimos 3 meses
    casos_con_alerta = 0
    total_casos_con_contexto = 0
    
    for i, row in temporal_data.iterrows():
        if row["casos"] > 0:
            total_casos_con_contexto += row["casos"]
            
            # Buscar epizootias positivas en los 3 meses anteriores
            start_idx = max(0, i - 3)
            epi_previas = temporal_data.iloc[start_idx:i]["epizootias_positivas"].sum()
            
            if epi_previas > 0:
                casos_con_alerta += row["casos"]
    
    if total_casos_con_contexto == 0:
        return 0
    
    return (casos_con_alerta / total_casos_con_contexto) * 100


def show_additional_charts_positive_only(temporal_data, colors):
    """
    ACTUALIZADA: Gráficos adicionales considerando solo epizootias positivas.
    """
    st.subheader("📈 Análisis Temporal Adicional")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # ACTUALIZADO: Gráfico de barras apiladas
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
            
            # Barras de epizootias positivas
            fig_bars.add_trace(go.Bar(
                x=temporal_data["año_mes"],
                y=temporal_data["epizootias_positivas"],
                name="Epizootias Positivas",
                marker_color=colors["warning"],
                opacity=0.8
            ))
            
            fig_bars.update_layout(
                title="Distribución Mensual - Solo Eventos Positivos",
                xaxis_title="Mes",
                yaxis_title="Número de Eventos",
                height=400,
                barmode='group'
            )
            
            st.plotly_chart(fig_bars, use_container_width=True)
    
    with col2:
        # NUEVO: Gráfico de nivel de riesgo
        if not temporal_data.empty:
            # Crear mapeo de colores para niveles de riesgo
            risk_colors = {
                0: colors["success"],   # Sin riesgo
                1: colors["info"],      # Riesgo bajo  
                2: colors["warning"],   # Riesgo medio
                3: colors["danger"]     # Riesgo alto
            }
            
            risk_labels = {
                0: "Sin Riesgo",
                1: "Riesgo Bajo", 
                2: "Riesgo Medio",
                3: "Riesgo Alto"
            }
            
            # Crear gráfico de barras de riesgo
            temporal_data["risk_color"] = temporal_data["riesgo_nivel"].map(risk_colors)
            temporal_data["risk_label"] = temporal_data["riesgo_nivel"].map(risk_labels)
            
            fig_risk = px.bar(
                temporal_data,
                x="periodo",
                y="actividad_total",
                color="risk_label",
                title="Nivel de Riesgo por Período",
                color_discrete_map=risk_colors,
                labels={
                    "actividad_total": "Actividad Total",
                    "periodo": "Período",
                    "risk_label": "Nivel de Riesgo"
                }
            )
            
            fig_risk.update_layout(height=400)
            st.plotly_chart(fig_risk, use_container_width=True)

    # ACTUALIZADA: Tabla resumen mensual
    st.subheader("📋 Resumen Mensual")
    
    if not temporal_data.empty:
        # Crear tabla resumen mejorada
        resumen_tabla = temporal_data[["año_mes", "casos", "fallecidos", "epizootias_positivas", "actividad_total", "risk_label"]].copy()
        resumen_tabla.columns = ["Mes", "Casos", "Fallecidos", "Epi Positivas", "Actividad Total", "Nivel de Riesgo"]
        
        # Ordenar por mes descendente
        resumen_tabla = resumen_tabla.sort_values("Mes", ascending=False)
        
        st.dataframe(resumen_tabla, use_container_width=True, height=300)
        
        # Opción de descarga
        csv_temporal = resumen_tabla.to_csv(index=False)
        st.download_button(
            label="📄 Descargar Análisis Temporal",
            data=csv_temporal,
            file_name=f"analisis_temporal_positivas_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
        )

    # ACTUALIZADA: Interpretación para epizootias positivas
    st.markdown("---")
    st.markdown(
        f"""
    <div style="background-color: #e8f4fd; padding: 15px; border-radius: 8px; border-left: 5px solid {colors['info']};">
        <h5 style="color: {colors['info']}; margin-top: 0;">💡 Interpretación para Vigilancia Epidemiológica</h5>
        <p><strong>Función de las Epizootias Positivas:</strong> Cada epizootia positiva confirma circulación viral activa 
        en el ecosistema local. Son indicadores directos de riesgo para población humana.</p>
        <p><strong>Sistema de Alerta:</strong> La presencia de epizootias positivas debe activar inmediatamente:</p>
        <ul style="margin-left: 20px;">
            <li>🚨 Intensificación de vigilancia médica en la zona</li>
            <li>🦟 Control vectorial inmediato</li>
            <li>💉 Campañas de vacunación preventiva</li>
            <li>📢 Educación comunitaria sobre prevención</li>
        </ul>
        <p><strong>Interpretación Temporal:</strong> Períodos con alta actividad de epizootias positivas 
        requieren máximo estado de alerta epidemiológica.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # NUEVA: Correlación entre eventos
    if not temporal_data.empty and len(temporal_data) > 1:
        correlacion = temporal_data["casos"].corr(temporal_data["epizootias_positivas"])
        
        st.markdown("---")
        st.markdown("### 🔗 Análisis de Correlación")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.metric(
                label="Correlación Casos-Epi+",
                value=f"{correlacion:.3f}",
                help="Correlación entre casos humanos y epizootias positivas (-1 a 1)"
            )
        
        with col2:
            # Interpretación de la correlación
            if correlacion > 0.7:
                interpretacion = "🔴 Correlación muy alta - Vigilancia crítica"
                color_corr = colors["danger"]
            elif correlacion > 0.4:
                interpretacion = "🟡 Correlación moderada - Vigilancia activa"
                color_corr = colors["warning"]
            elif correlacion > 0.1:
                interpretacion = "🟢 Correlación baja - Vigilancia rutinaria"
                color_corr = colors["success"]
            else:
                interpretacion = "🔵 Sin correlación aparente"
                color_corr = colors["info"]
            
            st.markdown(
                f"""
                <div style="background: {color_corr}; color: white; padding: 10px; border-radius: 6px; font-weight: 600;">
                    {interpretacion}
                </div>
                """,
                unsafe_allow_html=True
            )