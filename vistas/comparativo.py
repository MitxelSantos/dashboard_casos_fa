"""
Vista de seguimiento temporal del dashboard de Fiebre Amarilla.
Enfoque minimalista en la relación temporal entre epizootias y casos humanos.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def show(data_filtered, filters, colors):
    """
    Muestra la vista de seguimiento temporal simplificada.

    Args:
        data_filtered (dict): Datos filtrados
        filters (dict): Filtros aplicados
        colors (dict): Colores institucionales
    """
    st.subheader("📈 Seguimiento Temporal")

    casos = data_filtered["casos"]
    epizootias = data_filtered["epizootias"]

    if casos.empty and epizootias.empty:
        st.warning("No hay datos disponibles para el seguimiento temporal.")
        return

    # Información sobre las epizootias como sistema de alerta temprana
    st.markdown(
        f"""
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 5px solid {colors['primary']}; margin-bottom: 20px;">
        <h4 style="color: {colors['primary']}; margin-top: 0;">🐒 Epizootias como Sistema de Alerta Temprana</h4>
        <p>Las epizootias en primates no humanos funcionan como <strong>faros de advertencia</strong> que pueden indicar circulación del virus antes de la aparición de casos humanos.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Crear análisis temporal
    temporal_data = create_temporal_analysis(casos, epizootias)

    if temporal_data.empty:
        st.info("No hay suficientes datos temporales para el análisis.")
        return

    # Gráfico temporal principal
    show_temporal_evolution_chart(temporal_data, colors)

    # Métricas temporales
    st.markdown("---")
    show_temporal_metrics(temporal_data, casos, epizootias, colors)

    # Análisis de correlación temporal
    st.markdown("---")
    show_correlation_analysis(temporal_data, colors)


def create_temporal_analysis(casos, epizootias):
    """
    Crea análisis temporal por períodos mensuales.
    """
    temporal_data = []

    # Obtener fechas de ambos datasets
    fechas_casos = []
    if not casos.empty and "fecha_inicio_sintomas" in casos.columns:
        fechas_casos = casos["fecha_inicio_sintomas"].dropna().tolist()

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

        # Contar epizootias en el período
        total_epi_periodo = 0
        positivas_periodo = 0
        if not epizootias.empty and "fecha_recoleccion" in epizootias.columns:
            epi_mes = epizootias[
                (epizootias["fecha_recoleccion"] >= periodo)
                & (epizootias["fecha_recoleccion"] <= fin_periodo)
            ]
            total_epi_periodo = len(epi_mes)

            if "descripcion" in epi_mes.columns:
                positivas_periodo = (epi_mes["descripcion"] == "POSITIVO FA").sum()

        temporal_data.append(
            {
                "periodo": periodo,
                "año_mes": periodo.strftime("%Y-%m"),
                "casos": casos_periodo,
                "fallecidos": fallecidos_periodo,
                "epizootias_total": total_epi_periodo,
                "epizootias_positivas": positivas_periodo,
                "actividad_total": casos_periodo + positivas_periodo,
            }
        )

    return pd.DataFrame(temporal_data)


def show_temporal_evolution_chart(temporal_data, colors):
    """
    Muestra el gráfico de evolución temporal principal.
    """
    st.subheader("📊 Evolución Temporal: Casos vs Epizootias Positivas")

    # Crear gráfico con doble eje Y
    fig = make_subplots(
        specs=[[{"secondary_y": True}]],
        subplot_titles=["Seguimiento Temporal de Fiebre Amarilla"],
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

    # Actualizar títulos de ejes
    fig.update_xaxes(title_text="Período")
    fig.update_yaxes(
        title_text="<b>Casos Humanos</b>", secondary_y=False, color=colors["danger"]
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
            text="Casos humanos vs Epizootias positivas como sistema de alerta temprana",
            x=0.5,
            font=dict(size=14),
        ),
    )

    st.plotly_chart(fig, use_container_width=True)


