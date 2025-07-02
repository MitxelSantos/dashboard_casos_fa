"""
Utilidades para hacer el dashboard completamente responsive.
Funciones para detectar dispositivos, adaptar layouts y optimizar contenido.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Tuple, Union

# Configuraciones de breakpoints
BREAKPOINTS = {
    'mobile': 768,
    'tablet': 1024,
    'desktop': 1200
}

def detect_device_type() -> str:
    """
    Detecta el tipo de dispositivo (aproximado) basado en user agent.
    En Streamlit no tenemos acceso directo al viewport, así que usamos CSS responsive.
    
    Returns:
        str: 'mobile', 'tablet', o 'desktop'
    """
    # Por defecto retornamos 'responsive' para usar CSS adaptativo
    # En una implementación real, podrías usar JavaScript para detectar el viewport
    return 'responsive'

def get_responsive_columns(device_type: str = 'responsive') -> List[int]:
    """
    Retorna configuración de columnas según el dispositivo.
    
    Args:
        device_type (str): Tipo de dispositivo
        
    Returns:
        List[int]: Lista de proporciones de columnas
    """
    configs = {
        'mobile': [1],           # 1 columna en móvil
        'tablet': [1, 1],        # 2 columnas en tablet
        'desktop': [1, 1, 1, 1], # 4 columnas en desktop
        'responsive': [1, 1, 1, 1]  # CSS adaptativo manejará el responsive
    }
    
    return configs.get(device_type, [1, 1, 1, 1])

def create_responsive_metric_cards(metrics_data: List[Dict], colors: Dict) -> None:
    """
    Crea tarjetas de métricas responsive.
    
    Args:
        metrics_data (List[Dict]): Lista con datos de métricas
        colors (Dict): Diccionario de colores
    """
    # CSS específico para tarjetas de métricas
    st.markdown(
        f"""
        <style>
        .responsive-metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: clamp(0.75rem, 2vw, 1.25rem);
            margin: clamp(1rem, 3vw, 1.5rem) 0;
        }}
        
        .responsive-metric-card {{
            background: linear-gradient(135deg, white 0%, #f8f9fa 100%);
            border-radius: 12px;
            padding: clamp(1rem, 3vw, 1.5rem);
            text-align: center;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
            border-top: 4px solid {colors.get('primary', '#7D0F2B')};
            min-height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}
        
        .responsive-metric-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }}
        
        .metric-icon {{
            font-size: clamp(1.5rem, 4vw, 2rem);
            margin-bottom: 0.5rem;
        }}
        
        .metric-title {{
            font-size: clamp(0.8rem, 2vw, 0.9rem);
            color: #666;
            font-weight: 600;
            margin-bottom: 0.25rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .metric-value {{
            font-size: clamp(1.5rem, 4vw, 2rem);
            font-weight: 700;
            color: {colors.get('primary', '#7D0F2B')};
            margin-bottom: 0.25rem;
        }}
        
        .metric-subtitle {{
            font-size: clamp(0.7rem, 2vw, 0.8rem);
            color: #888;
            margin: 0;
        }}
        
        @media (max-width: 768px) {{
            .responsive-metric-grid {{
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 0.75rem;
            }}
            
            .responsive-metric-card {{
                min-height: 100px;
                padding: 0.75rem;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Generar HTML para las tarjetas
    cards_html = '<div class="responsive-metric-grid">'
    
    for metric in metrics_data:
        icon = metric.get('icon', '📊')
        title = metric.get('title', 'Métrica')
        value = metric.get('value', '0')
        subtitle = metric.get('subtitle', '')
        
        card_html = f"""
        <div class="responsive-metric-card">
            <div class="metric-icon">{icon}</div>
            <div class="metric-title">{title}</div>
            <div class="metric-value">{value}</div>
            {f'<div class="metric-subtitle">{subtitle}</div>' if subtitle else ''}
        </div>
        """
        cards_html += card_html
    
    cards_html += '</div>'
    st.markdown(cards_html, unsafe_allow_html=True)

def optimize_plotly_chart(fig: go.Figure, device_type: str = 'responsive') -> go.Figure:
    """
    Optimiza un gráfico de Plotly para diferentes dispositivos.
    
    Args:
        fig (go.Figure): Figura de Plotly
        device_type (str): Tipo de dispositivo
        
    Returns:
        go.Figure: Figura optimizada
    """
    # Configuraciones por dispositivo
    configs = {
        'mobile': {
            'height': 300,
            'font_size': 10,
            'margin': {'l': 40, 'r': 20, 't': 40, 'b': 40},
            'legend_x': 0,
            'legend_y': -0.2
        },
        'tablet': {
            'height': 400,
            'font_size': 12,
            'margin': {'l': 50, 'r': 30, 't': 50, 'b': 50},
            'legend_x': 0,
            'legend_y': -0.15
        },
        'desktop': {
            'height': 500,
            'font_size': 14,
            'margin': {'l': 60, 'r': 40, 't': 60, 'b': 60},
            'legend_x': 0,
            'legend_y': -0.1
        },
        'responsive': {
            'height': None,  # Auto height
            'font_size': 12,
            'margin': {'l': 50, 'r': 30, 't': 50, 'b': 50},
            'legend_x': 0,
            'legend_y': -0.15
        }
    }
    
    config = configs.get(device_type, configs['responsive'])
    
    # Aplicar configuraciones
    fig.update_layout(
        height=config['height'],
        margin=config['margin'],
        font={'size': config['font_size']},
        legend={'x': config['legend_x'], 'y': config['legend_y'], 'orientation': 'h'},
        autosize=True,
        responsive=True
    )
    
    # Optimizaciones específicas para móviles
    if device_type == 'mobile':
        fig.update_layout(
            title={'font': {'size': 14}},
            xaxis={'title': {'font': {'size': 10}}},
            yaxis={'title': {'font': {'size': 10}}}
        )
        
        # Reducir número de ticks en móviles
        fig.update_xaxes(nticks=5)
        fig.update_yaxes(nticks=5)
    
    return fig

def create_responsive_dataframe(df: pd.DataFrame, max_height: int = 400) -> None:
    """
    Muestra un DataFrame de manera responsive.
    
    Args:
        df (pd.DataFrame): DataFrame a mostrar
        max_height (int): Altura máxima en píxeles
    """
    if df.empty:
        st.info("No hay datos para mostrar")
        return
    
    # CSS para tablas responsive
    st.markdown(
        """
        <style>
        .responsive-dataframe {
            overflow-x: auto;
            overflow-y: auto;
            max-height: 400px;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
        }
        
        .responsive-dataframe table {
            font-size: clamp(0.75rem, 2vw, 0.85rem);
            width: 100%;
        }
        
        .responsive-dataframe th {
            background-color: #f8f9fa;
            font-weight: 600;
            color: #2c2c2c;
            padding: 0.5rem;
            border-bottom: 2px solid #dee2e6;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        
        .responsive-dataframe td {
            padding: 0.5rem;
            border-bottom: 1px solid #dee2e6;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 200px;
        }
        
        .responsive-dataframe tr:hover {
            background-color: #f8f9fa;
        }
        
        @media (max-width: 768px) {
            .responsive-dataframe th,
            .responsive-dataframe td {
                padding: 0.25rem;
                font-size: 0.7rem;
                max-width: 100px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Mostrar DataFrame con configuración responsive
    st.dataframe(
        df,
        use_container_width=True,
        height=max_height
    )

def create_responsive_container(content: str, container_type: str = 'default') -> str:
    """
    Crea un contenedor HTML responsive.
    
    Args:
        content (str): Contenido HTML
        container_type (str): Tipo de contenedor
        
    Returns:
        str: HTML del contenedor
    """
    container_styles = {
        'default': 'padding: clamp(1rem, 3vw, 1.5rem); margin: 1rem 0;',
        'card': '''
            background: white;
            border-radius: 12px;
            padding: clamp(1rem, 3vw, 1.5rem);
            margin: 1rem 0;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            border-left: 4px solid #7D0F2B;
        ''',
        'alert': '''
            padding: clamp(0.75rem, 2vw, 1rem);
            margin: 0.5rem 0;
            border-radius: 6px;
            border-left: 4px solid #F2A900;
            background-color: #fff3cd;
        ''',
        'section': '''
            padding: clamp(1.5rem, 4vw, 2rem) 0;
            margin: 1rem 0;
        '''
    }
    
    style = container_styles.get(container_type, container_styles['default'])
    
    return f'<div style="{style}">{content}</div>'

def create_responsive_info_box(title: str, content: str, icon: str = "ℹ️", color: str = "#4682B4") -> None:
    """
    Crea una caja de información responsive.
    
    Args:
        title (str): Título de la caja
        content (str): Contenido
        icon (str): Icono
        color (str): Color del borde
    """
    st.markdown(
        f"""
        <div style="
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: clamp(1rem, 3vw, 1.5rem);
            margin: clamp(0.75rem, 2vw, 1rem) 0;
            border-left: 5px solid {color};
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        ">
            <h4 style="
                color: {color};
                margin-top: 0;
                margin-bottom: 0.75rem;
                font-size: clamp(1rem, 3vw, 1.1rem);
                display: flex;
                align-items: center;
                gap: 0.5rem;
            ">
                {icon} {title}
            </h4>
            <div style="
                color: #2c2c2c;
                line-height: 1.5;
                font-size: clamp(0.85rem, 2vw, 0.95rem);
            ">
                {content}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def optimize_sidebar_for_mobile() -> None:
    """
    Optimiza la barra lateral para dispositivos móviles.
    """
    st.markdown(
        """
        <style>
        /* Optimizaciones móviles para sidebar */
        @media (max-width: 768px) {
            .css-1d391kg {
                width: 280px !important;
                max-width: 90vw !important;
            }
            
            /* Hacer que los selectboxes sean más grandes en móvil */
            .sidebar .stSelectbox > div > div,
            .sidebar .stMultiSelect > div > div {
                min-height: 44px !important;
                font-size: 16px !important; /* Previene zoom en iOS */
            }
            
            /* Botones más grandes para mejor experiencia táctil */
            .sidebar .stButton > button {
                min-height: 44px !important;
                padding: 0.75rem 1rem !important;
                font-size: 0.9rem !important;
            }
            
            /* Reducir espaciado en móvil */
            .sidebar .stMarkdown {
                margin-bottom: 0.5rem !important;
            }
            
            /* Mejorar legibilidad en móvil */
            .sidebar h1, .sidebar h2, .sidebar h3 {
                line-height: 1.2 !important;
            }
        }
        
        /* Optimización para tablets */
        @media (min-width: 769px) and (max-width: 1024px) {
            .css-1d391kg {
                width: 300px !important;
            }
            
            .sidebar .stSelectbox > div > div,
            .sidebar .stMultiSelect > div > div {
                min-height: 40px !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def create_responsive_tabs(tab_labels: List[str], tab_contents: List[str]) -> None:
    """
    Crea pestañas responsive optimizadas para todos los dispositivos.
    
    Args:
        tab_labels (List[str]): Etiquetas de las pestañas
        tab_contents (List[str]): Contenido de cada pestaña
    """
    # CSS para pestañas responsive
    st.markdown(
        """
        <style>
        .stTabs [data-baseweb="tab-list"] {
            gap: clamp(0.25rem, 1vw, 0.5rem);
            overflow-x: auto;
            overflow-y: hidden;
            white-space: nowrap;
            padding: 0 0 0.5rem 0;
            margin: 0 0 1rem 0;
            -webkit-overflow-scrolling: touch;
        }
        
        .stTabs [data-baseweb="tab"] {
            font-size: clamp(0.8rem, 2vw, 0.9rem);
            padding: clamp(0.5rem, 2vw, 0.75rem) clamp(0.75rem, 3vw, 1rem);
            border-radius: 8px 8px 0 0;
            white-space: nowrap;
            min-width: max-content;
            transition: all 0.3s ease;
            border: 1px solid #dee2e6;
            border-bottom: none;
            background-color: #f8f9fa;
        }
        
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: #7D0F2B;
            color: white;
            font-weight: 600;
            border-color: #7D0F2B;
        }
        
        .stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
            background-color: #e9ecef;
        }
        
        .stTabs [data-baseweb="tab-panel"] {
            padding: clamp(1rem, 3vw, 1.5rem) 0;
        }
        
        @media (max-width: 768px) {
            .stTabs [data-baseweb="tab"] {
                font-size: 0.75rem;
                padding: 0.5rem 0.75rem;
            }
            
            .stTabs [data-baseweb="tab-panel"] {
                padding: 1rem 0;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def get_chart_config_for_device(device_type: str = 'responsive') -> Dict:
    """
    Retorna configuración de gráficos optimizada para el dispositivo.
    
    Args:
        device_type (str): Tipo de dispositivo
        
    Returns:
        Dict: Configuración del gráfico
    """
    configs = {
        'mobile': {
            'displayModeBar': False,
            'staticPlot': False,
            'responsive': True,
            'toImageButtonOptions': {
                'format': 'png',
                'filename': 'grafico',
                'height': 300,
                'width': 300,
                'scale': 2
            }
        },
        'tablet': {
            'displayModeBar': True,
            'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
            'responsive': True,
            'toImageButtonOptions': {
                'format': 'png',
                'filename': 'grafico',
                'height': 400,
                'width': 600,
                'scale': 2
            }
        },
        'desktop': {
            'displayModeBar': True,
            'responsive': True,
            'toImageButtonOptions': {
                'format': 'png',
                'filename': 'grafico',
                'height': 500,
                'width': 800,
                'scale': 2
            }
        },
        'responsive': {
            'displayModeBar': True,
            'modeBarButtonsToRemove': ['pan2d', 'lasso2d'],
            'responsive': True,
            'toImageButtonOptions': {
                'format': 'png',
                'filename': 'grafico_fiebre_amarilla',
                'scale': 2
            }
        }
    }
    
    return configs.get(device_type, configs['responsive'])

def apply_mobile_optimizations() -> None:
    """
    Aplica todas las optimizaciones para dispositivos móviles.
    """
    st.markdown(
        """
        <style>
        /* Meta viewport para móviles */
        @viewport {
            width: device-width;
            initial-scale: 1.0;
            maximum-scale: 1.0;
            user-scalable: no;
        }
        
        /* Prevenir zoom en inputs en iOS */
        input, select, textarea {
            font-size: 16px !important;
        }
        
        /* Optimizar touch targets */
        button, a, input, select {
            min-height: 44px;
            min-width: 44px;
        }
        
        /* Mejorar scrolling en móviles */
        * {
            -webkit-overflow-scrolling: touch;
        }
        
        /* Optimizar texto para pantallas pequeñas */
        @media (max-width: 768px) {
            body {
                -webkit-text-size-adjust: 100%;
                -ms-text-size-adjust: 100%;
            }
            
            /* Reducir espaciado general */
            .block-container {
                padding: 0.5rem !important;
            }
            
            /* Hacer que las columnas se apilen en móvil */
            .css-1r6slb0 {
                flex: 1 1 100% !important;
                margin-bottom: 1rem !important;
            }
            
            /* Optimizar tablas para móvil */
            .dataframe {
                font-size: 0.7rem !important;
            }
            
            .dataframe th, .dataframe td {
                padding: 0.25rem !important;
                max-width: 80px !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def create_responsive_grid(items: List[Dict], columns_config: Dict = None) -> None:
    """
    Crea una grilla responsive para mostrar elementos.
    
    Args:
        items (List[Dict]): Lista de elementos a mostrar
        columns_config (Dict): Configuración de columnas por dispositivo
    """
    if not columns_config:
        columns_config = {
            'mobile': 1,
            'tablet': 2,
            'desktop': 3
        }
    
    # CSS para la grilla responsive
    st.markdown(
        f"""
        <style>
        .responsive-grid {{
            display: grid;
            gap: clamp(0.75rem, 2vw, 1.25rem);
            margin: 1rem 0;
        }}
        
        /* Mobile */
        @media (max-width: 768px) {{
            .responsive-grid {{
                grid-template-columns: repeat({columns_config['mobile']}, 1fr);
            }}
        }}
        
        /* Tablet */
        @media (min-width: 769px) and (max-width: 1024px) {{
            .responsive-grid {{
                grid-template-columns: repeat({columns_config['tablet']}, 1fr);
            }}
        }}
        
        /* Desktop */
        @media (min-width: 1025px) {{
            .responsive-grid {{
                grid-template-columns: repeat({columns_config['desktop']}, 1fr);
            }}
        }}
        
        .grid-item {{
            background: white;
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}
        
        .grid-item:hover {{
            transform: translateY(-2px);
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Generar HTML para la grilla
    grid_html = '<div class="responsive-grid">'
    
    for item in items:
        item_html = f"""
        <div class="grid-item">
            {item.get('content', '')}
        </div>
        """
        grid_html += item_html
    
    grid_html += '</div>'
    st.markdown(grid_html, unsafe_allow_html=True)

# Función principal para inicializar todas las optimizaciones responsive
def init_responsive_utils():
    """
    Inicializa todas las utilidades responsive.
    """
    apply_mobile_optimizations()
    optimize_sidebar_for_mobile()
    create_responsive_tabs([], [])  # Aplicar solo CSS
    
    # Agregar meta tags para móviles si es posible
    st.markdown(
        '''
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <meta name="mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="default">
        ''',
        unsafe_allow_html=True
    )