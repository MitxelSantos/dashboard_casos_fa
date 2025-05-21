import os
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("FiebreAmarilla-Dashboard")

# Deshabilitar detección automática de páginas de Streamlit
os.environ["STREAMLIT_PAGES_ENABLED"] = "false"

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

# Importar utilidades de Google Drive
from gdrive_utils import get_file_from_drive

# Definir rutas
ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
ASSETS_DIR = ROOT_DIR / "assets"
IMAGES_DIR = ASSETS_DIR / "images"

# Asegurar que las carpetas existan
DATA_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(exist_ok=True)

# Configuración de IDs de archivos en Google Drive (se leerán de secrets en producción)
DRIVE_FILE_IDS = {
    "fiebre_amarilla": "YOUR_GOOGLE_DRIVE_FILE_ID",  # Esto será reemplazado por el ID real en secrets
    "logo_gobernacion": "YOUR_LOGO_FILE_ID"
}

# Agregar rutas al path para importar módulos
import sys
sys.path.insert(0, str(ROOT_DIR))

# Lista de vistas a importar
vista_modules = ["overview", "geographic", "demographic", "insurance", "trends"]
vistas_modules = {}

# Función para importar módulos de vistas con manejo de errores
def import_vista_module(module_name):
    """
    Importa un módulo de vista específico con manejo de errores.
    
    Args:
        module_name (str): Nombre del módulo a importar.
        
    Returns:
        module: El módulo importado o None en caso de error.
    """
    try:
        module = __import__(f"vistas.{module_name}", fromlist=[module_name])
        logger.info(f"Módulo {module_name} importado correctamente")
        return module
    except ImportError as e:
        logger.error(f"No se pudo importar el módulo {module_name}: {str(e)}")
        st.error(f"No se pudo importar el módulo {module_name}")
        return None

# Importar módulos de vistas
for module_name in vista_modules:
    vistas_modules[module_name] = import_vista_module(module_name)


# Función para cargar datos
def load_datasets():
    """
    Carga los datasets necesarios para la aplicación desde Google Drive.
    Utiliza secretos de Streamlit para la autenticación.
    
    Returns:
        dict: Diccionario con los dataframes cargados.
    """
    try:
        # Inicializar contador de progreso
        progress_bar = st.progress(0)
        status_text = st.empty()
        status_text.text("Conectando con Google Drive...")
        
        # Cargar archivo de fiebre amarilla desde Google Drive
        # En producción, obtendremos el ID del archivo desde los secretos de Streamlit
        if hasattr(st.secrets, "drive_files") and "fiebre_amarilla" in st.secrets.drive_files:
            file_id = st.secrets.drive_files["fiebre_amarilla"]
        else:
            # Si no hay secretos configurados, usar ID predeterminado (para desarrollo)
            file_id = DRIVE_FILE_IDS["fiebre_amarilla"]
            # Mostrar advertencia en modo desarrollo
            if not file_id.startswith("YOUR_"):  # Solo si se ha configurado un ID real
                st.warning("Usando ID de archivo predeterminado. En producción, configure los secretos.")
        
        status_text.text("Descargando datos desde Google Drive...")
        progress_bar.progress(30)
        
        # Obtener archivo desde Google Drive
        if file_id.startswith("YOUR_"):  # ID de placeholder, intentar carga local
            logger.warning("Usando carga de datos local (modo desarrollo)")
            fiebre_file = DATA_DIR / "FIBRE AMARILLA DEPURADA.xlsx"
            if not fiebre_file.exists():
                raise FileNotFoundError(f"Archivo no encontrado: {fiebre_file}")
        else:
            # Carga desde Google Drive
            excel_path = get_file_from_drive(file_id, "fiebre_amarilla.xlsx")
            if not excel_path:
                raise FileNotFoundError("No se pudo descargar el archivo desde Google Drive")
            fiebre_file = excel_path
        
        status_text.text("Procesando datos...")
        progress_bar.progress(60)
        
        # Cargar Excel con optimizaciones para archivos grandes
        try:
            # Leer Excel 
            fiebre_df = pd.read_excel(
                fiebre_file,
                engine='openpyxl',
                na_values=['NA', 'N/A', ''],
                keep_default_na=True
            )
            logger.info(f"Archivo Excel cargado correctamente: {len(fiebre_df)} filas")
        except Exception as e:
            logger.error(f"Error al cargar el archivo Excel: {str(e)}")
            st.error(f"Error al cargar el archivo Excel: {str(e)}")
            raise
        
        progress_bar.progress(80)
        
        # Normalizar nombres de columnas (quitar espacios)
        fiebre_df.columns = [col.strip() for col in fiebre_df.columns]
        
        # Crear DataFrame de departamentos para análisis geográfico
        if 'cod_dpto_r' in fiebre_df.columns and 'ndep_resi' in fiebre_df.columns:
            # Agrupar por departamento
            deptos_df = fiebre_df.groupby(['cod_dpto_r', 'ndep_resi']).size().reset_index()
            deptos_df.columns = ['cod_dpto', 'departamento', 'casos']
        else:
            # Crear un dataframe vacío con estructura si no existen las columnas
            deptos_df = pd.DataFrame(columns=['cod_dpto', 'departamento', 'casos'])
            
        # Calcular métricas generales
        metricas_df = calculate_metrics(fiebre_df)
        
        progress_bar.progress(100)
        status_text.text("Datos cargados correctamente!")
        
        # Limpiar elementos de UI temporales después de un breve retraso
        import time
        time.sleep(1)
        status_text.empty()
        progress_bar.empty()
        
        return {
            "fiebre": fiebre_df,
            "departamentos": deptos_df,
            "metricas": metricas_df
        }
    except Exception as e:
        logger.error(f"Error al cargar los datos: {str(e)}")
        if progress_bar:
            progress_bar.empty()
        if status_text:
            status_text.empty()
        
        st.error(f"Error al cargar los datos: {str(e)}")
        
        # Retornar diccionario con DataFrames vacíos para permitir carga de la aplicación
        return {
            "fiebre": pd.DataFrame(),
            "departamentos": pd.DataFrame(),
            "metricas": pd.DataFrame()
        }


