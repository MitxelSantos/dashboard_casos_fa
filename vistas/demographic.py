import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


def show(data, filters, colors):
    """
    Muestra la página de perfil demográfico del dashboard.

    Args:
        data (dict): Diccionario con los dataframes
        filters (dict): Filtros seleccionados
        colors (dict): Colores institucionales
    """
    st.title("Perfil Demográfico")

    # Mostrar descripción general
    st.markdown("""
    Esta sección analiza las características demográficas de los casos de fiebre amarilla,
    incluyendo distribución por edad, sexo, pertenencia étnica y factores de vulnerabilidad.
    """)

    # Distribución por edad
    st.subheader("Distribución por Edad")

    if "edad_" in data["fiebre"].columns:
        # Estadísticas básicas
        edad_mean = data["fiebre"]["edad_"].mean()
        edad_median = data["fiebre"]["edad_"].median()
        edad_std = data["fiebre"]["edad_"].std()
        edad_min = data["fiebre"]["edad_"].min()
        edad_max = data["fiebre"]["edad_"].max()
        
        # Mostrar estadísticas en columnas
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            create_stat_box("Media", f"{edad_mean:.1f} años", colors["primary"])
        
        with col2:
            create_stat_box("Mediana", f"{edad_median:.0f} años", colors["secondary"])
        
        with col3:
            create_stat_box("Desv. Estándar", f"{edad_std:.1f}", colors["accent"])
        
        with col4:
            create_stat_box("Mínimo", f"{edad_min:.0f} años", colors["primary"])
        
        with col5:
            create_stat_box("Máximo", f"{edad_max:.0f} años", colors["secondary"])
        
        # Histograma de edad
        st.subheader("Distribución de Edad")
        
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
        
        # Histograma de edad (valores continuos)
        st.subheader("Histograma de Edad")
        
        # Filtrar valores nulos
        edad_values = data["fiebre"]["edad_"].dropna()
        
        if not edad_values.empty:
            # Crear histograma con Plotly
            fig = px.histogram(
                edad_values, 
                nbins=20,
                title="Histograma de Edad",
                color_discrete_sequence=[colors["secondary"]]
            )
            
            # Añadir línea de densidad
            fig.update_traces(opacity=0.75)
            
            # Añadir línea para la media
            fig.add_vline(
                x=edad_mean,
                line_dash="dash",
                line_color=colors["accent"],
                annotation_text=f"Media: {edad_mean:.1f}",
                annotation_position="top right"
            )
            
            # Añadir línea para la mediana
            fig.add_vline(
                x=edad_median,
                line_dash="dash",
                line_color=colors["primary"],
                annotation_text=f"Mediana: {edad_median:.0f}",
                annotation_position="top left"
            )
            
            # Configurar diseño
            fig.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                margin=dict(l=10, r=10, t=40, b=10),
                title={"y": 0.98, "x": 0.5, "xanchor": "center", "yanchor": "top"},
                title_font=dict(size=16),
                xaxis_title="Edad (años)",
                yaxis_title="Frecuencia",
            )
            
            # Mostrar gráfico
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No se encontraron datos sobre la edad de los casos.")

    # Distribución por sexo
    st.subheader("Distribución por Sexo")
    
    col1, col2 = st.columns(2)
    
    with col1:
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
            
            # Mostrar tabla de datos
            st.dataframe(sexo_count, use_container_width=True)
        else:
            st.warning("No se encontraron datos sobre el sexo de los casos.")
    
    with col2:
        if "sexo_" in data["fiebre"].columns and "edad_" in data["fiebre"].columns:
            # Crear rangos de edad
            df_edad_sexo = data["fiebre"].copy()
            df_edad_sexo["grupo_edad"] = df_edad_sexo["edad_"].apply(crear_grupo_edad)
            
            # Filtrar valores válidos
            df_edad_sexo = df_edad_sexo[~df_edad_sexo["grupo_edad"].isin(["No especificado"])]
            
            # Crear tabla cruzada
            sexo_edad = pd.crosstab(
                df_edad_sexo["grupo_edad"],
                df_edad_sexo["sexo_"],
                margins=True,
                margins_name="Total"
            )
            
            # Reordenar filas según el orden definido
            if set(sexo_edad.index) - set(["Total"]).issubset(set(orden_grupos)):
                ordered_index = [g for g in orden_grupos if g in sexo_edad.index and g != "No especificado"]
                if "Total" in sexo_edad.index:
                    ordered_index.append("Total")
                sexo_edad = sexo_edad.reindex(ordered_index)
            
            # Mostrar tabla
            st.subheader("Distribución por Sexo y Grupo de Edad")
            st.dataframe(sexo_edad, use_container_width=True)
            
            # Crear gráfico de barras apiladas para visualizar distribución
            # Preparar datos
            sexo_edad_plot = pd.crosstab(
                df_edad_sexo["grupo_edad"],
                df_edad_sexo["sexo_"]
            )
            
            # Convertir a formato largo para Plotly
            sexo_edad_long = sexo_edad_plot.reset_index().melt(
                id_vars="grupo_edad",
                var_name="Sexo",
                value_name="Cantidad"
            )
            
            # Ordenar por grupo de edad
            if set(sexo_edad_long["grupo_edad"]).issubset(set(orden_grupos)):
                sexo_edad_long["grupo_edad"] = pd.Categorical(
                    sexo_edad_long["grupo_edad"],
                    categories=[g for g in orden_grupos if g in sexo_edad_long["grupo_edad"].unique()],
                    ordered=True
                )
                sexo_edad_long = sexo_edad_long.sort_values("grupo_edad")
            
            # Crear gráfico de barras apiladas
            fig = px.bar(
                sexo_edad_long,
                x="grupo_edad",
                y="Cantidad",
                color="Sexo",
                title="Distribución por Sexo y Grupo de Edad",
                color_discrete_sequence=[colors["primary"], colors["secondary"], colors["accent"]],
                barmode="stack"
            )
            
            # Configurar diseño
            fig.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                margin=dict(l=10, r=10, t=40, b=10),
                title={"y": 0.98, "x": 0.5, "xanchor": "center", "yanchor": "top"},
                title_font=dict(size=16),
                xaxis_title="Grupo de Edad",
                yaxis_title="Cantidad"
            )
            
            # Mostrar gráfico
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No se encontraron datos suficientes para el análisis por sexo y edad.")

    # Distribución por pertenencia étnica
    st.subheader("Distribución por Pertenencia Étnica")
    
    if "per_etn_" in data["fiebre"].columns:
        # Mapeo de códigos a nombres
        etnia_mapping = {
            1: "Indígena",
            2: "Gitano",
            3: "Raizal",
            4: "Palenqueros",
            5: "Afrocolombiano",
            6: "Otro"
        }
        
        # Crear copia del dataframe para la transformación
        df_etnia = data["fiebre"].copy()
        
        # Aplicar mapeo
        df_etnia["etnia_desc"] = df_etnia["per_etn_"].map(etnia_mapping).fillna("No especificado")
        
        # Contar casos por etnia
        etnia_count = df_etnia["etnia_desc"].value_counts().reset_index()
        etnia_count.columns = ["Pertenencia Étnica", "Cantidad"]
        
        # Crear gráfico de barras con Plotly
        fig = px.bar(
            etnia_count, 
            x="Pertenencia Étnica", 
            y="Cantidad",
            title="Distribución por Pertenencia Étnica",
            color_discrete_sequence=[colors["primary"]],
            text_auto=True
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
        st.dataframe(etnia_count, use_container_width=True)
    else:
        st.warning("No se encontraron datos sobre pertenencia étnica.")

    # Grupos especiales de poblaciones
    st.subheader("Poblaciones Especiales")
    
    # Definir los grupos a analizar
    grupos_especiales = {
        "gp_discapa": "Discapacidad",
        "gp_desplaz": "Desplazados",
        "gp_migrant": "Migrantes",
        "gp_gestan": "Gestantes",
        "gp_indigen": "Indígenas",
        "gp_carcela": "Carcelarios",
        "gp_pobicbf": "ICBF",
        "gp_vic_vio": "Víctimas de violencia"
    }
    
    # Verificar cuáles existen en el dataframe
    grupos_existentes = [col for col in grupos_especiales.keys() if col in data["fiebre"].columns]
    
    if grupos_existentes:
        # Crear dataframe para almacenar los conteos
        grupos_df = pd.DataFrame(columns=["Grupo", "Sí", "No", "Total"])
        
        # Calcular conteos para cada grupo
        for col in grupos_existentes:
            # Mapeo de valores
            si_count = (data["fiebre"][col] == 1).sum()
            no_count = (data["fiebre"][col] == 2).sum()
            total = si_count + no_count
            
            # Añadir al dataframe
            grupos_df = pd.concat([
                grupos_df,
                pd.DataFrame({
                    "Grupo": [grupos_especiales[col]],
                    "Sí": [si_count],
                    "No": [no_count],
                    "Total": [total],
                    "Porcentaje Sí": [si_count / total * 100 if total > 0 else 0]
                })
            ])
        
        # Ordenar por porcentaje descendente
        grupos_df = grupos_df.sort_values("Porcentaje Sí", ascending=False)
        
        # Crear visualización
        if len(grupos_df) > 0:
            # Crear gráfico de barras horizontal
            fig = px.bar(
                grupos_df,
                y="Grupo",
                x="Porcentaje Sí",
                title="Porcentaje de Casos en Poblaciones Especiales",
                color_discrete_sequence=[colors["primary"]],
                text_auto='.1f',
                labels={"Porcentaje Sí": "Porcentaje (%)"}
            )
            
            # Añadir sufijo % a los valores
            fig.update_traces(texttemplate='%{text}%', textposition='outside')
            
            # Configurar diseño
            fig.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                margin=dict(l=10, r=10, t=40, b=10),
                title={"y": 0.98, "x": 0.5, "xanchor": "center", "yanchor": "top"},
                title_font=dict(size=16),
                xaxis=dict(range=[0, max(100, grupos_df["Porcentaje Sí"].max() * 1.1)])
            )
            
            # Mostrar gráfico
            st.plotly_chart(fig, use_container_width=True)
            
            # Mostrar tabla completa
            st.dataframe(
                grupos_df[["Grupo", "Sí", "No", "Total", "Porcentaje Sí"]].rename(
                    columns={"Porcentaje Sí": "Porcentaje Sí (%)"}
                ),
                use_container_width=True
            )
        else:
            st.warning("No se encontraron datos disponibles para poblaciones especiales.")
    else:
        st.warning("No se encontraron columnas de grupos poblacionales especiales en los datos.")

    # Si existe algún grupo específico con más detalle
    if "gp_gestan" in data["fiebre"].columns and "sem_ges_" in data["fiebre"].columns:
        st.subheader("Análisis de Casos en Gestantes")
        
        # Filtrar solo gestantes
        gestantes_df = data["fiebre"][data["fiebre"]["gp_gestan"] == 1].copy()
        
        if len(gestantes_df) > 0:
            # Estadísticas de semanas de gestación
            sem_mean = gestantes_df["sem_ges_"].mean()
            sem_median = gestantes_df["sem_ges_"].median()
            sem_min = gestantes_df["sem_ges_"].min()
            sem_max = gestantes_df["sem_ges_"].max()
            
            # Mostrar estadísticas en columnas
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                create_stat_box("Total Gestantes", f"{len(gestantes_df)}", colors["primary"])
            
            with col2:
                create_stat_box("Promedio Semanas", f"{sem_mean:.1f}", colors["secondary"])
            
            with col3:
                create_stat_box("Mediana Semanas", f"{sem_median:.0f}", colors["accent"])
            
            with col4:
                create_stat_box("Rango Semanas", f"{sem_min:.0f} - {sem_max:.0f}", colors["primary"])
            
            # Crear histograma de semanas de gestación
            fig = px.histogram(
                gestantes_df["sem_ges_"].dropna(),
                nbins=10,
                title="Distribución de Semanas de Gestación",
                color_discrete_sequence=[colors["secondary"]]
            )
            
            # Configurar diseño
            fig.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                margin=dict(l=10, r=10, t=40, b=10),
                title={"y": 0.98, "x": 0.5, "xanchor": "center", "yanchor": "top"},
                title_font=dict(size=16),
                xaxis_title="Semanas de Gestación",
                yaxis_title="Frecuencia",
            )
            
            # Mostrar gráfico
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay casos registrados de gestantes.")


def create_stat_box(title, value, color="#AB0520"):
    """
    Crea una caja de estadística con estilo.
    
    Args:
        title (str): Título de la estadística
        value (str): Valor a mostrar
        color (str): Color de la caja
    """
    # CSS personalizado para crear la caja
    st.markdown(
        f"""
        <div style="background-color: white; padding: 10px; border-radius: 5px; border-left: 5px solid {color}; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1); height: 80px; display: flex; flex-direction: column; justify-content: center;">
            <h4 style="color: #333; font-size: 14px; margin-bottom: 5px; text-align: center;">{title}</h4>
            <p style="color: {color}; font-size: 20px; font-weight: bold; margin: 0; text-align: center;">{value}</p>
        </div>
        """,
        unsafe_allow_html=True
    )