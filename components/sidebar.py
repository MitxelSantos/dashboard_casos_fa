"""
Componente de barra lateral del dashboard - Simplificado para profesionales médicos.
CORREGIDO: Sin información técnica innecesaria.
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
    Crea la barra lateral del dashboard simplificada para médicos.
    """
    with st.sidebar:
        # Logo de la Gobernación
        display_logo()

        # Información médica relevante
        st.markdown("---")
        
        # Información de contacto médico
        st.markdown("""
        <div style="
            background-color: #f8f9fa; 
            padding: 15px; 
            border-radius: 8px; 
            border-left: 4px solid #7D0F2B;
            margin-bottom: 15px;
        ">
            <h4 style="color: #7D0F2B; margin: 0 0 10px 0; font-size: 1rem;">
                🏥 Información de Contacto
            </h4>
            <p style="margin: 5px 0; font-size: 0.85rem; color: #2c2c2c;">
                <strong>Secretaría de Salud del Tolima</strong><br>
                Vigilancia Epidemiológica
            </p>
            <p style="margin: 5px 0; font-size: 0.8rem; color: #666;">
                Para reportes urgentes de casos<br>
                sospechosos de fiebre amarilla.
            </p>
        </div>
        """, unsafe_allow_html=True)


def display_logo():
    """
    Muestra el logo de manera responsive con búsqueda corregida.
    CORREGIDO: Búsqueda mejorada del logo.
    """
    logo_displayed = False

    # Lista de rutas posibles para el logo (CORREGIDA)
    possible_logo_paths = [
        # Carpeta data (prioridad principal)
        DATA_DIR / "Gobernacion.png",
        DATA_DIR / "gobernacion.png",
        DATA_DIR / "logo.png",
        
        # Directorio raíz (segunda opción)
        ROOT_DIR / "Gobernacion.png",
        ROOT_DIR / "gobernacion.png", 
        ROOT_DIR / "logo.png",
        
        # Assets/images (tercera opción)
        IMAGES_DIR / "Gobernacion.png",
        IMAGES_DIR / "logo_gobernacion.png",
        IMAGES_DIR / "gobernacion.png",
    ]

    # Buscar logo en las rutas definidas
    for logo_path in possible_logo_paths:
        if logo_path.exists():
            display_logo_image(str(logo_path), f"Logo encontrado: {logo_path.parent.name}/")
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
                    display_logo_image(logo_path, "Logo desde Google Drive")
                    logo_displayed = True
        except Exception:
            pass  # Silenciar errores de Google Drive

    # Si no se encuentra ningún logo, mostrar placeholder
    if not logo_displayed:
        create_logo_placeholder()


def display_logo_image(logo_path, caption_text):
    """
    Muestra una imagen de logo de manera responsive.
    """
    try:
        # CSS para hacer la imagen responsive
        st.markdown(
            """
            <style>
            .logo-container {
                display: flex;
                justify-content: center;
                margin-bottom: 1.5rem;
            }
            .logo-container img {
                max-width: 100%;
                height: auto;
                max-height: 120px;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # Mostrar imagen con contenedor responsive
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(
                logo_path, 
                caption=None,  # Sin caption visible para médicos
                use_container_width=True
            )

    except Exception:
        # Si hay error mostrando la imagen, usar placeholder
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


def show_medical_help():
    """
    Muestra ayuda específica para profesionales médicos.
    """
    with st.sidebar.expander("❓ Guía Médica"):
        st.markdown(
            """
            **🩺 Para Profesionales de la Salud:**
            
            **📋 Información Principal:**
            - Fichas con situación epidemiológica actual
            - Alertas médicas prioritarias
            - Indicadores clínicos relevantes
            
            **📊 Análisis Comparativo:**
            - Correlación casos humanos vs fauna
            - Patrones geográficos de transmisión
            - Evolución temporal de la enfermedad
            
            **🔍 Filtros:**
            - Use filtros para análisis específicos por área
            - Los datos se actualizan automáticamente
            - Exporte reportes para referencias médicas
            
            **⚠️ Casos Sospechosos:**
            Reporte inmediatamente casos sospechosos
            a la Secretaría de Salud del Tolima.
            """,
        )


def show_data_update_info():
    """
    Muestra información médicamente relevante sobre actualización de datos.
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔄 Última Actualización")

    # Verificar fechas de modificación de archivos principales
    files_to_check = [
        (DATA_DIR / "BD_positivos.xlsx", "Casos"),
        (ROOT_DIR / "BD_positivos.xlsx", "Casos"),
        (DATA_DIR / "Información_Datos_FA.xlsx", "Epizootias"),
        (ROOT_DIR / "Información_Datos_FA.xlsx", "Epizootias"),
    ]

    latest_update = None
    for file_path, file_type in files_to_check:
        if file_path.exists():
            import os
            modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            if latest_update is None or modified_time > latest_update:
                latest_update = modified_time
            break

    if latest_update:
        st.sidebar.caption(f"📅 {latest_update.strftime('%d/%m/%Y %H:%M')}")
    else:
        st.sidebar.caption("📅 Fecha no disponible")

    # Botón de recarga simplificado
    if st.sidebar.button("🔄 Actualizar", help="Recargar datos más recientes"):
        st.cache_data.clear()
        st.rerun()


def add_responsive_css():
    """
    Agrega CSS para mejorar la responsividad del sidebar médico.
    """
    st.markdown(
        """
        <style>
        /* Sidebar médico responsive */
        .css-1d391kg {
            min-width: 280px;
            background-color: #fafafa;
        }
        
        /* Texto responsive en sidebar */
        .sidebar .stMarkdown {
            font-size: clamp(0.8rem, 2vw, 0.9rem);
            line-height: 1.4;
        }
        
        /* Botones médicos responsive */
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
        
        /* Expandir médico */
        .sidebar .streamlit-expanderHeader {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            font-weight: 600;
        }
        
        /* Mobile adjustments para médicos */
        @media (max-width: 768px) {
            .css-1d391kg {
                min-width: 250px;
            }
            
            .sidebar .stMarkdown h4 {
                font-size: 1rem !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# Función principal para inicializar sidebar médico
def init_responsive_sidebar():
    """
    Inicializa la barra lateral simplificada para profesionales médicos.
    """
    add_responsive_css()
    create_sidebar()
    show_data_update_info()
    show_medical_help()
