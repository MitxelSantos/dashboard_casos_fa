import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


def show(data, filters, colors):
    """
    Muestra la página de distribución geográfica del dashboard.

    Args:
        data (dict): Diccionario con los dataframes
        filters (dict): Filtros seleccionados
        colors (dict): Colores institucionales
    """
    st.title("Distribución Geográfica")

    # Mostrar descripción general
    st.markdown("""
    Esta sección muestra la distribución geográfica de los casos de fiebre amarilla por departamento y municipio.
    El análisis permite identificar las zonas con mayor incidencia.
    """)

    # Distribución por departamento
    st.subheader("Distribución por Departamento")
    
    if "ndep_resi" in data["fiebre"].columns:
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
            title={"y": 0.98, "x": 0.5, "xanchor": "center", "yanchor": "top"},
            title_font=dict(size=16),
            yaxis=dict(title=""),
            xaxis=dict(title="Número de Casos")
        )
        
        # Mostrar gráfico
        st.plotly_chart(fig, use_container_width=True)
        
        # Crear mapa departamental si hay suficientes datos
        try:
            # Verificar si hay al menos 3 departamentos
            if len(depto_count) >= 3:
                st.subheader("Mapa de Calor por Departamento")
                
                # Crear un mapa de coropletas de Colombia
                st.info("Se requiere un mapa geográfico de Colombia para mostrar la distribución departamental. Por favor, habilite la funcionalidad geoespacial para visualizar este mapa.")
                
                # Nota: En un entorno real, se implementaría esto con geopandas y Folium
                # Pero para esta demostración, solo mostramos un mensaje informativo
        except Exception as e:
            st.error(f"Error al generar mapa: {str(e)}")
        
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
    else:
        st.warning("No se encontraron datos sobre departamentos en el archivo.")

    # Distribución por municipio
    st.subheader("Distribución por Municipio")
    
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
            title={"y": 0.98, "x": 0.5, "xanchor": "center", "yanchor": "top"},
            title_font=dict(size=16),
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
    if "ndep_resi" in data["fiebre"].columns and "nmun_resi" in data["fiebre"].columns:
        st.subheader("Análisis por Departamento y Municipio")
        
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
                
                # Métricas del departamento seleccionado
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    create_metric_card(
                        title="Total Casos",
                        value=f"{total_depto:,}".replace(",", "."),
                        color=colors["primary"]
                    )
                
                with col2:
                    create_metric_card(
                        title="Municipios Afectados",
                        value=str(num_municipios),
                        color=colors["secondary"]
                    )
                
                with col3:
                    # Calcular porcentaje respecto al total nacional
                    total_nacional = depto_muni["Casos"].sum()
                    porcentaje = total_depto / total_nacional * 100
                    create_metric_card(
                        title="% del Total Nacional",
                        value=f"{porcentaje:.1f}%",
                        color=colors["accent"]
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
                    title={"y": 0.98, "x": 0.5, "xanchor": "center", "yanchor": "top"},
                    title_font=dict(size=16),
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
    if "tip_zona" in data["fiebre"].columns:
        st.subheader("Análisis por Tipo de Zona")
        
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
        
        # Configurar diseño
        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=10, r=10, t=40, b=10),
            title={"y": 0.98, "x": 0.5, "xanchor": "center", "yanchor": "top"},
            title_font=dict(size=16),
        )
        
        # Mostrar gráfico
        st.plotly_chart(fig, use_container_width=True)
        
        # Mostrar tabla
        st.dataframe(
            zona_count[["Tipo de Zona", "Cantidad"]],
            use_container_width=True
        )


def create_metric_card(title, value, delta=None, color="#AB0520"):
    """
    Crea una tarjeta de métrica estilizada.
    
    Args:
        title (str): Título de la métrica
        value (str): Valor de la métrica
        delta (str): Texto de cambio o información adicional
        color (str): Color de la tarjeta
    """
    # CSS personalizado para crear la tarjeta
    st.markdown(
        f"""
        <div style="background-color: white; padding: 15px; border-radius: 5px; border-left: 5px solid {color}; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);">
            <h3 style="color: #333; font-size: 16px; margin-bottom: 5px;">{title}</h3>
            <p style="color: {color}; font-size: 24px; font-weight: bold; margin: 0;">{value}</p>
            {f'<p style="color: #666; font-size: 12px; margin-top: 5px;">{delta}</p>' if delta else ''}
        </div>
        """,
        unsafe_allow_html=True
    )