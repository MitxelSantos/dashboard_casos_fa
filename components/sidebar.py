"""
Componente de barra lateral.
"""

import streamlit as st
from pathlib import Path

# Definir rutas
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
ASSETS_DIR = ROOT_DIR / "assets"
IMAGES_DIR = ASSETS_DIR / "images"

def create_sidebar():
    """Crea la barra lateral completa."""
    with st.sidebar:
        display_logo()
        st.markdown("---")

def display_logo():
    """Muestra logo con fallback automático."""
    # Rutas posibles para el logo
    logo_paths = [
        DATA_DIR / "Gobernacion.png",
        DATA_DIR / "gobernacion.png", 
        DATA_DIR / "logo.png",
        IMAGES_DIR / "Gobernacion.png",
    ]
    
    # Buscar logo local
    for logo_path in logo_paths:
        if logo_path.exists():
            try:
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.image(logo_path, use_container_width=True)
                return
            except Exception:
                continue
    
    # Intentar Google Drive si está disponible
    if try_google_drive_logo():
        return
    
    # Fallback: placeholder
    create_logo_placeholder()

def try_google_drive_logo():
    """Intenta cargar logo desde Google Drive."""
    try:
        from gdrive_utils import check_google_drive_availability, get_file_from_drive
        
        if (check_google_drive_availability() and 
            hasattr(st.secrets, "drive_files") and 
            "logo_gobernacion" in st.secrets.drive_files):
            
            logo_id = st.secrets.drive_files["logo_gobernacion"]
            logo_path = get_file_from_drive(logo_id, "Gobernacion.png")
            
            if logo_path and Path(logo_path).exists():
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.image(logo_path, use_container_width=True)
                return True
    except Exception:
        pass
    
    return False

def create_logo_placeholder():
    """Crea placeholder visual cuando no hay logo."""
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
    """Agrega copyright al final del sidebar."""
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

def init_responsive_sidebar():
    """Inicializa sidebar con CSS responsive."""
    # CSS minimalista para sidebar
    st.markdown(
        """
        <style>
        .css-1d391kg {
            min-width: 280px;
            background-color: #fafafa;
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
    
    # Crear sidebar
    create_sidebar()