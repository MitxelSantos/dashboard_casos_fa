"""
Colores institucionales del Tolima y paleta de colores del dashboard.
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

# Paletas de colores para gráficos
COLOR_PALETTES = {
    "categorical": [
        COLORS["primary"],
        COLORS["secondary"],
        COLORS["accent"],
        COLORS["success"],
        COLORS["warning"],
        COLORS["danger"],
        COLORS["info"],
    ],
    "sequential_primary": ["#FFFFFF", COLORS["primary"]],
    "sequential_secondary": ["#FFFFFF", COLORS["secondary"]],
    "diverging": [COLORS["success"], "#FFFFFF", COLORS["danger"]],
}

# Configuración de estilos CSS
CSS_STYLES = {
    "metric_box": {
        "background_color": "white",
        "border_radius": "8px",
        "box_shadow": "0 3px 10px rgba(0,0,0,0.1)",
        "padding": "15px",
        "width": "200px",
        "height": "130px",
        "hover_transform": "translateY(-5px)",
    },
    "info_banner": {
        "background_color": COLORS["light"],
        "border_left_color": COLORS["primary"],
        "border_radius": "10px",
        "padding": "20px",
    },
}
