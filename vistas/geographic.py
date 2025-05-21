"""
Módulo para la vista de distribución geográfica del dashboard de Fiebre Amarilla.
Contiene funciones para visualización de mapas y gráficos por ubicación.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
from pathlib import Path
import requests
import io
import logging

# Configurar logger
logger = logging.getLogger("FiebreAmarilla-Dashboard")

# GeoJSON simplificado de Colombia (departamentos) para cargar desde URL
GEOJSON_URL = "https://gist.githubusercontent.com/john-guerra/43c7656821069d00dcbc/raw/be6a6e239cd5b5b803c6e7c2ec405b793a9064dd/Colombia.geo.json"

# Mapeo de nombres de departamentos para coincidir con el GeoJSON
DPTO_MAPPING = {
    "AMAZONAS": "Amazonas",
    "ANTIOQUIA": "Antioquia",
    "ARAUCA": "Arauca",
    "ATLANTICO": "Atlántico",
    "BOLIVAR": "Bolívar",
    "BOYACA": "Boyacá",
    "CALDAS": "Caldas",
    "CAQUETA": "Caquetá",
    "CASANARE": "Casanare",
    "CAUCA": "Cauca",
    "CESAR": "Cesar",
    "CHOCO": "Chocó",
    "CORDOBA": "Córdoba",
    "CUNDINAMARCA": "Cundinamarca",
    "GUAINIA": "Guainía",
    "GUAVIARE": "Guaviare",
    "HUILA": "Huila",
    "LA GUAJIRA": "La Guajira",
    "MAGDALENA": "Magdalena",
    "META": "Meta",
    "NARIÑO": "Nariño",
    "NORTE DE SANTANDER": "Norte de Santander",
    "PUTUMAYO": "Putumayo",
    "QUINDIO": "Quindío",
    "RISARALDA": "Risaralda",
    "SAN ANDRES Y PROVIDENCIA": "San Andrés y Providencia",
    "SANTANDER": "Santander",
    "SUCRE": "Sucre",
    "TOLIMA": "Tolima",
    "VALLE DEL CAUCA": "Valle del Cauca",
    "VAUPES": "Vaupés",
    "VICHADA": "Vichada",
    "BOGOTA, D.C.": "Bogotá",
}


def load_geojson():
    """
    Carga el archivo GeoJSON de Colombia desde una URL.
    
    Returns:
        dict: Datos GeoJSON para visualización de mapas o None en caso de error.
    """
    try:
        response = requests.get(GEOJSON_URL)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error al cargar GeoJSON: {str(e)}")
        st.error(f"No se pudo cargar el mapa de Colombia: {str(e)}")
        return None


def show(data, filters, colors):
    """
    Muestra la página de distribución geográfica del dashboard.

    Args:
        data (dict): Diccionario con los dataframes
        filters (dict): Filtros seleccionados
        colors (dict): Colores institucionales
    """
    # Usar el mismo estilo mejorado de títulos que en overview.py
    st.markdown('<h1 class="main-title">Distribución Geográfica</h1>', unsafe_allow_html=True)

    # Mostrar descripción general con un diseño más atractivo
    st.markdown(
        f"""
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid {colors['primary']}; margin-bottom: 30px;">
            <h3 style="color: {colors['primary']}; margin-top: 0;">Análisis Geográfico</h3>
            <p>Esta sección muestra la distribución geográfica de los casos de fiebre amarilla por departamento y municipio.
            El análisis permite identificar las zonas con mayor incidencia y planificar intervenciones focalizadas.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Mapa de calor de Colombia por departamentos
    st.markdown('<h2 style="color: #5A4214; border-bottom: 2px solid #F2A900; padding-bottom: 8px;">Mapa de Casos por Departamento</h2>', unsafe_allow_html=True)
    
    # Verificar si tenemos los datos necesarios
    if "ndep_resi" in data["fiebre"].columns:
        try:
            # Cargar GeoJSON
            geojson_data = load_geojson()
            
            if geojson_data:
                # Preparar datos
                depto_count = data["fiebre"]["ndep_resi"].value_counts().reset_index()
                depto_count.columns = ["Departamento", "Cantidad"]
                
                # Normalizar nombres de departamentos (mayúsculas) para mapeo
                depto_count["Departamento"] = depto_count["Departamento"].str.upper()
                
                # Aplicar mapeo para coincidencia con el GeoJSON
                depto_count["Departamento_Norm"] = depto_count["Departamento"].map(
                    lambda x: DPTO_MAPPING.get(x, x)
                )
                
                # Crear mapa coroplético con Plotly
                fig = px.choropleth_mapbox(
                    depto_count,
                    geojson=geojson_data,
                    locations="Departamento_Norm",
                    featureidkey="properties.NOMBRE_DPT",
                    color="Cantidad",
                    color_continuous_scale=[colors["primary"], colors["secondary"]],
                    range_color=[0, depto_count["Cantidad"].max()],
                    mapbox_style="carto-positron",
                    zoom=4.5,
                    center={"lat": 4.5709, "lon": -74.2973},
                    opacity=0.8,
                    labels={"Cantidad": "Número de Casos"}
                )
                
                # Ajustar layout
                fig.update_layout(
                    title="Mapa de Calor de Casos por Departamento",
                    title_font=dict(size=18, color="#5A4214"),
                    margin={"r": 0, "t": 40, "l": 0, "b": 0},
                    height=550,
                )
                
                # Mostrar mapa
                st.plotly_chart(fig, use_container_width=True)
                
                # Añadir nota informativa
                st.info("""
                    **Nota:** Este mapa muestra la concentración de casos por departamento. 
                    Los colores más intensos indican mayor número de casos. Pase el cursor sobre los departamentos para ver detalles.
                """)
            else:
                # Si no se pudo cargar el GeoJSON, mostrar gráfico de barras como alternativa
                st.warning("No se pudo cargar el mapa interactivo. Mostrando visualización alternativa:")
                show_departamentos_chart(data, colors)
        except Exception as e:
            logger.error(f"Error al generar mapa: {str(e)}")
            st.error(f"Error al generar mapa: {str(e)}")
            show_departamentos_chart(data, colors)
    else:
        st.warning("No se encontraron datos sobre departamentos en el archivo.")
        
    # Distribución por departamento (gráfico de barras)
    st.markdown('<h2 style="color: #5A4214; border-bottom: 2px solid #F2A900; padding-bottom: 8px; margin-top: 40px;">Distribución por Departamento</h2>', unsafe_allow_html=True)
    
    if "ndep_resi" in data["fiebre"].columns:
        show_departamentos_chart(data, colors)
    else:
        st.warning("No se encontraron datos sobre departamentos en el archivo.")

    # Distribución por municipio
    st.markdown('<h2 style="color: #5A4214; border-bottom: 2px solid #F2A900; padding-bottom: 8px; margin-top: 40px;">Distribución por Municipio</h2>', unsafe_allow_html=True)
    
    if "nmun_resi" in data["fiebre"].columns:
        # Contar casos por municipio
        muni_count = data["fiebre"]["nmun_resi"].value_counts().reset_index()
        muni_count.columns = ["Municipio", "Cantidad"]
        total_municipios = muni_count["Cantidad"].sum()
        
        # Calcular porcentaje
        muni_count["Porcentaje"] = muni_count["Cantidad"] / total_municipios * 100
        
        # Ordenar por cantidad descendente
        muni_count = muni_count.sort_values("Cantidad", ascending=False)
        
        # Crear gráfico de barras con Plotly
        fig = px.bar(
            muni_count.head(15), 
            y="Municipio", 
            x="Cantidad",
            title="Top 15 Municipios con Casos de Fiebre Amarilla",
            color_discrete_sequence=[colors["secondary"]],
            text="Cantidad",
            orientation="h"
        )
        
        # Configurar diseño
        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=10, r=10, t=40, b=10),
            title={
                "y": 0.98,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
                "font": dict(size=16, color="#5A4214")
            },
            yaxis=dict(title=""),
            xaxis=dict(title="Número de Casos")
        )
        
        # Mostrar gráfico
        st.plotly_chart(fig, use_container_width=True)
        
        # Mostrar tabla con paginación
        st.subheader("Tabla de Casos por Municipio")
        
        # Añadir opción para mostrar más municipios
        num_rows = st.slider(
            "Número de municipios a mostrar",
            min_value=10,
            max_value=min(100, len(muni_count)),
            value=20,
            step=10
        )
        
        # Mostrar tabla con los N municipios principales
        st.dataframe(
            muni_count.head(num_rows).rename(
                columns={
                    "Cantidad": "Casos",
                    "Porcentaje": "Porcentaje (%)"
                }
            ).style.format({
                "Porcentaje (%)": "{:.2f}%"
            }),
            use_container_width=True
        )
    else:
        st.warning("No se encontraron datos sobre municipios en el archivo.")

    # Análisis por departamento y municipio (cruzado)
    st.markdown('<h2 style="color: #5A4214; border-bottom: 2px solid #F2A900; padding-bottom: 8px; margin-top: 40px;">Análisis por Departamento y Municipio</h2>', unsafe_allow_html=True)
    
    if "ndep_resi" in data["fiebre"].columns and "nmun_resi" in data["fiebre"].columns:
        # Agrupar por departamento y municipio
        depto_muni = data["fiebre"].groupby(["ndep_resi", "nmun_resi"]).size().reset_index()
        depto_muni.columns = ["Departamento", "Municipio", "Casos"]
        
        # Ordenar por casos descendentes
        depto_muni = depto_muni.sort_values("Casos", ascending=False)
        
        # Selector de departamento
        selected_depto = st.selectbox(
            "Seleccionar departamento para ver detalle:",
            ["Todos"] + sorted(data["fiebre"]["ndep_resi"].unique().tolist())
        )
        
        if selected_depto != "Todos":
            # Filtrar por departamento seleccionado
            depto_detail = depto_muni[depto_muni["Departamento"] == selected_depto]
            
            if not depto_detail.empty:
                # Mostrar información general del departamento
                total_depto = depto_detail["Casos"].sum()
                num_municipios = len(depto_detail)
                
                # Métricas del departamento seleccionado - estilo mejorado
                st.markdown(
                    f"""
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 30px;">
                        <div class="big-metric-container" style="border-top: 5px solid {colors['primary']}">
                            <div class="big-metric-title">Total Casos</div>
                            <div class="big-metric-value" style="color: {colors['primary']};">{total_depto:,}</div>
                        </div>
                        
                        <div class="big-metric-container" style="border-top: 5px solid {colors['secondary']}">
                            <div class="big-metric-title">Municipios Afectados</div>
                            <div class="big-metric-value" style="color: {colors['secondary']};">{num_municipios}</div>
                        </div>
                        
                        <div class="big-metric-container" style="border-top: 5px solid {colors['accent']}">
                            <div class="big-metric-title">% del Total Nacional</div>
                            <div class="big-metric-value" style="color: {colors['accent']};">{total_depto / depto_muni["Casos"].sum() * 100:.1f}%</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Crear gráfico de barras para municipios del departamento
                fig = px.bar(
                    depto_detail,
                    y="Municipio",
                    x="Casos",
                    title=f"Casos por Municipio en {selected_depto}",
                    color_discrete_sequence=[colors["primary"]],
                    text="Casos",
                    orientation="h"
                )
                
                # Configurar diseño
                fig.update_layout(
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    margin=dict(l=10, r=10, t=40, b=10),
                    title={
                        "y": 0.98,
                        "x": 0.5,
                        "xanchor": "center",
                        "yanchor": "top",
                        "font": dict(size=16, color="#5A4214")
                    },
                    yaxis=dict(title=""),
                    xaxis=dict(title="Número de Casos")
                )
                
                # Mostrar gráfico
                st.plotly_chart(fig, use_container_width=True)
                
                # Mostrar tabla detallada
                st.dataframe(depto_detail, use_container_width=True)
            else:
                st.info(f"No hay datos disponibles para el departamento {selected_depto}.")
        else:
            # Mostrar resumen general
            st.subheader("Resumen General")
            
            # Mostrar tabla con los primeros 20 municipios a nivel nacional
            st.dataframe(depto_muni.head(20), use_container_width=True)
    
    # Análisis de casos por tipo de zona (urbana/rural)
    st.markdown('<h2 style="color: #5A4214; border-bottom: 2px solid #F2A900; padding-bottom: 8px; margin-top: 40px;">Análisis por Tipo de Zona</h2>', unsafe_allow_html=True)
    
    if "tip_zona" in data["fiebre"].columns:
        # Mapeo de códigos a descripciones
        zona_mapping = {
            1: "Cabecera Municipal",
            2: "Centro Poblado",
            3: "Rural Disperso"
        }
        
        # Contar casos por tipo de zona
        zona_count = data["fiebre"]["tip_zona"].value_counts().reset_index()
        zona_count.columns = ["Código Zona", "Cantidad"]
        
        # Aplicar mapeo
        zona_count["Tipo de Zona"] = zona_count["Código Zona"].map(zona_mapping).fillna("No especificado")
        
        # Crear gráfico
        fig = px.pie(
            zona_count,
            names="Tipo de Zona",
            values="Cantidad",
            title="Distribución de Casos por Tipo de Zona",
            color_discrete_sequence=[colors["primary"], colors["secondary"], colors["accent"]],
            hole=0.4
        )
        
        # Mejorar presentación
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label+value',
            textfont_size=12,
            marker=dict(line=dict(color='#FFFFFF', width=2))
        )
        
        # Configurar diseño
        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=10, r=10, t=40, b=10),
            title={
                "y": 0.98,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
                "font": dict(size=16, color="#5A4214")
            },
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.1,
                xanchor="center",
                x=0.5
            )
        )
        
        # Mostrar gráfico
        st.plotly_chart(fig, use_container_width=True)
        
        # Mostrar tabla
        st.dataframe(
            zona_count[["Tipo de Zona", "Cantidad"]],
            use_container_width=True
        )
        
        # Añadir análisis adicional - relación entre zona y severidad
        if "con_fin_" in data["fiebre"].columns:
            st.subheader("Relación entre Tipo de Zona y Condición Final")
            
            # Crear tabla cruzada
            zona_fin = pd.crosstab(
                data["fiebre"]["tip_zona"].map(zona_mapping),
                data["fiebre"]["con_fin_"].map({1: "Vivo", 2: "Fallecido"}),
                margins=True,
                margins_name="Total"
            )
            
            # Mostrar tabla
            st.dataframe(zona_fin, use_container_width=True)
            
            # Calcular letalidad por zona
            st.markdown(
                f"""
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid {colors['primary']}; margin: 20px 0;">
                    <h3 style="color: {colors['primary']}; margin-top: 0;">Análisis de Letalidad por Zona</h3>
                    <p>La zona de residencia puede tener relación con la letalidad debido a factores como el acceso a servicios de salud, 
                    tiempo de desplazamiento a centros médicos, y la prontitud en el diagnóstico y tratamiento.</p>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.warning("No se encontraron datos sobre el tipo de zona.")

    # Pie de página con créditos y fecha de actualización
    fecha_actualizacion = "No disponible"
    if "fecha_actualizacion" in data["metricas"].columns:
        fecha_actualizacion = data["metricas"]["fecha_actualizacion"].iloc[0]
    
    st.markdown(
        f"""
        <div style="text-align: center; margin-top: 50px; padding-top: 20px; border-top: 1px solid #e0e0e0;">
            <p style="color: #666; font-size: 0.9rem;">
                Dashboard desarrollado para la Secretaría de Salud del Tolima | Datos actualizados al {fecha_actualizacion}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


def show_departamentos_chart(data, colors):
    """
    Muestra un gráfico de barras con la distribución por departamento.
    
    Args:
        data (dict): Diccionario con los dataframes
        colors (dict): Colores institucionales
    """
    # Contar casos por departamento
    depto_count = data["fiebre"]["ndep_resi"].value_counts().reset_index()
    depto_count.columns = ["Departamento", "Cantidad"]
    total_casos = depto_count["Cantidad"].sum()
    
    # Calcular porcentaje
    depto_count["Porcentaje"] = depto_count["Cantidad"] / total_casos * 100
    
    # Ordenar por cantidad descendente
    depto_count = depto_count.sort_values("Cantidad", ascending=False)
    
    # Crear gráfico de barras con Plotly
    fig = px.bar(
        depto_count.head(15), 
        y="Departamento", 
        x="Cantidad",
        title="Top 15 Departamentos con Casos de Fiebre Amarilla",
        color_discrete_sequence=[colors["primary"]],
        text="Cantidad",
        orientation="h"
    )
    
    # Configurar diseño
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=10, t=40, b=10),
        title={
            "y": 0.98,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": dict(size=16, color="#5A4214")
        },
        yaxis=dict(title=""),
        xaxis=dict(title="Número de Casos")
    )
    
    # Mostrar gráfico
    st.plotly_chart(fig, use_container_width=True)
    
    # Mostrar tabla completa
    st.subheader("Tabla de Casos por Departamento")
    st.dataframe(
        depto_count.rename(
            columns={
                "Cantidad": "Casos",
                "Porcentaje": "Porcentaje (%)"
            }
        ).style.format({
            "Porcentaje (%)": "{:.2f}%"
        }),
        use_container_width=True
    )