"""
Vista de seguimiento temporal del dashboard de Fiebre Amarilla.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging

logger = logging.getLogger(__name__)

def show(data_filtered, filters, colors):
    """Vista principal de seguimiento temporal OPTIMIZADA."""
    logger.info("📈 Iniciando vista temporal optimizada")
    
    casos_filtrados = data_filtered["casos"]
    epizootias_filtradas = data_filtered["epizootias"]
    
    # Verificación básica
    if not isinstance(casos_filtrados, pd.DataFrame) or not isinstance(epizootias_filtradas, pd.DataFrame):
        st.error("Error: datos no válidos")
        return

    # Información de contexto
    active_filters = filters.get("active_filters", [])
    context = "datos filtrados" if active_filters else "datos completos del Tolima"
    
    if active_filters:
        st.info(f"📈 Análisis temporal de {context}: {' • '.join(active_filters[:2])}")

    if casos_filtrados.empty and epizootias_filtradas.empty:
        st.warning("No hay datos disponibles para el seguimiento temporal con los filtros aplicados.")
        return

    # Crear análisis temporal
    temporal_data = create_temporal_analysis(casos_filtrados, epizootias_filtradas)

    if temporal_data.empty:
        st.info("No hay suficientes datos temporales para el análisis con los filtros aplicados.")
        return

    # Secciones principales
    show_evolution_chart(temporal_data, colors, filters)
    
    st.markdown("---")
    show_temporal_metrics(temporal_data, colors, filters)
    
    st.markdown("---")
    show_additional_charts(temporal_data, colors, filters)

def create_temporal_analysis(casos_filtrados, epizootias_filtradas):
    """Crea análisis temporal optimizado."""
    logger.info(f"Creando análisis temporal: {len(casos_filtrados)} casos, {len(epizootias_filtradas)} epizootias")
    
    # Obtener fechas
    fechas_casos = casos_filtrados["fecha_inicio_sintomas"].dropna().tolist() if "fecha_inicio_sintomas" in casos_filtrados.columns else []
    fechas_epi = epizootias_filtradas["fecha_recoleccion"].dropna().tolist() if "fecha_recoleccion" in epizootias_filtradas.columns else []
    
    todas_fechas = fechas_casos + fechas_epi
    if not todas_fechas:
        return pd.DataFrame()

    # Crear rango mensual
    fecha_min = min(todas_fechas).replace(day=1)
    fecha_max = max(todas_fechas)
    periodos = pd.date_range(start=fecha_min, end=fecha_max, freq="MS")
    
    temporal_data = []
    
    for periodo in periodos:
        fin_periodo = (periodo + pd.DateOffset(months=1)) - pd.DateOffset(days=1)
        
        # Contar casos en el período
        casos_periodo = 0
        fallecidos_periodo = 0
        if not casos_filtrados.empty and "fecha_inicio_sintomas" in casos_filtrados.columns:
            casos_mes = casos_filtrados[
                (casos_filtrados["fecha_inicio_sintomas"] >= periodo) &
                (casos_filtrados["fecha_inicio_sintomas"] <= fin_periodo)
            ]
            casos_periodo = len(casos_mes)
            if "condicion_final" in casos_mes.columns:
                fallecidos_periodo = (casos_mes["condicion_final"] == "Fallecido").sum()
        
        # Contar epizootias en el período
        epizootias_periodo = 0
        positivas_periodo = 0
        en_estudio_periodo = 0
        if not epizootias_filtradas.empty and "fecha_recoleccion" in epizootias_filtradas.columns:
            epi_mes = epizootias_filtradas[
                (epizootias_filtradas["fecha_recoleccion"] >= periodo) &
                (epizootias_filtradas["fecha_recoleccion"] <= fin_periodo)
            ]
            epizootias_periodo = len(epi_mes)
            if "descripcion" in epi_mes.columns:
                positivas_periodo = (epi_mes["descripcion"] == "POSITIVO FA").sum()
                en_estudio_periodo = (epi_mes["descripcion"] == "EN ESTUDIO").sum()
        
        temporal_data.append({
            "periodo": periodo,
            "año_mes": periodo.strftime("%Y-%m"),
            "casos": casos_periodo,
            "fallecidos": fallecidos_periodo,
            "epizootias": epizootias_periodo,
            "epizootias_positivas": positivas_periodo,
            "epizootias_en_estudio": en_estudio_periodo,
            "actividad_total": casos_periodo + epizootias_periodo,
            "categoria_actividad": get_activity_level(casos_periodo, epizootias_periodo),
        })

    return pd.DataFrame(temporal_data)

def get_activity_level(casos, epizootias):
    """Categoriza nivel de actividad."""
    total = casos + epizootias
    if total == 0:
        return "Sin actividad"
    elif total <= 2:
        return "Actividad baja"
    elif total <= 5:
        return "Actividad moderada"
    else:
        return "Actividad alta"

def show_evolution_chart(temporal_data, colors, filters):
    """Gráfico de evolución temporal optimizado."""
    active_filters = filters.get("active_filters", [])
    title_context = f"Filtrado por: {' • '.join(active_filters[:2])}" if active_filters else "Tolima completo"
    
    st.subheader(f"📊 Evolución Temporal: Casos vs Epizootias ({title_context})")

    # Crear gráfico con doble eje Y
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Línea de casos humanos
    fig.add_trace(
        go.Scatter(
            x=temporal_data["periodo"],
            y=temporal_data["casos"],
            mode="lines+markers",
            name="Casos Humanos",
            line=dict(color=colors["danger"], width=4),
            marker=dict(size=8),
        ),
        secondary_y=False,
    )

    # Línea de epizootias
    fig.add_trace(
        go.Scatter(
            x=temporal_data["periodo"],
            y=temporal_data["epizootias"],
            mode="lines+markers",
            name="Epizootias",
            line=dict(color=colors["warning"], width=4, dash="dot"),
            marker=dict(size=8, symbol="diamond"),
        ),
        secondary_y=True,
    )

    # Línea de actividad total
    fig.add_trace(
        go.Scatter(
            x=temporal_data["periodo"],
            y=temporal_data["actividad_total"],
            mode="lines",
            name="Actividad Total",
            line=dict(color=colors["primary"], width=2, dash="dash"),
            opacity=0.7,
        ),
        secondary_y=False,
    )

    # Configurar ejes
    fig.update_xaxes(title_text="Período")
    fig.update_yaxes(title_text="Casos Humanos & Actividad Total", secondary_y=False, color=colors["danger"])
    fig.update_yaxes(title_text="Epizootias", secondary_y=True, color=colors["warning"])

    fig.update_layout(
        height=500,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(248,249,250,0.8)",
    )

    st.plotly_chart(fig, use_container_width=True)

def show_temporal_metrics(temporal_data, colors, filters):
    """Métricas temporales optimizadas."""
    active_filters = filters.get("active_filters", [])
    context_info = "datos filtrados" if active_filters else "datos completos"
    
    st.subheader(f"📊 Métricas Temporales ({context_info})")

    col1, col2, col3, col4 = st.columns(4)

    # Calcular métricas
    periodos_con_casos = (temporal_data["casos"] > 0).sum()
    periodos_con_epizootias = (temporal_data["epizootias"] > 0).sum()
    total_periodos = len(temporal_data)
    max_casos_mes = temporal_data["casos"].max() if not temporal_data.empty else 0
    max_epizootias_mes = temporal_data["epizootias"].max() if not temporal_data.empty else 0

    with col1:
        st.metric("Períodos con Casos", f"{periodos_con_casos}", delta=f"de {total_periodos} meses")

    with col2:
        st.metric("Períodos con Epizootias", f"{periodos_con_epizootias}", delta=f"de {total_periodos} meses")

    with col3:
        st.metric("Pico Máximo Casos", f"{max_casos_mes}")

    with col4:
        st.metric("Pico Máximo Epizootias", f"{max_epizootias_mes}")

    # Información contextual
    if active_filters:
        st.markdown(
            f"""
            <div style="background: {colors['light']}; padding: 15px; border-radius: 10px; margin: 15px 0; border-left: 4px solid {colors['info']};">
                <strong>📍 Contexto:</strong> {' • '.join(active_filters[:2])}<br>
                <strong>⏱️ Período:</strong> {total_periodos} meses con datos disponibles
            </div>
            """,
            unsafe_allow_html=True,
        )

def show_additional_charts(temporal_data, colors, filters):
    """Gráficos adicionales optimizados."""
    active_filters = filters.get("active_filters", [])
    context_title = "Datos Filtrados" if active_filters else "Datos Completos"
    
    st.subheader(f"📈 Análisis Temporal Adicional ({context_title})")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de barras apiladas
        if not temporal_data.empty:
            fig_bars = go.Figure()
            
            fig_bars.add_trace(go.Bar(
                x=temporal_data["año_mes"],
                y=temporal_data["casos"],
                name="Casos Humanos",
                marker_color=colors["danger"],
                opacity=0.8
            ))
            
            fig_bars.add_trace(go.Bar(
                x=temporal_data["año_mes"],
                y=temporal_data["epizootias"],
                name="Epizootias",
                marker_color=colors["warning"],
                opacity=0.8
            ))
            
            if "epizootias_positivas" in temporal_data.columns:
                fig_bars.add_trace(go.Bar(
                    x=temporal_data["año_mes"],
                    y=temporal_data["epizootias_positivas"],
                    name="Positivas",
                    marker_color=colors["danger"],
                    opacity=0.6
                ))
            
            fig_bars.update_layout(
                title=f"Distribución Mensual - {context_title}",
                xaxis_title="Mes",
                yaxis_title="Eventos",
                height=400,
                barmode='group'
            )
            
            st.plotly_chart(fig_bars, use_container_width=True)
    
    with col2:
        # Gráfico de nivel de actividad
        if not temporal_data.empty:
            activity_colors = {
                "Sin actividad": colors["info"],
                "Actividad baja": colors["success"],
                "Actividad moderada": colors["warning"],
                "Actividad alta": colors["primary"]
            }
            
            fig_activity = px.bar(
                temporal_data,
                x="periodo",
                y="actividad_total",
                color="categoria_actividad",
                title=f"Nivel de Actividad ({context_title})",
                color_discrete_map=activity_colors,
                labels={
                    "actividad_total": "Actividad Total",
                    "periodo": "Período",
                    "categoria_actividad": "Nivel"
                }
            )
            
            fig_activity.update_layout(height=400)
            st.plotly_chart(fig_activity, use_container_width=True)

    # Tabla resumen
    show_summary_table(temporal_data, colors, context_title, active_filters)
    
    # Estadísticas descriptivas
    show_descriptive_stats(temporal_data, colors, context_title)

def show_summary_table(temporal_data, colors, context_title, active_filters):
    """Tabla resumen optimizada."""
    st.subheader(f"📋 Resumen Mensual ({context_title})")
    
    if not temporal_data.empty:
        # Preparar tabla
        if "epizootias_positivas" in temporal_data.columns:
            cols = ["año_mes", "casos", "fallecidos", "epizootias_positivas", "epizootias_en_estudio", "epizootias", "categoria_actividad"]
            col_names = ["Mes", "Casos", "Fallecidos", "Positivas", "En Estudio", "Total Epizootias", "Nivel"]
        else:
            cols = ["año_mes", "casos", "fallecidos", "epizootias", "actividad_total", "categoria_actividad"]
            col_names = ["Mes", "Casos", "Fallecidos", "Epizootias", "Total", "Nivel"]
        
        resumen_tabla = temporal_data[cols].copy()
        resumen_tabla.columns = col_names
        resumen_tabla = resumen_tabla.sort_values("Mes", ascending=False)
        
        st.dataframe(resumen_tabla, use_container_width=True, height=300)
        
        # Descarga
        context_suffix = "filtrados" if active_filters else "completos"
        csv_data = resumen_tabla.to_csv(index=False)
        st.download_button(
            label=f"📄 Descargar Análisis ({context_title})",
            data=csv_data,
            file_name=f"temporal_{context_suffix}_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

def show_descriptive_stats(temporal_data, colors, context_title):
    """Estadísticas descriptivas optimizadas."""
    st.markdown(f"### 📊 Estadísticas Descriptivas ({context_title})")
    
    if not temporal_data.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Período más activo
            if temporal_data["actividad_total"].max() > 0:
                max_idx = temporal_data["actividad_total"].idxmax()
                max_period = temporal_data.loc[max_idx, "año_mes"]
                max_value = temporal_data.loc[max_idx, "actividad_total"]
                st.metric("Período Más Activo", max_period, delta=f"{max_value} eventos")
            else:
                st.metric("Período Más Activo", "Sin actividad")
        
        with col2:
            # Duración del seguimiento
            duracion = len(temporal_data)
            fecha_inicio = temporal_data["periodo"].min().strftime('%m/%Y')
            fecha_fin = temporal_data["periodo"].max().strftime('%m/%Y')
            st.metric("Duración", f"{duracion} meses", delta=f"{fecha_inicio} - {fecha_fin}")
        
        with col3:
            # Proporción casos vs epizootias
            total_casos = temporal_data["casos"].sum()
            total_epi = temporal_data["epizootias"].sum()
            
            if total_casos + total_epi > 0:
                prop_casos = (total_casos / (total_casos + total_epi)) * 100
                st.metric("Proporción Casos", f"{prop_casos:.1f}%", delta=f"{total_casos} casos")
            else:
                st.metric("Proporción Casos", "0%")
        
        with col4:
            # Continuidad del seguimiento
            consecutivos = calculate_consecutive_periods(temporal_data)
            st.metric("Mayor Secuencia", f"{consecutivos} meses")

def calculate_consecutive_periods(temporal_data):
    """Calcula períodos consecutivos con actividad."""
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