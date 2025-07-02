"""
Vista de análisis comparativo del dashboard de Fiebre Amarilla.
SIMPLIFICADO: Análisis básico y superficial entre casos confirmados y epizootias.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def show(data_filtered, filters, colors):
    """
    Muestra la vista de análisis comparativo simplificado.

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
    st.markdown(
        f"""
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid {colors['primary']}; margin-bottom: 30px;">
        <h3 style="color: {colors['primary']}; margin-top: 0;">Análisis Básico</h3>
        <p>Esta sección presenta un análisis comparativo básico entre casos confirmados y epizootias, 
        mostrando relaciones simples y patrones generales entre ambos tipos de eventos.</p>
        <p><strong>Enfoque:</strong> Análisis informativo y descriptivo para comprensión general.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    casos = data_filtered["casos"]
    epizootias = data_filtered["epizootias"]

    if casos.empty and epizootias.empty:
        st.warning("No hay datos disponibles para el análisis comparativo.")
        return

    # Análisis básico en pestañas
    tab1, tab2, tab3 = st.tabs(
        ["📊 Comparación General", "📍 Distribución Geográfica", "📈 Relación Temporal"]
    )

    with tab1:
        show_general_comparison(casos, epizootias, colors)

    with tab2:
        show_geographic_distribution(casos, epizootias, colors)

    with tab3:
        show_temporal_relationship(casos, epizootias, colors)


def show_general_comparison(casos, epizootias, colors):
    """Muestra comparación general básica."""
    st.subheader("📊 Comparación General")

    # Métricas básicas
    total_casos = len(casos)
    total_epizootias = len(epizootias)

    # Métricas de casos
    fallecidos = 0
    if not casos.empty and "condicion_final" in casos.columns:
        fallecidos = (casos["condicion_final"] == "Fallecido").sum()

    # Métricas de epizootias
    positivos = 0
    if not epizootias.empty and "descripcion" in epizootias.columns:
        positivos = (epizootias["descripcion"] == "POSITIVO FA").sum()

    # Mostrar métricas comparativas
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="🦠 Casos Totales",
            value=total_casos,
            help="Total de casos confirmados",
        )

    with col2:
        st.metric(
            label="🐒 Epizootias Totales",
            value=total_epizootias,
            help="Total de epizootias reportadas",
        )

    with col3:
        st.metric(
            label="⚰️ Casos Fallecidos",
            value=fallecidos,
            delta=f"{(fallecidos/total_casos*100):.1f}%" if total_casos > 0 else "0%",
            help="Casos que resultaron en fallecimiento",
        )

    with col4:
        st.metric(
            label="🔴 Epizootias Positivas",
            value=positivos,
            delta=(
                f"{(positivos/total_epizootias*100):.1f}%"
                if total_epizootias > 0
                else "0%"
            ),
            help="Epizootias positivas para fiebre amarilla",
        )

    # Gráfico comparativo de distribución
    st.subheader("📈 Distribución de Resultados")

    col1, col2 = st.columns(2)

    with col1:
        # Distribución de casos por condición
        if not casos.empty and "condicion_final" in casos.columns:
            condicion_dist = casos["condicion_final"].value_counts()

            fig = px.pie(
                values=condicion_dist.values,
                names=condicion_dist.index,
                title="Casos por Condición Final",
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
                title="Epizootias por Resultado",
                color_discrete_map=color_map,
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de resultados de epizootias.")

    # Relación básica
    st.subheader("🔗 Relación Básica")

    ratio_epi_casos = total_epizootias / total_casos if total_casos > 0 else 0

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            label="📊 Ratio Epizootias/Casos",
            value=f"{ratio_epi_casos:.1f}",
            help="Número de epizootias por cada caso confirmado",
        )

    with col2:
        # Interpretación simple
        if ratio_epi_casos > 5:
            interpretacion = "Alta actividad en fauna vs casos humanos"
            color_interp = colors["warning"]
        elif ratio_epi_casos > 2:
            interpretacion = "Actividad moderada en fauna"
            color_interp = colors["info"]
        elif ratio_epi_casos > 0:
            interpretacion = "Actividad baja en fauna"
            color_interp = colors["success"]
        else:
            interpretacion = "Sin datos de fauna"
            color_interp = colors["dark"]

        st.markdown(
            f"""
        <div style="background-color: {color_interp}; color: white; padding: 1rem; border-radius: 8px; text-align: center;">
            <strong>📝 Interpretación:</strong><br>
            {interpretacion}
        </div>
        """,
            unsafe_allow_html=True,
        )


def show_geographic_distribution(casos, epizootias, colors):
    """Muestra distribución geográfica básica."""
    st.subheader("📍 Distribución Geográfica")

    # Crear datos de distribución geográfica
    geo_data = create_geographic_summary(casos, epizootias)

    if geo_data.empty:
        st.info("No hay suficientes datos geográficos para el análisis.")
        return

    # Tabla de resumen geográfico
    st.write("**📋 Resumen por Municipio:**")
    st.dataframe(
        geo_data.style.background_gradient(subset=["Casos", "Epizootias"], cmap="Reds"),
        use_container_width=True,
        hide_index=True,
    )

    # Gráficos geográficos
    col1, col2 = st.columns(2)

    with col1:
        # Top municipios por casos
        top_casos = geo_data.nlargest(10, "Casos")
        if not top_casos.empty and top_casos["Casos"].sum() > 0:
            fig = px.bar(
                top_casos,
                x="Casos",
                y="Municipio",
                title="Top 10 Municipios - Casos",
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
        top_epi = geo_data.nlargest(10, "Epizootias")
        if not top_epi.empty and top_epi["Epizootias"].sum() > 0:
            fig = px.bar(
                top_epi,
                x="Epizootias",
                y="Municipio",
                title="Top 10 Municipios - Epizootias",
                color="Epizootias",
                color_continuous_scale="Oranges",
                orientation="h",
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay epizootias para mostrar.")

    # Coincidencias geográficas
    st.subheader("🎯 Coincidencias Geográficas")

    municipios_casos = set(geo_data[geo_data["Casos"] > 0]["Municipio"])
    municipios_epi = set(geo_data[geo_data["Epizootias"] > 0]["Municipio"])

    coincidencias = municipios_casos.intersection(municipios_epi)
    solo_casos = municipios_casos - municipios_epi
    solo_epi = municipios_epi - municipios_casos

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="🔄 Municipios con Ambos",
            value=len(coincidencias),
            help="Municipios que reportan tanto casos como epizootias",
        )

    with col2:
        st.metric(
            label="🦠 Solo Casos",
            value=len(solo_casos),
            help="Municipios que solo reportan casos humanos",
        )

    with col3:
        st.metric(
            label="🐒 Solo Epizootias",
            value=len(solo_epi),
            help="Municipios que solo reportan epizootias",
        )

    # Interpretación geográfica simple
    total_municipios = len(municipios_casos.union(municipios_epi))
    if total_municipios > 0:
        porcentaje_coincidencia = (len(coincidencias) / total_municipios) * 100

        st.markdown(
            f"""
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 5px solid {colors['info']};">
            <h5 style="color: {colors['info']};">📊 Análisis Geográfico</h5>
            <p><strong>Coincidencia geográfica:</strong> {porcentaje_coincidencia:.1f}% de los municipios reportan ambos tipos de eventos.</p>
            <p><strong>Interpretación:</strong> 
            {'Alta coincidencia geográfica sugiere relación espacial entre casos humanos y fauna.' if porcentaje_coincidencia > 60 
             else 'Coincidencia moderada en la distribución geográfica.' if porcentaje_coincidencia > 30
             else 'Baja coincidencia geográfica entre casos humanos y eventos en fauna.'}
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )


