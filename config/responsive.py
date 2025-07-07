"""
Configuración de responsividad para el dashboard de Fiebre Amarilla.
"""

import streamlit as st

# Breakpoints para dispositivos
BREAKPOINTS = {
    'mobile': 768,
    'tablet': 1024,
    'desktop': 1200
}

# Configuraciones responsive por componente
RESPONSIVE_CONFIG = {
    'sidebar': {
        'min_width_mobile': '250px',
        'min_width_tablet': '280px', 
        'min_width_desktop': '300px'
    },
    'main_content': {
        'padding_mobile': '1rem',
        'padding_tablet': '1.5rem',
        'padding_desktop': '2rem'
    },
    'charts': {
        'height_mobile': 300,
        'height_tablet': 400,
        'height_desktop': 500
    },
    'tables': {
        'font_size_mobile': '0.8rem',
        'font_size_tablet': '0.85rem',
        'font_size_desktop': '0.9rem'
    },
    'metrics': {
        'columns_mobile': 2,
        'columns_tablet': 3,
        'columns_desktop': 4
    }
}

def get_device_type():
    """
    Determina el tipo de dispositivo basado en el ancho de la pantalla.
    Nota: Esta es una aproximación ya que Streamlit no proporciona dimensiones del viewport.
    """
    # En Streamlit no tenemos acceso directo al ancho de pantalla
    # Por ahora retornamos 'responsive' para usar CSS adaptativo
    return 'responsive'