def show_temporal_metrics(temporal_data, casos, epizootias, colors):
    """
    Muestra métricas temporales clave.
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
            label="Períodos con Epizootias +",
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
            label="Pico Máximo Epizootias +",
            value=f"{max_positivas_mes}",
            help="Mayor número de epizootias positivas en un mes",
        )


def show_correlation_analysis(temporal_data, colors):
    """
    Muestra análisis de correlación temporal simple.
    """
    st.subheader("🔍 Relación Temporal")

    if len(temporal_data) < 3:
        st.info("Se necesitan más datos para analizar la relación temporal.")
        return

    # Calcular correlación
    correlacion = temporal_data["casos"].corr(temporal_data["epizootias_positivas"])

    # Análisis de adelanto/retraso (si las epizootias preceden a los casos)
    correlacion_adelanto = None
    if len(temporal_data) > 1:
        # Comparar epizootias del mes anterior con casos del mes actual
        temporal_shifted = temporal_data.copy()
        temporal_shifted["epizootias_mes_anterior"] = temporal_shifted[
            "epizootias_positivas"
        ].shift(1)
        correlacion_adelanto = temporal_shifted["casos"].corr(
            temporal_shifted["epizootias_mes_anterior"]
        )

    col1, col2 = st.columns(2)

    with col1:
        # Mostrar correlación contemporánea
        st.metric(
            label="Correlación Simultánea",
            value=f"{correlacion:.3f}",
            help="Correlación entre casos y epizootias en el mismo período",
        )

        # Interpretación de la correlación
        if abs(correlacion) > 0.7:
            interpretacion = "Correlación fuerte"
            color_interp = colors["danger"]
        elif abs(correlacion) > 0.4:
            interpretacion = "Correlación moderada"
            color_interp = colors["warning"]
        elif abs(correlacion) > 0.2:
            interpretacion = "Correlación débil"
            color_interp = colors["info"]
        else:
            interpretacion = "Sin correlación aparente"
            color_interp = colors["success"]

        st.markdown(
            f"""
        <div style="
            background-color: #f8f9fa; 
            padding: 10px; 
            border-radius: 6px; 
            border-left: 4px solid {color_interp};
            text-align: center;
        ">
            <strong>{interpretacion}</strong>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        if correlacion_adelanto is not None:
            st.metric(
                label="Correlación con Desfase",
                value=f"{correlacion_adelanto:.3f}",
                help="Correlación entre epizootias del mes anterior y casos del mes actual",
            )

            # Interpretación del sistema de alerta temprana
            if correlacion_adelanto > correlacion and correlacion_adelanto > 0.3:
                alerta_text = "Las epizootias pueden predecir casos futuros"
                alerta_color = colors["warning"]
            elif correlacion > correlacion_adelanto and correlacion > 0.3:
                alerta_text = "Eventos simultáneos, vigilancia coordinada"
                alerta_color = colors["info"]
            else:
                alerta_text = "Vigilancia independiente recomendada"
                alerta_color = colors["success"]

            st.markdown(
                f"""
            <div style="
                background-color: #f8f9fa; 
                padding: 10px; 
                border-radius: 6px; 
                border-left: 4px solid {alerta_color};
                text-align: center;
            ">
                <strong>{alerta_text}</strong>
            </div>
            """,
                unsafe_allow_html=True,
            )

    # Gráfico de dispersión para visualizar la relación
    if (
        temporal_data["casos"].sum() > 0
        and temporal_data["epizootias_positivas"].sum() > 0
    ):
        st.subheader("📈 Visualización de la Relación")

        fig_scatter = px.scatter(
            temporal_data,
            x="epizootias_positivas",
            y="casos",
            title="Relación entre Epizootias Positivas y Casos Humanos por Mes",
            labels={
                "epizootias_positivas": "Epizootias Positivas (mes)",
                "casos": "Casos Humanos (mes)",
            },
            hover_data=["año_mes"],
            color_discrete_sequence=[colors["primary"]],
        )

        # Agregar línea de tendencia si hay correlación
        if abs(correlacion) > 0.2:
            fig_scatter.add_traces(
                px.scatter(
                    temporal_data, x="epizootias_positivas", y="casos", trendline="ols"
                ).data[1]
            )

        fig_scatter.update_layout(height=400)
        st.plotly_chart(fig_scatter, use_container_width=True)

    # Resumen de interpretación médica
    st.markdown("---")
    st.markdown(
        f"""
    <div style="background-color: #e8f4fd; padding: 15px; border-radius: 8px; border-left: 5px solid {colors['info']};">
        <h5 style="color: {colors['info']}; margin-top: 0;">💡 Interpretación para Vigilancia Epidemiológica</h5>
        <p><strong>Función de las Epizootias:</strong> Las epizootias positivas actúan como un sistema de alerta temprana, 
        ya que los primates no humanos son más susceptibles al virus y pueden mostrar signos de infección antes que los humanos.</p>
        <p><strong>Recomendación:</strong> 
        {'Implementar vigilancia intensiva tras detección de epizootias positivas.' if correlacion_adelanto and correlacion_adelanto > 0.3
         else 'Mantener vigilancia coordinada entre fauna y población humana.' if correlacion > 0.3
         else 'Continuar vigilancia rutinaria de ambos componentes.'}
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )
