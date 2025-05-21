import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


def show(data, filters, colors):
    """
    Muestra la página de visión general del dashboard.

    Args:
        data (dict): Diccionario con los dataframes
        filters (dict): Filtros seleccionados
        colors (dict): Colores institucionales
    """
    st.title("Visión General - Fiebre Amarilla")

    # Mostrar descripción general
    st.markdown("""
    La Fiebre Amarilla es una enfermedad viral aguda transmitida por mosquitos, de carácter endémico-epidémico. 
    Este dashboard presenta el análisis de los casos registrados en Colombia, con enfoque en el departamento del Tolima.
    """)

    # Métricas principales
    st.subheader("Métricas Principales")

    # Calcular métricas generales
    total_casos = len(data["fiebre"])
    
    # Métricas de letalidad
    letalidad = 0
    fallecidos = 0
    if "con_fin_" in data["fiebre"].columns:
        fallecidos = data["fiebre"][data["fiebre"]["con_fin_"] == 2].shape[0]
        letalidad = (fallecidos / total_casos * 100) if total_casos > 0 else 0
    
    # Casos confirmados
    confirmados = 0
    if "tip_cas_" in data["fiebre"].columns:
        # Contar casos confirmados (tipos 3, 4 y 5)
        confirmados = data["fiebre"][data["fiebre"]["tip_cas_"].isin([3, 4, 5])].shape[0]
    
    # Mostrar métricas en tarjetas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        create_metric_card(
            title="Total de Casos", 
            value=f"{total_casos:,}".replace(",", "."),
            delta=None,
            color=colors["primary"]
        )
    
    with col2:
        create_metric_card(
            title="Casos Confirmados", 
            value=f"{confirmados:,}".replace(",", "."),
            delta=f"{confirmados/total_casos*100:.1f}% del total" if total_casos > 0 else "0%",
            color=colors["secondary"]
        )
    
    with col3:
        create_metric_card(
            title="Fallecidos", 
            value=f"{fallecidos:,}".replace(",", "."),
            delta=None,
            color=colors["danger"]
        )
    
    with col4:
        create_metric_card(
            title="Tasa de Letalidad", 
            value=f"{letalidad:.2f}%",
            delta=None,
            color=colors["warning"]
        )

    # Distribución por tipo de caso
    st.subheader("Distribución por Tipo de Caso")
    
    if "tip_cas_" in data["fiebre"].columns:
        # Mapeo de códigos a nombres
        tipo_mapping = {
            1: "Sospechoso", 
            2: "Probable", 
            3: "Confirmado por Laboratorio",
            4: "Confirmado por Clínica",
            5: "Confirmado por Nexo Epidemiológico"
        }
        
        # Crear copia del dataframe para la transformación
        df_tipo = data["fiebre"].copy()
        
        # Aplicar mapeo
        df_tipo["tipo_caso_desc"] = df_tipo["tip_cas_"].map(tipo_mapping).fillna("No especificado")
        
        # Contar casos por tipo
        tipo_count = df_tipo["tipo_caso_desc"].value_counts().reset_index()
        tipo_count.columns = ["Tipo de Caso", "Cantidad"]
        
        # Crear gráfico con Plotly
        fig = px.bar(
            tipo_count, 
            x="Tipo de Caso", 
            y="Cantidad",
            title="Distribución por Tipo de Caso",
            color_discrete_sequence=[colors["primary"]]
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
    else:
        st.warning("No se encontraron datos sobre el tipo de caso.")

    # Distribución por condición final
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Condición Final de los Casos")
        
        if "con_fin_" in data["fiebre"].columns:
            # Mapeo de códigos a nombres
            condicion_mapping = {
                1: "Vivo", 
                2: "Fallecido"
            }
            
            # Crear copia del dataframe para la transformación
            df_condicion = data["fiebre"].copy()
            
            # Aplicar mapeo
            df_condicion["condicion_desc"] = df_condicion["con_fin_"].map(condicion_mapping).fillna("No especificado")
            
            # Contar casos por condición
            condicion_count = df_condicion["condicion_desc"].value_counts().reset_index()
            condicion_count.columns = ["Condición Final", "Cantidad"]
            
            # Crear gráfico de pastel con Plotly
            fig = px.pie(
                condicion_count, 
                names="Condición Final", 
                values="Cantidad",
                title="Condición Final de los Casos",
                color_discrete_sequence=[colors["primary"], colors["danger"], colors["accent"]],
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
        else:
            st.warning("No se encontraron datos sobre la condición final.")
    
    with col2:
        st.subheader("Distribución por Sexo")
        
        if "sexo_" in data["fiebre"].columns:
            # Contar casos por sexo
            sexo_count = data["fiebre"]["sexo_"].value_counts().reset_index()
            sexo_count.columns = ["Sexo", "Cantidad"]
            
            # Crear gráfico de pastel con Plotly
            fig = px.pie(
                sexo_count, 
                names="Sexo", 
                values="Cantidad",
                title="Distribución por Sexo",
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
        else:
            st.warning("No se encontraron datos sobre el sexo.")

    # Evolución temporal
    st.subheader("Evolución Temporal de Casos")
    
    if "año" in data["fiebre"].columns:
        # Agrupar por año
        año_count = data["fiebre"]["año"].value_counts().reset_index()
        año_count.columns = ["Año", "Cantidad"]
        año_count = año_count.sort_values("Año")
        
        # Crear gráfico de línea con Plotly
        fig = px.line(
            año_count, 
            x="Año", 
            y="Cantidad",
            title="Evolución Anual de Casos",
            markers=True,
            color_discrete_sequence=[colors["primary"]]
        )
        
        # Agregar puntos para mejor visualización
        fig.add_trace(
            go.Scatter(
                x=año_count["Año"],
                y=año_count["Cantidad"],
                mode="markers",
                marker=dict(color=colors["secondary"], size=8),
                name="Casos por año"
            )
        )
        
        # Configurar diseño
        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=10, r=10, t=40, b=10),
            title={"y": 0.98, "x": 0.5, "xanchor": "center", "yanchor": "top"},
            title_font=dict(size=16),
            showlegend=False
        )
        
        # Mostrar gráfico
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No se encontraron datos sobre el año de los casos.")

    # Distribución geográfica
    st.subheader("Distribución Geográfica")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if "ndep_resi" in data["fiebre"].columns:
            # Contar casos por departamento
            depto_count = data["fiebre"]["ndep_resi"].value_counts().reset_index()
            depto_count.columns = ["Departamento", "Cantidad"]
            depto_count = depto_count.sort_values("Cantidad", ascending=False).head(10)  # Top 10
            
            # Crear gráfico de barras con Plotly
            fig = px.bar(
                depto_count, 
                y="Departamento", 
                x="Cantidad",
                title="Top 10 Departamentos con más Casos",
                color_discrete_sequence=[colors["primary"]],
                orientation="h"
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
        else:
            st.warning("No se encontraron datos sobre departamentos.")
    
    with col2:
        if "nmun_resi" in data["fiebre"].columns:
            # Contar casos por municipio
            muni_count = data["fiebre"]["nmun_resi"].value_counts().reset_index()
            muni_count.columns = ["Municipio", "Cantidad"]
            muni_count = muni_count.sort_values("Cantidad", ascending=False).head(10)  # Top 10
            
            # Crear gráfico de barras con Plotly
            fig = px.bar(
                muni_count, 
                y="Municipio", 
                x="Cantidad",
                title="Top 10 Municipios con más Casos",
                color_discrete_sequence=[colors["secondary"]],
                orientation="h"
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
        else:
            st.warning("No se encontraron datos sobre municipios.")

    # Información adicional - Casos por grupo de edad
    if "edad_" in data["fiebre"].columns:
        st.subheader("Distribución por Grupo de Edad")
        
        # Crear rangos de edad
        def crear_grupo_edad(edad):
            if pd.isna(edad):
                return "No especificado"
            elif edad < 5:
                return "0-4 años"
            elif edad < 15:
                return "5-14 años"
            elif edad < 20:
                return "15-19 años"
            elif edad < 30:
                return "20-29 años"
            elif edad < 40:
                return "30-39 años"
            elif edad < 50:
                return "40-49 años"
            elif edad < 60:
                return "50-59 años"
            elif edad < 70:
                return "60-69 años"
            elif edad < 80:
                return "70-79 años"
            else:
                return "80+ años"
        
        # Aplicar función para crear grupos de edad
        df_edad = data["fiebre"].copy()
        df_edad["grupo_edad"] = df_edad["edad_"].apply(crear_grupo_edad)
        
        # Orden de los grupos de edad
        orden_grupos = [
            "0-4 años", "5-14 años", "15-19 años", "20-29 años",
            "30-39 años", "40-49 años", "50-59 años", "60-69 años",
            "70-79 años", "80+ años", "No especificado"
        ]
        
        # Contar casos por grupo de edad
        edad_count = df_edad["grupo_edad"].value_counts().reset_index()
        edad_count.columns = ["Grupo de Edad", "Cantidad"]
        
        # Reordenar según el orden definido
        if set(edad_count["Grupo de Edad"]).issubset(set(orden_grupos)):
            edad_count["Grupo de Edad"] = pd.Categorical(
                edad_count["Grupo de Edad"],
                categories=orden_grupos,
                ordered=True
            )
            edad_count = edad_count.sort_values("Grupo de Edad")
        
        # Crear gráfico de barras con Plotly
        fig = px.bar(
            edad_count, 
            x="Grupo de Edad", 
            y="Cantidad",
            title="Distribución por Grupo de Edad",
            color_discrete_sequence=[colors["primary"]]
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
    
    # Distribución por tipo de seguridad social
    if "tip_ss_" in data["fiebre"].columns:
        st.subheader("Distribución por Tipo de Aseguramiento")
        
        # Mapeo de códigos a descripciones
        ss_mapping = {
            "C": "Contributivo",
            "S": "Subsidiado",
            "P": "Excepción",
            "E": "Especial",
            "N": "No asegurado",
            "I": "Indeterminado/Pendiente"
        }
        
        # Crear copia del dataframe para la transformación
        df_ss = data["fiebre"].copy()
        
        # Aplicar mapeo (convertir a string primero para manejar valores numéricos)
        df_ss["ss_desc"] = df_ss["tip_ss_"].astype(str).map(ss_mapping).fillna("No especificado")
        
        # Contar casos por tipo de seguridad social
        ss_count = df_ss["ss_desc"].value_counts().reset_index()
        ss_count.columns = ["Tipo de Seguridad Social", "Cantidad"]
        
        # Crear gráfico de barras con Plotly
        fig = px.bar(
            ss_count, 
            x="Tipo de Seguridad Social", 
            y="Cantidad",
            title="Distribución por Tipo de Aseguramiento",
            color_discrete_sequence=[colors["secondary"]]
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