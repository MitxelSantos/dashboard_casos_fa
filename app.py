"""
app.py
"""

import os
import time
import logging
from datetime import datetime
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

from data_loader import (
    check_data_availability,
    load_main_data,
    show_data_setup_instructions
)

from utils.data_processor import (
    excel_date_to_datetime,
    process_complete_data_structure_authoritative,
    process_veredas_dataframe_simple,
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("FiebreAmarilla-Dashboard")

# Configuraciones
os.environ["STREAMLIT_PAGES_ENABLED"] = "false"

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
ASSETS_DIR = ROOT_DIR / "assets"

# Crear directorios
DATA_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)

# Importar configuraciones
try:
    from config.colors import COLORS
    from config.settings import DASHBOARD_CONFIG
    from utils.data_processor import (
        excel_date_to_datetime,
        process_complete_data_structure_authoritative,
    )
    from components.filters import create_unified_filter_system

    logger.info("✅ Configuraciones importadas")
except ImportError as e:
    logger.error(f"❌ Error importando configuraciones: {str(e)}")
    st.error(f"Error en configuraciones: {str(e)}")
    st.stop()

# Importar vistas
vista_modules = ["mapas", "tablas", "comparativo"]
vistas_modules = {}

def import_vista_safely(module_name):
    """Importa una vista de manera segura."""
    try:
        module = __import__(f"vistas.{module_name}", fromlist=[module_name])
        if hasattr(module, "show"):
            logger.info(f"✅ Vista {module_name} importada")
            return module
        else:
            logger.error(f"❌ Vista {module_name} no tiene función 'show'")
            return None
    except ImportError as e:
        logger.error(f"❌ Error importando vista {module_name}: {str(e)}")
        return None

# Importar todas las vistas
for module_name in vista_modules:
    vistas_modules[module_name] = import_vista_safely(module_name)

