"""
Vista de análisis comparativo del dashboard de Fiebre Amarilla.
CORREGIDO: Sin dependencia de matplotlib, enfoque médico simplificado.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def show(data_filtered, filters, colors):
    """
    Muestra la vista de análisis comparativo médico simplificado.

    Args:
        data_filtered (dict): Datos filtrados
        filters (dict): Filtros aplicados
        colors (dict): Colores institucionales
    """
    st.markdown(
        '<h1 style="color: #5A4214; border-bottom: 2px solid #F2A900; padding-bottom: 8px;">📊 Análisis Comparativo</h1>',
        unsafe_allow_html=True,
    )

    # Información médica de contexto
    st.markdown(
        f"""
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid {colors['primary']}; margin-bottom: 30px;">
        <h3 style="color: {colors['primary']}; margin-top: 0;">🩺 Análisis Médico Comparativo</h3>
        <p>Comparación epidemiológica entre casos humanos y circulación viral en fauna silvestre.</p>
        <p><strong>Enfoque:</strong> Análisis médico para comprensión de la dinámica de transmisión.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    casos = data_filtered["casos"]
    epizootias = data_filtered["epizootias"]

    if casos.empty and epizootias.empty:
        st.warning("No hay datos disponibles para el análisis comparativo.")
        return

    # Análisis médico en pestañas
    tab1, tab2, tab3 = st.tabs(
        ["🩺 Situación Clínica", "📍 Patrón Geográfico", "📈 Evolución Temporal"]
    )

    with tab1:
        show_clinical_comparison(casos, epizootias, colors)

    with tab2:
        show_geographic_pattern(casos, epizootias, colors)

    with tab3:
        show_temporal_evolution(casos, epizootias, colors)