def calculate_metrics(df):
    """
    Calcula métricas generales sobre los datos de fiebre amarilla.
    
    Args:
        df (DataFrame): DataFrame con los datos de fiebre amarilla.
        
    Returns:
        DataFrame: DataFrame con las métricas calculadas.
    """
    # Crear dataframe para métricas
    metrics = pd.DataFrame()
    
    # Total de casos
    total_casos = len(df)
    
    # Casos por tipo
    if 'tip_cas_' in df.columns:
        casos_tipo = df['tip_cas_'].value_counts().to_dict()
    else:
        casos_tipo = {"No disponible": total_casos}
    
    # Casos por condición final
    if 'con_fin_' in df.columns:
        condicion_final = df['con_fin_'].value_counts().to_dict()
        # Calcular tasa de letalidad
        fallecidos = condicion_final.get(2, 0)  # 2 = Muerto
        letalidad = (fallecidos / total_casos * 100) if total_casos > 0 else 0
    else:
        condicion_final = {"No disponible": total_casos}
        letalidad = 0
    
    # Casos por tipo de aseguramiento
    if 'tip_ss_' in df.columns:
        tipo_aseguramiento = df['tip_ss_'].value_counts().to_dict()
    else:
        tipo_aseguramiento = {"No disponible": total_casos}
    
    # Distribucion por sexo
    if 'sexo_' in df.columns:
        distribucion_sexo = df['sexo_'].value_counts().to_dict()
    else:
        distribucion_sexo = {"No disponible": total_casos}
    
    # Crear diccionario con todas las métricas
    metricas_dict = {
        "total_casos": [total_casos],
        "letalidad": [letalidad],
        "fecha_actualizacion": [datetime.now().strftime("%Y-%m-%d %H:%M")]
    }
    
    # Agregar métricas adicionales
    if 'tip_cas_' in df.columns:
        # Contar casos confirmados (tipos 3, 4 y 5)
        confirmados = df[df['tip_cas_'].isin([3, 4, 5])].shape[0]
        metricas_dict["confirmados"] = [confirmados]
    
    # Convertir diccionario a DataFrame
    metrics = pd.DataFrame(metricas_dict)
    
    return metrics


