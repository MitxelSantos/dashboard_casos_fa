"""
Componente de barra lateral del dashboard - Minimalista.
"""

import streamlit as st
from pathlib import Path
from datetime import datetime

# Importación opcional de Google Drive
try:
    from gdrive_utils import get_file_from_drive, check_google_drive_availability

    GDRIVE_AVAILABLE = True
except ImportError:
    GDRIVE_AVAILABLE = False

# Definir rutas
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
ASSETS_DIR = ROOT_DIR / "assets"
IMAGES_DIR = ASSETS_DIR / "images"


def create_sidebar():
    """
    Crea la barra lateral del dashboard minimalista.
    """
    with st.sidebar:
        # Logo de la Gobernación
        display_logo()

        # Separador minimalista
        st.markdown("---")


def display_logo():
    """
    Muestra el logo de manera responsive con búsqueda corregida.
    """
    logo_displayed = False

    # Lista de rutas posibles para el logo
    possible_logo_paths = [
        ROOT_DIR / "Gobernacion.png",
        ROOT_DIR / "gobernacion.png",
        ROOT_DIR / "logo.png",
        DATA_DIR / "Gobernacion.png",
        DATA_DIR / "gobernacion.png",
        DATA_DIR / "logo.png",
        IMAGES_DIR / "Gobernacion.png",
        IMAGES_DIR / "logo_gobernacion.png",
        IMAGES_DIR / "gobernacion.png",
    ]

    # Buscar logo en las rutas definidas
    for logo_path in possible_logo_paths:
        if logo_path.exists():
            display_logo_image(str(logo_path))
            logo_displayed = True
            break

    # Intentar cargar logo desde Google Drive si está disponible
    if not logo_displayed and GDRIVE_AVAILABLE and check_google_drive_availability():
        try:
            if (
                hasattr(st.secrets, "drive_files")
                and "logo_gobernacion" in st.secrets.drive_files
            ):
                logo_id = st.secrets.drive_files["logo_gobernacion"]
                logo_path = get_file_from_drive(logo_id, "Gobernacion.png")
                if logo_path and Path(logo_path).exists():
                    display_logo_image(logo_path)
                    logo_displayed = True
        except Exception:
            pass

    # Si no se encuentra ningún logo, mostrar placeholder
    if not logo_displayed:
        create_logo_placeholder()


def display_logo_image(logo_path):
    """
    Muestra una imagen de logo de manera responsive.
    """
    try:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(
                logo_path,
                caption=None,
                use_container_width=True,
            )
    except Exception:
        create_logo_placeholder()


def create_logo_placeholder():
    """
    Crea un placeholder visual responsive cuando no se encuentra el logo.
    """
    st.markdown(
        """
        <div style="
            width: 100%; 
            max-width: 200px;
            height: 100px; 
            background: linear-gradient(135deg, #7D0F2B, #F2A900); 
            border-radius: 12px; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            color: white; 
            font-weight: bold; 
            font-size: clamp(0.7rem, 2vw, 0.9rem);
            text-align: center;
            margin: 0 auto 1.5rem auto;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        ">
            GOBERNACIÓN<br>DEL TOLIMA
        </div>
        """,
        unsafe_allow_html=True,
    )

def add_copyright():
    """
    Agrega copyright minimalista al final de la sidebar.
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        <div style="
            text-align: center; 
            color: #666; 
            font-size: 0.7rem;
            padding: 0.5rem 0;
        ">
            <div style="margin-bottom: 4px;">
                Desarrollado por: Ing. Jose Miguel Santos
            </div>
            <div style="opacity: 0.8;">
                © 2025 Secretaria de salud del Tolima
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def add_responsive_css():
    """
    Agrega CSS minimalista para el sidebar.
    """
    st.markdown(
        """
        <style>
        .css-1d391kg {
            min-width: 280px;
            background-color: #fafafa;
        }
        
        .sidebar .stMarkdown {
            font-size: clamp(0.8rem, 2vw, 0.9rem);
            line-height: 1.4;
        }
        
        .sidebar .stButton > button {
            width: 100%;
            font-size: clamp(0.8rem, 2vw, 0.9rem);
            background-color: #7D0F2B;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 0.5rem 1rem;
            font-weight: 600;
        }
        
        .sidebar .stButton > button:hover {
            background-color: #5A4214;
            transition: all 0.3s ease;
        }
        
        @media (max-width: 768px) {
            .css-1d391kg {
                min-width: 250px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# Función principal para inicializar sidebar minimalista
def init_responsive_sidebar():
    """
    Inicializa la barra lateral minimalista.
    """
    add_responsive_css()
    create_sidebar()
    add_copyright()
