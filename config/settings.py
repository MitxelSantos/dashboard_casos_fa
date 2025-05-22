"""
Configuraciones globales del dashboard de Fiebre Amarilla.
"""

from pathlib import Path

# Configuración de rutas
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
ASSETS_DIR = ROOT_DIR / "assets"
IMAGES_DIR = ASSETS_DIR / "images"

# Configuración de IDs de archivos en Google Drive
DRIVE_FILE_IDS = {
    "fiebre_amarilla": "YOUR_GOOGLE_DRIVE_FILE_ID",
    "logo_gobernacion": "YOUR_LOGO_FILE_ID",
}

# Configuración de la aplicación
DASHBOARD_CONFIG = {
    "page_title": "Dashboard Fiebre Amarilla - Tolima",
    "page_icon": "🦟",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
    "max_municipios_dropdown": 50,  # Límite para evitar dropdowns muy largos
}

# Mapeos de códigos utilizados en el dashboard
FILTER_MAPPINGS = {
    "tipo_caso": {
        1: "Sospechoso",
        2: "Probable",
        3: "Confirmado por Laboratorio",
        4: "Confirmado por Clínica",
        5: "Confirmado por Nexo Epidemiológico",
    },
    "seguridad_social": {
        "C": "Contributivo",
        "S": "Subsidiado",
        "P": "Excepción",
        "E": "Especial",
        "N": "No asegurado",
        "I": "Indeterminado/Pendiente",
    },
    "condicion_final": {1: "Vivo", 2: "Fallecido"},
    "pertenencia_etnica": {
        1: "Indígena",
        2: "Gitano",
        3: "Raizal",
        4: "Palenqueros",
        5: "Afrocolombiano",
        6: "Otro",
    },
    "tipo_zona": {1: "Cabecera Municipal", 2: "Centro Poblado", 3: "Rural Disperso"},
}

# Tipos de casos confirmados
CASOS_CONFIRMADOS = [3, 4, 5]

# Columnas de fechas importantes
COLUMNAS_FECHAS = {
    "fecha_consulta": "fec_con_",
    "fecha_inicio_sintomas": "ini_sin_",
    "fecha_hospitalizacion": "fec_hos_",
    "fecha_fallecimiento": "fec_def_",
    "fecha_vacunacion": "fec_fa1",
}

# Grupos de edad predefinidos
GRUPOS_EDAD = [
    "0-4 años",
    "5-14 años",
    "15-19 años",
    "20-29 años",
    "30-39 años",
    "40-49 años",
    "50-59 años",
    "60-69 años",
    "70-79 años",
    "80+ años",
    "No especificado",
]

# Configuración de logging
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
}