# Configuración de la página
def configure_page():
    """
    Configura la página de Streamlit con estilos personalizados.
    """
    st.set_page_config(
        page_title="Dashboard Fiebre Amarilla - Tolima",
        page_icon="🦟",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Cargar CSS personalizado
    css_file = Path(ASSETS_DIR) / "styles" / "main.css"
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
    # CSS responsivo adicional
    css_responsive = Path(ASSETS_DIR) / "styles" / "responsive.css"
    if css_responsive.exists():
        with open(css_responsive) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        # Si no existe, agregar CSS responsivo básico
        st.markdown("""
        <style>
        /* Estilos responsivos para el Dashboard */
        @media (max-width: 768px) {
            .metric-card {padding: 0.5rem;}
            .metric-value {font-size: 1.2rem;}
            h1 {font-size: 1.5rem !important;}
            h2 {font-size: 1.2rem !important;}
        }
        
        /* Mejoras estéticas generales */
        .main-title {
            color: #7D0F2B;
            font-size: 2.2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            text-align: center;
            padding-bottom: 0.5rem;
            border-bottom: 3px solid #F2A900;
        }
        
        .subtitle {
            color: #5A4214;
            font-size: 1.2rem;
            text-align: center;
            margin-bottom: 1.5rem;
        }
        
        /* Mejoras para tarjetas de métricas */
        .big-metric-container {
            background-color: white;
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        
        .big-metric-container:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }
        
        .big-metric-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #5A4214;
            margin-bottom: 0.7rem;
        }
        
        .big-metric-value {
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 0.3rem;
        }
        
        .update-info {
            font-size: 0.75rem;
            color: #666;
            font-style: italic;
            text-align: right;
            margin-top: 1rem;
        }
        </style>
        """, unsafe_allow_html=True)


# Colores institucionales del Tolima
COLORS = {
    "primary": "#7D0F2B",    # Vinotinto
    "secondary": "#F2A900",   # Amarillo/Dorado
    "accent": "#5A4214",      # Marrón dorado oscuro
    "background": "#F5F5F5",  # Fondo gris claro
    "success": "#509E2F",     # Verde
    "warning": "#F7941D",     # Naranja
    "danger": "#E51937",      # Rojo brillante
}


# Aplicar filtros a los datos
def apply_filters(data, filters):
    """
    Aplica los filtros seleccionados a los datos.
    
    Args:
        data (dict): Diccionario con los dataframes originales.
        filters (dict): Diccionario con los filtros a aplicar.
        
    Returns:
        dict: Diccionario con los dataframes filtrados.
    """
    # Crear copias para no modificar los originales
    filtered_data = {
        "fiebre": data["fiebre"].copy(),
        "departamentos": data["departamentos"].copy(),
        "metricas": data["metricas"].copy()
    }
    
    # Filtro por año
    if filters["año"] != "Todos" and "año" in filtered_data["fiebre"].columns:
        año_filtro = filters["año"]
        if año_filtro.isdigit():  # Si el filtro es un número
            filtered_data["fiebre"] = filtered_data["fiebre"][filtered_data["fiebre"]["año"] == int(año_filtro)]
        else:
            filtered_data["fiebre"] = filtered_data["fiebre"][filtered_data["fiebre"]["año"] == año_filtro]
    
    # Filtro por tipo de caso
    if filters["tipo_caso"] != "Todos" and "tip_cas_" in filtered_data["fiebre"].columns:
        tipo_filtro = filters["tipo_caso"]
        # Mapeo de nombres a códigos
        tipo_mapping = {
            "Sospechoso": 1, 
            "Probable": 2, 
            "Confirmado por Laboratorio": 3,
            "Confirmado por Clínica": 4,
            "Confirmado por Nexo Epidemiológico": 5
        }
        
        if tipo_filtro in tipo_mapping:
            filtered_data["fiebre"] = filtered_data["fiebre"][filtered_data["fiebre"]["tip_cas_"] == tipo_mapping[tipo_filtro]]
        else:
            # Si es un valor personalizado que no está en el mapeo
            filtered_data["fiebre"] = filtered_data["fiebre"][filtered_data["fiebre"]["tip_cas_"] == tipo_filtro]
    
    # Filtro por departamento
    if filters["departamento"] != "Todos" and "ndep_resi" in filtered_data["fiebre"].columns:
        filtered_data["fiebre"] = filtered_data["fiebre"][
            filtered_data["fiebre"]["ndep_resi"].str.lower() == filters["departamento"].lower()
        ]
    
    # Filtro por tipo de seguridad social
    if filters["tipo_ss"] != "Todos" and "tip_ss_" in filtered_data["fiebre"].columns:
        tipo_ss_filtro = filters["tipo_ss"]
        # Verificar si el filtro es un código con descripción (ej: "C - Contributivo")
        if " - " in tipo_ss_filtro:
            codigo = tipo_ss_filtro.split(" - ")[0]
            filtered_data["fiebre"] = filtered_data["fiebre"][
                filtered_data["fiebre"]["tip_ss_"].astype(str) == codigo
            ]
        else:
            filtered_data["fiebre"] = filtered_data["fiebre"][
                filtered_data["fiebre"]["tip_ss_"] == tipo_ss_filtro
            ]
    
    # Filtro por sexo
    if filters["sexo"] != "Todos" and "sexo_" in filtered_data["fiebre"].columns:
        filtered_data["fiebre"] = filtered_data["fiebre"][
            filtered_data["fiebre"]["sexo_"] == filters["sexo"]
        ]
    
    # Recalcular métricas con datos filtrados
    filtered_data["metricas"] = calculate_metrics(filtered_data["fiebre"])
    
    # Recalcular datos departamentales
    if 'cod_dpto_r' in filtered_data["fiebre"].columns and 'ndep_resi' in filtered_data["fiebre"].columns:
        filtered_data["departamentos"] = filtered_data["fiebre"].groupby(['cod_dpto_r', 'ndep_resi']).size().reset_index()
        filtered_data["departamentos"].columns = ['cod_dpto', 'departamento', 'casos']
    
    return filtered_data


def main():
    """Aplicación principal del dashboard."""
    # Configurar página
    configure_page()
    
    # Detectar tamaño de pantalla con JavaScript
    st.markdown(
        """
    <script>
        // Detectar tamaño de pantalla
        var updateScreenSize = function() {
            var width = window.innerWidth;
            var isSmall = width < 1200;
            
            // Almacenar en sessionStorage para que Streamlit pueda acceder
            sessionStorage.setItem('_screen_width', width);
            sessionStorage.setItem('_is_small_screen', isSmall);
        };
        
        // Actualizar inmediatamente y al cambiar tamaño
        updateScreenSize();
        window.addEventListener('resize', updateScreenSize);
    </script>
    """,
        unsafe_allow_html=True,
    )

    # Intentar recuperar el tamaño de pantalla
    screen_width = st.session_state.get("_screen_width", 1200)
    st.session_state["_is_small_screen"] = screen_width < 1200

    # Cargar datos
    data_load_state = st.empty()
    
    try:
        with data_load_state:
            data = load_datasets()
    except Exception as e:
        logger.error(f"Error al cargar datos: {str(e)}")
        st.error(f"Error al cargar datos: {str(e)}")
        st.info(
            """
            Por favor, asegúrate que el archivo de datos 'FIBRE AMARILLA DEPURADA.xlsx' esté disponible:
            - Si estás en Streamlit Cloud, configura los secretos con el ID del archivo en Google Drive
            - Si estás en desarrollo local, coloca el archivo en la carpeta data/
            """
        )
        return

    # Barra lateral con logo y filtros
    with st.sidebar:
        # Logo de la Gobernación
        if hasattr(st.secrets, "drive_files") and "logo_gobernacion" in st.secrets.drive_files:
            # Obtener logo desde Google Drive
            logo_id = st.secrets.drive_files["logo_gobernacion"]
            logo_path = get_file_from_drive(logo_id, "logo_gobernacion.png")
            if logo_path and Path(logo_path).exists():
                st.image(
                    logo_path, width=150, caption="Secretaría de Salud del Tolima"
                )
            else:
                st.warning("No se pudo cargar el logo desde Google Drive")
        else:
            # Buscar logo local
            logo_path = IMAGES_DIR / "logo_gobernacion.png"
            if logo_path.exists():
                st.image(
                    str(logo_path), width=150, caption="Secretaría de Salud del Tolima"
                )
            else:
                st.warning(
                    "Logo no encontrado. Coloca el logo en assets/images/logo_gobernacion.png"
                )

        st.title("Dashboard Fiebre Amarilla")
        st.subheader("Vigilancia Epidemiológica")

        # Filtros globales
        st.subheader("Filtros")

        # Función para aplicar filtros automáticamente
        def on_filter_change():
            st.session_state.filters = {
                "año": st.session_state.año_filter,
                "tipo_caso": st.session_state.tipo_caso_filter,
                "departamento": st.session_state.departamento_filter,
                "tipo_ss": st.session_state.tipo_ss_filter,
                "sexo": st.session_state.sexo_filter,
            }

        # Obtener años únicos
        años = ["Todos"]
        if "año" in data["fiebre"].columns and not data["fiebre"].empty:
            años_unicos = data["fiebre"]["año"].dropna().unique().tolist()
            años += sorted([str(int(año)) if isinstance(año, (int, float)) else str(año) for año in años_unicos if not pd.isna(año)])
        
        año = st.selectbox(
            "Año",
            options=años,
            key="año_filter",
            on_change=on_filter_change,
        )

        # Obtener tipos de caso
        tipos_caso = ["Todos"]
        if "tip_cas_" in data["fiebre"].columns and not data["fiebre"].empty:
            # Mapeo de códigos a nombres
            tipo_mapping = {
                1: "Sospechoso", 
                2: "Probable", 
                3: "Confirmado por Laboratorio",
                4: "Confirmado por Clínica",
                5: "Confirmado por Nexo Epidemiológico"
            }
            
            # Obtener valores únicos
            tipos_unicos = data["fiebre"]["tip_cas_"].dropna().unique().tolist()
            
            # Convertir códigos a nombres descriptivos
            for tipo in tipos_unicos:
                if tipo in tipo_mapping:
                    tipos_caso.append(tipo_mapping[tipo])
                else:
                    tipos_caso.append(str(tipo))
        
        tipo_caso = st.selectbox(
            "Tipo de Caso",
            options=tipos_caso,
            key="tipo_caso_filter",
            on_change=on_filter_change,
        )

        # Obtener departamentos
        departamentos = ["Todos"]
        if "ndep_resi" in data["fiebre"].columns and not data["fiebre"].empty:
            deptos_unicos = data["fiebre"]["ndep_resi"].dropna().unique().tolist()
            departamentos += sorted([str(depto) for depto in deptos_unicos])
        
        departamento = st.selectbox(
            "Departamento",
            options=departamentos,
            key="departamento_filter",
            on_change=on_filter_change,
        )

        # Obtener tipos de seguridad social
        tipos_ss = ["Todos"]
        if "tip_ss_" in data["fiebre"].columns and not data["fiebre"].empty:
            # Mapeo de códigos a descripciones
            ss_mapping = {
                "C": "Contributivo",
                "S": "Subsidiado",
                "P": "Excepción",
                "E": "Especial",
                "N": "No asegurado",
                "I": "Indeterminado/Pendiente"
            }
            
            # Obtener valores únicos
            ss_unicos = data["fiebre"]["tip_ss_"].dropna().unique().tolist()
            
            # Añadir valores con descripciones
            for ss in ss_unicos:
                ss_str = str(ss)
                if ss_str in ss_mapping:
                    tipos_ss.append(f"{ss_str} - {ss_mapping[ss_str]}")
                else:
                    tipos_ss.append(ss_str)
        
        tipo_ss = st.selectbox(
            "Tipo de Seguridad Social",
            options=tipos_ss,
            key="tipo_ss_filter",
            on_change=on_filter_change,
        )

        # Obtener valores de sexo
        sexos = ["Todos"]
        if "sexo_" in data["fiebre"].columns and not data["fiebre"].empty:
            sexos_unicos = data["fiebre"]["sexo_"].dropna().unique().tolist()
            sexos += sorted([str(sexo) for sexo in sexos_unicos])
        
        sexo = st.selectbox(
            "Sexo",
            options=sexos,
            key="sexo_filter",
            on_change=on_filter_change,
        )

        # Función para resetear todos los filtros
        def reset_filters():
            # Usar las claves para reiniciar todos los filtros
            for key in [
                "año_filter",
                "tipo_caso_filter",
                "departamento_filter",
                "tipo_ss_filter",
                "sexo_filter",
            ]:
                # Esta es la forma correcta de resetear, usando .update()
                st.session_state.update({key: "Todos"})

            # Actualizar filtros después del reset
            on_filter_change()

        # Botón para resetear filtros
        if st.button("Restablecer Filtros", on_click=reset_filters):
            pass  # La lógica está en reset_filters

        # Información del desarrollador
        st.sidebar.markdown("---")
        st.sidebar.caption("Desarrollado para la Secretaría de Salud del Tolima")
        st.sidebar.caption(f"© {datetime.now().year}")

    # Inicializar filtros si no existen
    if "filters" not in st.session_state:
        st.session_state.filters = {
            "año": "Todos",
            "tipo_caso": "Todos",
            "departamento": "Todos",
            "tipo_ss": "Todos",
            "sexo": "Todos",
        }

    # Banner principal y logos
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown('<h1 class="main-title">Dashboard Fiebre Amarilla - Tolima</h1>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle">Secretaría de Salud del Tolima - Vigilancia Epidemiológica</p>', unsafe_allow_html=True)

    # Mostrar filtros activos en un banner con fondo vinotinto
    active_filters = [
        f"{k.capitalize()}: {v}"
        for k, v in st.session_state.filters.items()
        if v != "Todos"
    ]
    if active_filters:
        st.markdown(
            f"""
            <div style="background-color: {COLORS['primary']}; color: white; padding: 10px; border-radius: 5px; margin-bottom: 15px;">
                <strong>Filtros aplicados:</strong> {', '.join(active_filters)}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Aplicar filtros a los datos
    filtered_data = apply_filters(data, st.session_state.filters)

    # Pestañas de navegación
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "Visión General",
            "Distribución Geográfica",
            "Perfil Demográfico",
            "Aseguramiento",
            "Tendencias",
        ]
    )

    # Contenido de cada pestaña
    with tab1:
        if "overview" in vistas_modules and vistas_modules["overview"]:
            vistas_modules["overview"].show(
                filtered_data,
                st.session_state.filters,
                COLORS
            )
        else:
            # Vista básica por defecto
            st.header("Visión General")
            
            # Métricas principales
            total_casos = len(filtered_data["fiebre"])
            
            # Métricas de letalidad
            letalidad = 0
            fallecidos = 0
            if "con_fin_" in filtered_data["fiebre"].columns:
                fallecidos = filtered_data["fiebre"][filtered_data["fiebre"]["con_fin_"] == 2].shape[0]
                letalidad = (fallecidos / total_casos * 100) if total_casos > 0 else 0
            
            # Casos confirmados
            confirmados = 0
            if "tip_cas_" in filtered_data["fiebre"].columns:
                # Contar casos confirmados (tipos 3, 4 y 5)
                confirmados = filtered_data["fiebre"][filtered_data["fiebre"]["tip_cas_"].isin([3, 4, 5])].shape[0]
            
            # Mostrar fecha de actualización si está disponible
            fecha_actualizacion = ""
            if "fecha_actualizacion" in filtered_data["metricas"].columns:
                fecha_actualizacion = filtered_data["metricas"]["fecha_actualizacion"].iloc[0]
            
            # Mostrar métricas en tarjetas mejoradas
            st.markdown('<div style="margin-bottom: 30px;">', unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(
                    f"""
                    <div class="big-metric-container" style="border-top: 5px solid {COLORS['primary']}">
                        <div class="big-metric-title">Total de Casos</div>
                        <div class="big-metric-value" style="color: {COLORS['primary']};">{total_casos:,}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            with col2:
                # Calcular porcentaje de confirmados
                porcentaje_conf = (confirmados / total_casos * 100) if total_casos > 0 else 0
                st.markdown(
                    f"""
                    <div class="big-metric-container" style="border-top: 5px solid {COLORS['secondary']}">
                        <div class="big-metric-title">Casos Confirmados</div>
                        <div class="big-metric-value" style="color: {COLORS['secondary']};">{confirmados:,}</div>
                        <div style="font-size: 0.9rem; color: #666;">{porcentaje_conf:.1f}% del total</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            with col3:
                st.markdown(
                    f"""
                    <div class="big-metric-container" style="border-top: 5px solid {COLORS['danger']}">
                        <div class="big-metric-title">Fallecidos</div>
                        <div class="big-metric-value" style="color: {COLORS['danger']};">{fallecidos:,}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            with col4:
                st.markdown(
                    f"""
                    <div class="big-metric-container" style="border-top: 5px solid {COLORS['warning']}">
                        <div class="big-metric-title">Tasa de Letalidad</div>
                        <div class="big-metric-value" style="color: {COLORS['warning']};">{letalidad:.2f}%</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            # Mostrar fecha de actualización
            if fecha_actualizacion:
                st.markdown(
                    f'<div class="update-info">Última actualización: {fecha_actualizacion}</div>',
                    unsafe_allow_html=True
                )
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Distribución por tipo de caso
            if "tip_cas_" in filtered_data["fiebre"].columns:
                st.subheader("Distribución por Tipo de Caso")
                
                # Mapeo de códigos a nombres
                tipo_mapping = {
                    1: "Sospechoso", 
                    2: "Probable", 
                    3: "Confirmado por Laboratorio",
                    4: "Confirmado por Clínica",
                    5: "Confirmado por Nexo Epidemiológico"
                }
                
                # Crear copia del dataframe para la transformación
                df_tipo = filtered_data["fiebre"].copy()
                
                # Aplicar mapeo
                df_tipo["tipo_caso_desc"] = df_tipo["tip_cas_"].map(tipo_mapping).fillna("Otro")
                
                # Contar casos por tipo
                tipo_count = df_tipo["tipo_caso_desc"].value_counts().reset_index()
                tipo_count.columns = ["Tipo de Caso", "Cantidad"]
                
                # Mostrar gráfico
                st.bar_chart(tipo_count.set_index("Tipo de Caso"))
                
                # Mostrar tabla
                st.dataframe(tipo_count, use_container_width=True)
            
            # Distribución por condición final
            if "con_fin_" in filtered_data["fiebre"].columns:
                st.subheader("Condición Final de los Casos")
                
                # Mapeo de códigos a nombres
                condicion_mapping = {
                    1: "Vivo", 
                    2: "Fallecido"
                }
                
                # Crear copia del dataframe para la transformación
                df_condicion = filtered_data["fiebre"].copy()
                
                # Aplicar mapeo
                df_condicion["condicion_desc"] = df_condicion["con_fin_"].map(condicion_mapping).fillna("No especificado")
                
                # Contar casos por condición
                condicion_count = df_condicion["condicion_desc"].value_counts().reset_index()
                condicion_count.columns = ["Condición Final", "Cantidad"]
                
                # Mostrar gráfico
                st.bar_chart(condicion_count.set_index("Condición Final"))
                
                # Mostrar tabla
                st.dataframe(condicion_count, use_container_width=True)
            
            # Distribución por año 
            if "año" in filtered_data["fiebre"].columns:
                st.subheader("Distribución por Año")
                
                # Contar casos por año
                año_count = filtered_data["fiebre"]["año"].value_counts().reset_index()
                año_count.columns = ["Año", "Cantidad"]
                año_count = año_count.sort_values("Año")
                
                # Mostrar gráfico
                st.line_chart(año_count.set_index("Año"))
                
                # Mostrar tabla
                st.dataframe(año_count, use_container_width=True)

    with tab2:
        if "geographic" in vistas_modules and vistas_modules["geographic"]:
            vistas_modules["geographic"].show(
                filtered_data,
                st.session_state.filters,
                COLORS
            )
        else:
            st.header("Distribución Geográfica")
            
            # Distribución por departamento
            if "ndep_resi" in filtered_data["fiebre"].columns:
                st.subheader("Distribución por Departamento")
                
                # Contar casos por departamento
                depto_count = filtered_data["fiebre"]["ndep_resi"].value_counts().reset_index()
                depto_count.columns = ["Departamento", "Cantidad"]
                depto_count = depto_count.sort_values("Cantidad", ascending=False)
                
                # Mostrar gráfico
                st.bar_chart(depto_count.set_index("Departamento"))
                
                # Mostrar tabla
                st.dataframe(depto_count, use_container_width=True)
            
            # Distribución por municipio
            if "nmun_resi" in filtered_data["fiebre"].columns:
                st.subheader("Distribución por Municipio")
                
                # Contar casos por municipio
                muni_count = filtered_data["fiebre"]["nmun_resi"].value_counts().reset_index()
                muni_count.columns = ["Municipio", "Cantidad"]
                muni_count = muni_count.sort_values("Cantidad", ascending=False).head(20)  # Top 20
                
                # Mostrar gráfico
                st.bar_chart(muni_count.set_index("Municipio"))
                
                # Mostrar tabla
                st.dataframe(muni_count, use_container_width=True)

    with tab3:
        if "demographic" in vistas_modules and vistas_modules["demographic"]:
            vistas_modules["demographic"].show(
                filtered_data,
                st.session_state.filters,
                COLORS
            )
        else:
            st.header("Perfil Demográfico")
            
            # Distribución por sexo
            if "sexo_" in filtered_data["fiebre"].columns:
                st.subheader("Distribución por Sexo")
                
                # Contar casos por sexo
                sexo_count = filtered_data["fiebre"]["sexo_"].value_counts().reset_index()
                sexo_count.columns = ["Sexo", "Cantidad"]
                
                # Mostrar gráfico
                st.bar_chart(sexo_count.set_index("Sexo"))
                
                # Mostrar tabla
                st.dataframe(sexo_count, use_container_width=True)
            
            # Distribución por edad
            if "edad_" in filtered_data["fiebre"].columns:
                st.subheader("Distribución por Edad")
                
                # Crear rangos de edad
                def crear_grupo_edad(edad):
                    if pd.isna(edad):
                        return "No especificado"
                    elif edad < 5:
                        return "0-4 años"
                    elif edad < 15:
                        return "5-14 años"
                    elif edad < 20:
                        return "15-19 años"
                    elif edad < 30:
                        return "20-29 años"
                    elif edad < 40:
                        return "30-39 años"
                    elif edad < 50:
                        return "40-49 años"
                    elif edad < 60:
                        return "50-59 años"
                    elif edad < 70:
                        return "60-69 años"
                    elif edad < 80:
                        return "70-79 años"
                    else:
                        return "80+ años"
                
                # Aplicar función para crear grupos de edad
                df_edad = filtered_data["fiebre"].copy()
                df_edad["grupo_edad"] = df_edad["edad_"].apply(crear_grupo_edad)
                
                # Orden de los grupos de edad
                orden_grupos = [
                    "0-4 años", "5-14 años", "15-19 años", "20-29 años",
                    "30-39 años", "40-49 años", "50-59 años", "60-69 años",
                    "70-79 años", "80+ años", "No especificado"
                ]
                
                # Contar casos por grupo de edad
                edad_count = df_edad["grupo_edad"].value_counts().reset_index()
                edad_count.columns = ["Grupo de Edad", "Cantidad"]
                
                # Reordenar según el orden definido
                edad_count["Grupo de Edad"] = pd.Categorical(
                    edad_count["Grupo de Edad"],
                    categories=orden_grupos,
                    ordered=True
                )
                edad_count = edad_count.sort_values("Grupo de Edad")
                
                # Mostrar gráfico
                st.bar_chart(edad_count.set_index("Grupo de Edad"))
                
                # Mostrar tabla
                st.dataframe(edad_count, use_container_width=True)
            
            # Distribución por pertenencia étnica
            if "per_etn_" in filtered_data["fiebre"].columns:
                st.subheader("Distribución por Pertenencia Étnica")
                
                # Mapeo de códigos a nombres
                etnia_mapping = {
                    1: "Indígena",
                    2: "Gitano",
                    3: "Raizal",
                    4: "Palenqueros",
                    5: "Afrocolombiano",
                    6: "Otro"
                }
                
                # Crear copia del dataframe para la transformación
                df_etnia = filtered_data["fiebre"].copy()
                
                # Aplicar mapeo
                df_etnia["etnia_desc"] = df_etnia["per_etn_"].map(etnia_mapping).fillna("No especificado")
                
                # Contar casos por etnia
                etnia_count = df_etnia["etnia_desc"].value_counts().reset_index()
                etnia_count.columns = ["Pertenencia Étnica", "Cantidad"]
                
                # Mostrar gráfico
                st.bar_chart(etnia_count.set_index("Pertenencia Étnica"))
                
                # Mostrar tabla
                st.dataframe(etnia_count, use_container_width=True)

    with tab4:
        if "insurance" in vistas_modules and vistas_modules["insurance"]:
            vistas_modules["insurance"].show(
                filtered_data,
                st.session_state.filters,
                COLORS
            )
        else:
            st.header("Aseguramiento")
            
            # Distribución por tipo de seguridad social
            if "tip_ss_" in filtered_data["fiebre"].columns:
                st.subheader("Distribución por Tipo de Seguridad Social")
                
                # Mapeo de códigos a descripciones
                ss_mapping = {
                    "C": "Contributivo",
                    "S": "Subsidiado",
                    "P": "Excepción",
                    "E": "Especial",
                    "N": "No asegurado",
                    "I": "Indeterminado/Pendiente"
                }
                
                # Crear copia del dataframe para la transformación
                df_ss = filtered_data["fiebre"].copy()
                
                # Aplicar mapeo
                df_ss["ss_desc"] = df_ss["tip_ss_"].apply(lambda x: ss_mapping.get(str(x), "No especificado"))
                
                # Contar casos por tipo de seguridad social
                ss_count = df_ss["ss_desc"].value_counts().reset_index()
                ss_count.columns = ["Tipo de Seguridad Social", "Cantidad"]
                
                # Mostrar gráfico
                st.bar_chart(ss_count.set_index("Tipo de Seguridad Social"))
                
                # Mostrar tabla
                st.dataframe(ss_count, use_container_width=True)
            
            # Distribución por aseguradora
            if "cod_ase_" in filtered_data["fiebre"].columns:
                st.subheader("Distribución por Aseguradora")
                
                # Contar casos por código de aseguradora
                ase_count = filtered_data["fiebre"]["cod_ase_"].value_counts().reset_index()
                ase_count.columns = ["Código Aseguradora", "Cantidad"]
                ase_count = ase_count.sort_values("Cantidad", ascending=False)
                
                # Mostrar gráfico
                st.bar_chart(ase_count.head(10).set_index("Código Aseguradora"))
                
                # Mostrar tabla
                st.dataframe(ase_count, use_container_width=True)

    with tab5:
        if "trends" in vistas_modules and vistas_modules["trends"]:
            vistas_modules["trends"].show(
                filtered_data,
                st.session_state.filters,
                COLORS
            )
        else:
            st.header("Tendencias")
            
            # Evolución de casos por año
            if "año" in filtered_data["fiebre"].columns:
                st.subheader("Evolución de Casos por Año")
                
                # Contar casos por año
                año_count = filtered_data["fiebre"]["año"].value_counts().reset_index()
                año_count.columns = ["Año", "Cantidad"]
                año_count = año_count.sort_values("Año")
                
                # Mostrar gráfico
                st.line_chart(año_count.set_index("Año"))
                
                # Mostrar tabla
                st.dataframe(año_count, use_container_width=True)
            
            # Evolución de casos por mes si hay fecha de inicio de síntomas
            if "ini_sin_" in filtered_data["fiebre"].columns:
                st.subheader("Evolución de Casos por Mes")
                
                # Convertir a datetime
                df_fecha = filtered_data["fiebre"].copy()
                df_fecha["ini_sin_"] = pd.to_datetime(df_fecha["ini_sin_"], errors="coerce")
                
                # Filtrar fechas válidas
                df_fecha = df_fecha[~df_fecha["ini_sin_"].isna()]
                
                if not df_fecha.empty:
                    # Extraer año y mes
                    df_fecha["año_mes"] = df_fecha["ini_sin_"].dt.to_period("M")
                    
                    # Contar casos por año y mes
                    mes_count = df_fecha["año_mes"].value_counts().reset_index()
                    mes_count.columns = ["Año-Mes", "Cantidad"]
                    mes_count = mes_count.sort_values("Año-Mes")
                    
                    # Convertir período a string para gráfico
                    mes_count["Año-Mes"] = mes_count["Año-Mes"].astype(str)
                    
                    # Mostrar gráfico
                    st.line_chart(mes_count.set_index("Año-Mes"))
                    
                    # Mostrar tabla
                    st.dataframe(mes_count, use_container_width=True)
                else:
                    st.info("No hay fechas válidas para mostrar evolución por mes.")


if __name__ == "__main__":
    main()