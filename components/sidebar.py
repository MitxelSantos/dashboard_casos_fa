"""
components/sidebar.py - CORRECCIÓN PARA LOGO
"""

import streamlit as st
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def create_sidebar():
    """Crea la barra lateral."""
    with st.sidebar:
        display_logo()
        st.markdown("---")

def display_logo():
    """Muestra logo con fallback CORREGIDO."""
    # ✅ CORRECCIÓN: Usar ConsolidatedDataLoader en lugar de autenticación separada
    if load_logo_with_consolidated_loader():
        return
    
    # 2. Buscar logo local como backup
    logo_paths = [
        Path("data") / "Gobernacion.png",
        Path("data") / "gobernacion.png", 
        Path("data") / "logo.png",
    ]
    
    for logo_path in logo_paths:
        if logo_path.exists():
            try:
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.image(logo_path, use_container_width=True)
                logger.info(f"✅ Logo cargado desde archivo local: {logo_path}")
                return
            except Exception as e:
                logger.warning(f"⚠️ Error cargando logo local {logo_path}: {str(e)}")
                continue
    
    # 3. Fallback: placeholder
    logger.warning("⚠️ Logo no encontrado, usando placeholder")
    create_logo_placeholder()

def load_logo_with_consolidated_loader():
    """
    ✅ NUEVA FUNCIÓN: Usa ConsolidatedDataLoader que ya funciona
    """
    try:
        logger.info("🖼️ Cargando logo con ConsolidatedDataLoader...")
        
        # 1. Verificar que el sistema esté disponible
        from data_loader import get_data_loader, check_data_availability
        
        if not check_data_availability():
            logger.warning("❌ ConsolidatedDataLoader no disponible")
            return False
        
        # 2. Usar el loader que ya está autenticado
        loader = get_data_loader()
        logo_path = loader.load_logo_image()  # ← Usa método del loader
        
        # 3. Mostrar imagen si se descargó
        if logo_path and Path(logo_path).exists():
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(logo_path, use_container_width=True)
            logger.info("✅ Logo cargado exitosamente con ConsolidatedDataLoader")
            return True
        else:
            logger.warning("❌ ConsolidatedDataLoader no pudo descargar logo")
            return False
            
    except ImportError as e:
        logger.warning(f"⚠️ ConsolidatedDataLoader no disponible: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ Error cargando logo con ConsolidatedDataLoader: {str(e)}")
        return False

# ✅ ELIMINAR load_logo_direct_pattern() - ya no se necesita

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