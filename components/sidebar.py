"""
Componente de barra lateral del dashboard - Responsive y optimizado.
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
    Crea la barra lateral del dashboard con logo y información.
    Optimizado para diferentes tamaños de pantalla.
    
    Returns:
        None
    """
    with st.sidebar:
        # Logo de la Gobernación
        display_logo()
        
        # Título y subtítulo con tamaño responsive
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 2rem;">
                <h1 style="font-size: clamp(1.5rem, 4vw, 2rem); color: #7D0F2B; margin-bottom: 0.5rem;">
                    🦟 Fiebre Amarilla
                </h1>
                <h3 style="font-size: clamp(1rem, 3vw, 1.2rem); color: #5A4214; margin-bottom: 0;">
                    Vigilancia Epidemiológica
                </h3>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Información adicional
        st.markdown("---")
        
        # Información responsive
        st.markdown(
            """
            <div style="text-align: center; font-size: 0.85rem; color: #666;">
                <p style="margin-bottom: 0.5rem;">
                    <strong>Secretaría de Salud del Tolima</strong>
                </p>
                <p style="margin-bottom: 0;">
                    © 2025
                </p>
            </div>
            """, 
            unsafe_allow_html=True
        )

def display_logo():
    """
    Muestra el logo de la Secretaría de Salud de manera responsive.
    Busca primero en la carpeta data, luego en assets/images, y finalmente en Google Drive.
    
    Returns:
        None
    """
    logo_displayed = False
    
    # Buscar logo en carpeta data (prioridad principal)
    data_logo_path = DATA_DIR / "Gobernacion.png"
    if data_logo_path.exists():
        display_logo_image(str(data_logo_path), "Logo encontrado en carpeta data")
        logo_displayed = True
    
    # Buscar logo en assets/images como respaldo
    if not logo_displayed:
        assets_logo_paths = [
            IMAGES_DIR / "Gobernacion.png",
            IMAGES_DIR / "logo_gobernacion.png",
            IMAGES_DIR / "gobernacion.png"
        ]
        
        for logo_path in assets_logo_paths:
            if logo_path.exists():
                display_logo_image(str(logo_path), "Logo encontrado en assets")
                logo_displayed = True
                break
    
    # Intentar cargar logo desde Google Drive si está disponible
    if not logo_displayed and GDRIVE_AVAILABLE and check_google_drive_availability():
        try:
            if hasattr(st.secrets, "drive_files") and "logo_gobernacion" in st.secrets.drive_files:
                logo_id = st.secrets.drive_files["logo_gobernacion"]
                logo_path = get_file_from_drive(logo_id, "Gobernacion.png")
                if logo_path and Path(logo_path).exists():
                    display_logo_image(logo_path, "Logo cargado desde Google Drive")
                    logo_displayed = True
        except Exception as e:
            st.sidebar.caption(f"⚠️ Error cargando logo desde Google Drive: {str(e)[:50]}...")
    
    # Si no se encuentra ningún logo, mostrar placeholder
    if not logo_displayed:
        create_logo_placeholder()

def display_logo_image(logo_path, caption_text):
    """
    Muestra una imagen de logo de manera responsive.
    
    Args:
        logo_path (str): Ruta al archivo de logo
        caption_text (str): Texto de caption para debug
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
            unsafe_allow_html=True
        )
        
        # Mostrar imagen con contenedor responsive
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(
                logo_path, 
                caption="Secretaría de Salud del Tolima",
                use_container_width=True
            )
            
        # Caption de debug solo en desarrollo
        if st.session_state.get('debug_mode', False):
            st.caption(f"🔍 {caption_text}")
            
    except Exception as e:
        st.sidebar.error(f"Error mostrando logo: {str(e)}")
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
            SECRETARÍA<br>DE SALUD<br>TOLIMA
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Mensaje informativo sobre el logo
    with st.expander("ℹ️ Información del Logo", expanded=False):
        st.markdown(
            """
            **Logo no encontrado.**
            
            **Ubicaciones verificadas:**
            - 📁 `data/Gobernacion.png` ← **Recomendado**
            - 📁 `assets/images/logo_gobernacion.png`
            - ☁️ Google Drive (si está configurado)
            
            **Para agregar el logo:**
            1. Coloque el archivo `Gobernacion.png` en la carpeta `data/`
            2. O configure Google Drive con el archivo
            """
        )

def create_info_section(title, content, icon="ℹ️"):
    """
    Crea una sección informativa responsive en la barra lateral.
    
    Args:
        title (str): Título de la sección
        content (str): Contenido de la sección
        icon (str): Icono a mostrar
        
    Returns:
        None
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"""
        <div style="margin-bottom: 1rem;">
            <h4 style="color: #7D0F2B; margin-bottom: 0.5rem; font-size: clamp(1rem, 3vw, 1.1rem);">
                {icon} {title}
            </h4>
            <div style="font-size: 0.9rem; line-height: 1.4;">
                {content}
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )

def create_download_section():
    """
    Crea una sección de descarga responsive en la barra lateral.
    
    Returns:
        None
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📥 Descargar Datos")
    
    # Botones responsive
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("📊 Datos", key="download_data", help="Descargar datos filtrados"):
            st.sidebar.info("Disponible en la pestaña de Tablas Detalladas")
    
    with col2:
        if st.button("📄 Reporte", key="download_report", help="Generar reporte PDF"):
            st.sidebar.info("Funcionalidad en desarrollo")

