"""
Configuraciones esenciales del dashboard.
"""

from pathlib import Path

# ===== RUTAS ESENCIALES =====
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
ASSETS_DIR = ROOT_DIR / "assets"

# ===== CONFIGURACIÓN DE APLICACIÓN =====
DASHBOARD_CONFIG = {
    "page_title": "Dashboard Fiebre Amarilla - Tolima",
    "page_icon": "🦟",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# ===== ARCHIVOS DE DATOS =====
DATA_FILES = {
    "casos_confirmados": "BD_positivos.xlsx",
    "epizootias": "BD_positivos.xlsx",  
    "casos_sheet": "ACUMU",
    "epizootias_sheet": "EPIZOOTIAS",  
    "veredas_sheet": "VEREDAS",
}

# ===== MAPEOS CRÍTICOS =====
# Mapeo de columnas para casos
CASOS_COLUMNS_MAP = {
    "edad_": "edad",
    "sexo_": "sexo",
    "vereda_": "vereda",
    "nmun_proce": "municipio",
    "Condición Final": "condicion_final",
    "Inicio de sintomas": "fecha_inicio_sintomas",
}

# Mapeo de columnas para epizootias
EPIZOOTIAS_COLUMNS_MAP = {
    "MUNICIPIO": "municipio",
    "VEREDA": "vereda", 
    "FECHA_NOTIFICACION": "fecha_notificacion",
    "INFORMANTE": "proveniente",
    "DESCRIPCIÓN": "descripcion",
}

# ===== GRUPOS DE EDAD =====
GRUPOS_EDAD = [
    {"min": 0, "max": 14, "label": "0-14 años"},
    {"min": 15, "max": 29, "label": "15-29 años"},
    {"min": 30, "max": 44, "label": "30-44 años"},
    {"min": 45, "max": 59, "label": "45-59 años"},
    {"min": 60, "max": 120, "label": "60+ años"},
]

# ===== MAPEOS BÁSICOS =====
CONDICION_FINAL_MAP = {
    "Fallecido": {"color": "#E51937", "categoria": "Crítico"},
    "Vivo": {"color": "#509E2F", "categoria": "Bueno"},
}

DESCRIPCION_EPIZOOTIAS_MAP = {
    "POSITIVO FA": {"color": "#E51937", "categoria": "Positivo"},
    "EN ESTUDIO": {"color": "#4682B4", "categoria": "En estudio"},
}

# ===== CONFIGURACIÓN DE FILTROS =====
FILTROS_CONFIG = {
    "municipio": {
        "titulo": "📍 MUNICIPIO",
        "default": "Todos",
        "jerarquia": 1,
    },
    "vereda": {
        "titulo": "🏘️ VEREDA", 
        "default": "Todas",
        "jerarquia": 2,
    },
}

# ===== CONFIGURACIÓN DE PESTAÑAS =====
TABS_CONFIG = {
    "mapas": {"titulo": "🗺️ Mapas", "descripcion": "Distribución geográfica"},
    "tablas": {"titulo": "📊 Información Detallada", "descripcion": "Datos y análisis"},
    "comparativo": {"titulo": "📈 Seguimiento Temporal", "descripcion": "Análisis temporal"},
}

# ===== VERSIÓN =====
VERSION_INFO = {
    "version": "1.0",
    "descripcion": "Dashboard Optimizado Fiebre Amarilla",
    "fecha_release": "2025-07-13",
}