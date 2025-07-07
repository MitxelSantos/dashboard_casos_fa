"""
Vista de seguimiento temporal CORREGIDA del dashboard de Fiebre Amarilla.
CORRECCIÓN CRÍTICA:
- TODAS las funciones garantizan uso de datos filtrados recibidos
- Verificación explícita en cada función de análisis temporal
- Eliminación completa de accesos a datos originales
- Logging detallado para debugging de filtros temporales
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging

# Configurar logging
logger = logging.getLogger(__name__)

def show(data_filtered, filters, colors):
    """
    Vista de seguimiento temporal CORREGIDA - GARANTIZA USO DE DATOS FILTRADOS.

    Args:
        data_filtered (dict): DATOS YA FILTRADOS por el sistema principal
        filters (dict): Filtros aplicados (para información)
        colors (dict): Colores institucionales
    """
    logger.info("📈 INICIANDO VISTA TEMPORAL CON DATOS FILTRADOS")
    
    # **VERIFICACIÓN CRÍTICA INICIAL**
    casos_filtrados = data_filtered["casos"]
    epizootias_filtradas = data_filtered["epizootias"]  # Ya solo son positivas + en estudio
    
    # **LOG DE VERIFICACIÓN**
    logger.info(f"📈 Vista temporal recibió: {len(casos_filtrados)} casos filtrados, {len(epizootias_filtradas)} epizootias filtradas")
    
    # **VERIFICAR QUE SON DATAFRAMES VÁLIDOS**
    if not isinstance(casos_filtrados, pd.DataFrame):
        logger.error(f"❌ casos_filtrados no es DataFrame: {type(casos_filtrados)}")
        st.error("Error: datos de casos no válidos")
        return
    
    if not isinstance(epizootias_filtradas, pd.DataFrame):
        logger.error(f"❌ epizootias_filtradas no es DataFrame: {type(epizootias_filtradas)}")
        st.error("Error: datos de epizootias no válidos")
        return

    # **MOSTRAR INFO DE CONTEXTO DE FILTRADO**
    active_filters = filters.get("active_filters", [])
    if active_filters:
        st.info(f"📈 Análisis temporal de datos filtrados: {' • '.join(active_filters[:2])}")
        logger.info(f"📈 Mostrando análisis temporal con filtros: {active_filters}")
    else:
        st.info("📈 Análisis temporal de datos completos del Tolima")
        logger.info("📈 Mostrando análisis temporal sin filtros (datos completos)")

    if casos_filtrados.empty and epizootias_filtradas.empty:
        st.warning("No hay datos disponibles para el seguimiento temporal con los filtros aplicados.")
        return

    # **CREAR ANÁLISIS TEMPORAL CON DATOS FILTRADOS VERIFICADOS**
    temporal_data = create_temporal_analysis_GUARANTEED_FILTERED(casos_filtrados, epizootias_filtradas)

    if temporal_data.empty:
        st.info("No hay suficientes datos temporales para el análisis con los filtros aplicados.")
        return

    # **SECCIÓN 1: Gráfico temporal principal con datos filtrados**
    show_temporal_evolution_chart_VERIFIED(temporal_data, colors, filters)

    # **SECCIÓN 2: Métricas temporales básicas con datos filtrados**
    st.markdown("---")
    show_temporal_metrics_GUARANTEED_FILTERED(temporal_data, casos_filtrados, epizootias_filtradas, colors, filters)

    # **SECCIÓN 3: Gráficos adicionales con datos filtrados**
    st.markdown("---")
    show_additional_charts_VERIFIED(temporal_data, colors, filters)

def create_temporal_analysis_GUARANTEED_FILTERED(casos_filtrados, epizootias_filtradas):
    """
    CORREGIDO: Análisis temporal que GARANTIZA uso de datos filtrados.
    
    Args:
        casos_filtrados (pd.DataFrame): Casos filtrados por el sistema principal
        epizootias_filtradas (pd.DataFrame): Epizootias filtradas por el sistema principal
        
    Returns:
        pd.DataFrame: Análisis temporal de los datos filtrados
    """
    logger.info(f"🔄 Creando análisis temporal con datos filtrados: {len(casos_filtrados)} casos, {len(epizootias_filtradas)} epizootias")
    
    # **VERIFICACIÓN EXPLÍCITA**
    from utils.data_processor import verify_filtered_data_usage, debug_data_flow
    
    verify_filtered_data_usage(casos_filtrados, "create_temporal_analysis - casos_filtrados")
    verify_filtered_data_usage(epizootias_filtradas, "create_temporal_analysis - epizootias_filtradas")
    
    # DEBUG: Registrar el uso de datos filtrados
    debug_data_flow(
        {"casos": casos_filtrados, "epizootias": epizootias_filtradas},
        {"casos": casos_filtrados, "epizootias": epizootias_filtradas},
        {},
        "ANALISIS_TEMPORAL_FILTRADO"
    )
    
    temporal_data = []

    # **OBTENER FECHAS DE AMBOS DATASETS FILTRADOS ÚNICAMENTE**
    fechas_casos = []
    if not casos_filtrados.empty and "fecha_inicio_sintomas" in casos_filtrados.columns:
        fechas_casos = casos_filtrados["fecha_inicio_sintomas"].dropna().tolist()

    fechas_epi = []
    if not epizootias_filtradas.empty and "fecha_recoleccion" in epizootias_filtradas.columns:
        fechas_epi = epizootias_filtradas["fecha_recoleccion"].dropna().tolist()

    todas_fechas = fechas_casos + fechas_epi

    if not todas_fechas:
        logger.warning("⚠️ No hay fechas válidas en los datos filtrados para análisis temporal")
        return pd.DataFrame()

    logger.info(f"📅 Rango temporal en datos filtrados: {min(todas_fechas).strftime('%Y-%m-%d')} a {max(todas_fechas).strftime('%Y-%m-%d')}")

    # Crear rango mensual desde la primera fecha hasta la última
    fecha_min = min(todas_fechas).replace(day=1)
    fecha_max = max(todas_fechas)

    # Generar períodos mensuales
    periodos = pd.date_range(start=fecha_min, end=fecha_max, freq="MS")
    logger.info(f"📊 Generando análisis para {len(periodos)} períodos mensuales")

    for periodo in periodos:
        fin_periodo = (periodo + pd.DateOffset(months=1)) - pd.DateOffset(days=1)

        # **CONTAR CASOS EN EL PERÍODO DE DATOS FILTRADOS ÚNICAMENTE**
        casos_periodo = 0
        fallecidos_periodo = 0
        if not casos_filtrados.empty and "fecha_inicio_sintomas" in casos_filtrados.columns:
            casos_mes = casos_filtrados[
                (casos_filtrados["fecha_inicio_sintomas"] >= periodo)
                & (casos_filtrados["fecha_inicio_sintomas"] <= fin_periodo)
            ]
            casos_periodo = len(casos_mes)

            if "condicion_final" in casos_mes.columns:
                fallecidos_periodo = (casos_mes["condicion_final"] == "Fallecido").sum()
                
        # **EPIZOOTIAS DE DATOS FILTRADOS ÚNICAMENTE**
        epizootias_periodo = 0
        positivas_periodo = 0
        en_estudio_periodo = 0
        if not epizootias_filtradas.empty and "fecha_recoleccion" in epizootias_filtradas.columns:
            epi_mes = epizootias_filtradas[
                (epizootias_filtradas["fecha_recoleccion"] >= periodo)
                & (epizootias_filtradas["fecha_recoleccion"] <= fin_periodo)
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
            "categoria_actividad": categorize_activity_level(casos_periodo, epizootias_periodo),
        })

    logger.info(f"✅ Análisis temporal creado: {len(temporal_data)} períodos analizados")
    return pd.DataFrame(temporal_data)

def categorize_activity_level(casos, epizootias):
    """Categorización descriptiva de nivel de actividad."""
    actividad_total = casos + epizootias
    
    if actividad_total == 0:
        return "Sin actividad"
    elif actividad_total <= 2:
        return "Actividad baja"
    elif actividad_total <= 5:
        return "Actividad moderada"
    else:
        return "Actividad alta"

def show_temporal_evolution_chart_VERIFIED(temporal_data, colors, filters):
    """
    CORREGIDO: Gráfico de evolución temporal que especifica datos filtrados.
    """
    logger.info(f"📊 Creando gráfico temporal con {len(temporal_data)} períodos")
    
    # **TÍTULO CONTEXTUAL SEGÚN FILTROS**
    active_filters = filters.get("active_filters", [])
    if active_filters:
        title_context = f"Filtrado por: {' • '.join(active_filters[:2])}"
        if len(active_filters) > 2:
            title_context += f" • +{len(active_filters)-2} más"
    else:
        title_context = "Tolima completo"
    
    st.subheader(f"📊 Evolución Temporal: Casos vs Epizootias ({title_context})")

    # Crear gráfico con doble eje Y
    fig = make_subplots(
        specs=[[{"secondary_y": True}]],
        subplot_titles=[f"Seguimiento de Eventos Confirmados - {title_context}"],
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
            text=f"Evolución temporal de datos filtrados - {title_context}",
            x=0.5,
            font=dict(size=14),
        ),
    )

    st.plotly_chart(fig, use_container_width=True)

def show_temporal_metrics_GUARANTEED_FILTERED(temporal_data, casos_filtrados, epizootias_filtradas, colors, filters):
    """
    CORREGIDO: Métricas temporales que GARANTIZAN uso de datos filtrados.
    """
    logger.info(f"📊 Calculando métricas temporales con datos filtrados: {len(casos_filtrados)} casos, {len(epizootias_filtradas)} epizootias")
    
    # **VERIFICACIÓN EXPLÍCITA**
    from utils.data_processor import verify_filtered_data_usage
    verify_filtered_data_usage(casos_filtrados, "show_temporal_metrics - casos_filtrados")
    verify_filtered_data_usage(epizootias_filtradas, "show_temporal_metrics - epizootias_filtradas")
    
    # **TÍTULO CONTEXTUAL**
    active_filters = filters.get("active_filters", [])
    context_info = "datos filtrados" if active_filters else "datos completos"
    
    st.subheader(f"📊 Métricas Temporales ({context_info})")

    col1, col2, col3, col4 = st.columns(4)

    # **TOTALES POR PERÍODO DE DATOS FILTRADOS ÚNICAMENTE**
    periodos_con_casos = (temporal_data["casos"] > 0).sum()
    periodos_con_epizootias = (temporal_data["epizootias"] > 0).sum()
    total_periodos = len(temporal_data)

    # **PICOS MÁXIMOS DE DATOS FILTRADOS ÚNICAMENTE**
    max_casos_mes = temporal_data["casos"].max() if not temporal_data.empty else 0
    max_epizootias_mes = temporal_data["epizootias"].max() if not temporal_data.empty else 0

    with col1:
        st.metric(
            label="Períodos con Casos",
            value=f"{periodos_con_casos}",
            delta=f"de {total_periodos} meses",
            help=f"Meses con al menos un caso humano en {context_info}",
        )

    with col2:
        st.metric(
            label="Períodos con Epizootias",
            value=f"{periodos_con_epizootias}",
            delta=f"de {total_periodos} meses",
            help=f"Meses con al menos una epizootia en {context_info}",
        )

    with col3:
        st.metric(
            label="Pico Máximo Casos",
            value=f"{max_casos_mes}",
            help=f"Mayor número de casos en un mes ({context_info})",
        )

    with col4:
        st.metric(
            label="Pico Máximo Epizootias",
            value=f"{max_epizootias_mes}",
            help=f"Mayor número de epizootias en un mes ({context_info})",
        )

    # **INFORMACIÓN CONTEXTUAL DE FILTRADO**
    if active_filters:
        st.markdown(
            f"""
            <div style="background: {colors['light']}; padding: 15px; border-radius: 10px; margin: 15px 0; border-left: 4px solid {colors['info']};">
                <strong>📍 Contexto de Análisis:</strong> {' • '.join(active_filters[:2])}<br>
                <strong>📊 Datos incluidos:</strong> Solo eventos que cumplen los filtros aplicados<br>
                <strong>⏱️ Período analizado:</strong> {total_periodos} meses con datos disponibles
            </div>
            """,
            unsafe_allow_html=True,
        )

def show_additional_charts_VERIFIED(temporal_data, colors, filters):
    """
    CORREGIDO: Gráficos adicionales que especifican uso de datos filtrados.
    """
    logger.info(f"📈 Creando gráficos adicionales con {len(temporal_data)} períodos de datos filtrados")
    
    # **TÍTULO CONTEXTUAL**
    active_filters = filters.get("active_filters", [])
    context_title = "Datos Filtrados" if active_filters else "Datos Completos"
    
    st.subheader(f"📈 Análisis Temporal Adicional ({context_title})")
    
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
            if "epizootias_positivas" in temporal_data.columns:
                fig_bars.add_trace(go.Bar(
                    x=temporal_data["año_mes"],
                    y=temporal_data["epizootias_positivas"],
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
                title=f"Distribución Mensual - {context_title}",
                xaxis_title="Mes",
                yaxis_title="Número de Eventos",
                height=400,
                barmode='group'
            )
            
            st.plotly_chart(fig_bars, use_container_width=True)
    
    with col2:
        # Gráfico de nivel de actividad
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
                title=f"Nivel de Actividad por Período ({context_title})",
                color_discrete_map=activity_colors,
                labels={
                    "actividad_total": "Actividad Total",
                    "periodo": "Período",
                    "categoria_actividad": "Nivel de Actividad"
                }
            )
            
            fig_activity.update_layout(height=400)
            st.plotly_chart(fig_activity, use_container_width=True)

    # **TABLA RESUMEN MENSUAL CON INFORMACIÓN DE FILTRADO**
    st.subheader(f"📋 Resumen Mensual ({context_title})")
    
    if not temporal_data.empty:
        # Incluir desglose de epizootias si está disponible
        if "epizootias_positivas" in temporal_data.columns:
            resumen_tabla = temporal_data[["año_mes", "casos", "fallecidos", "epizootias_positivas", "epizootias_en_estudio", "epizootias", "categoria_actividad"]].copy()
            resumen_tabla.columns = ["Mes", "Casos (Filtrados)", "Fallecidos (Filtrados)", "Positivas (Filtradas)", "En Estudio (Filtradas)", "Total Epizootias (Filtradas)", "Nivel de Actividad"]
        else:
            resumen_tabla = temporal_data[["año_mes", "casos", "fallecidos", "epizootias", "actividad_total", "categoria_actividad"]].copy()
            resumen_tabla.columns = ["Mes", "Casos (Filtrados)", "Fallecidos (Filtrados)", "Epizootias (Filtradas)", "Actividad Total (Filtrada)", "Nivel de Actividad"]
        
        # Ordenar por mes descendente
        resumen_tabla = resumen_tabla.sort_values("Mes", ascending=False)
        
        st.dataframe(resumen_tabla, use_container_width=True, height=300)
        
        # **INFORMACIÓN CONTEXTUAL PARA EXPORTACIÓN**
        context_suffix = "filtrados" if active_filters else "completos"
        export_filename = f"analisis_temporal_{context_suffix}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv"
        
        # Opción de descarga
        csv_temporal = resumen_tabla.to_csv(index=False)
        st.download_button(
            label=f"📄 Descargar Análisis Temporal ({context_title})",
            data=csv_temporal,
            file_name=export_filename,
            mime="text/csv",
            help=f"Descarga el análisis temporal de {context_suffix}"
        )

    # **ESTADÍSTICAS ADICIONALES DESCRIPTIVAS CON DATOS FILTRADOS**
    st.markdown("---")
    st.markdown(f"### 📊 Estadísticas Descriptivas ({context_title})")
    
    if not temporal_data.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Período más activo
            if temporal_data["actividad_total"].max() > 0:
                max_activity_idx = temporal_data["actividad_total"].idxmax()
                max_activity_period = temporal_data.loc[max_activity_idx, "año_mes"]
                max_activity_value = temporal_data.loc[max_activity_idx, "actividad_total"]
                
                st.metric(
                    label="Período Más Activo",
                    value=max_activity_period,
                    delta=f"{max_activity_value} eventos",
                    help=f"Mes con mayor actividad registrada en {context_title.lower()}"
                )
            else:
                st.metric("Período Más Activo", "Sin actividad", help="No hay actividad en los datos filtrados")
        
        with col2:
            # Duración del seguimiento
            fecha_inicio = temporal_data["periodo"].min()
            fecha_fin = temporal_data["periodo"].max()
            duracion_meses = len(temporal_data)
            
            st.metric(
                label="Duración Seguimiento",
                value=f"{duracion_meses} meses",
                delta=f"{fecha_inicio.strftime('%m/%Y')} - {fecha_fin.strftime('%m/%Y')}",
                help=f"Período total de seguimiento en {context_title.lower()}"
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
                    help=f"Porcentaje de eventos que son casos humanos en {context_title.lower()}"
                )
            else:
                st.metric("Proporción Casos", "0%", help="Sin eventos en los datos filtrados")
        
        with col4:
            # Continuidad del seguimiento
            periodos_consecutivos = calculate_consecutive_periods(temporal_data)
            st.metric(
                label="Mayor Secuencia Activa",
                value=f"{periodos_consecutivos} meses",
                help=f"Mayor número de meses consecutivos con actividad en {context_title.lower()}"
            )

    # **INFORMACIÓN FINAL DE CONTEXTO**
    if active_filters:
        st.markdown(
            f"""
            <div style="background: {colors['light']}; padding: 15px; border-radius: 10px; margin: 20px 0; border-left: 4px solid {colors['primary']};">
                <strong>ℹ️ Información Importante:</strong><br>
                • Este análisis temporal muestra únicamente los datos que cumplen con los filtros aplicados<br>
                • Filtros activos: {' • '.join(active_filters[:3])}<br>
                • Para ver el análisis completo del Tolima, limpie todos los filtros en el sidebar<br>
                • Las estadísticas y gráficos reflejan la actividad solo en el contexto filtrado
            </div>
            """,
            unsafe_allow_html=True,
        )

def calculate_consecutive_periods(temporal_data):
    """
    Calcula el mayor número de períodos consecutivos con actividad.
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