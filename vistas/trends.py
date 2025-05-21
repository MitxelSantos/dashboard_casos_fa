import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime


def show(data, filters, colors):
    """
    Muestra la página de tendencias temporales del dashboard.

    Args:
        data (dict): Diccionario con los dataframes
        filters (dict): Filtros seleccionados
        colors (dict): Colores institucionales
    """
    st.title("Tendencias Temporales")

    # Mostrar descripción general
    st.markdown("""
    Esta sección analiza la evolución temporal de los casos de fiebre amarilla, 
    permitiendo identificar patrones estacionales y tendencias a lo largo del tiempo.
    """)

    # Análisis por año
    st.subheader("Evolución Anual de Casos")
    
    if "año" in data["fiebre"].columns:
        # Contar casos por año
        año_count = data["fiebre"]["año"].value_counts().reset_index()
        año_count.columns = ["Año", "Cantidad"]
        
        # Ordenar por año
        año_count = año_count.sort_values("Año")
        
        # Crear gráfico de línea con Plotly
        fig = px.line(
            año_count, 
            x="Año", 
            y="Cantidad",
            title="Evolución de Casos por Año",
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
        
        # Calcular tendencia
        if len(año_count) >= 3:
            # Calcular promedio móvil
            año_count["Promedio_Movil"] = año_count["Cantidad"].rolling(window=3, min_periods=1).mean()
            
            # Calcular tendencia (crecimiento o decrecimiento)
            try:
                # Usar los últimos 3 años para calcular tendencia
                ultimos_años = año_count.tail(3)
                first_val = ultimos_años["Cantidad"].iloc[0]
                last_val = ultimos_años["Cantidad"].iloc[-1]
                
                cambio_porcentual = ((last_val - first_val) / first_val * 100) if first_val > 0 else 0
                
                # Mostrar tendencia
                if cambio_porcentual > 10:
                    st.warning(f"⚠️ Tendencia creciente: Aumento del {cambio_porcentual:.1f}% en los últimos 3 años.")
                elif cambio_porcentual < -10:
                    st.success(f"✅ Tendencia decreciente: Disminución del {abs(cambio_porcentual):.1f}% en los últimos 3 años.")
                else:
                    st.info(f"ℹ️ Tendencia estable: Variación del {cambio_porcentual:.1f}% en los últimos 3 años.")
            except:
                st.info("No se pudo calcular la tendencia por insuficiencia de datos.")
        
        # Mostrar tabla de casos por año
        st.dataframe(año_count, use_container_width=True)
    else:
        st.warning("No se encontraron datos sobre el año de los casos.")

    # Análisis por mes (si existe fecha de inicio de síntomas)
    st.subheader("Distribución Mensual de Casos")
    
    if "ini_sin_" in data["fiebre"].columns:
        # Convertir a datetime
        data_fecha = data["fiebre"].copy()
        data_fecha["ini_sin_"] = pd.to_datetime(data_fecha["ini_sin_"], errors="coerce")
        
        # Filtrar registros con fecha válida
        data_fecha = data_fecha[~data_fecha["ini_sin_"].isna()]
        
        if not data_fecha.empty:
            # Extraer mes
            data_fecha["Mes"] = data_fecha["ini_sin_"].dt.month
            
            # Mapeo de meses
            meses_mapping = {
                1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
                5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
                9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
            }
            
            data_fecha["Nombre_Mes"] = data_fecha["Mes"].map(meses_mapping)
            
            # Contar casos por mes
            mes_count = data_fecha["Nombre_Mes"].value_counts().reset_index()
            mes_count.columns = ["Mes", "Cantidad"]
            
            # Ordenar por mes natural
            mes_order = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                         "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            mes_count["Mes"] = pd.Categorical(mes_count["Mes"], categories=mes_order, ordered=True)
            mes_count = mes_count.sort_values("Mes")
            
            # Crear gráfico de barras
            fig = px.bar(
                mes_count,
                x="Mes",
                y="Cantidad",
                title="Distribución de Casos por Mes",
                color_discrete_sequence=[colors["secondary"]],
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
            st.dataframe(mes_count, use_container_width=True)
            
            # Análisis estacional
            st.subheader("Análisis Estacional")
            
            # Definir estaciones (para Colombia, país tropical)
            def asignar_estacion(mes):
                if mes in [12, 1, 2]:  # Diciembre, Enero, Febrero
                    return "Seca (Diciembre-Febrero)"
                elif mes in [3, 4, 5]:  # Marzo, Abril, Mayo
                    return "Lluviosa (Marzo-Mayo)"
                elif mes in [6, 7, 8]:  # Junio, Julio, Agosto
                    return "Seca (Junio-Agosto)"
                else:  # Septiembre, Octubre, Noviembre
                    return "Lluviosa (Septiembre-Noviembre)"
            
            # Aplicar la función de estación
            data_fecha["Estacion"] = data_fecha["Mes"].apply(asignar_estacion)
            
            # Contar por estación
            estacion_count = data_fecha["Estacion"].value_counts().reset_index()
            estacion_count.columns = ["Estación", "Cantidad"]
            
            # Orden de estaciones
            orden_estaciones = [
                "Seca (Diciembre-Febrero)",
                "Lluviosa (Marzo-Mayo)",
                "Seca (Junio-Agosto)",
                "Lluviosa (Septiembre-Noviembre)"
            ]
            
            estacion_count["Estación"] = pd.Categorical(
                estacion_count["Estación"],
                categories=orden_estaciones,
                ordered=True
            )
            estacion_count = estacion_count.sort_values("Estación")
            
            # Crear gráfico de barras
            fig = px.bar(
                estacion_count,
                x="Estación",
                y="Cantidad",
                title="Distribución de Casos por Temporada",
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
            
            # Interpretación de estacionalidad
            st.subheader("Interpretación de Estacionalidad")
            
            # Determinar estación con más casos
            if not estacion_count.empty:
                max_estacion = estacion_count.loc[estacion_count["Cantidad"].idxmax(), "Estación"]
                max_cantidad = estacion_count.loc[estacion_count["Cantidad"].idxmax(), "Cantidad"]
                total_estacion = estacion_count["Cantidad"].sum()
                porcentaje = max_cantidad / total_estacion * 100 if total_estacion > 0 else 0
                
                st.info(f"""
                **Interpretación de Estacionalidad:**
                
                El {porcentaje:.1f}% de los casos se concentran en la temporada {max_estacion}.
                
                Las variaciones estacionales en los casos de fiebre amarilla pueden estar relacionadas con:
                - Cambios en la población y actividad del mosquito vector (Aedes aegypti en áreas urbanas y Haemagogus en áreas selváticas)
                - Patrones de precipitación que afectan el desarrollo de criaderos de mosquitos
                - Movimientos migratorios humanos que influyen en la exposición al virus
                """)
        else:
            st.warning("No se encontraron fechas de inicio de síntomas válidas para el análisis mensual.")
    else:
        st.warning("No se encontraron datos sobre la fecha de inicio de síntomas.")

    # Análisis de tiempo entre síntomas y hospitalización
    st.subheader("Tiempo entre Síntomas y Hospitalización")
    
    if "ini_sin_" in data["fiebre"].columns and "fec_hos_" in data["fiebre"].columns:
        # Convertir a datetime
        data_tiempos = data["fiebre"].copy()
        data_tiempos["ini_sin_"] = pd.to_datetime(data_tiempos["ini_sin_"], errors="coerce")
        data_tiempos["fec_hos_"] = pd.to_datetime(data_tiempos["fec_hos_"], errors="coerce")
        
        # Filtrar registros con fechas válidas en ambos campos
        data_tiempos = data_tiempos[~data_tiempos["ini_sin_"].isna() & ~data_tiempos["fec_hos_"].isna()]
        
        if not data_tiempos.empty:
            # Calcular diferencia en días
            data_tiempos["Dias_Hasta_Hospitalizacion"] = (
                data_tiempos["fec_hos_"] - data_tiempos["ini_sin_"]
            ).dt.days
            
            # Filtrar valores lógicos (positivos y no extremos)
            data_tiempos = data_tiempos[
                (data_tiempos["Dias_Hasta_Hospitalizacion"] >= 0) & 
                (data_tiempos["Dias_Hasta_Hospitalizacion"] <= 30)  # Filtrar valores extremos
            ]
            
            if not data_tiempos.empty:
                # Calcular estadísticas
                tiempo_promedio = data_tiempos["Dias_Hasta_Hospitalizacion"].mean()
                tiempo_mediano = data_tiempos["Dias_Hasta_Hospitalizacion"].median()
                tiempo_min = data_tiempos["Dias_Hasta_Hospitalizacion"].min()
                tiempo_max = data_tiempos["Dias_Hasta_Hospitalizacion"].max()
                
                # Mostrar estadísticas en columnas
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    create_metric_card(
                        title="Tiempo Promedio",
                        value=f"{tiempo_promedio:.1f} días",
                        color=colors["primary"]
                    )
                
                with col2:
                    create_metric_card(
                        title="Tiempo Mediano",
                        value=f"{tiempo_mediano:.0f} días",
                        color=colors["secondary"]
                    )
                
                with col3:
                    create_metric_card(
                        title="Tiempo Mínimo",
                        value=f"{tiempo_min:.0f} días",
                        color=colors["success"]
                    )
                
                with col4:
                    create_metric_card(
                        title="Tiempo Máximo",
                        value=f"{tiempo_max:.0f} días",
                        color=colors["warning"]
                    )
                
                # Crear histograma
                fig = px.histogram(
                    data_tiempos["Dias_Hasta_Hospitalizacion"],
                    nbins=15,
                    title="Distribución de Tiempo entre Síntomas y Hospitalización",
                    labels={"value": "Días", "count": "Frecuencia"},
                    color_discrete_sequence=[colors["primary"]]
                )
                
                # Añadir línea vertical para la media
                fig.add_vline(
                    x=tiempo_promedio,
                    line_dash="dash",
                    line_color=colors["danger"],
                    annotation_text=f"Media: {tiempo_promedio:.1f}",
                    annotation_position="top right"
                )
                
                # Añadir línea vertical para la mediana
                fig.add_vline(
                    x=tiempo_mediano,
                    line_dash="dash",
                    line_color=colors["secondary"],
                    annotation_text=f"Mediana: {tiempo_mediano:.0f}",
                    annotation_position="top left"
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
                
                # Interpretación
                st.markdown(f"""
                **Interpretación:**
                
                El tiempo entre el inicio de síntomas y la hospitalización es un indicador importante
                de la oportunidad en la atención médica. La fiebre amarilla tiene un periodo de incubación
                de 3 a 6 días, y los síntomas iniciales pueden confundirse con otras enfermedades.
                
                En estos datos, el tiempo promedio hasta la hospitalización es de {tiempo_promedio:.1f} días,
                con una mediana de {tiempo_mediano:.0f} días.
                """)
            else:
                st.warning("No se encontraron registros con valores válidos de tiempo entre síntomas y hospitalización.")
        else:
            st.warning("No se encontraron registros con fechas válidas tanto de inicio de síntomas como de hospitalización.")
    else:
        st.warning("No se encontraron datos suficientes para analizar el tiempo entre síntomas y hospitalización.")

    # Análisis de supervivencia (si hay datos)
    if "ini_sin_" in data["fiebre"].columns and "fec_def_" in data["fiebre"].columns and "con_fin_" in data["fiebre"].columns:
        st.subheader("Análisis de Tiempo hasta Desenlace")
        
        # Convertir a datetime
        data_supervivencia = data["fiebre"].copy()
        data_supervivencia["ini_sin_"] = pd.to_datetime(data_supervivencia["ini_sin_"], errors="coerce")
        data_supervivencia["fec_def_"] = pd.to_datetime(data_supervivencia["fec_def_"], errors="coerce")
        
        # Filtrar solo casos fallecidos con fechas válidas
        fallecidos = data_supervivencia[
            (data_supervivencia["con_fin_"] == 2) &  # Código 2 = fallecido
            (~data_supervivencia["ini_sin_"].isna()) &
            (~data_supervivencia["fec_def_"].isna())
        ]
        
        if not fallecidos.empty:
            # Calcular días hasta fallecimiento
            fallecidos["Dias_Hasta_Fallecimiento"] = (
                fallecidos["fec_def_"] - fallecidos["ini_sin_"]
            ).dt.days
            
            # Filtrar valores lógicos (positivos y no extremos)
            fallecidos = fallecidos[
                (fallecidos["Dias_Hasta_Fallecimiento"] >= 0) & 
                (fallecidos["Dias_Hasta_Fallecimiento"] <= 30)  # Filtrar valores extremos
            ]
            
            if not fallecidos.empty:
                # Calcular estadísticas
                tiempo_promedio = fallecidos["Dias_Hasta_Fallecimiento"].mean()
                tiempo_mediano = fallecidos["Dias_Hasta_Fallecimiento"].median()
                tiempo_min = fallecidos["Dias_Hasta_Fallecimiento"].min()
                tiempo_max = fallecidos["Dias_Hasta_Fallecimiento"].max()
                
                # Mostrar estadísticas en columnas
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    create_metric_card(
                        title="Tiempo Promedio",
                        value=f"{tiempo_promedio:.1f} días",
                        color=colors["danger"]
                    )
                
                with col2:
                    create_metric_card(
                        title="Tiempo Mediano",
                        value=f"{tiempo_mediano:.0f} días",
                        color=colors["danger"]
                    )
                
                with col3:
                    create_metric_card(
                        title="Tiempo Mínimo",
                        value=f"{tiempo_min:.0f} días",
                        color=colors["warning"]
                    )
                
                with col4:
                    create_metric_card(
                        title="Tiempo Máximo",
                        value=f"{tiempo_max:.0f} días",
                        color=colors["warning"]
                    )
                
                # Crear histograma
                fig = px.histogram(
                    fallecidos["Dias_Hasta_Fallecimiento"],
                    nbins=15,
                    title="Distribución de Tiempo entre Síntomas y Fallecimiento",
                    labels={"value": "Días", "count": "Frecuencia"},
                    color_discrete_sequence=[colors["danger"]]
                )
                
                # Añadir línea vertical para la media
                fig.add_vline(
                    x=tiempo_promedio,
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"Media: {tiempo_promedio:.1f}",
                    annotation_position="top right"
                )
                
                # Añadir línea vertical para la mediana
                fig.add_vline(
                    x=tiempo_mediano,
                    line_dash="dash",
                    line_color="black",
                    annotation_text=f"Mediana: {tiempo_mediano:.0f}",
                    annotation_position="top left"
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
                
                # Interpretación
                st.markdown(f"""
                **Interpretación:**
                
                El tiempo entre el inicio de síntomas y el fallecimiento es un indicador importante
                del curso clínico de la enfermedad. La fiebre amarilla severa puede progresar rápidamente
                a falla multiorgánica, particularmente con afectación hepática y renal.
                
                En estos datos, el tiempo promedio hasta el fallecimiento es de {tiempo_promedio:.1f} días,
                con una mediana de {tiempo_mediano:.0f} días desde el inicio de síntomas.
                """)
            else:
                st.warning("No se encontraron registros con valores válidos de tiempo hasta fallecimiento.")
        else:
            st.info("No se encontraron casos fallecidos con fechas válidas para realizar este análisis.")


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