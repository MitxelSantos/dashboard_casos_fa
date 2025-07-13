"""
Sistema responsive.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Union

# ===== CONFIGURACIÓN BASE =====

BREAKPOINTS = {
    'mobile': 768,
    'tablet': 1024,
    'desktop': 1200
}

def detect_device_type():
    """Detecta tipo de dispositivo usando CSS responsive."""
    return 'responsive'  # CSS adaptativo maneja todo

def get_responsive_columns(device_type='responsive'):
    """Configuración de columnas responsive."""
    configs = {
        'mobile': [1],
        'tablet': [1, 1],
        'desktop': [1, 1, 1, 1],
        'responsive': [1, 1, 1, 1]
    }
    return configs.get(device_type, [1, 1, 1, 1])

# ===== CSS RESPONSIVE PRINCIPAL =====

def get_responsive_css():
    """CSS responsive consolidado y optimizado."""
    return """
    <style>
    /* =============== VARIABLES CSS RESPONSIVE =============== */
    :root {
        --primary-color: #7D0F2B;
        --secondary-color: #F2A900;
        --accent-color: #5A4214;
        --success-color: #509E2F;
        --warning-color: #F7941D;
        --danger-color: #E51937;
        --info-color: #4682B4;
        --light-color: #F9F6E9;
        --dark-color: #2C2C2C;
        
        /* Responsive spacing */
        --spacing-xs: clamp(0.25rem, 1vw, 0.5rem);
        --spacing-sm: clamp(0.5rem, 2vw, 1rem);
        --spacing-md: clamp(1rem, 3vw, 1.5rem);
        --spacing-lg: clamp(1.5rem, 4vw, 2rem);
        
        /* Responsive fonts */
        --font-xs: clamp(0.7rem, 2vw, 0.8rem);
        --font-sm: clamp(0.8rem, 2vw, 0.9rem);
        --font-md: clamp(0.9rem, 2.5vw, 1rem);
        --font-lg: clamp(1rem, 3vw, 1.2rem);
        --font-xl: clamp(1.2rem, 4vw, 1.5rem);
        --font-title: clamp(1.8rem, 6vw, 2.5rem);
    }
    
    /* =============== LAYOUT BASE =============== */
    .block-container {
        padding: var(--spacing-md) var(--spacing-sm) !important;
        max-width: 100% !important;
    }
    
    /* =============== MAPAS RESPONSIVE =============== */
    .mobile-maps-container,
    .desktop-maps-container {
        width: 100% !important;
        max-width: 100% !important;
        overflow: visible !important;
    }
    
    /* Mobile: Mapas centrados */
    .mobile-map-section {
        width: 100% !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        padding: 0 15px !important;
        margin-bottom: 1.5rem !important;
    }
    
    /* =============== RESPONSIVE BREAKPOINTS =============== */
    
    /* MOBILE */
    @media (max-width: 768px) {
        .mobile-map-section iframe {
            width: 100% !important;
            max-width: min(350px, calc(100vw - 30px)) !important;
            min-width: 280px !important;
            height: 350px !important;
            margin: 0 auto !important;
            display: block !important;
            border-radius: 12px !important;
            border: 2px solid #e1e5e9 !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
        }
        
        .desktop-maps-container { display: none !important; }
        .mobile-maps-container { display: block !important; }
        
        /* Sidebar móvil */
        .css-1d391kg {
            width: 280px !important;
            max-width: 90vw !important;
        }
        
        .sidebar .stSelectbox > div > div,
        .sidebar .stMultiSelect > div > div {
            min-height: 44px !important;
            font-size: 16px !important;
        }
        
        .sidebar .stButton > button {
            min-height: 44px !important;
            padding: 0.75rem 1rem !important;
        }
        
        /* Métricas responsive */
        .css-1r6slb0 {
            flex: 1 1 100% !important;
            margin-bottom: 1rem !important;
        }
        
        /* Pestañas móviles */
        .stTabs [data-baseweb="tab"] {
            font-size: 0.75rem !important;
            padding: 0.5rem 0.75rem !important;
        }
    }
    
    /* TABLET */
    @media (min-width: 769px) and (max-width: 1024px) {
        .desktop-map-section iframe {
            width: 100% !important;
            max-width: 500px !important;
            height: 450px !important;
            border-radius: 12px !important;
        }
        
        .css-1r6slb0 {
            flex: 1 1 45% !important;
            margin-bottom: 1rem !important;
        }
    }
    
    /* DESKTOP */
    @media (min-width: 1025px) {
        .desktop-map-section iframe {
            width: 100% !important;
            max-width: 700px !important;
            height: 500px !important;
            border-radius: 12px !important;
        }
        
        .mobile-maps-container { display: none !important; }
        .desktop-maps-container { display: block !important; }
        
        .css-1r6slb0 {
            flex: 1 1 22% !important;
            margin-bottom: 1rem !important;
        }
    }
    
    /* =============== COMPONENTES RESPONSIVE =============== */
    
    /* Métricas */
    [data-testid="metric-container"] {
        background-color: white !important;
        border-radius: 10px !important;
        padding: var(--spacing-md) !important;
        text-align: center !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
        min-height: clamp(100px, 15vw, 140px) !important;
        transition: transform 0.3s ease !important;
        margin-bottom: var(--spacing-sm) !important;
    }
    
    [data-testid="metric-container"]:hover {
        transform: translateY(-3px) !important;
    }
    
    /* Botones responsive */
    .stButton > button {
        width: 100% !important;
        font-size: var(--font-sm) !important;
        padding: var(--spacing-xs) var(--spacing-sm) !important;
        border-radius: 6px !important;
        transition: all 0.3s ease !important;
    }
    
    /* Pestañas responsive */
    .stTabs [data-baseweb="tab-list"] {
        gap: var(--spacing-xs) !important;
        overflow-x: auto !important;
        white-space: nowrap !important;
        -webkit-overflow-scrolling: touch !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-size: var(--font-sm) !important;
        padding: var(--spacing-xs) var(--spacing-sm) !important;
        border-radius: 6px 6px 0 0 !important;
        white-space: nowrap !important;
        min-width: max-content !important;
    }
    
    /* Tablas responsive */
    .dataframe {
        font-size: var(--font-sm) !important;
        width: 100% !important;
        overflow-x: auto !important;
    }
    
    .dataframe th, .dataframe td {
        padding: var(--spacing-xs) !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        max-width: 200px !important;
    }
    
    /* =============== UTILIDADES =============== */
    .text-center { text-align: center !important; }
    .hide-mobile { display: block !important; }
    .show-mobile { display: none !important; }
    
    @media (max-width: 768px) {
        .hide-mobile { display: none !important; }
        .show-mobile { display: block !important; }
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 8px !important;
        height: 8px !important;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1 !important;
        border-radius: 4px !important;
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--primary-color) !important;
        border-radius: 4px !important;
        opacity: 0.7 !important;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--accent-color) !important;
        opacity: 1 !important;
    }
    </style>
    """

def apply_responsive_css():
    """Aplica CSS responsive al dashboard."""
    st.markdown(get_responsive_css(), unsafe_allow_html=True)

# ===== COMPONENTES RESPONSIVE =====

def create_responsive_metric_cards(metrics_data: List[Dict], colors: Dict) -> None:
    """Crea tarjetas de métricas responsive."""
    # Usar métricas nativas de Streamlit que ya son responsive
    cols = st.columns(len(metrics_data))
    
    for i, metric in enumerate(metrics_data):
        with cols[i]:
            st.metric(
                label=metric.get('title', 'Métrica'),
                value=metric.get('value', '0'),
                delta=metric.get('subtitle', None),
                help=metric.get('help', None)
            )

def optimize_plotly_chart(fig: go.Figure, device_type: str = 'responsive') -> go.Figure:
    """Optimiza gráfico de Plotly para responsive."""
    # Configuración responsive básica
    fig.update_layout(
        height=None,  # Auto height
        margin={'l': 40, 'r': 20, 't': 40, 'b': 40},
        font={'size': 12},
        autosize=True,
        responsive=True
    )
    
    return fig

def create_responsive_dataframe(df: pd.DataFrame, max_height: int = 400) -> None:
    """Muestra DataFrame responsive."""
    if df.empty:
        st.info("No hay datos para mostrar")
        return
    
    st.dataframe(
        df,
        use_container_width=True,
        height=max_height
    )

def get_chart_config_for_device(device_type: str = 'responsive') -> Dict:
    """Configuración de gráficos responsive."""
    return {
        'displayModeBar': True,
        'modeBarButtonsToRemove': ['pan2d', 'lasso2d'],
        'responsive': True,
        'toImageButtonOptions': {
            'format': 'png',
            'filename': 'grafico_fiebre_amarilla',
            'scale': 2
        }
    }

# ===== INICIALIZACIÓN =====

def init_responsive_utils():
    """Inicializa sistema responsive."""
    apply_responsive_css()
    
    # Meta tags para móviles
    st.markdown(
        '''
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <meta name="mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-capable" content="yes">
        ''',
        unsafe_allow_html=True
    )

init_responsive_dashboard = init_responsive_utils
apply_mobile_optimizations = apply_responsive_css
optimize_sidebar_for_mobile = lambda: None  # Ya incluido en CSS principal
create_responsive_tabs = lambda x, y: None  # Ya incluido en CSS principal