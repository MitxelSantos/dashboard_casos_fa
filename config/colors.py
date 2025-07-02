"""
Colores institucionales del Tolima y paleta de colores del dashboard.
OPTIMIZADO: Para profesionales médicos con colores claros y contrastantes.
"""

# Colores principales institucionales del Tolima
COLORS = {
    "primary": "#7D0F2B",  # Vinotinto institucional
    "secondary": "#F2A900",  # Amarillo/Dorado institucional
    "accent": "#5A4214",  # Marrón dorado oscuro
    "background": "#F5F5F5",  # Fondo gris claro
    "success": "#509E2F",  # Verde para estados positivos
    "warning": "#F7941D",  # Naranja para advertencias
    "danger": "#E51937",  # Rojo para peligros/fallecidos
    "info": "#4682B4",  # Azul para información
    "light": "#F9F6E9",  # Crema claro
    "dark": "#2C2C2C",  # Gris oscuro para texto
}

# Paletas de colores para gráficos médicos
COLOR_PALETTES = {
    "medical_categorical": [
        COLORS["primary"],
        COLORS["secondary"],
        COLORS["accent"],
        COLORS["success"],
        COLORS["warning"],
        COLORS["danger"],
        COLORS["info"],
    ],
    "clinical_severity": [
        COLORS["success"],    # Bajo riesgo
        COLORS["warning"],    # Riesgo moderado
        COLORS["danger"]      # Alto riesgo
    ],
    "epidemiological": [
        COLORS["info"],       # Vigilancia
        COLORS["warning"],    # Alerta
        COLORS["danger"]      # Emergencia
    ],
    "sequential_cases": ["#FFFFFF", COLORS["danger"]],
    "sequential_surveillance": ["#FFFFFF", COLORS["warning"]],
}

# Configuración de estilos CSS médicos
CSS_STYLES = {
    "medical_card": {
        "background_color": "white",
        "border_radius": "12px",
        "box_shadow": "0 4px 15px rgba(0,0,0,0.1)",
        "padding": "20px",
        "min_height": "180px",
        "border_top": f"4px solid {COLORS['primary']}",
        "hover_transform": "translateY(-3px)",
    },
    "alert_banner": {
        "background_color": COLORS["light"],
        "border_left_color": COLORS["primary"],
        "border_radius": "10px",
        "padding": "20px",
    },
    "clinical_metric": {
        "font_size": "2.2rem",
        "font_weight": "800",
        "color": COLORS["primary"]
    }
}

# Mapeo de colores para condiciones médicas
MEDICAL_COLOR_MAP = {
    "critical": COLORS["danger"],
    "high": COLORS["warning"], 
    "moderate": COLORS["info"],
    "low": COLORS["success"],
    "unknown": COLORS["dark"]
}

# Colores específicos para fiebre amarilla
YELLOW_FEVER_COLORS = {
    "confirmed_case": COLORS["danger"],
    "suspected_case": COLORS["warning"],
    "negative_case": COLORS["success"],
    "deceased": COLORS["dark"],
    "recovered": COLORS["success"],
    "positive_epizootic": COLORS["danger"],
    "negative_epizootic": COLORS["success"],
    "unsuitable_sample": COLORS["warning"],
    "under_study": COLORS["info"]
}
