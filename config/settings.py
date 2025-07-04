"""
Configuraciones globales del dashboard de Fiebre Amarilla v2.1.
OPTIMIZADO: Eliminadas referencias a timeline y funcionalidades no usadas.
ENFOQUE: Dashboard informativo simplificado.
"""

from pathlib import Path

# Configuración de rutas
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
ASSETS_DIR = ROOT_DIR / "assets"
IMAGES_DIR = ASSETS_DIR / "images"

# Configuración de archivos de datos
DATA_FILES = {
    "casos_confirmados": "BD_positivos.xlsx",
    "epizootias": "Información_Datos_FA.xlsx",
    "casos_sheet": "ACUMU",
    "epizootias_sheet": "Base de Datos",
}

# Configuración de la aplicación
DASHBOARD_CONFIG = {
    "page_title": "Dashboard Fiebre Amarilla - Tolima",
    "page_icon": "🦟",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
    "max_municipios_dropdown": 50,
    "max_veredas_dropdown": 100,
}

# Mapeos de columnas para casos confirmados
CASOS_COLUMNS_MAP = {
    "edad_": "edad",
    "sexo_": "sexo",
    "vereda_": "vereda",
    "nmun_proce": "municipio",
    "cod_ase_": "eps",
    "Condición Final": "condicion_final",
    "Inicio de sintomas": "fecha_inicio_sintomas",
}

# Mapeos de columnas para epizootias
EPIZOOTIAS_COLUMNS_MAP = {
    "MUNICIPIO": "municipio",
    "VEREDA": "vereda",
    "FECHA RECOLECCIÓN ": "fecha_recoleccion",
    "PROVENIENTE ": "proveniente",
    "DESCRIPCIÓN": "descripcion",
}

# Mapeos de valores para casos confirmados
CONDICION_FINAL_MAP = {
    "Fallecido": {
        "color": "#E51937",  # COLORS['danger']
        "icon": "⚰️",
        "categoria": "Crítico",
        "descripcion": "Paciente fallecido",
    },
    "Vivo": {
        "color": "#509E2F",  # COLORS['success']
        "icon": "💚",
        "categoria": "Bueno",
        "descripcion": "Paciente vivo",
    },
}

# Mapeos de valores para epizootias
DESCRIPCION_EPIZOOTIAS_MAP = {
    "POSITIVO FA": {
        "color": "#E51937",  # COLORS['danger']
        "icon": "🔴",
        "categoria": "Positivo",
        "descripcion": "Muestra positiva para fiebre amarilla",
    },
    "NEGATIVO FA": {
        "color": "#509E2F",  # COLORS['success']
        "icon": "🟢",
        "categoria": "Negativo",
        "descripcion": "Muestra negativa para fiebre amarilla",
    },
    "NO APTA": {
        "color": "#F7941D",  # COLORS['warning']
        "icon": "🟡",
        "categoria": "No apta",
        "descripcion": "Muestra no apta para análisis",
    },
    "EN ESTUDIO": {
        "color": "#4682B4",  # COLORS['info']
        "icon": "🔵",
        "categoria": "En estudio",
        "descripcion": "Muestra en proceso de análisis",
    },
}

# Mapeos de fuentes de epizootias
PROVENIENTE_MAP = {
    "VIGILANCIA COMUNITARIA (EPIZOOTIAS)": {
        "abreviacion": "Vigilancia Com.",
        "tipo": "Comunitaria",
        "descripcion": "Reporte de la comunidad",
    },
    "VIGILANCIA PROVENIENTE DE PROCESOS DE INCAUTACIÓN O RESCATE DE FAUNA SILVETRE": {
        "abreviacion": "Incautación",
        "tipo": "Institucional",
        "descripcion": "Incautación o rescate de fauna",
    },
}

# Mapeos de sexo
SEXO_MAP = {
    "M": "Masculino",
    "F": "Femenino",
    "Masculino": "Masculino",
    "Femenino": "Femenino",
}

# Grupos de edad predefinidos
GRUPOS_EDAD = [
    {"min": 0, "max": 4, "label": "0-4 años", "categoria": "Infantil"},
    {"min": 5, "max": 14, "label": "5-14 años", "categoria": "Escolar"},
    {"min": 15, "max": 19, "label": "15-19 años", "categoria": "Adolescente"},
    {"min": 20, "max": 29, "label": "20-29 años", "categoria": "Adulto Joven"},
    {"min": 30, "max": 39, "label": "30-39 años", "categoria": "Adulto"},
    {"min": 40, "max": 49, "label": "40-49 años", "categoria": "Adulto"},
    {"min": 50, "max": 59, "label": "50-59 años", "categoria": "Adulto Mayor"},
    {"min": 60, "max": 69, "label": "60-69 años", "categoria": "Adulto Mayor"},
    {"min": 70, "max": 79, "label": "70-79 años", "categoria": "Adulto Mayor"},
    {"min": 80, "max": 120, "label": "80+ años", "categoria": "Adulto Mayor"},
]