def show_temporal_relationship(casos, epizootias, colors):
    """Muestra relación temporal básica."""
    st.subheader("📈 Relación Temporal")

    # Crear series temporales básicas
    temporal_data = create_temporal_summary(casos, epizootias)

    if temporal_data.empty:
        st.info("No hay suficientes datos temporales para el análisis.")
        return

    # Gráfico temporal combinado
    fig = go.Figure()

    # Línea de casos
    fig.add_trace(
        go.Scatter(
            x=temporal_data["periodo"],
            y=temporal_data["casos"],
            mode="lines+markers",
            name="Casos Confirmados",
            line=dict(color=colors["danger"], width=3),
            marker=dict(size=8),
        )
    )

    # Línea de epizootias en eje secundario
    fig.add_trace(
        go.Scatter(
            x=temporal_data["periodo"],
            y=temporal_data["epizootias"],
            mode="lines+markers",
            name="Epizootias",
            line=dict(color=colors["warning"], width=3),
            marker=dict(size=8),
            yaxis="y2",
        )
    )

    # Configurar layout
    fig.update_layout(
        title="Evolución Temporal: Casos vs Epizootias",
        xaxis_title="Período",
        yaxis=dict(title="Casos Confirmados", side="left", color=colors["danger"]),
        yaxis2=dict(
            title="Epizootias", side="right", overlaying="y", color=colors["warning"]
        ),
        height=500,
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True)

    # Análisis temporal básico
    st.subheader("📊 Análisis Temporal")

    # Estadísticas básicas por período
    col1, col2 = st.columns(2)

    with col1:
        st.write("**🦠 Casos por Período:**")
        casos_stats = temporal_data["casos"].describe()
        st.write(f"- **Promedio:** {casos_stats['mean']:.1f} casos/período")
        st.write(f"- **Máximo:** {casos_stats['max']:.0f} casos")
        st.write(f"- **Total:** {temporal_data['casos'].sum():.0f} casos")

    with col2:
        st.write("**🐒 Epizootias por Período:**")
        epi_stats = temporal_data["epizootias"].describe()
        st.write(f"- **Promedio:** {epi_stats['mean']:.1f} epizootias/período")
        st.write(f"- **Máximo:** {epi_stats['max']:.0f} epizootias")
        st.write(f"- **Total:** {temporal_data['epizootias'].sum():.0f} epizootias")

    # Tabla de datos temporales
    st.write("**📋 Datos por Período:**")
    temporal_display = temporal_data.copy()
    temporal_display["Total Eventos"] = (
        temporal_display["casos"] + temporal_display["epizootias"]
    )
    temporal_display["Ratio Epi/Casos"] = (
        temporal_display["epizootias"] / temporal_display["casos"]
    )
    temporal_display["Ratio Epi/Casos"] = (
        temporal_display["Ratio Epi/Casos"]
        .replace([np.inf, -np.inf], 0)
        .fillna(0)
        .round(2)
    )

    st.dataframe(
        temporal_display.rename(
            columns={"periodo": "Período", "casos": "Casos", "epizootias": "Epizootias"}
        ),
        use_container_width=True,
        hide_index=True,
    )


