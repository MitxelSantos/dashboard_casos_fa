"""
Componente de barra lateral del dashboard.
"""
import streamlit as st
from pathlib import Path
from config.settings import IMAGES_DIR
from gdrive_utils import get_file_from_drive

def create_sidebar():
    """
    Crea la barra lateral del dashboard con logo y información.
    
    Returns:
        None
    """
    with st.sidebar:
        # Logo de la Gobernación
        display_logo()
        
        # Título y subtítulo
        st.title("Dashboard Fiebre Amarilla")
        st.subheader("Vigilancia Epidemiológica")
        
        # Información adicional
        st.sidebar.markdown("---")
        st.sidebar.caption("Desarrollado para la Secretaría de Salud del Tolima")
        from datetime import datetime
        st.sidebar.caption(f"© {datetime.now().year}")


def display_logo():
    """
    Muestra el logo de la Secretaría de Salud.
    
    Returns:
        None
    """
    # Intentar cargar logo desde Google Drive
    if hasattr(st.secrets, "drive_files") and "logo_gobernacion" in st.secrets.drive_files:
        logo_id = st.secrets.drive_files["logo_gobernacion"]
        logo_path = get_file_from_drive(logo_id, "logo_gobernacion.png")
        if logo_path and Path(logo_path).exists():
            st.image(
                logo_path, 
                width=150, 
                caption="Secretaría de Salud del Tolima"
            )
            return
    
    # Buscar logo local como respaldo
    logo_path = IMAGES_DIR / "logo_gobernacion.png"
    if logo_path.exists():
        st.image(
            str(logo_path), 
            width=150, 
            caption="Secretaría de Salud del Tolima"
        )
    else:
        # Mostrar mensaje informativo si no se encuentra el logo
        st.info("Logo no encontrado. Coloque el logo en assets/images/logo_gobernacion.png")


def create_info_section(title, content, icon="ℹ️"):
    """
    Crea una sección informativa en la barra lateral.
    
    Args:
        title (str): Título de la sección
        content (str): Contenido de la sección
        icon (str): Icono a mostrar
        
    Returns:
        None
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"### {icon} {title}")
    st.sidebar.markdown(content)


def create_download_section():
    """
    Crea una sección de descarga de datos en la barra lateral.
    
    Returns:
        None
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📥 Descargar Datos")
    
    # Botón para descargar datos filtrados
    if st.sidebar.button("Descargar Datos Filtrados"):
        st.sidebar.info("Funcionalidad en desarrollo")
    
    # Botón para descargar reporte
    if st.sidebar.button("Generar Reporte PDF"):
        st.sidebar.info("Funcionalidad en desarrollo")


def show_filter_summary(active_filters):
    """
    Muestra un resumen de los filtros activos en la barra lateral.
    
    Args:
        active_filters (dict): Diccionario con filtros activos
        
    Returns:
        None
    """
    active_count = sum(1 for v in active_filters.values() if v != "Todos")
    
    if active_count > 0:
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"### 🔍 Filtros Activos ({active_count})")
        
        for key, value in active_filters.items():
            if value != "Todos":
                st.sidebar.markdown(f"**{key.capitalize()}:** {value}")
    else:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🔍 Sin Filtros Aplicados")
        st.sidebar.caption("Mostrando todos los datos disponibles")