# Configuraciones de visualización (SIN MAPAS, SIN TIMELINE)
VISUALIZATION_CONFIG = {
    "max_items_chart": 15,  # Máximo de elementos en gráficos
    "default_chart_height": 400,
    "date_format": "%Y-%m-%d",
    "datetime_format": "%Y-%m-%d %H:%M",
}

# Configuración de métricas principales
METRICAS_CONFIG = {
    "casos_confirmados": {
        "titulo": "Casos Confirmados",
        "icon": "🦠",
        "color": "danger",
    },
    "epizootias": {"titulo": "Epizootias", "icon": "🐒", "color": "warning"},
    "veredas_afectadas": {"titulo": "Veredas Afectadas", "icon": "🏘️", "color": "info"},
    "letalidad": {
        "titulo": "Tasa de Letalidad",
        "icon": "⚰️",
        "color": "danger",
        "formato": "porcentaje",
    },
    "positividad": {
        "titulo": "Positividad Epizootias",
        "icon": "🔴",
        "color": "warning",
        "formato": "porcentaje",
    },
}

# Configuración de filtros (JERARQUÍA CLARA)
FILTROS_CONFIG = {
    "municipio": {
        "titulo": "📍 MUNICIPIO (Principal)",
        "help": "Seleccione un municipio para filtrar los datos",
        "default": "Todos",
        "jerarquia": 1,  # Prioridad máxima
    },
    "vereda": {
        "titulo": "🏘️ VEREDA (Secundario)",
        "help": "Primero seleccione un municipio para ver sus veredas",
        "default": "Todas",
        "jerarquia": 2,  # Prioridad alta
    },
    "tipo_datos": {
        "titulo": "📋 Mostrar",
        "opciones": ["Casos Confirmados", "Epizootias"],
        "default": ["Casos Confirmados", "Epizootias"],
        "jerarquia": 3,  # Prioridad media
    },
    "fecha_rango": {
        "titulo": "📅 Rango de Fechas",
        "help": "Seleccione el rango de fechas para analizar",
        "jerarquia": 3,  # Prioridad media
    },
}

# Configuración de pestañas (OPTIMIZADO)
TABS_CONFIG = {
    "mapas": {
        "titulo": "🗺️ Mapas",
        "descripcion": "Distribución geográfica (próximamente)",
    },
    "tablas": {
        "titulo": "📋 Tablas Detalladas",
        "descripcion": "Fichas informativas y datos detallados",
    },
    "comparativo": {
        "titulo": "📊 Análisis Comparativo",
        "descripcion": "Comparación básica entre casos y epizootias",
    },
}

# Configuración de logging
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
}

# Configuración de archivos de salida
OUTPUT_CONFIG = {
    "export_formats": ["CSV", "Excel"],  # Removido PDF por simplicidad
    "temp_folder": "temp",
    "reports_folder": "reports",
}

# Textos informativos
TEXTOS_INFO = {
    "bienvenida": """
    Dashboard informativo para el análisis de casos confirmados de fiebre amarilla 
    y epizootias registradas en el departamento del Tolima.
    """,
    "casos_confirmados": """
    Los casos confirmados corresponden a pacientes diagnosticados con fiebre amarilla 
    a través de pruebas de laboratorio, criterios clínicos o nexo epidemiológico.
    """,
    "epizootias": """
    Las epizootias son eventos de mortalidad en primates no humanos que pueden indicar 
    circulación del virus de fiebre amarilla en áreas silvestres.
    """,
    "interpretacion_letalidad": """
    La tasa de letalidad indica el porcentaje de casos confirmados que resultaron en fallecimiento.
    """,
    "interpretacion_positividad": """
    La positividad en epizootias indica el porcentaje de muestras que resultaron positivas 
    para fiebre amarilla, señalando circulación viral en fauna silvestre.
    """,
    "veredas_afectadas": """
    El número de veredas afectadas muestra la distribución geográfica de los eventos 
    de fiebre amarilla en el territorio.
    """,
}

# Configuración de colores por departamento
DEPARTAMENTOS_CONFIG = {
    "TOLIMA": {
        "color_principal": "#7D0F2B",
        "color_secundario": "#F2A900",
        "color_acento": "#5A4214",
    }
}

# Versión del dashboard
VERSION_INFO = {
    "version": "2.1.0",
    "descripcion": "Dashboard Informativo Optimizado",
    "fecha_release": "2025-01-02",
    "características": [
        "Diseño responsive",
        "Filtros jerárquicos",
        "Fichas informativas",
        "Análisis comparativo básico",
        "Exportación de datos",
        "Vista de mapas preparada",
    ],
}