def show_filter_summary(active_filters):
    """
    Muestra un resumen responsive de los filtros activos en la barra lateral.
    
    Args:
        active_filters (list): Lista de filtros activos
        
    Returns:
        None
    """
    if not active_filters:
        return
        
    active_count = len(active_filters)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"""
        <div style="background-color: #f8f9fa; padding: 0.75rem; border-radius: 8px; border-left: 4px solid #7D0F2B;">
            <h4 style="color: #7D0F2B; margin: 0 0 0.5rem 0; font-size: 1rem;">
                🔍 Filtros Activos ({active_count})
            </h4>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Mostrar filtros de manera compacta
    for i, filter_desc in enumerate(active_filters[:5]):  # Máximo 5 filtros visibles
        st.sidebar.markdown(
            f"""
            <div style="font-size: 0.85rem; margin-bottom: 0.25rem; padding-left: 0.5rem;">
                • {filter_desc}
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    # Si hay más de 5 filtros, mostrar indicador
    if len(active_filters) > 5:
        remaining = len(active_filters) - 5
        st.sidebar.markdown(
            f"""
            <div style="font-size: 0.8rem; color: #666; padding-left: 0.5rem;">
                ... y {remaining} filtro(s) más
            </div>
            """, 
            unsafe_allow_html=True
        )