def show_clinical_comparison(casos, epizootias, colors):
    """Muestra comparación desde perspectiva clínica y epidemiológica."""
    st.subheader("🩺 Situación Clínica vs Vigilancia de Fauna")

    # Métricas clínicas principales
    total_casos = len(casos)
    total_epizootias = len(epizootias)

    # Análisis clínico de casos
    fallecidos = 0
    letalidad = 0
    if not casos.empty and "condicion_final" in casos.columns:
        fallecidos = (casos["condicion_final"] == "Fallecido").sum()
        letalidad = (fallecidos / total_casos * 100) if total_casos > 0 else 0

    # Análisis de circulación viral
    positivos = 0
    positividad = 0
    if not epizootias.empty and "descripcion" in epizootias.columns:
        positivos = (epizootias["descripcion"] == "POSITIVO FA").sum()
        positividad = (
            (positivos / total_epizootias * 100) if total_epizootias > 0 else 0
        )

    # Tarjetas comparativas médicas
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
        <div style="
            background: linear-gradient(135deg, #fff5f5 0%, #ffe6e6 100%);
            border: 2px solid {colors['danger']};
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            margin-bottom: 20px;
        ">
            <div style="font-size: 2rem; margin-bottom: 10px;">🦠</div>
            <div style="font-size: 1.8rem; font-weight: bold; color: {colors['danger']};">{total_casos}</div>
            <div style="font-size: 0.9rem; color: #666; margin: 5px 0;">CASOS HUMANOS</div>
            <div style="font-size: 0.8rem; background: rgba(220,53,69,0.1); padding: 4px 8px; border-radius: 8px;">
                {fallecidos} fallecidos
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
        <div style="
            background: linear-gradient(135deg, #fffbf0 0%, #fef3c7 100%);
            border: 2px solid {colors['warning']};
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            margin-bottom: 20px;
        ">
            <div style="font-size: 2rem; margin-bottom: 10px;">🐒</div>
            <div style="font-size: 1.8rem; font-weight: bold; color: {colors['warning']};">{total_epizootias}</div>
            <div style="font-size: 0.9rem; color: #666; margin: 5px 0;">EPIZOOTIAS</div>
            <div style="font-size: 0.8rem; background: rgba(247,148,29,0.1); padding: 4px 8px; border-radius: 8px;">
                {positivos} positivas
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        color_letalidad = (
            colors["danger"]
            if letalidad > 10
            else colors["warning"] if letalidad > 0 else colors["success"]
        )
        st.markdown(
            f"""
        <div style="
            background: white;
            border: 2px solid {color_letalidad};
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            margin-bottom: 20px;
        ">
            <div style="font-size: 2rem; margin-bottom: 10px;">⚰️</div>
            <div style="font-size: 1.8rem; font-weight: bold; color: {color_letalidad};">{letalidad:.1f}%</div>
            <div style="font-size: 0.9rem; color: #666; margin: 5px 0;">LETALIDAD</div>
            <div style="font-size: 0.8rem; background: rgba(108,117,125,0.1); padding: 4px 8px; border-radius: 8px;">
                Mortalidad clínica
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col4:
        color_positividad = (
            colors["danger"]
            if positividad > 15
            else colors["warning"] if positividad > 0 else colors["success"]
        )
        st.markdown(
            f"""
        <div style="
            background: white;
            border: 2px solid {color_positividad};
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            margin-bottom: 20px;
        ">
            <div style="font-size: 2rem; margin-bottom: 10px;">🔴</div>
            <div style="font-size: 1.8rem; font-weight: bold; color: {color_positividad};">{positividad:.1f}%</div>
            <div style="font-size: 0.9rem; color: #666; margin: 5px 0;">POSITIVIDAD</div>
            <div style="font-size: 0.8rem; background: rgba(108,117,125,0.1); padding: 4px 8px; border-radius: 8px;">
                Circulación viral
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Gráficos comparativos médicos
    st.subheader("📈 Comparación Visual")

    col1, col2 = st.columns(2)

    with col1:
        # Distribución de casos por condición
        if not casos.empty and "condicion_final" in casos.columns:
            condicion_dist = casos["condicion_final"].value_counts()

            fig = px.pie(
                values=condicion_dist.values,
                names=condicion_dist.index,
                title="Estado Clínico de Casos",
                color_discrete_map={
                    "Vivo": colors["success"],
                    "Fallecido": colors["danger"],
                },
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de condición final de casos.")

    with col2:
        # Distribución de epizootias por resultado
        if not epizootias.empty and "descripcion" in epizootias.columns:
            resultado_dist = epizootias["descripcion"].value_counts()

            color_map = {
                "POSITIVO FA": colors["danger"],
                "NEGATIVO FA": colors["success"],
                "NO APTA": colors["warning"],
                "EN ESTUDIO": colors["info"],
            }

            fig = px.pie(
                values=resultado_dist.values,
                names=resultado_dist.index,
                title="Resultados de Vigilancia",
                color_discrete_map=color_map,
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de resultados de epizootias.")

    # Interpretación médica
    st.subheader("🩺 Interpretación Médica")

    ratio_epi_casos = total_epizootias / total_casos if total_casos > 0 else 0

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            label="📊 Ratio Vigilancia/Casos",
            value=f"{ratio_epi_casos:.1f}",
            help="Número de epizootias por cada caso humano confirmado",
        )

    with col2:
        # Interpretación clínica
        if ratio_epi_casos > 5 and positividad > 10:
            interpretacion = "Alta circulación viral con casos humanos limitados"
            recomendacion = "Reforzar prevención y vacunación"
            color_interp = colors["warning"]
        elif letalidad > 10:
            interpretacion = "Casos severos requieren atención clínica intensiva"
            recomendacion = "Mejorar manejo clínico temprano"
            color_interp = colors["danger"]
        elif positivos > 0 and total_casos == 0:
            interpretacion = "Circulación viral detectada sin casos humanos"
            recomendacion = "Mantener vigilancia preventiva"
            color_interp = colors["info"]
        elif total_casos == 0 and total_epizootias == 0:
            interpretacion = "Sin evidencia de actividad viral actual"
            recomendacion = "Continuar vigilancia rutinaria"
            color_interp = colors["success"]
        else:
            interpretacion = "Situación epidemiológica estable"
            recomendacion = "Mantener protocolos actuales"
            color_interp = colors["info"]

        st.markdown(
            f"""
        <div style="background-color: {color_interp}; color: white; padding: 1rem; border-radius: 8px; text-align: center;">
            <strong>🩺 Evaluación Médica:</strong><br>
            {interpretacion}<br><br>
            <strong>💡 Recomendación:</strong><br>
            {recomendacion}
        </div>
        """,
            unsafe_allow_html=True,
        )


def show_geographic_pattern(casos, epizootias, colors):
    """Muestra patrón geográfico desde perspectiva médica."""
    st.subheader("📍 Distribución Geográfica - Enfoque Epidemiológico")

    # Crear datos de distribución geográfica
    geo_data = create_medical_geographic_summary(casos, epizootias)

    if geo_data.empty:
        st.info("No hay suficientes datos geográficos para el análisis.")
        return

    # Tabla médica SIN background_gradient (evita error matplotlib)
    st.write("**📋 Situación Epidemiológica por Municipio:**")

    # Mostrar datos en formato médico amigable
    for _, row in geo_data.head(10).iterrows():
        riesgo_color = (
            colors["danger"]
            if row["Riesgo"] == "ALTO"
            else colors["warning"] if row["Riesgo"] == "MODERADO" else colors["success"]
        )

        st.markdown(
            f"""
        <div style="
            background-color: white;
            border: 1px solid #dee2e6;
            border-left: 4px solid {riesgo_color};
            border-radius: 8px;
            padding: 12px;
            margin: 6px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        ">
            <div style="flex: 2;">
                <strong style="color: {colors['primary']}; font-size: 1rem;">{row['Municipio']}</strong>
                <div style="color: #666; font-size: 0.85rem;">Riesgo: <strong style="color: {riesgo_color};">{row['Riesgo']}</strong></div>
            </div>
            <div style="flex: 3; display: flex; gap: 15px; text-align: center; font-size: 0.9rem;">
                <div>
                    <div style="font-weight: bold; color: {colors['danger']};">{row['Casos']}</div>
                    <div style="font-size: 0.75rem; color: #666;">Casos</div>
                </div>
                <div>
                    <div style="font-weight: bold; color: {colors['warning']};">{row['Epizootias']}</div>
                    <div style="font-size: 0.75rem; color: #666;">Epizootias</div>
                </div>
                <div>
                    <div style="font-weight: bold; color: {colors['info']};">{row['Fallecidos']}</div>
                    <div style="font-size: 0.75rem; color: #666;">Fallecidos</div>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Gráficos geográficos médicos
    col1, col2 = st.columns(2)

    with col1:
        # Top municipios por casos
        top_casos = geo_data.nlargest(8, "Casos")
        if not top_casos.empty and top_casos["Casos"].sum() > 0:
            fig = px.bar(
                top_casos,
                x="Casos",
                y="Municipio",
                title="Municipios con Mayor Carga de Enfermedad",
                color="Casos",
                color_continuous_scale="Reds",
                orientation="h",
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay casos para mostrar.")

    with col2:
        # Top municipios por epizootias
        top_epi = geo_data.nlargest(8, "Epizootias")
        if not top_epi.empty and top_epi["Epizootias"].sum() > 0:
            fig = px.bar(
                top_epi,
                x="Epizootias",
                y="Municipio",
                title="Municipios con Mayor Vigilancia de Fauna",
                color="Epizootias",
                color_continuous_scale="Oranges",
                orientation="h",
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay epizootias para mostrar.")

    # Análisis geográfico médico
    st.subheader("🎯 Análisis Geográfico Médico")

    municipios_casos = set(geo_data[geo_data["Casos"] > 0]["Municipio"])
    municipios_epi = set(geo_data[geo_data["Epizootias"] > 0]["Municipio"])

    coincidencias = municipios_casos.intersection(municipios_epi)
    solo_casos = municipios_casos - municipios_epi
    solo_epi = municipios_epi - municipios_casos

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="🔄 Áreas de Convergencia",
            value=len(coincidencias),
            help="Municipios con casos humanos Y epizootias",
        )

    with col2:
        st.metric(
            label="🦠 Solo Casos Humanos",
            value=len(solo_casos),
            help="Municipios con casos pero sin epizootias detectadas",
        )

    with col3:
        st.metric(
            label="🐒 Solo Vigilancia Fauna",
            value=len(solo_epi),
            help="Municipios con epizootias pero sin casos humanos",
        )

    # Recomendaciones médicas geográficas
    total_municipios = len(municipios_casos.union(municipios_epi))
    if total_municipios > 0:
        porcentaje_coincidencia = (len(coincidencias) / total_municipios) * 100

        st.markdown(
            f"""
        <div style="background-color: #e8f4fd; padding: 15px; border-radius: 8px; border-left: 5px solid {colors['info']};">
            <h5 style="color: {colors['info']}; margin-top: 0;">📊 Evaluación Geográfica Médica</h5>
            <p><strong>Convergencia epidemiológica:</strong> {porcentaje_coincidencia:.1f}% de municipios presentan ambos tipos de eventos.</p>
            <p><strong>Recomendación clínica:</strong> 
            {'Implementar medidas intensivas en áreas de convergencia. Vigilancia estrecha requerida.' if porcentaje_coincidencia > 60 
             else 'Fortalecer vigilancia en áreas de divergencia. Monitoreo preventivo en zonas de riesgo.' if porcentaje_coincidencia > 30
             else 'Establecer corredores de vigilancia entre áreas afectadas. Prevención focalizada.'}
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )


def show_temporal_evolution(casos, epizootias, colors):
    """Muestra evolución temporal desde perspectiva médica."""
    st.subheader("📈 Evolución Temporal - Perspectiva Clínica")

    # Crear series temporales médicas
    temporal_data = create_medical_temporal_summary(casos, epizootias)

    if temporal_data.empty:
        st.info("No hay suficientes datos temporales para el análisis médico.")
        return

    # Gráfico temporal médico
    fig = go.Figure()

    # Línea de casos (eje izquierdo)
    fig.add_trace(
        go.Scatter(
            x=temporal_data["periodo"],
            y=temporal_data["casos"],
            mode="lines+markers",
            name="Casos Humanos",
            line=dict(color=colors["danger"], width=3),
            marker=dict(size=8, symbol="circle"),
            yaxis="y1",
        )
    )

    # Línea de epizootias positivas (eje derecho)
    fig.add_trace(
        go.Scatter(
            x=temporal_data["periodo"],
            y=temporal_data["positivos"],
            mode="lines+markers",
            name="Epizootias Positivas",
            line=dict(color=colors["warning"], width=3),
            marker=dict(size=8, symbol="diamond"),
            yaxis="y2",
        )
    )

    # Configurar layout médico
    fig.update_layout(
        title="Evolución Epidemiológica: Casos Humanos vs Circulación Viral",
        xaxis_title="Período",
        yaxis=dict(
            title="Casos Humanos", side="left", color=colors["danger"], showgrid=True
        ),
        yaxis2=dict(
            title="Epizootias Positivas",
            side="right",
            overlaying="y",
            color=colors["warning"],
            showgrid=False,
        ),
        height=500,
        hovermode="x unified",
        legend=dict(x=0.02, y=0.98),
        plot_bgcolor="rgba(248,249,250,0.8)",
    )

    st.plotly_chart(fig, use_container_width=True)

    # Análisis temporal médico
    st.subheader("📊 Evaluación Temporal Médica")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🦠 Tendencia de Casos Humanos:**")
        casos_stats = temporal_data["casos"].describe()
        total_casos_periodo = temporal_data["casos"].sum()
        periodos_con_casos = (temporal_data["casos"] > 0).sum()

        st.write(f"- **Total en período:** {int(total_casos_periodo)} casos")
        st.write(f"- **Promedio mensual:** {casos_stats['mean']:.1f} casos")
        st.write(f"- **Pico máximo:** {int(casos_stats['max'])} casos")
        st.write(
            f"- **Períodos activos:** {periodos_con_casos} de {len(temporal_data)}"
        )

    with col2:
        st.markdown("**🐒 Patrón de Circulación Viral:**")
        epi_stats = temporal_data["positivos"].describe()
        total_positivos_periodo = temporal_data["positivos"].sum()
        periodos_con_positivos = (temporal_data["positivos"] > 0).sum()

        st.write(f"- **Total positivas:** {int(total_positivos_periodo)} epizootias")
        st.write(f"- **Promedio mensual:** {epi_stats['mean']:.1f} positivas")
        st.write(f"- **Pico máximo:** {int(epi_stats['max'])} positivas")
        st.write(
            f"- **Períodos activos:** {periodos_con_positivos} de {len(temporal_data)}"
        )

    # Correlación médica simple
    if len(temporal_data) > 3:
        correlacion = temporal_data["casos"].corr(temporal_data["positivos"])

        if abs(correlacion) > 0.5:
            patron = "Correlación significativa entre casos humanos y fauna"
            color_patron = colors["warning"]
        elif abs(correlacion) > 0.3:
            patron = "Correlación moderada entre ambos eventos"
            color_patron = colors["info"]
        else:
            patron = "Eventos independientes en fauna y humanos"
            color_patron = colors["success"]

        st.markdown(
            f"""
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 5px solid {color_patron};">
            <h5 style="color: {color_patron}; margin-top: 0;">📈 Patrón Epidemiológico</h5>
            <p><strong>Correlación temporal:</strong> {correlacion:.2f}</p>
            <p><strong>Interpretación médica:</strong> {patron}</p>
            <p><strong>Implicación clínica:</strong> 
            {'Los eventos en fauna pueden predecir casos humanos. Vigilancia anticipada recomendada.' if abs(correlacion) > 0.5
             else 'Vigilancia coordinada entre fauna y humanos necesaria.' if abs(correlacion) > 0.3
             else 'Vigilancia independiente suficiente para cada tipo de evento.'}
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )


def create_medical_geographic_summary(casos, epizootias):
    """Crea resumen geográfico desde perspectiva médica."""
    geo_data = []

    # Obtener municipios únicos
    municipios_casos = set()
    municipios_epi = set()

    if not casos.empty and "municipio" in casos.columns:
        municipios_casos.update(casos["municipio"].dropna())

    if not epizootias.empty and "municipio" in epizootias.columns:
        municipios_epi.update(epizootias["municipio"].dropna())

    todos_municipios = municipios_casos.union(municipios_epi)

    for municipio in todos_municipios:
        # Contar casos
        casos_count = 0
        fallecidos_count = 0
        if not casos.empty and "municipio" in casos.columns:
            casos_municipio = casos[casos["municipio"] == municipio]
            casos_count = len(casos_municipio)

            if "condicion_final" in casos_municipio.columns:
                fallecidos_count = (
                    casos_municipio["condicion_final"] == "Fallecido"
                ).sum()

        # Contar epizootias
        epi_count = 0
        if not epizootias.empty and "municipio" in epizootias.columns:
            epi_count = (epizootias["municipio"] == municipio).sum()

        # Evaluación médica del riesgo
        if casos_count > 3 or fallecidos_count > 0:
            riesgo = "ALTO"
        elif casos_count > 0 or epi_count > 5:
            riesgo = "MODERADO"
        else:
            riesgo = "BAJO"

        geo_data.append(
            {
                "Municipio": municipio,
                "Casos": casos_count,
                "Fallecidos": fallecidos_count,
                "Epizootias": epi_count,
                "Riesgo": riesgo,
                "Total_Eventos": casos_count + epi_count,
            }
        )

    if geo_data:
        df = pd.DataFrame(geo_data)
        return df.sort_values("Total_Eventos", ascending=False)

    return pd.DataFrame()


def create_medical_temporal_summary(casos, epizootias):
    """Crea resumen temporal médico por mes."""
    temporal_data = []

    # Obtener fechas de casos
    fechas_casos = []
    if not casos.empty and "fecha_inicio_sintomas" in casos.columns:
        fechas_casos = casos["fecha_inicio_sintomas"].dropna().tolist()

    # Obtener fechas de epizootias
    fechas_epi = []
    if not epizootias.empty and "fecha_recoleccion" in epizootias.columns:
        fechas_epi = epizootias["fecha_recoleccion"].dropna().tolist()

    todas_fechas = fechas_casos + fechas_epi

    if not todas_fechas:
        return pd.DataFrame()

    # Crear rango mensual
    fecha_min = min(todas_fechas)
    fecha_max = max(todas_fechas)

    periodos = pd.date_range(start=fecha_min.replace(day=1), end=fecha_max, freq="MS")

    for periodo in periodos:
        fin_periodo = (periodo + pd.DateOffset(months=1)) - pd.DateOffset(days=1)

        # Contar casos en el período
        casos_periodo = 0
        if not casos.empty and "fecha_inicio_sintomas" in casos.columns:
            casos_periodo = casos[
                (casos["fecha_inicio_sintomas"] >= periodo)
                & (casos["fecha_inicio_sintomas"] <= fin_periodo)
            ].shape[0]

        # Contar epizootias positivas en el período
        positivos_periodo = 0
        if not epizootias.empty and "fecha_recoleccion" in epizootias.columns:
            epi_periodo = epizootias[
                (epizootias["fecha_recoleccion"] >= periodo)
                & (epizootias["fecha_recoleccion"] <= fin_periodo)
            ]

            if "descripcion" in epi_periodo.columns:
                positivos_periodo = (epi_periodo["descripcion"] == "POSITIVO FA").sum()

        temporal_data.append(
            {"periodo": periodo, "casos": casos_periodo, "positivos": positivos_periodo}
        )

    if temporal_data:
        return pd.DataFrame(temporal_data)

    return pd.DataFrame()
