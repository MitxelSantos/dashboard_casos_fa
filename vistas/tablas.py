"""
Vista de información principal del dashboard de Fiebre Amarilla.
Simplificada y minimalista para profesionales médicos.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
from utils.data_processor import prepare_dataframe_for_display


def show(data_filtered, filters, colors):
    """
    Muestra la vista de información principal simplificada.

    Args:
        data_filtered (dict): Datos filtrados
        filters (dict): Filtros aplicados
        colors (dict): Colores institucionales
    """
    casos = data_filtered["casos"]
    epizootias = data_filtered["epizootias"]

    # Métricas principales sin colores de alerta
    create_main_metrics(casos, epizootias, colors)

    # Secciones informativas
    st.markdown("---")
    show_epidemiological_summary(casos, epizootias, colors)

    st.markdown("---")
    show_geographic_summary(casos, epizootias, colors)


def create_main_metrics(casos, epizootias, colors):
    """
    Crea las métricas principales sin alertas de color.
    """
    # Calcular métricas básicas
    total_casos = len(casos)
    total_epizootias = len(epizootias)

    # Métricas de casos
    fallecidos = 0
    vivos = 0
    letalidad = 0
    if total_casos > 0 and "condicion_final" in casos.columns:
        fallecidos = (casos["condicion_final"] == "Fallecido").sum()
        vivos = (casos["condicion_final"] == "Vivo").sum()
        letalidad = (fallecidos / total_casos * 100) if total_casos > 0 else 0

    # Métricas de epizootias
    positivos_fa = 0
    positividad = 0
    if total_epizootias > 0 and "descripcion" in epizootias.columns:
        positivos_fa = (epizootias["descripcion"] == "POSITIVO FA").sum()
        positividad = (
            (positivos_fa / total_epizootias * 100) if total_epizootias > 0 else 0
        )

    # Métricas geográficas
    municipios_afectados = set()
    if not casos.empty and "municipio_normalizado" in casos.columns:
        municipios_afectados.update(casos["municipio_normalizado"].dropna())
    if not epizootias.empty and "municipio_normalizado" in epizootias.columns:
        municipios_afectados.update(epizootias["municipio_normalizado"].dropna())

    veredas_afectadas = set()
    if not casos.empty and "vereda_normalizada" in casos.columns:
        veredas_afectadas.update(casos["vereda_normalizada"].dropna())
    if not epizootias.empty and "vereda_normalizada" in epizootias.columns:
        veredas_afectadas.update(epizootias["vereda_normalizada"].dropna())

    # Fechas importantes
    ultima_fecha_caso = None
    ultima_fecha_epi_positiva = None

    if not casos.empty and "fecha_inicio_sintomas" in casos.columns:
        fechas_casos = casos["fecha_inicio_sintomas"].dropna()
        if not fechas_casos.empty:
            ultima_fecha_caso = fechas_casos.max()

    if not epizootias.empty and "fecha_recoleccion" in epizootias.columns:
        epi_positivas = epizootias[epizootias["descripcion"] == "POSITIVO FA"]
        if not epi_positivas.empty:
            fechas_positivas = epi_positivas["fecha_recoleccion"].dropna()
            if not fechas_positivas.empty:
                ultima_fecha_epi_positiva = fechas_positivas.max()

    # CSS para tarjetas sin alertas
    st.markdown(
        f"""
    <style>
    .metric-card {{
        background: linear-gradient(135deg, white 0%, #f8f9fa 100%);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease;
        margin-bottom: 20px;
        border-top: 4px solid {colors['primary']};
        min-height: 150px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }}
    
    .metric-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    }}
    
    .card-icon {{
        font-size: 2rem;
        margin-bottom: 10px;
    }}
    
    .card-title {{
        font-size: 0.9rem;
        font-weight: 600;
        color: {colors['dark']};
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    .card-value {{
        font-size: 2rem;
        font-weight: 700;
        color: {colors['primary']};
        margin-bottom: 8px;
        line-height: 1;
    }}
    
    .card-subtitle {{
        font-size: 0.85rem;
        color: #666;
        margin: 0;
    }}
    
    @media (max-width: 768px) {{
        .metric-card {{
            min-height: 120px;
            padding: 15px;
        }}
        
        .card-icon {{
            font-size: 1.5rem;
        }}
        
        .card-value {{
            font-size: 1.5rem;
        }}
    }}
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Primera fila - Casos humanos
    st.subheader("🦠 Casos Humanos")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="card-icon">🦠</div>
            <div class="card-title">Casos Totales</div>
            <div class="card-value">{total_casos}</div>
            <div class="card-subtitle">Confirmados</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="card-icon">💚</div>
            <div class="card-title">Vivos</div>
            <div class="card-value">{vivos}</div>
            <div class="card-subtitle">Pacientes</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="card-icon">⚰️</div>
            <div class="card-title">Fallecidos</div>
            <div class="card-value">{fallecidos}</div>
            <div class="card-subtitle">Letalidad: {letalidad:.1f}%</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col4:
        dias_ultimo_caso = "Sin datos"
        if ultima_fecha_caso:
            dias_ultimo_caso = (datetime.now() - ultima_fecha_caso).days
            fecha_display = ultima_fecha_caso.strftime("%d/%m/%Y")
            dias_display = f"Hace {dias_ultimo_caso} días"
        else:
            fecha_display = "Sin datos"
            dias_display = ""

        st.markdown(
            f"""
        <div class="metric-card">
            <div class="card-icon">📅</div>
            <div class="card-title">Último Caso</div>
            <div class="card-value" style="font-size: 1.2rem;">{fecha_display}</div>
            <div class="card-subtitle">{dias_display}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Segunda fila - Vigilancia de fauna
    st.subheader("🐒 Vigilancia de Fauna")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="card-icon">🐒</div>
            <div class="card-title">Epizootias Totales</div>
            <div class="card-value">{total_epizootias}</div>
            <div class="card-subtitle">Registradas</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="card-icon">🔴</div>
            <div class="card-title">Positivas FA</div>
            <div class="card-value">{positivos_fa}</div>
            <div class="card-subtitle">{positividad:.1f}% del total</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        municipios_count = len(municipios_afectados)
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="card-icon">🏛️</div>
            <div class="card-title">Municipios</div>
            <div class="card-value">{municipios_count}</div>
            <div class="card-subtitle">Con eventos</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col4:
        dias_ultima_epi = "Sin datos"
        if ultima_fecha_epi_positiva:
            dias_ultima_epi = (datetime.now() - ultima_fecha_epi_positiva).days
            fecha_display = ultima_fecha_epi_positiva.strftime("%d/%m/%Y")
            dias_display = f"Hace {dias_ultima_epi} días"
        else:
            fecha_display = "Sin datos"
            dias_display = ""

        st.markdown(
            f"""
        <div class="metric-card">
            <div class="card-icon">🔬</div>
            <div class="card-title">Última Positiva</div>
            <div class="card-value" style="font-size: 1.2rem;">{fecha_display}</div>
            <div class="card-subtitle">{dias_display}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )


def show_epidemiological_summary(casos, epizootias, colors):
    """Muestra resumen epidemiológico con gráficos simples."""
    st.subheader("📊 Resumen Epidemiológico")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🦠 Perfil de Casos**")

        if not casos.empty:
            # Distribución por sexo
            if "sexo" in casos.columns:
                sexo_dist = casos["sexo"].value_counts()
                if not sexo_dist.empty:
                    fig_sexo = px.pie(
                        values=sexo_dist.values,
                        names=sexo_dist.index,
                        title="Distribución por Sexo",
                        color_discrete_map={
                            "Masculino": colors["info"],
                            "Femenino": colors["secondary"],
                        },
                    )
                    fig_sexo.update_layout(height=300, showlegend=True)
                    st.plotly_chart(fig_sexo, use_container_width=True)
        else:
            st.info("No hay datos de casos disponibles.")

    with col2:
        st.markdown("**🐒 Resultados de Análisis**")

        if not epizootias.empty:
            # Distribución por resultado
            if "descripcion" in epizootias.columns:
                resultado_dist = epizootias["descripcion"].value_counts()

                color_map = {
                    "POSITIVO FA": colors["danger"],
                    "NEGATIVO FA": colors["success"],
                    "NO APTA": colors["warning"],
                    "EN ESTUDIO": colors["info"],
                }

                fig_resultado = px.pie(
                    values=resultado_dist.values,
                    names=resultado_dist.index,
                    title="Resultados de Vigilancia",
                    color_discrete_map=color_map,
                )
                fig_resultado.update_layout(height=300, showlegend=True)
                st.plotly_chart(fig_resultado, use_container_width=True)
        else:
            st.info("No hay datos de epizootias disponibles.")


def show_geographic_summary(casos, epizootias, colors):
    """Muestra distribución geográfica simplificada y entendible."""
    st.subheader("📍 Distribución por Municipio")

    # Crear resumen simplificado por municipio
    municipio_data = create_simple_geographic_summary(casos, epizootias)

    if municipio_data.empty:
        st.info("No hay datos geográficos disponibles.")
        return

    # Mostrar top 10 municipios de manera clara
    st.markdown("**Top 10 Municipios con Mayor Actividad**")

    # Crear tabla clara sin background_gradient
    for i, (_, row) in enumerate(municipio_data.head(10).iterrows()):
        if i % 2 == 0:
            bg_color = "#f8f9fa"
        else:
            bg_color = "white"

        st.markdown(
            f"""
        <div style="
            background-color: {bg_color};
            padding: 12px;
            border-radius: 6px;
            margin: 4px 0;
            border-left: 4px solid {colors['primary']};
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="flex: 2;">
                    <strong style="color: {colors['primary']}; font-size: 1rem;">
                        {row['Municipio']}
                    </strong>
                </div>
                <div style="flex: 3; display: flex; gap: 15px; text-align: center; font-size: 0.9rem;">
                    <div>
                        <div style="font-weight: bold; color: {colors['danger']};">{row['Casos']}</div>
                        <div style="font-size: 0.75rem; color: #666;">Casos</div>
                    </div>
                    <div>
                        <div style="font-weight: bold; color: {colors['warning']};">{row['Epizootias_Positivas']}</div>
                        <div style="font-size: 0.75rem; color: #666;">Epi +</div>
                    </div>
                    <div>
                        <div style="font-weight: bold; color: {colors['info']};">{row['Total_Epizootias']}</div>
                        <div style="font-size: 0.75rem; color: #666;">Total Epi</div>
                    </div>
                    <div>
                        <div style="font-weight: bold; color: {colors['dark']};">{row['Fallecidos']}</div>
                        <div style="font-size: 0.75rem; color: #666;">Fallecidos</div>
                    </div>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Gráficos comparativos
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        # Top municipios por casos
        top_casos = municipio_data.nlargest(8, "Casos")
        if not top_casos.empty and top_casos["Casos"].sum() > 0:
            fig = px.bar(
                top_casos,
                x="Casos",
                y="Municipio",
                title="Municipios con Más Casos",
                color="Casos",
                color_continuous_scale="Reds",
                orientation="h",
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay casos para graficar.")

    with col2:
        # Top municipios por epizootias positivas
        top_epi = municipio_data.nlargest(8, "Epizootias_Positivas")
        if not top_epi.empty and top_epi["Epizootias_Positivas"].sum() > 0:
            fig = px.bar(
                top_epi,
                x="Epizootias_Positivas",
                y="Municipio",
                title="Municipios con Más Epizootias Positivas",
                color="Epizootias_Positivas",
                color_continuous_scale="Oranges",
                orientation="h",
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay epizootias positivas para graficar.")

    # Botón de exportación
    st.markdown("---")
    csv_data = municipio_data.to_csv(index=False)
    st.download_button(
        label="📄 Exportar Datos por Municipio",
        data=csv_data,
        file_name=f"municipios_fiebre_amarilla_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )


def create_simple_geographic_summary(casos, epizootias):
    """
    Crea un resumen geográfico simple y entendible.
    Corrige la lógica para ser más clara.
    """
    municipio_data = []

    # Obtener todos los municipios únicos de ambos datasets
    municipios_casos = set()
    municipios_epi = set()

    if not casos.empty and "municipio" in casos.columns:
        municipios_casos.update(casos["municipio"].dropna())

    if not epizootias.empty and "municipio" in epizootias.columns:
        municipios_epi.update(epizootias["municipio"].dropna())

    todos_municipios = sorted(municipios_casos.union(municipios_epi))

    for municipio in todos_municipios:
        # Contar casos en este municipio
        casos_municipio = 0
        fallecidos_municipio = 0
        if not casos.empty and "municipio" in casos.columns:
            casos_mpio = casos[casos["municipio"] == municipio]
            casos_municipio = len(casos_mpio)

            if "condicion_final" in casos_mpio.columns:
                fallecidos_municipio = (
                    casos_mpio["condicion_final"] == "Fallecido"
                ).sum()

        # Contar epizootias en este municipio
        total_epizootias = 0
        epizootias_positivas = 0
        if not epizootias.empty and "municipio" in epizootias.columns:
            epi_mpio = epizootias[epizootias["municipio"] == municipio]
            total_epizootias = len(epi_mpio)

            if "descripcion" in epi_mpio.columns:
                epizootias_positivas = (epi_mpio["descripcion"] == "POSITIVO FA").sum()

        # Calcular total de eventos (para ordenar)
        total_eventos = casos_municipio + epizootias_positivas

        # Solo incluir municipios con al menos algún evento
        if total_eventos > 0:
            municipio_data.append(
                {
                    "Municipio": municipio,
                    "Casos": casos_municipio,
                    "Fallecidos": fallecidos_municipio,
                    "Epizootias_Positivas": epizootias_positivas,
                    "Total_Epizootias": total_epizootias,
                    "Total_Eventos": total_eventos,
                }
            )

    if municipio_data:
        df = pd.DataFrame(municipio_data)
        # Ordenar por total de eventos (casos + epizootias positivas)
        return df.sort_values("Total_Eventos", ascending=False)

    return pd.DataFrame()
