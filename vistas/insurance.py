import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


def show(data, filters, colors):
    """
    Muestra la página de aseguramiento del dashboard.

    Args:
        data (dict): Diccionario con los dataframes
        filters (dict): Filtros seleccionados
        colors (dict): Colores institucionales
    """
    st.title("Análisis de Aseguramiento")

    # Mostrar descripción general
    st.markdown("""
    Esta sección analiza la distribución de casos por tipo de aseguramiento y entidades aseguradoras,
    permitiendo identificar patrones en la cobertura del Sistema General de Seguridad Social en Salud.
    """)

    # Análisis por tipo de seguridad social
    st.subheader("Distribución por Tipo de Aseguramiento")
    
    if "tip_ss_" in data["fiebre"].columns:
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
        df_ss["tip_ss_"] = df_ss["tip_ss_"].astype(str)
        df_ss["ss_desc"] = df_ss["tip_ss_"].map(ss_mapping).fillna("No especificado")
        
        # Contar casos por tipo de seguridad social
        ss_count = df_ss["ss_desc"].value_counts().reset_index()
        ss_count.columns = ["Tipo de Aseguramiento", "Cantidad"]
        
        # Calcular porcentaje
        total_casos = ss_count["Cantidad"].sum()
        ss_count["Porcentaje"] = ss_count["Cantidad"] / total_casos * 100
        
        # Crear gráfico de barras
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = px.bar(
                ss_count, 
                x="Tipo de Aseguramiento", 
                y="Cantidad",
                title="Distribución por Tipo de Aseguramiento",
                color_discrete_sequence=[colors["primary"]],
                text="Cantidad"
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
        
        with col2:
            # Gráfico de pastel para porcentajes
            fig = px.pie(
                ss_count, 
                names="Tipo de Aseguramiento", 
                values="Cantidad",
                title="Distribución Porcentual",
                color_discrete_sequence=[colors["primary"], colors["secondary"], colors["accent"], 
                                         colors["success"], colors["warning"], colors["danger"]],
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
        
        # Mostrar tabla completa
        st.dataframe(
            ss_count.rename(
                columns={
                    "Porcentaje": "Porcentaje (%)"
                }
            ).style.format({
                "Porcentaje (%)": "{:.2f}%"
            }),
            use_container_width=True
        )
    else:
        st.warning("No se encontraron datos sobre tipo de aseguramiento en el archivo.")

    # Análisis por aseguradora
    st.subheader("Distribución por Aseguradora")
    
    if "cod_ase_" in data["fiebre"].columns:
        # Crear copia del dataframe 
        df_ase = data["fiebre"].copy()
        
        # Contar casos por código de aseguradora
        ase_count = df_ase["cod_ase_"].value_counts().reset_index()
        ase_count.columns = ["Código Aseguradora", "Cantidad"]
        
        # Calcular porcentaje
        total_casos_ase = ase_count["Cantidad"].sum()
        ase_count["Porcentaje"] = ase_count["Cantidad"] / total_casos_ase * 100
        
        # Ordenar por cantidad
        ase_count = ase_count.sort_values("Cantidad", ascending=False)
        
        # Crear gráfico de barras para las 15 principales aseguradoras
        fig = px.bar(
            ase_count.head(15), 
            y="Código Aseguradora", 
            x="Cantidad",
            title="Top 15 Aseguradoras con Casos de Fiebre Amarilla",
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
        )
        
        # Mostrar gráfico
        st.plotly_chart(fig, use_container_width=True)
        
        # Mostrar tabla completa
        st.subheader("Tabla de Casos por Aseguradora")
        
        # Añadir opción para mostrar más aseguradoras
        num_rows = st.slider(
            "Número de aseguradoras a mostrar",
            min_value=10,
            max_value=min(50, len(ase_count)),
            value=20,
            step=5
        )
        
        # Mostrar tabla con las N aseguradoras principales
        st.dataframe(
            ase_count.head(num_rows).rename(
                columns={
                    "Porcentaje": "Porcentaje (%)"
                }
            ).style.format({
                "Porcentaje (%)": "{:.2f}%"
            }),
            use_container_width=True
        )
        
        # Buscar coincidencias con entidades conocidas
        st.subheader("Identificación de Entidades")
        st.markdown("""
        A continuación, se muestra la relación entre los códigos de aseguradoras presentes en los datos
        y las entidades registradas en el Sistema General de Seguridad Social en Salud (SGSSS).
        """)
        
        # Esta sería la implementación ideal, pero para simplificar vamos a mostrar una tabla de ejemplo
        st.info("""
        Para implementar esta funcionalidad completamente, se requeriría cruzar los códigos de aseguradoras
        con la información del archivo PDF 'entidades_sgsss.pdf'. Esto permitiría identificar correctamente
        las entidades a las que corresponden los códigos.
        """)
        
        # Mostrar una tabla de ejemplo con algunas entidades comunes
        ejemplo_entidades = pd.DataFrame({
            "Código": ["EPS005", "EPS008", "EPS010", "EPS017", "EPS037", "CCF024", "CCF053"],
            "Nombre Entidad": [
                "ENTIDAD PROMOTORA DE SALUD SANITAS S.A.S.",
                "CAJA DE COMPENSACIÓN FAMILIAR COMPENSAR",
                "EPS SURAMERICANA S.A.",
                "EPS FAMISANAR S.A.S.",
                "NUEVA EPS S.A.",
                "CAJA DE COMPENSACIÓN FAMILIAR DEL HUILA 'COMFAMILIAR'",
                "CAJA DE COMPENSACIÓN FAMILIAR DE CUNDINAMARCA 'COMFACUNDI'"
            ],
            "Régimen": ["CNT", "CNT", "CNT", "CNT", "CNT", "SBS", "SBS"]
        })
        
        st.dataframe(ejemplo_entidades, use_container_width=True)
    else:
        st.warning("No se encontraron datos sobre códigos de aseguradoras en el archivo.")

    # Cruce entre tipo de aseguramiento y departamentos
    st.subheader("Análisis Cruzado: Aseguramiento por Ubicación")
    
    if "tip_ss_" in data["fiebre"].columns and "ndep_resi" in data["fiebre"].columns:
        # Crear dataframe con mapeo
        df_ss_dep = data["fiebre"].copy()
        df_ss_dep["tip_ss_"] = df_ss_dep["tip_ss_"].astype(str)
        df_ss_dep["ss_desc"] = df_ss_dep["tip_ss_"].map(ss_mapping).fillna("No especificado")
        
        # Crear tabla cruzada
        tabla_cruzada = pd.crosstab(
            df_ss_dep["ndep_resi"],
            df_ss_dep["ss_desc"],
            margins=True,
            margins_name="Total"
        )
        
        # Mostrar tabla
        st.dataframe(tabla_cruzada, use_container_width=True)
        
        # Ofrecer visualización específica
        st.subheader("Distribución de Aseguramiento por Departamento")
        
        # Seleccionar departamento
        top_deptos = df_ss_dep["ndep_resi"].value_counts().head(10).index.tolist()
        selected_depto = st.selectbox(
            "Seleccionar departamento:",
            ["Todos"] + top_deptos
        )
        
        if selected_depto != "Todos":
            # Filtrar datos por departamento
            df_filtrado = df_ss_dep[df_ss_dep["ndep_resi"] == selected_depto]
            
            # Contar por tipo de aseguramiento
            tipo_count = df_filtrado["ss_desc"].value_counts().reset_index()
            tipo_count.columns = ["Tipo de Aseguramiento", "Cantidad"]
            
            # Crear gráfico
            fig = px.pie(
                tipo_count,
                names="Tipo de Aseguramiento",
                values="Cantidad",
                title=f"Distribución de Aseguramiento en {selected_depto}",
                color_discrete_sequence=[colors["primary"], colors["secondary"], colors["accent"], 
                                         colors["success"], colors["warning"], colors["danger"]],
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
            # Mostrar gráfico para todos los departamentos (top 5)
            top5_deptos = df_ss_dep["ndep_resi"].value_counts().head(5).index.tolist()
            
            # Filtrar para los top 5 departamentos
            df_top5 = df_ss_dep[df_ss_dep["ndep_resi"].isin(top5_deptos)]
            
            # Crear gráfico de barras apiladas
            fig = px.histogram(
                df_top5,
                x="ndep_resi",
                color="ss_desc",
                title="Distribución de Aseguramiento en Top 5 Departamentos",
                labels={"ndep_resi": "Departamento", "ss_desc": "Tipo de Aseguramiento", "count": "Cantidad"},
                color_discrete_sequence=[colors["primary"], colors["secondary"], colors["accent"], 
                                         colors["success"], colors["warning"], colors["danger"]],
                barmode="stack"
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
        st.warning("No se encontraron datos suficientes para realizar el análisis cruzado.")

    # Relación entre aseguramiento y condición final
    if "tip_ss_" in data["fiebre"].columns and "con_fin_" in data["fiebre"].columns:
        st.subheader("Relación entre Aseguramiento y Condición Final")
        
        # Crear dataframe con mapeos
        df_ss_fin = data["fiebre"].copy()
        
        # Mapeo de seguridad social
        df_ss_fin["tip_ss_"] = df_ss_fin["tip_ss_"].astype(str)
        df_ss_fin["ss_desc"] = df_ss_fin["tip_ss_"].map(ss_mapping).fillna("No especificado")
        
        # Mapeo de condición final
        condicion_mapping = {
            1: "Vivo",
            2: "Fallecido"
        }
        df_ss_fin["fin_desc"] = df_ss_fin["con_fin_"].map(condicion_mapping).fillna("No especificado")
        
        # Crear tabla cruzada
        tabla_ss_fin = pd.crosstab(
            df_ss_fin["ss_desc"],
            df_ss_fin["fin_desc"],
            margins=True,
            margins_name="Total"
        )
        
        # Mostrar tabla
        st.dataframe(tabla_ss_fin, use_container_width=True)
        
        # Calcular tasas de letalidad por tipo de aseguramiento
        st.subheader("Tasa de Letalidad por Tipo de Aseguramiento")
        
        # Crear dataframe para letalidad
        letalidad_df = pd.DataFrame(columns=["Tipo de Aseguramiento", "Tasa de Letalidad (%)"])
        
        for tipo in tabla_ss_fin.index:
            if tipo != "Total":
                # Verificar si existe columna fallecidos
                if "Fallecido" in tabla_ss_fin.columns:
                    fallecidos = tabla_ss_fin.loc[tipo, "Fallecido"]
                    total = tabla_ss_fin.loc[tipo, "Total"]
                    
                    # Calcular tasa de letalidad
                    if total > 0:
                        letalidad = fallecidos / total * 100
                        
                        # Añadir al dataframe
                        letalidad_df = pd.concat([
                            letalidad_df,
                            pd.DataFrame({
                                "Tipo de Aseguramiento": [tipo],
                                "Tasa de Letalidad (%)": [letalidad]
                            })
                        ])
        
        # Ordenar por tasa de letalidad
        if not letalidad_df.empty:
            letalidad_df = letalidad_df.sort_values("Tasa de Letalidad (%)", ascending=False)
            
            # Crear gráfico de barras
            fig = px.bar(
                letalidad_df,
                x="Tipo de Aseguramiento",
                y="Tasa de Letalidad (%)",
                title="Tasa de Letalidad por Tipo de Aseguramiento",
                color_discrete_sequence=[colors["danger"]],
                text_auto='.1f'
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
            )
            
            # Mostrar gráfico
            st.plotly_chart(fig, use_container_width=True)
            
            # Mostrar tabla formateada
            st.dataframe(
                letalidad_df.style.format({
                    "Tasa de Letalidad (%)": "{:.2f}%"
                }),
                use_container_width=True
            )
        else:
            st.info("No hay suficientes datos para calcular la tasa de letalidad por tipo de aseguramiento.")
    else:
        st.warning("No se encontraron datos suficientes para analizar la relación entre aseguramiento y condición final.")