def create_geographic_summary(casos, epizootias):
    """Crea resumen geográfico de casos y epizootias."""
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
        if not casos.empty and "municipio" in casos.columns:
            casos_count = (casos["municipio"] == municipio).sum()

        # Contar epizootias
        epi_count = 0
        if not epizootias.empty and "municipio" in epizootias.columns:
            epi_count = (epizootias["municipio"] == municipio).sum()

        # Calcular veredas afectadas
        veredas = set()
        if not casos.empty and "vereda" in casos.columns:
            veredas_casos = casos[casos["municipio"] == municipio]["vereda"].dropna()
            veredas.update(veredas_casos)

        if not epizootias.empty and "vereda" in epizootias.columns:
            veredas_epi = epizootias[epizootias["municipio"] == municipio][
                "vereda"
            ].dropna()
            veredas.update(veredas_epi)

        geo_data.append(
            {
                "Municipio": municipio,
                "Casos": casos_count,
                "Epizootias": epi_count,
                "Veredas Afectadas": len(veredas),
                "Total Eventos": casos_count + epi_count,
            }
        )

    if geo_data:
        df = pd.DataFrame(geo_data)
        return df.sort_values("Total Eventos", ascending=False)

    return pd.DataFrame()


def create_temporal_summary(casos, epizootias):
    """Crea resumen temporal básico por mes."""
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

        # Contar epizootias en el período
        epi_periodo = 0
        if not epizootias.empty and "fecha_recoleccion" in epizootias.columns:
            epi_periodo = epizootias[
                (epizootias["fecha_recoleccion"] >= periodo)
                & (epizootias["fecha_recoleccion"] <= fin_periodo)
            ].shape[0]

        temporal_data.append(
            {"periodo": periodo, "casos": casos_periodo, "epizootias": epi_periodo}
        )

    if temporal_data:
        return pd.DataFrame(temporal_data)

    return pd.DataFrame()