def show_data_source_info():
    """
    Muestra información responsive sobre la fuente de datos actual.
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Fuente de Datos")
    
    # Verificar archivos locales en carpeta data
    casos_file = DATA_DIR / "BD_positivos.xlsx"
    epi_file = DATA_DIR / "Información_Datos_FA.xlsx"
    
    # También verificar en directorio raíz como respaldo
    casos_file_root = ROOT_DIR / "BD_positivos.xlsx"
    epi_file_root = ROOT_DIR / "Información_Datos_FA.xlsx"
    
    # Estado de los archivos
    casos_disponible = casos_file.exists() or casos_file_root.exists()
    epi_disponible = epi_file.exists() or epi_file_root.exists()
    
    if casos_disponible and epi_disponible:
        source_location = "data/" if casos_file.exists() else "raíz"
        st.sidebar.success(f"✅ Archivos locales ({source_location})")
        st.sidebar.caption("Datos cargados desde archivos Excel locales")
    elif GDRIVE_AVAILABLE and check_google_drive_availability():
        st.sidebar.info("☁️ Google Drive")
        st.sidebar.caption("Datos cargados desde Google Drive")
    else:
        st.sidebar.warning("⚠️ Fuente no disponible")
        st.sidebar.caption("Verifique que los archivos de datos estén disponibles")

def show_system_status():
    """
    Muestra el estado del sistema de manera responsive y compacta.
    """
    with st.sidebar.expander("🔧 Estado del Sistema"):
        # Estado de archivos de datos
        st.markdown("**📁 Archivos de datos:**")
        
        # Verificar en carpeta data primero
        casos_data = DATA_DIR / "BD_positivos.xlsx"
        epi_data = DATA_DIR / "Información_Datos_FA.xlsx"
        
        # Verificar en raíz como respaldo
        casos_root = ROOT_DIR / "BD_positivos.xlsx"
        epi_root = ROOT_DIR / "Información_Datos_FA.xlsx"
        
        # Status casos
        if casos_data.exists():
            st.markdown("✅ BD_positivos.xlsx (data/)")
        elif casos_root.exists():
            st.markdown("✅ BD_positivos.xlsx (raíz)")
        else:
            st.markdown("❌ BD_positivos.xlsx")
            
        # Status epizootias
        if epi_data.exists():
            st.markdown("✅ Información_Datos_FA.xlsx (data/)")
        elif epi_root.exists():
            st.markdown("✅ Información_Datos_FA.xlsx (raíz)")
        else:
            st.markdown("❌ Información_Datos_FA.xlsx")
        
        # Estado de Google Drive
        st.markdown("**☁️ Google Drive:**")
        if GDRIVE_AVAILABLE:
            if check_google_drive_availability():
                st.markdown("✅ Configurado")
            else:
                st.markdown("⚠️ No configurado")
        else:
            st.markdown("❌ No disponible")
        
        # Estado del logo
        st.markdown("**🖼️ Logo:**")
        logo_data = DATA_DIR / "Gobernacion.png"
        logo_assets = IMAGES_DIR / "logo_gobernacion.png"
        
        if logo_data.exists():
            st.markdown("✅ Gobernacion.png (data/)")
        elif logo_assets.exists():
            st.markdown("✅ logo_gobernacion.png (assets/)")
        else:
            st.markdown("❌ Logo no encontrado")

def create_help_section():
    """
    Crea una sección de ayuda responsive y compacta.
    """
    with st.sidebar.expander("❓ Ayuda"):
        st.markdown(
            """
            **🚀 Inicio rápido:**
            1. Coloque los archivos Excel en `data/`
            2. Use filtros en la barra lateral
            3. Navegue por las pestañas
            
            **📊 Archivos requeridos:**
            - `BD_positivos.xlsx` (casos confirmados)
            - `Información_Datos_FA.xlsx` (epizootias)
            - `Gobernacion.png` (logo, opcional)
            
            **🔍 Funciones:**
            - **Mapas**: Distribución geográfica
            - **Timeline**: Evolución temporal  
            - **Tablas**: Datos detallados y exportación
            - **Comparativo**: Análisis estadístico
            
            **⚡ Consejos:**
            - Use "Restablecer Filtros" para limpiar selecciones
            - Los filtros se combinan automáticamente
            - Exporte datos desde "Tablas Detalladas"
            """, 
        )

def show_data_update_info():
    """
    Muestra información responsive sobre actualización de datos.
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔄 Última Actualización")
    
    # Verificar fechas de modificación de archivos
    files_to_check = [
        (DATA_DIR / "BD_positivos.xlsx", "Casos"),
        (DATA_DIR / "Información_Datos_FA.xlsx", "Epizootias"),
        (ROOT_DIR / "BD_positivos.xlsx", "Casos (raíz)"),
        (ROOT_DIR / "Información_Datos_FA.xlsx", "Epizootias (raíz)")
    ]
    
    for file_path, file_type in files_to_check:
        if file_path.exists():
            import os
            modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            st.sidebar.caption(f"{file_type}: {modified_time.strftime('%Y-%m-%d %H:%M')}")
            break  # Solo mostrar el primero encontrado
    
    # Botón de recarga
    if st.sidebar.button("🔄 Recargar Datos", help="Limpia caché y recarga datos"):
        # Limpiar caché de Streamlit
        st.cache_data.clear()
        st.rerun()

def add_responsive_css():
    """
    Agrega CSS para mejorar la responsividad del sidebar.
    """
    st.markdown(
        """
        <style>
        /* Sidebar responsive */
        .css-1d391kg {
            min-width: 280px;
        }
        
        /* Texto responsive en sidebar */
        .sidebar .stMarkdown {
            font-size: clamp(0.8rem, 2vw, 0.9rem);
        }
        
        /* Botones responsive en sidebar */
        .sidebar .stButton > button {
            width: 100%;
            font-size: clamp(0.8rem, 2vw, 0.9rem);
        }
        
        /* Métricas responsive */
        .css-1r6slb0 {
            font-size: clamp(1rem, 3vw, 1.2rem);
        }
        
        /* Inputs responsive en sidebar */
        .sidebar .stSelectbox > div > div {
            font-size: clamp(0.8rem, 2vw, 0.9rem);
        }
        
        /* Mobile adjustments */
        @media (max-width: 768px) {
            .css-1d391kg {
                min-width: 250px;
            }
            
            .sidebar .stMarkdown h1 {
                font-size: 1.5rem !important;
            }
            
            .sidebar .stMarkdown h3 {
                font-size: 1rem !important;
            }
        }
        </style>
        """, 
        unsafe_allow_html=True
    )

# Función principal para inicializar sidebar responsive
def init_responsive_sidebar():
    """
    Inicializa la barra lateral con todas las mejoras responsive.
    """
    add_responsive_css()
    create_sidebar()