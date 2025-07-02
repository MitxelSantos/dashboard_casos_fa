"""
Vista de información principal del dashboard de Fiebre Amarilla.
Muestra fichas informativas claras para profesionales médicos.
ENFOCADO: Información médica relevante con diseño tipo tarjetas.
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
    Muestra la vista de información principal con fichas médicas.
    
    Args:
        data_filtered (dict): Datos filtrados
        filters (dict): Filtros aplicados
        colors (dict): Colores institucionales
    """
    st.markdown(
        '<h1 style="color: #5A4214; border-bottom: 2px solid #F2A900; padding-bottom: 8px;">📋 Información Principal</h1>',
        unsafe_allow_html=True,
    )
    
    # Información médica de contexto
    st.markdown(f"""
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid {colors['primary']}; margin-bottom: 30px;">
        <h3 style="color: {colors['primary']}; margin-top: 0;">🏥 Panel Médico de Fiebre Amarilla</h3>
        <p><strong>Información epidemiológica para toma de decisiones clínicas y de salud pública.</strong></p>
        <p>Datos actualizados de casos confirmados y vigilancia de epizootias en el departamento del Tolima.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Crear fichas médicas principales
    create_medical_dashboard(data_filtered, colors)
    
    # Información detallada en secciones
    st.markdown("---")
    show_clinical_alerts(data_filtered, colors)
    
    st.markdown("---")
    show_epidemiological_summary(data_filtered, colors)
    
    st.markdown("---")
    show_geographic_medical_summary(data_filtered, colors)

def create_medical_dashboard(data_filtered, colors):
    """
    Crea el dashboard principal con fichas médicas.
    """
    casos = data_filtered["casos"]
    epizootias = data_filtered["epizootias"]
    
    # Calcular métricas médicas principales
    total_casos = len(casos)
    total_epizootias = len(epizootias)
    
    # Métricas clínicas de casos
    fallecidos = 0
    vivos = 0
    letalidad = 0
    if total_casos > 0 and 'condicion_final' in casos.columns:
        fallecidos = (casos['condicion_final'] == 'Fallecido').sum()
        vivos = (casos['condicion_final'] == 'Vivo').sum()
        letalidad = (fallecidos / total_casos * 100) if total_casos > 0 else 0
    
    # Métricas de vigilancia epidemiológica
    positivos_fa = 0
    positividad = 0
    if total_epizootias > 0 and 'descripcion' in epizootias.columns:
        positivos_fa = (epizootias['descripcion'] == 'POSITIVO FA').sum()
        positividad = (positivos_fa / total_epizootias * 100) if total_epizootias > 0 else 0
    
    # Métricas geográficas
    municipios_afectados = set()
    if not casos.empty and 'municipio_normalizado' in casos.columns:
        municipios_afectados.update(casos['municipio_normalizado'].dropna())
    if not epizootias.empty and 'municipio_normalizado' in epizootias.columns:
        municipios_afectados.update(epizootias['municipio_normalizado'].dropna())
    
    veredas_afectadas = set()
    if not casos.empty and 'vereda_normalizada' in casos.columns:
        veredas_afectadas.update(casos['vereda_normalizada'].dropna())
    if not epizootias.empty and 'vereda_normalizada' in epizootias.columns:
        veredas_afectadas.update(epizootias['vereda_normalizada'].dropna())
    
    # Fechas médicamente relevantes
    ultima_fecha_caso = None
    ultima_fecha_epi_positiva = None
    
    if not casos.empty and 'fecha_inicio_sintomas' in casos.columns:
        fechas_casos = casos['fecha_inicio_sintomas'].dropna()
        if not fechas_casos.empty:
            ultima_fecha_caso = fechas_casos.max()
    
    if not epizootias.empty and 'fecha_recoleccion' in epizootias.columns:
        epi_positivas = epizootias[epizootias['descripcion'] == 'POSITIVO FA']
        if not epi_positivas.empty:
            fechas_positivas = epi_positivas['fecha_recoleccion'].dropna()
            if not fechas_positivas.empty:
                ultima_fecha_epi_positiva = fechas_positivas.max()
    
    # TARJETAS MÉDICAS PRINCIPALES
    st.subheader("🏥 Situación Epidemiológica Actual")
    
    # Crear tarjetas médicas con CSS personalizado
    create_medical_cards_css(colors)
    
    # Primera fila - Situación de casos humanos
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Tarjeta de casos confirmados
        alert_class = "critical" if total_casos > 10 else "moderate" if total_casos > 0 else "low"
        st.markdown(f"""
        <div class="medical-card {alert_class}">
            <div class="card-icon">🦠</div>
            <div class="card-title">CASOS CONFIRMADOS</div>
            <div class="card-value">{total_casos}</div>
            <div class="card-subtitle">{fallecidos} fallecidos | {vivos} vivos</div>
            <div class="card-status">Situación: {'Crítica' if total_casos > 10 else 'Estable' if total_casos > 0 else 'Sin casos'}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Tarjeta de letalidad
        alert_class = "critical" if letalidad > 10 else "moderate" if letalidad > 0 else "low"
        st.markdown(f"""
        <div class="medical-card {alert_class}">
            <div class="card-icon">⚰️</div>
            <div class="card-title">TASA DE LETALIDAD</div>
            <div class="card-value">{letalidad:.1f}%</div>
            <div class="card-subtitle">Mortalidad por FA</div>
            <div class="card-status">Nivel: {'Alto' if letalidad > 10 else 'Moderado' if letalidad > 0 else 'Sin mortalidad'}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # Tarjeta de último caso
        dias_ultimo_caso = "N/A"
        if ultima_fecha_caso:
            dias_ultimo_caso = (datetime.now() - ultima_fecha_caso).days
            alert_class = "critical" if dias_ultimo_caso < 30 else "moderate" if dias_ultimo_caso < 90 else "low"
        else:
            alert_class = "low"
            
        st.markdown(f"""
        <div class="medical-card {alert_class}">
            <div class="card-icon">📅</div>
            <div class="card-title">ÚLTIMO CASO</div>
            <div class="card-value">{ultima_fecha_caso.strftime('%d/%m/%Y') if ultima_fecha_caso else 'Sin datos'}</div>
            <div class="card-subtitle">{f'Hace {dias_ultimo_caso} días' if isinstance(dias_ultimo_caso, int) else 'No disponible'}</div>
            <div class="card-status">Actividad: {'Reciente' if isinstance(dias_ultimo_caso, int) and dias_ultimo_caso < 30 else 'Controlada'}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Segunda fila - Vigilancia epidemiológica
    st.subheader("🐒 Vigilancia de Epizootias")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Tarjeta de epizootias totales
        alert_class = "critical" if total_epizootias > 20 else "moderate" if total_epizootias > 0 else "low"
        st.markdown(f"""
        <div class="medical-card {alert_class}">
            <div class="card-icon">🐒</div>
            <div class="card-title">EPIZOOTIAS TOTALES</div>
            <div class="card-value">{total_epizootias}</div>
            <div class="card-subtitle">{positivos_fa} positivas para FA</div>
            <div class="card-status">Vigilancia: {'Intensa' if total_epizootias > 20 else 'Activa' if total_epizootias > 0 else 'Sin eventos'}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Tarjeta de positividad
        alert_class = "critical" if positividad > 15 else "moderate" if positividad > 0 else "low"
        st.markdown(f"""
        <div class="medical-card {alert_class}">
            <div class="card-icon">🔴</div>
            <div class="card-title">POSITIVIDAD FA</div>
            <div class="card-value">{positividad:.1f}%</div>
            <div class="card-subtitle">En fauna silvestre</div>
            <div class="card-status">Circulación viral: {'Alta' if positividad > 15 else 'Detectada' if positividad > 0 else 'No detectada'}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # Tarjeta de última epizootia positiva
        dias_ultima_epi = "N/A"
        if ultima_fecha_epi_positiva:
            dias_ultima_epi = (datetime.now() - ultima_fecha_epi_positiva).days
            alert_class = "critical" if dias_ultima_epi < 60 else "moderate" if dias_ultima_epi < 180 else "low"
        else:
            alert_class = "low"
            
        st.markdown(f"""
        <div class="medical-card {alert_class}">
            <div class="card-icon">🔬</div>
            <div class="card-title">ÚLTIMA EPIZOOTIA +</div>
            <div class="card-value">{ultima_fecha_epi_positiva.strftime('%d/%m/%Y') if ultima_fecha_epi_positiva else 'Sin datos'}</div>
            <div class="card-subtitle">{f'Hace {dias_ultima_epi} días' if isinstance(dias_ultima_epi, int) else 'No disponible'}</div>
            <div class="card-status">Riesgo: {'Actual' if isinstance(dias_ultima_epi, int) and dias_ultima_epi < 60 else 'Bajo'}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Tercera fila - Distribución geográfica
    st.subheader("📍 Distribución Geográfica")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        alert_class = "critical" if len(municipios_afectados) > 10 else "moderate" if len(municipios_afectados) > 0 else "low"
        st.markdown(f"""
        <div class="medical-card {alert_class}">
            <div class="card-icon">🏛️</div>
            <div class="card-title">MUNICIPIOS AFECTADOS</div>
            <div class="card-value">{len(municipios_afectados)}</div>
            <div class="card-subtitle">De 47 municipios</div>
            <div class="card-status">Dispersión: {'Amplia' if len(municipios_afectados) > 10 else 'Localizada' if len(municipios_afectados) > 0 else 'Sin afectación'}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        alert_class = "moderate" if len(veredas_afectadas) > 0 else "low"
        st.markdown(f"""
        <div class="medical-card {alert_class}">
            <div class="card-icon">🏘️</div>
            <div class="card-title">VEREDAS AFECTADAS</div>
            <div class="card-value">{len(veredas_afectadas)}</div>
            <div class="card-subtitle">Áreas rurales</div>
            <div class="card-status">Cobertura: {'Múltiple' if len(veredas_afectadas) > 0 else 'Sin afectación'}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # Calcular riesgo general
        riesgo_general = "BAJO"
        if total_casos > 5 or positivos_fa > 3 or letalidad > 5:
            riesgo_general = "ALTO"
        elif total_casos > 0 or positivos_fa > 0:
            riesgo_general = "MODERADO"
        
        alert_class = "critical" if riesgo_general == "ALTO" else "moderate" if riesgo_general == "MODERADO" else "low"
        st.markdown(f"""
        <div class="medical-card {alert_class}">
            <div class="card-icon">⚠️</div>
            <div class="card-title">NIVEL DE RIESGO</div>
            <div class="card-value">{riesgo_general}</div>
            <div class="card-subtitle">Evaluación general</div>
            <div class="card-status">Acción: {'Inmediata' if riesgo_general == 'ALTO' else 'Vigilancia' if riesgo_general == 'MODERADO' else 'Prevención'}</div>
        </div>
        """, unsafe_allow_html=True)

def create_medical_cards_css(colors):
    """Crea CSS para las tarjetas médicas."""
    st.markdown(f"""
    <style>
    .medical-card {{
        background: linear-gradient(135deg, white 0%, #f8f9fa 100%);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        margin-bottom: 20px;
        border-top: 4px solid;
        min-height: 180px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }}
    
    .medical-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    }}
    
    .medical-card.critical {{
        border-top-color: {colors['danger']};
        background: linear-gradient(135deg, #fff5f5 0%, #ffe6e6 100%);
    }}
    
    .medical-card.moderate {{
        border-top-color: {colors['warning']};
        background: linear-gradient(135deg, #fffbf0 0%, #fef3c7 100%);
    }}
    
    .medical-card.low {{
        border-top-color: {colors['success']};
        background: linear-gradient(135deg, #f0fff4 0%, #d4edda 100%);
    }}
    
    .card-icon {{
        font-size: 2.5rem;
        margin-bottom: 10px;
    }}
    
    .card-title {{
        font-size: 0.9rem;
        font-weight: 700;
        color: {colors['dark']};
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }}
    
    .card-value {{
        font-size: 2.2rem;
        font-weight: 800;
        color: {colors['primary']};
        margin-bottom: 8px;
        line-height: 1;
    }}
    
    .card-subtitle {{
        font-size: 0.85rem;
        color: #666;
        margin-bottom: 10px;
        font-weight: 500;
    }}
    
    .card-status {{
        font-size: 0.8rem;
        font-weight: 600;
        padding: 4px 8px;
        border-radius: 12px;
        background-color: rgba(0,0,0,0.05);
        color: {colors['dark']};
    }}
    
    @media (max-width: 768px) {{
        .medical-card {{
            min-height: 150px;
            padding: 15px;
        }}
        
        .card-icon {{
            font-size: 2rem;
        }}
        
        .card-value {{
            font-size: 1.8rem;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)

def show_clinical_alerts(data_filtered, colors):
    """Muestra alertas médicas importantes."""
    casos = data_filtered["casos"]
    epizootias = data_filtered["epizootias"]
    
    st.subheader("🚨 Alertas Médicas")
    
    alerts = []
    
    # Alertas basadas en casos
    if not casos.empty:
        total_casos = len(casos)
        
        if 'condicion_final' in casos.columns:
            fallecidos = (casos['condicion_final'] == 'Fallecido').sum()
            letalidad = (fallecidos / total_casos * 100) if total_casos > 0 else 0
            
            if letalidad > 10:
                alerts.append({
                    'type': 'critical',
                    'icon': '🔴',
                    'title': 'ALTA LETALIDAD',
                    'message': f'Tasa de letalidad del {letalidad:.1f}% - Requiere atención inmediata',
                    'action': 'Revisar protocolos de manejo clínico'
                })
            elif fallecidos > 0:
                alerts.append({
                    'type': 'warning',
                    'icon': '🟡',
                    'title': 'FALLECIMIENTOS REPORTADOS',
                    'message': f'{fallecidos} casos fatales registrados',
                    'action': 'Monitorear evolución clínica'
                })
        
        # Alerta de casos recientes
        if 'fecha_inicio_sintomas' in casos.columns:
            fechas_recientes = casos[casos['fecha_inicio_sintomas'] >= pd.Timestamp.now() - pd.Timedelta(days=30)]
            if len(fechas_recientes) > 0:
                alerts.append({
                    'type': 'warning',
                    'icon': '📅',
                    'title': 'CASOS RECIENTES',
                    'message': f'{len(fechas_recientes)} casos en los últimos 30 días',
                    'action': 'Intensificar vigilancia epidemiológica'
                })
    
    # Alertas basadas en epizootias
    if not epizootias.empty and 'descripcion' in epizootias.columns:
        positivos_recientes = epizootias[
            (epizootias['descripcion'] == 'POSITIVO FA') & 
            (epizootias['fecha_recoleccion'] >= pd.Timestamp.now() - pd.Timedelta(days=60))
        ] if 'fecha_recoleccion' in epizootias.columns else pd.DataFrame()
        
        if len(positivos_recientes) > 0:
            alerts.append({
                'type': 'warning',
                'icon': '🐒',
                'title': 'CIRCULACIÓN VIRAL ACTIVA',
                'message': f'{len(positivos_recientes)} epizootias positivas en últimos 60 días',
                'action': 'Reforzar medidas de prevención'
            })
    
    # Mostrar alertas
    if alerts:
        for alert in alerts:
            alert_color = colors['danger'] if alert['type'] == 'critical' else colors['warning']
            st.markdown(f"""
            <div style="
                background-color: {'#fff5f5' if alert['type'] == 'critical' else '#fffbf0'};
                border: 2px solid {alert_color};
                border-radius: 10px;
                padding: 15px;
                margin: 10px 0;
            ">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 1.5rem;">{alert['icon']}</span>
                    <div>
                        <h4 style="margin: 0; color: {alert_color};">{alert['title']}</h4>
                        <p style="margin: 5px 0; color: {colors['dark']};">{alert['message']}</p>
                        <small style="color: #666; font-weight: 500;">💡 {alert['action']}</small>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ No hay alertas médicas activas en este momento.")

def show_epidemiological_summary(data_filtered, colors):
    """Muestra resumen epidemiológico médico."""
    casos = data_filtered["casos"]
    epizootias = data_filtered["epizootias"]
    
    st.subheader("📊 Resumen Epidemiológico")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🦠 Perfil de Casos Humanos**")
        
        if not casos.empty:
            # Distribución por sexo
            if 'sexo' in casos.columns:
                sexo_dist = casos['sexo'].value_counts()
                if not sexo_dist.empty:
                    fig_sexo = px.pie(
                        values=sexo_dist.values,
                        names=sexo_dist.index,
                        title="Distribución por Sexo",
                        color_discrete_map={
                            'Masculino': colors['info'],
                            'Femenino': colors['secondary']
                        }
                    )
                    fig_sexo.update_layout(height=300, showlegend=True)
                    st.plotly_chart(fig_sexo, use_container_width=True)
            
            # Distribución por edad
            if 'edad' in casos.columns:
                edades = casos['edad'].dropna()
                if not edades.empty:
                    fig_edad = px.histogram(
                        x=edades,
                        nbins=10,
                        title="Distribución por Edad",
                        color_discrete_sequence=[colors['primary']]
                    )
                    fig_edad.update_layout(height=300)
                    fig_edad.update_xaxes(title="Edad (años)")
                    fig_edad.update_yaxes(title="Número de casos")
                    st.plotly_chart(fig_edad, use_container_width=True)
        else:
            st.info("No hay datos de casos para mostrar el perfil.")
    
    with col2:
        st.markdown("**🐒 Vigilancia de Fauna**")
        
        if not epizootias.empty:
            # Distribución por resultado
            if 'descripcion' in epizootias.columns:
                resultado_dist = epizootias['descripcion'].value_counts()
                
                color_map = {
                    'POSITIVO FA': colors['danger'],
                    'NEGATIVO FA': colors['success'],
                    'NO APTA': colors['warning'],
                    'EN ESTUDIO': colors['info']
                }
                
                fig_resultado = px.pie(
                    values=resultado_dist.values,
                    names=resultado_dist.index,
                    title="Resultados de Análisis",
                    color_discrete_map=color_map
                )
                fig_resultado.update_layout(height=300, showlegend=True)
                st.plotly_chart(fig_resultado, use_container_width=True)
            
            # Distribución temporal
            if 'fecha_recoleccion' in epizootias.columns:
                epizootias_temporal = epizootias.copy()
                epizootias_temporal['mes'] = epizootias_temporal['fecha_recoleccion'].dt.to_period('M')
                mes_counts = epizootias_temporal.groupby('mes').size()
                
                if not mes_counts.empty:
                    fig_temporal = px.line(
                        x=mes_counts.index.astype(str),
                        y=mes_counts.values,
                        title="Epizootias por Mes",
                        markers=True
                    )
                    fig_temporal.update_layout(height=300)
                    fig_temporal.update_xaxes(title="Mes")
                    fig_temporal.update_yaxes(title="Número de epizootias")
                    st.plotly_chart(fig_temporal, use_container_width=True)
        else:
            st.info("No hay datos de epizootias para mostrar.")

def show_geographic_medical_summary(data_filtered, colors):
    """Muestra resumen geográfico médico."""
    casos = data_filtered["casos"]
    epizootias = data_filtered["epizootias"]
    
    st.subheader("📍 Distribución Geográfica - Enfoque Médico")
    
    # Crear tabla de resumen por municipio para uso médico
    summary_data = []
    
    municipios_casos = set(casos['municipio'].dropna()) if 'municipio' in casos.columns and not casos.empty else set()
    municipios_epi = set(epizootias['municipio'].dropna()) if 'municipio' in epizootias.columns and not epizootias.empty else set()
    todos_municipios = sorted(municipios_casos.union(municipios_epi))
    
    for municipio in todos_municipios[:15]:  # Limitar a top 15 para visualización médica
        casos_mpio = casos[casos['municipio'] == municipio] if 'municipio' in casos.columns and not casos.empty else pd.DataFrame()
        epi_mpio = epizootias[epizootias['municipio'] == municipio] if 'municipio' in epizootias.columns and not epizootias.empty else pd.DataFrame()
        
        total_casos = len(casos_mpio)
        total_epizootias = len(epi_mpio)
        
        fallecidos = 0
        if not casos_mpio.empty and 'condicion_final' in casos_mpio.columns:
            fallecidos = (casos_mpio['condicion_final'] == 'Fallecido').sum()
        
        positivos_fa = 0
        if not epi_mpio.empty and 'descripcion' in epi_mpio.columns:
            positivos_fa = (epi_mpio['descripcion'] == 'POSITIVO FA').sum()
        
        # Evaluación médica del riesgo
        if total_casos > 5 or positivos_fa > 3 or fallecidos > 0:
            nivel_riesgo = "ALTO"
        elif total_casos > 0 or positivos_fa > 0:
            nivel_riesgo = "MODERADO"
        else:
            nivel_riesgo = "BAJO"
        
        summary_data.append({
            'Municipio': municipio,
            'Casos': total_casos,
            'Fallecidos': fallecidos,
            'Epizootias+': positivos_fa,
            'Total Epi': total_epizootias,
            'Riesgo': nivel_riesgo
        })
    
    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        
        # Mostrar tabla médica sin background_gradient (evita error matplotlib)
        st.markdown("**📋 Tabla de Situación por Municipio:**")
        
        # Crear una versión estilizada manualmente
        for _, row in summary_df.iterrows():
            riesgo_color = colors['danger'] if row['Riesgo'] == 'ALTO' else colors['warning'] if row['Riesgo'] == 'MODERADO' else colors['success']
            
            st.markdown(f"""
            <div style="
                background-color: white;
                border: 1px solid #dee2e6;
                border-left: 4px solid {riesgo_color};
                border-radius: 8px;
                padding: 15px;
                margin: 8px 0;
                display: flex;
                justify-content: space-between;
                align-items: center;
            ">
                <div style="flex: 2;">
                    <strong style="color: {colors['primary']}; font-size: 1.1rem;">{row['Municipio']}</strong>
                    <div style="color: #666; font-size: 0.9rem;">Nivel de riesgo: <strong style="color: {riesgo_color};">{row['Riesgo']}</strong></div>
                </div>
                <div style="flex: 3; display: flex; gap: 20px; text-align: center;">
                    <div>
                        <div style="font-size: 1.2rem; font-weight: bold; color: {colors['danger']};">{row['Casos']}</div>
                        <div style="font-size: 0.8rem; color: #666;">Casos</div>
                    </div>
                    <div>
                        <div style="font-size: 1.2rem; font-weight: bold; color: {colors['dark']};">{row['Fallecidos']}</div>
                        <div style="font-size: 0.8rem; color: #666;">Fallecidos</div>
                    </div>
                    <div>
                        <div style="font-size: 1.2rem; font-weight: bold; color: {colors['warning']};">{row['Epizootias+']}</div>
                        <div style="font-size: 0.8rem; color: #666;">Epi +</div>
                    </div>
                    <div>
                        <div style="font-size: 1.2rem; font-weight: bold; color: {colors['info']};">{row['Total Epi']}</div>
                        <div style="font-size: 0.8rem; color: #666;">Total Epi</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Botón de exportación médica
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            csv_data = summary_df.to_csv(index=False)
            st.download_button(
                label="📄 Exportar Resumen Médico",
                data=csv_data,
                file_name=f"resumen_medico_FA_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                help="Descargar resumen para revisión médica"
            )
        
        with col2:
            st.markdown("""
            <div style="background-color: #e8f4fd; padding: 10px; border-radius: 6px; border-left: 4px solid #0066cc;">
                <small><strong>💡 Uso médico:</strong> Esta información es para apoyo en la toma de decisiones clínicas y epidemiológicas.</small>
            </div>
            """, unsafe_allow_html=True)
    
    else:
        st.info("No hay datos geográficos disponibles con los filtros actuales.")