def get_responsive_css():
    """
    Retorna CSS personalizado para hacer el dashboard completamente responsive.
    """
    return """
    <style>
    /* =============== CORRECCIÓN SCROLL INFINITO =============== */
    
    /* Contenedor principal con altura limitada */
    .main .block-container {
        max-height: calc(100vh - 100px) !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
    }
    
    /* Limitar altura de elementos que pueden crecer */
    .stDataFrame > div {
        max-height: 400px !important;
        overflow-y: auto !important;
    }
    
    .element-container {
        max-height: none !important; /* Permitir que los contenedores se ajusten */
    }
    
    /* =============== BASE RESPONSIVE STYLES (SIN CAMBIOS) =============== */
    
    /* Variables CSS para consistencia */
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
        --spacing-xl: clamp(2rem, 5vw, 3rem);
        
        /* Responsive font sizes */
        --font-xs: clamp(0.7rem, 2vw, 0.8rem);
        --font-sm: clamp(0.8rem, 2vw, 0.9rem);
        --font-md: clamp(0.9rem, 2.5vw, 1rem);
        --font-lg: clamp(1rem, 3vw, 1.2rem);
        --font-xl: clamp(1.2rem, 4vw, 1.5rem);
        --font-xxl: clamp(1.5rem, 5vw, 2rem);
        --font-title: clamp(1.8rem, 6vw, 2.5rem);
    }
    
    /* =============== CHARTS RESPONSIVE =============== */
    
    /* Plotly charts CON ALTURA LIMITADA */
    .js-plotly-plot {
        width: 100% !important;
        max-height: 500px !important;
        overflow: hidden !important;
    }
    
    /* El resto del CSS permanece igual... */
    /* (mantén todo lo demás de la función original sin cambios) */
    
    </style>
    /* =============== BASE RESPONSIVE STYLES =============== */
    
    /* Variables CSS para consistencia */
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
        --spacing-xl: clamp(2rem, 5vw, 3rem);
        
        /* Responsive font sizes */
        --font-xs: clamp(0.7rem, 2vw, 0.8rem);
        --font-sm: clamp(0.8rem, 2vw, 0.9rem);
        --font-md: clamp(0.9rem, 2.5vw, 1rem);
        --font-lg: clamp(1rem, 3vw, 1.2rem);
        --font-xl: clamp(1.2rem, 4vw, 1.5rem);
        --font-xxl: clamp(1.5rem, 5vw, 2rem);
        --font-title: clamp(1.8rem, 6vw, 2.5rem);
    }
    
    /* =============== LAYOUT RESPONSIVE =============== */
    
    /* Main container */
    .block-container {
        padding-top: var(--spacing-md) !important;
        padding-bottom: var(--spacing-md) !important;
        padding-left: var(--spacing-sm) !important;
        padding-right: var(--spacing-sm) !important;
        max-width: 100% !important;
    }
    
    /* Sidebar responsive */
    .css-1d391kg {
        min-width: clamp(250px, 25vw, 320px) !important;
        padding: var(--spacing-sm) !important;
    }
    
    /* =============== TYPOGRAPHY RESPONSIVE =============== */
    
    /* Main titles */
    .main-title {
        color: var(--primary-color);
        font-size: var(--font-title) !important;
        font-weight: 700;
        margin-bottom: var(--spacing-sm);
        text-align: center;
        padding-bottom: var(--spacing-xs);
        border-bottom: 3px solid var(--secondary-color);
        line-height: 1.2;
    }
    
    .subtitle {
        color: var(--accent-color);
        font-size: var(--font-xl) !important;
        text-align: center;
        margin-bottom: var(--spacing-md);
        line-height: 1.3;
    }
    
    /* Section headers */
    h1, h2, h3, h4, h5, h6 {
        line-height: 1.3 !important;
    }
    
    h1 { font-size: var(--font-title) !important; }
    h2 { font-size: var(--font-xxl) !important; }
    h3 { font-size: var(--font-xl) !important; }
    h4 { font-size: var(--font-lg) !important; }
    h5, h6 { font-size: var(--font-md) !important; }
    
    /* =============== COMPONENTS RESPONSIVE =============== */
    
    /* Metrics cards */
    .metric-card, [data-testid="metric-container"] {
        background-color: white !important;
        border-radius: 10px !important;
        padding: var(--spacing-md) !important;
        text-align: center !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
        height: auto !important;
        min-height: clamp(100px, 15vw, 140px) !important;
        transition: transform 0.3s ease !important;
        margin-bottom: var(--spacing-sm) !important;
    }
    
    .metric-card:hover, [data-testid="metric-container"]:hover {
        transform: translateY(-3px) !important;
    }
    
    /* Metric values responsive */
    [data-testid="metric-container"] > div > div {
        font-size: var(--font-lg) !important;
    }
    
    [data-testid="metric-container"] [data-testid="metric-value"] {
        font-size: var(--font-xxl) !important;
        font-weight: 600 !important;
    }
    
    /* =============== BUTTONS RESPONSIVE =============== */
    
    .stButton > button {
        width: 100% !important;
        font-size: var(--font-sm) !important;
        padding: var(--spacing-xs) var(--spacing-sm) !important;
        border-radius: 6px !important;
        transition: all 0.3s ease !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
    }
    
    /* =============== FORMS RESPONSIVE =============== */
    
    /* Select boxes */
    .stSelectbox > div > div {
        font-size: var(--font-sm) !important;
    }
    
    /* Date inputs */
    .stDateInput > div > div {
        font-size: var(--font-sm) !important;
    }
    
    /* Multiselect */
    .stMultiSelect > div > div {
        font-size: var(--font-sm) !important;
    }
    
    /* Text inputs */
    .stTextInput > div > div > input {
        font-size: var(--font-sm) !important;
        padding: var(--spacing-xs) !important;
    }
    
    /* =============== TABLES RESPONSIVE =============== */
    
    .dataframe {
        font-size: var(--font-sm) !important;
        width: 100% !important;
        overflow-x: auto !important;
    }
    
    .dataframe table {
        min-width: 100% !important;
    }
    
    .dataframe th, .dataframe td {
        padding: var(--spacing-xs) !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        max-width: 200px !important;
    }
    
    /* =============== CHARTS RESPONSIVE =============== */
    
    /* Plotly charts */
    .js-plotly-plot {
        width: 100% !important;
        height: auto !important;
    }
    
    .plotly .modebar {
        display: none !important;
    }
    
    /* =============== TABS RESPONSIVE =============== */
    
    .stTabs [data-baseweb="tab-list"] {
        gap: var(--spacing-xs) !important;
        overflow-x: auto !important;
        overflow-y: hidden !important;
        white-space: nowrap !important;
        padding-bottom: var(--spacing-xs) !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-size: var(--font-sm) !important;
        padding: var(--spacing-xs) var(--spacing-sm) !important;
        border-radius: 6px 6px 0 0 !important;
        white-space: nowrap !important;
        min-width: max-content !important;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: var(--primary-color) !important;
        color: white !important;
    }
    
    /* =============== SIDEBAR RESPONSIVE =============== */
    
    .sidebar .stMarkdown {
        font-size: var(--font-sm) !important;
        line-height: 1.4 !important;
    }
    
    .sidebar .stSelectbox label,
    .sidebar .stMultiSelect label,
    .sidebar .stDateInput label {
        font-size: var(--font-sm) !important;
        font-weight: 600 !important;
    }
    
    /* =============== COLUMNS RESPONSIVE =============== */
    
    .css-1r6slb0 {
        flex: 1 1 auto !important;
        min-width: 0 !important;
        margin-bottom: var(--spacing-sm) !important;
    }
    
    /* =============== EXPANDERS RESPONSIVE =============== */
    
    .streamlit-expanderHeader {
        font-size: var(--font-md) !important;
        font-weight: 600 !important;
    }
    
    .streamlit-expanderContent {
        font-size: var(--font-sm) !important;
    }
    
    /* =============== ALERTS AND MESSAGES =============== */
    
    .stAlert {
        font-size: var(--font-sm) !important;
        padding: var(--spacing-sm) !important;
        border-radius: 6px !important;
        margin: var(--spacing-xs) 0 !important;
    }
    
    .stSuccess, .stInfo, .stWarning, .stError {
        font-size: var(--font-sm) !important;
        padding: var(--spacing-sm) !important;
        border-radius: 6px !important;
        margin: var(--spacing-xs) 0 !important;
    }
    
    /* =============== MOBILE SPECIFIC =============== */
    
    @media (max-width: 768px) {
        /* Hide sidebar by default on mobile */
        .css-1d391kg {
            transform: translateX(-100%) !important;
            transition: transform 0.3s ease !important;
        }
        
        .css-1d391kg.css-1d391kg-open {
            transform: translateX(0) !important;
        }
        
        /* Adjust main content for mobile */
        .block-container {
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
        
        /* Stack metrics vertically on mobile */
        .css-1r6slb0 {
            flex: 1 1 100% !important;
            margin-bottom: 1rem !important;
        }
        
        /* Reduce tab spacing on mobile */
        .stTabs [data-baseweb="tab"] {
            font-size: 0.75rem !important;
            padding: 0.4rem 0.6rem !important;
        }
        
        /* Smaller charts on mobile */
        .js-plotly-plot {
            height: 300px !important;
        }
        
        /* Adjust table text on mobile */
        .dataframe th, .dataframe td {
            font-size: 0.7rem !important;
            max-width: 100px !important;
        }
    }
    
    /* =============== TABLET SPECIFIC =============== */
    
    @media (min-width: 769px) and (max-width: 1024px) {
        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        
        .css-1r6slb0 {
            flex: 1 1 45% !important;
            margin-bottom: 1rem !important;
        }
        
        .js-plotly-plot {
            height: 400px !important;
        }
    }
    
    /* =============== DESKTOP SPECIFIC =============== */
    
    @media (min-width: 1025px) {
        .block-container {
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }
        
        .css-1r6slb0 {
            flex: 1 1 22% !important;
            margin-bottom: 1rem !important;
        }
        
        .js-plotly-plot {
            height: 500px !important;
        }
    }
    
    /* =============== PRINT STYLES =============== */
    
    @media print {
        .sidebar, .stButton, .stSelectbox {
            display: none !important;
        }
        
        .main-title, .subtitle {
            color: black !important;
        }
        
        .block-container {
            padding: 1rem !important;
        }
    }
    
    /* =============== HIGH CONTRAST MODE =============== */
    
    @media (prefers-contrast: high) {
        .metric-card, [data-testid="metric-container"] {
            border: 2px solid var(--dark-color) !important;
        }
        
        .stButton > button {
            border: 2px solid var(--primary-color) !important;
        }
    }
    
    /* =============== REDUCED MOTION =============== */
    
    @media (prefers-reduced-motion: reduce) {
        * {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }
        
        .metric-card:hover, [data-testid="metric-container"]:hover {
            transform: none !important;
        }
        
        .stButton > button:hover {
            transform: none !important;
        }
    }
    
    /* =============== DARK MODE SUPPORT =============== */
    
    @media (prefers-color-scheme: dark) {
        .metric-card, [data-testid="metric-container"] {
            background-color: #2b2b2b !important;
            color: white !important;
        }
        
        .dataframe {
            background-color: #2b2b2b !important;
            color: white !important;
        }
    }
    
    /* =============== UTILITIES =============== */
    
    .text-center { text-align: center !important; }
    .text-left { text-align: left !important; }
    .text-right { text-align: right !important; }
    
    .hide-mobile { display: block !important; }
    .show-mobile { display: none !important; }
    
    @media (max-width: 768px) {
        .hide-mobile { display: none !important; }
        .show-mobile { display: block !important; }
    }
    
    .responsive-margin { margin: var(--spacing-sm) 0 !important; }
    .responsive-padding { padding: var(--spacing-sm) !important; }
    
    /* =============== SCROLLBAR STYLING =============== */
    
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
    """
    Aplica el CSS responsive al dashboard.
    """
    st.markdown(get_responsive_css(), unsafe_allow_html=True)

def get_responsive_column_config(device_type='responsive'):
    """
    Retorna configuración de columnas basada en el tipo de dispositivo.
    """
    if device_type == 'mobile':
        return [1]  # Una columna en móvil
    elif device_type == 'tablet':
        return [1, 1]  # Dos columnas en tablet
    else:
        return [1, 1, 1, 1]  # Cuatro columnas en desktop

def get_chart_height(device_type='responsive', chart_type='default'):
    """
    Retorna altura de gráfico basada en el dispositivo y tipo de gráfico.
    """
    heights = {
        'mobile': {'default': 300, 'large': 350, 'small': 250},
        'tablet': {'default': 400, 'large': 450, 'small': 350},
        'desktop': {'default': 500, 'large': 600, 'small': 400}
    }
    
    return heights.get(device_type, heights['desktop']).get(chart_type, 400)

def create_responsive_container(content, container_type='default'):
    """
    Crea un contenedor responsive para el contenido.
    """
    container_styles = {
        'default': 'responsive-padding',
        'card': 'metric-card',
        'alert': 'stAlert',
        'section': 'responsive-margin'
    }
    
    css_class = container_styles.get(container_type, 'responsive-padding')
    
    return f'<div class="{css_class}">{content}</div>'

def optimize_for_mobile():
    """
    Aplicar optimizaciones específicas para móviles.
    """
    mobile_css = """
    <style>
    /* Mobile-first optimizations */
    @media (max-width: 768px) {
        /* Force single column layout */
        .css-1r6slb0 {
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }
        
        /* Reduce white space */
        .block-container {
            padding: 0.5rem !important;
        }
        
        /* Optimize touch targets */
        .stButton > button,
        .stSelectbox > div,
        .stMultiSelect > div {
            min-height: 44px !important;
            touch-action: manipulation !important;
        }
        
        /* Prevent zoom on input focus */
        input, select, textarea {
            font-size: 16px !important;
        }
        
        /* Optimize scrolling */
        .stTabs [data-baseweb="tab-list"] {
            -webkit-overflow-scrolling: touch !important;
        }
    }
    </style>
    """
    st.markdown(mobile_css, unsafe_allow_html=True)

# Función principal para inicializar responsividad
def init_responsive_dashboard():
    """
    Inicializa todas las configuraciones responsive del dashboard.
    """
    apply_responsive_css()
    optimize_for_mobile()
    
    # Agregar meta viewport para móviles
    st.markdown(
        '<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">',
        unsafe_allow_html=True
    )