def configure_page():
    """Configura la página principal."""
    st.set_page_config(
        page_title=DASHBOARD_CONFIG["page_title"],
        page_icon=DASHBOARD_CONFIG["page_icon"],
        layout=DASHBOARD_CONFIG["layout"],
        initial_sidebar_state=DASHBOARD_CONFIG["initial_sidebar_state"],
    )
    
    st.markdown(get_critical_css(), unsafe_allow_html=True)

    # CSS básico - el resto se maneja en archivos separados
    st.markdown(
        f"""
        <style>
        :root {{
            --primary-color: {COLORS['primary']};
            --secondary-color: {COLORS['secondary']};
            --success-color: {COLORS['success']};
            --warning-color: {COLORS['warning']};
            --danger-color: {COLORS['danger']};
            --info-color: {COLORS['info']};
        }}
        
        .main-title {{
            color: var(--primary-color);
            font-size: clamp(1.6rem, 5vw, 2.2rem);
            font-weight: 700;
            margin-bottom: 0.75rem;
            text-align: center;
            padding: 0.75rem 1rem;
            border-bottom: 3px solid var(--secondary-color);
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        }}
        
        /* Layout sin scroll para dashboard compacto */
        .main .block-container {{
            max-height: calc(100vh - 120px) !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
            padding: 1rem !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def get_critical_css():
    """CSS crítico que se aplica antes del primer render."""
    return """
    <style>
    /* PREVENIR SCROLL INFINITO DESDE EL INICIO */
    .main .block-container {
        max-height: calc(100vh - 80px) !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        padding: 1rem !important;
    }
    
    /* ALTURA FIJA PARA MAPAS DESDE EL INICIO */
    iframe[title="st_folium.st_folium"] {
        height: 450px !important;
        max-height: 450px !important;
        min-height: 350px !important;
    }
    
    /* PREVENIR ESPACIOS EN MÓVIL DESDE EL INICIO */
    @media (max-width: 768px) {
        .stColumns { gap: 0.5rem !important; }
        .stColumns > div { margin-bottom: 0.5rem !important; }
        iframe[title="st_folium.st_folium"] { height: 350px !important; }
    }
    </style>
    """

def load_data():
    """Función simplificada de carga de datos."""
    try:
        logger.info("🔄 Iniciando carga de datos consolidada")
        
        # Cargar datos desde Google Drive
        data = load_main_data()
        
        if data and not data["casos"].empty:
            logger.info(f"✅ Datos cargados: {len(data['casos'])} casos, {len(data['epizootias'])} epizootias")
            return data
        else:
            logger.error("❌ No se pudieron cargar los datos")
            show_data_setup_instructions()  # Mostrar instrucciones si falla
            return create_empty_structure()
            
    except Exception as e:
        logger.error(f"💥 Error crítico: {str(e)}")
        st.error(f"❌ Error crítico: {str(e)}")
        show_data_setup_instructions()  # Mostrar instrucciones si falla
        return create_empty_structure()

def create_empty_structure():
    """Helper para estructura vacía."""
    from data_loader import get_data_loader
    return get_data_loader().get_empty_data_structure()    

def handle_gray_area_click(municipio=None, vereda=None, data_original=None):
    """Maneja clics en áreas grises."""
    logger.info(f"🎯 Manejando clic en área gris: {municipio}, {vereda}")

    if data_original and "handle_empty_area" in data_original:
        return data_original["handle_empty_area"](
            municipio=municipio,
            vereda=vereda,
            casos_df=data_original.get("casos", pd.DataFrame()),
            epizootias_df=data_original.get("epizootias", pd.DataFrame()),
        )
    else:
        return {
            "casos": pd.DataFrame(),
            "epizootias": pd.DataFrame(),
            "tiene_datos": False,
            "area_info": {
                "municipio": municipio,
                "vereda": vereda,
                "tipo": "sin_datos",
            },
        }
        
def create_footer(filters, colors):
    """Footer."""
    # Separador visual claro
    st.markdown(
        """
        <div style="
            margin-top: 3rem; 
            padding-top: 1rem; 
            border-top: 2px solid #e2e8f0;
            clear: both;
            position: relative;
            z-index: 1000;
        ">
        """, 
        unsafe_allow_html=True
    )
    
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown(
            f"""
            <div style="
                text-align: center; 
                color: #666; 
                font-size: 0.75rem; 
                padding: 0.5rem 0;
                line-height: 1.4;
            ">
                <div style="margin-bottom: 4px; font-weight: 600;">
                    Dashboard Fiebre Amarilla v1.0
                </div>
                <div style="opacity: 0.9;">
                    Desarrollado por: Ing. Jose Miguel Santos • Secretaría de Salud del Tolima • © 2025
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        active_filters = filters.get("active_filters", [])
        modo_mapa = filters.get("modo_mapa", "Epidemiológico")

        if active_filters or modo_mapa != "Epidemiológico":
            badge_info = []
            if active_filters:
                badge_info.append(f"{len(active_filters)} filtros")
            if modo_mapa != "Epidemiológico":
                badge_info.append(modo_mapa[:8])

            badge_text = " • ".join(badge_info)

            st.markdown(
                f"""
                <div style="
                    background: {colors['info']}; 
                    color: white; 
                    padding: 0.4rem; 
                    border-radius: 6px; 
                    text-align: center; 
                    font-size: 0.7rem;
                    font-weight: 600;
                ">
                    🎯 {badge_text}
                </div>
                """,
                unsafe_allow_html=True,
            )
    
    # Cerrar el contenedor del footer
    st.markdown("</div>", unsafe_allow_html=True)

def main():
    """Función principal del dashboard."""
    # 1. CONFIGURAR PÁGINA PRIMERO
    configure_page()

    # 2. Sidebar
    try:
        from components.sidebar import create_sidebar
        create_sidebar()
    except ImportError:
        with st.sidebar:
            st.title("Dashboard Tolima")

    # 3. Cargar datos
    logger.info("🔄 Iniciando carga de datos")
    data = load_data()

    if data["casos"].empty and data["epizootias"].empty:
        st.error("❌ No se pudieron cargar los datos")
        return

    logger.info(
        f"📊 Datos cargados: {len(data['casos'])} casos, {len(data['epizootias'])} epizootias"
    )
    logger.info(f"🗂️ Regiones existentes: {len(data.get('regiones', {}))}")

    # 4. Aplicar filtros
    logger.info("🔄 Aplicando sistema de filtros")
    filter_result = create_unified_filter_system(data)
    filters = filter_result["filters"]
    data_filtered = filter_result["data_filtered"]

    # 5. Verificar si es un área sin datos
    municipio_filtrado = filters.get("municipio_display")
    vereda_filtrada = filters.get("vereda_display")

    # Si es área sin datos, manejar apropiadamente
    if (
        data_filtered["casos"].empty
        and data_filtered["epizootias"].empty
        and (municipio_filtrado != "Todos" or vereda_filtrada != "Todas")
    ):
        logger.info("🎯 Detectada área sin datos")
        data_filtered_with_zeros = handle_gray_area_click(
            municipio=municipio_filtrado if municipio_filtrado != "Todos" else None,
            vereda=vereda_filtrada if vereda_filtrada != "Todas" else None,
            data_original=data,
        )

        # Integrar información del área sin datos
        data_filtered.update(data_filtered_with_zeros)

    # 6. Verificar filtrado
    casos_reduction = len(data["casos"]) - len(data_filtered["casos"])
    epi_reduction = len(data["epizootias"]) - len(data_filtered["epizootias"])

    if casos_reduction > 0 or epi_reduction > 0:
        logger.info(
            f"📊 Filtrado aplicado: -{casos_reduction} casos, -{epi_reduction} epizootias"
        )

    # 8. PESTAÑAS PRINCIPALES
    tab1, tab2, tab3 = st.tabs(
        [
            "🗺️ Mapa Interactivo",
            "📊 Información Detallada",
            "📈 Análisis Visual",
        ]
    )

    with tab1:
        logger.info("🗺️ Mostrando vista de mapas interactivos")
        if "mapas" in vistas_modules and vistas_modules["mapas"]:
            try:
                vistas_modules["mapas"].show(data_filtered, filters, COLORS)
            except Exception as e:
                logger.error(f"❌ Error en vista de mapas: {str(e)}")
                st.error(f"Error en módulo de mapas: {str(e)}")
        else:
            st.warning("⚠️ Vista de mapas no disponible")

    with tab2:
        logger.info("📊 Mostrando información detallada")
        if "tablas" in vistas_modules and vistas_modules["tablas"]:
            try:
                vistas_modules["tablas"].show(data_filtered, filters, COLORS)
            except Exception as e:
                logger.error(f"❌ Error en análisis: {str(e)}")
                st.error(f"Error en módulo de análisis: {str(e)}")
        else:
            st.info("🔧 Módulo de análisis en desarrollo.")

    with tab3:
        logger.info("📈 Mostrando análisis visual")
        if "comparativo" in vistas_modules and vistas_modules["comparativo"]:
            try:
                vistas_modules["comparativo"].show(data_filtered, filters, COLORS)
            except Exception as e:
                logger.error(f"❌ Error en seguimiento temporal: {str(e)}")
                st.error(f"Error en módulo temporal: {str(e)}")
        else:
            st.info("🔧 Módulo temporal en desarrollo.")

    # 9. FOOTER
    create_footer(filters, COLORS)

if __name__ == "__main__":
    main()