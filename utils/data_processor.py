"""
utils/data_processor.py - SIMPLIFICADO
Los nombres ya coinciden exactamente, eliminado código de normalización innecesario
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
from pathlib import Path

from utils.name_normalizer import normalize_name, validate_municipio_name

logger = logging.getLogger(__name__)

# ===== FUNCIONES CORE DE FECHAS (mantener las existentes) =====


def excel_date_to_datetime(excel_date):
    """Convierte fecha de Excel a datetime con manejo robusto."""
    try:
        if isinstance(excel_date, (pd.Timestamp, datetime)):
            return excel_date

        if pd.isna(excel_date) or excel_date == "":
            return None

        if isinstance(excel_date, str):
            excel_date = excel_date.strip()
            if not excel_date or excel_date.lower() in ["nan", "none", "null"]:
                return None

            formatos_fecha = [
                "%d/%m/%Y",
                "%d/%m/%y",
                "%d-%m-%Y",
                "%d-%m-%y",
                "%Y-%m-%d",
                "%d.%m.%Y",
                "%d.%m.%y",
            ]

            for formato in formatos_fecha:
                try:
                    fecha_convertida = datetime.strptime(excel_date, formato)
                    if fecha_convertida.year < 50:
                        fecha_convertida = fecha_convertida.replace(
                            year=fecha_convertida.year + 2000
                        )
                    elif fecha_convertida.year < 100:
                        fecha_convertida = fecha_convertida.replace(
                            year=fecha_convertida.year + 1900
                        )
                    return fecha_convertida
                except ValueError:
                    continue

            try:
                return pd.to_datetime(excel_date, dayfirst=True, errors="coerce")
            except:
                return None

        if isinstance(excel_date, (int, float)):
            if pd.isna(excel_date) or excel_date < 0 or excel_date > 100000:
                return None
            try:
                return pd.to_datetime(excel_date, origin="1899-12-30", unit="D")
            except:
                return None

        return None

    except Exception as e:
        logger.warning(f"Error procesando fecha: {excel_date} - {str(e)}")
        return None


def format_date_display(date_value):
    """Formatea una fecha para mostrar."""
    if pd.isna(date_value):
        return ""
    try:
        if isinstance(date_value, (pd.Timestamp, datetime)):
            return date_value.strftime("%Y-%m-%d")
        else:
            converted_date = excel_date_to_datetime(date_value)
            return converted_date.strftime("%Y-%m-%d") if converted_date else ""
    except Exception as e:
        logger.warning(f"Error formateando fecha {date_value}: {e}")
        return ""


def calculate_days_since(date_value):
    """Calcula los días transcurridos desde una fecha hasta hoy."""
    if pd.isna(date_value):
        return None

    try:
        if isinstance(date_value, (pd.Timestamp, datetime)):
            fecha = date_value
        else:
            fecha = excel_date_to_datetime(date_value)

        if fecha:
            hoy = datetime.now()
            delta = hoy - fecha
            return delta.days
        return None
    except:
        return None


def format_time_elapsed(days):
    """Formatea tiempo transcurrido en formato legible."""
    if days is None or days < 0:
        return "Fecha inválida"

    if days == 0:
        return "Hoy"
    elif days == 1:
        return "Ayer"
    elif days < 7:
        return f"{days} días"
    elif days < 30:
        semanas = days // 7
        return f"{semanas} semana{'s' if semanas > 1 else ''}"
    elif days < 365:
        meses = days // 30
        return f"{meses} mes{'es' if meses > 1 else ''}"
    else:
        años = days // 365
        return f"{años} año{'s' if años > 1 else ''}"


# ===== CARGA DE LISTA COMPLETA - SIMPLIFICADO =====


def load_complete_veredas_list_authoritative(data_dir=None):
    """
    Carga la lista completa de veredas desde BD_positivos.xlsx hoja "VEREDAS"
    SIMPLIFICADO - sin normalización compleja
    """
    logger.info("🗂️ Cargando hoja VEREDAS - SIMPLIFICADO")

    # Rutas posibles para el archivo
    possible_paths = []

    if data_dir:
        possible_paths.append(Path(data_dir) / "BD_positivos.xlsx")

    # Rutas por defecto
    default_paths = [
        Path("data") / "BD_positivos.xlsx",
        Path("BD_positivos.xlsx"),
        Path("..") / "BD_positivos.xlsx",
    ]
    possible_paths.extend(default_paths)

    veredas_df = None

    # Intentar cargar desde cada ruta posible
    for path in possible_paths:
        if path.exists():
            try:
                logger.info(f"📁 Intentando cargar desde: {path}")

                # Verificar que la hoja "VEREDAS" existe
                excel_file = pd.ExcelFile(path)

                if "VEREDAS" in excel_file.sheet_names:
                    veredas_df = pd.read_excel(
                        path, sheet_name="VEREDAS", engine="openpyxl"
                    )
                    logger.info(f"✅ Hoja VEREDAS cargada desde {path}")
                    break
                else:
                    logger.warning(f"⚠️ Hoja 'VEREDAS' no encontrada en {path}")
                    logger.info(f"📋 Hojas disponibles: {excel_file.sheet_names}")

            except Exception as e:
                logger.warning(f"⚠️ Error cargando {path}: {str(e)}")
                continue

    if veredas_df is None:
        logger.error("❌ NO se pudo cargar hoja VEREDAS")
        return create_emergency_fallback()

    # Procesar DataFrame de veredas SIMPLIFICADO
    return process_veredas_dataframe_simple(veredas_df)


def process_veredas_dataframe_simple(veredas_df):
    """
    Procesa el DataFrame de veredas SIMPLIFICADO - sin normalización compleja
    """
    logger.info(f"🔧 Procesando hoja VEREDAS SIMPLIFICADO: {len(veredas_df)} registros")

    # Limpiar datos básicos
    veredas_df = veredas_df.dropna(how="all")
    veredas_df.columns = veredas_df.columns.str.strip()

    # Verificar columnas requeridas
    required_columns = ["municipi_1", "vereda_nor"]
    missing_columns = [col for col in required_columns if col not in veredas_df.columns]

    if missing_columns:
        logger.error(f"❌ Columnas faltantes en hoja VEREDAS: {missing_columns}")
        logger.info(f"📋 Columnas disponibles: {list(veredas_df.columns)}")
        return create_emergency_fallback()

    # Limpiar datos - solo espacios
    veredas_df = veredas_df[
        (veredas_df["municipi_1"].notna())
        & (veredas_df["vereda_nor"].notna())
        & (veredas_df["municipi_1"].str.strip() != "")
        & (veredas_df["vereda_nor"].str.strip() != "")
    ]

    # Solo limpiar espacios
    veredas_df["municipi_1"] = veredas_df["municipi_1"].str.strip()
    veredas_df["vereda_nor"] = veredas_df["vereda_nor"].str.strip()

    # Crear estructuras de datos usando nombres exactos
    veredas_por_municipio = {}
    municipios_authoritativos = sorted(veredas_df["municipi_1"].unique())

    for municipio in municipios_authoritativos:
        veredas_municipio = veredas_df[veredas_df["municipi_1"] == municipio]
        veredas_lista = sorted(veredas_municipio["vereda_nor"].unique())
        veredas_por_municipio[municipio] = veredas_lista

    # Crear mapeo display (nombres exactos = nombres display)
    municipio_display_map = {
        municipio: municipio for municipio in municipios_authoritativos
    }
    vereda_display_map = {}

    for _, row in veredas_df.iterrows():
        municipio = row["municipi_1"]
        vereda = row["vereda_nor"]
        vereda_key = f"{municipio}|{vereda}"
        vereda_display_map[vereda_key] = vereda

    # Extraer regiones si están disponibles
    regiones = {}
    if "region" in veredas_df.columns:
        regiones = get_regiones_from_dataframe_simple(veredas_df)

    logger.info(
        f"✅ HOJA VEREDAS procesada SIMPLIFICADO: {len(municipios_authoritativos)} municipios, {len(veredas_df)} veredas"
    )

    return {
        "veredas_por_municipio": veredas_por_municipio,
        "municipios_authoritativos": municipios_authoritativos,
        "veredas_completas": veredas_df,
        "municipio_display_map": municipio_display_map,
        "vereda_display_map": vereda_display_map,
        "regiones": regiones,
        "source": "hoja_veredas_simple",
    }


def get_regiones_from_dataframe_simple(veredas_df):
    """Extrae información de regiones del DataFrame SIMPLIFICADO."""
    if "region" not in veredas_df.columns:
        return {}

    regiones = {}

    for region in veredas_df["region"].dropna().unique():
        municipios_region = veredas_df[veredas_df["region"] == region][
            "municipi_1"
        ].unique()
        regiones[region] = sorted(municipios_region)

    logger.info(f"🗺️ Regiones extraídas: {list(regiones.keys())}")
    return regiones


def create_emergency_fallback():
    """Fallback de emergencia si no se puede cargar hoja VEREDAS."""
    logger.error("🚨 USANDO FALLBACK DE EMERGENCIA")

    # Lista mínima de municipios (nombres como están en shapefiles)
    municipios_emergency = [
        "IBAGUE",
        "ALPUJARRA",
        "ALVARADO",
        "AMBALEMA",
        "ANZOATEGUI",
        "ARMERO",
        "ATACO",
        "CAJAMARCA",
        "CARMEN DE APICALA",
        "CASABIANCA",
        "CHAPARRAL",
        "COELLO",
        "COYAIMA",
        "CUNDAY",
        "DOLORES",
        "ESPINAL",
        "FALAN",
        "FLANDES",
        "FRESNO",
        "GUAMO",
        "HERVEO",
        "HONDA",
        "ICONONZO",
        "LERIDA",
        "LIBANO",
        "MARIQUITA",
        "MELGAR",
        "MURILLO",
        "NATAGAIMA",
        "ORTEGA",
        "PALOCABILDO",
        "PIEDRAS",
        "PLANADAS",
        "PRADO",
        "PURIFICACION",
        "RIOBLANCO",
        "RONCESVALLES",
        "ROVIRA",
        "SALDANA",
        "SAN ANTONIO",
        "SAN LUIS",
        "SANTA ISABEL",
        "SUAREZ",
        "VALLE DE SAN JUAN",
        "VENADILLO",
        "VILLAHERMOSA",
        "VILLARRICA",
    ]

    veredas_por_municipio = {}
    municipio_display_map = {}

    for municipio in municipios_emergency:
        veredas_por_municipio[municipio] = [f"{municipio} CENTRO"]
        municipio_display_map[municipio] = municipio

    return {
        "veredas_por_municipio": veredas_por_municipio,
        "municipios_authoritativos": municipios_emergency,
        "veredas_completas": pd.DataFrame(),
        "municipio_display_map": municipio_display_map,
        "vereda_display_map": {},
        "regiones": {},
        "source": "emergency_fallback",
    }


def process_complete_data_structure_authoritative(
    casos_df, epizootias_df, shapefile_data=None, data_dir=None, veredas_data=None
):
    """
    Función principal que procesa datos SIMPLIFICADO - sin normalización compleja
    MODIFICADA: Ahora acepta veredas_data desde Google Drive como parámetro
    """
    logger.info("🚀 Procesando estructura SIMPLIFICADO")

    # Procesar DataFrames básicos
    casos_processed = process_casos_dataframe(casos_df)
    epizootias_processed = process_epizootias_dataframe(epizootias_df)

    # ✅ NUEVA LÓGICA: Cargar datos de hoja VEREDAS
    if veredas_data is not None:
        # Usar datos de veredas pasados como parámetro (desde Google Drive)
        logger.info("✅ Usando datos de veredas desde Google Drive")
        veredas_data_processed = veredas_data
    else:
        # Cargar desde archivo local (comportamiento original)
        logger.info("📁 Cargando datos de veredas desde archivo local")
        veredas_data_processed = load_complete_veredas_list_authoritative(data_dir)

    # Validación de datos SIMPLIFICADA
    validation_report = validate_data_simple(
        casos_processed,
        epizootias_processed,
        veredas_data_processed.get("municipios_authoritativos", []),
    )

    # Obtener ubicaciones de los datos actuales SIN NORMALIZACIÓN COMPLEJA
    ubicaciones_actuales = get_unique_locations_simple(
        casos_processed, epizootias_processed
    )

    # USAR HOJA VEREDAS como base, complementar con datos actuales
    municipios_authoritativos = veredas_data_processed.get(
        "municipios_authoritativos", []
    )
    veredas_por_municipio = veredas_data_processed.get(
        "veredas_por_municipio", {}
    ).copy()

    # Agregar municipios adicionales si existen
    municipios_adicionales = []
    for municipio in ubicaciones_actuales["municipios"]:
        if municipio not in municipios_authoritativos:
            municipios_adicionales.append(municipio)
            if municipio not in veredas_por_municipio:
                veredas_por_municipio[municipio] = [f"{municipio} CENTRO"]

    # Agregar veredas adicionales
    for municipio, veredas_data_current in ubicaciones_actuales[
        "veredas_por_municipio"
    ].items():
        if municipio in veredas_por_municipio:
            veredas_existentes = set(veredas_por_municipio[municipio])
            veredas_nuevas = set(veredas_data_current)
            veredas_adicionales = veredas_nuevas - veredas_existentes

            if veredas_adicionales:
                logger.info(
                    f"➕ Veredas adicionales para {municipio}: {list(veredas_adicionales)}"
                )
                veredas_por_municipio[municipio].extend(sorted(veredas_adicionales))

    # Crear lista final de municipios
    municipios_finales = sorted(set(municipios_authoritativos + municipios_adicionales))

    # Crear mapeos display
    municipio_display_map = veredas_data_processed.get(
        "municipio_display_map", {}
    ).copy()
    for municipio in municipios_adicionales:
        municipio_display_map[municipio] = municipio

    # ✅ VERIFICAR QUE TENEMOS DATOS REALES DE VEREDAS
    data_source = veredas_data_processed.get("source", "unknown")
    if data_source == "emergency_fallback":
        logger.warning(
            "⚠️ Usando datos de emergencia fallback - hoja VEREDAS no disponible"
        )
    else:
        logger.info(f"✅ Usando datos reales de hoja VEREDAS: {data_source}")

    # Resultado final
    resultado = {
        "casos": casos_processed,
        "epizootias": epizootias_processed,
        "municipios_normalizados": municipios_finales,
        "municipios_authoritativos": municipios_authoritativos,
        "veredas_por_municipio": veredas_por_municipio,  # ✅ Ahora poblado con datos reales
        "municipio_display_map": municipio_display_map,
        "vereda_display_map": veredas_data_processed.get("vereda_display_map", {}),
        "veredas_completas": veredas_data_processed.get(
            "veredas_completas", pd.DataFrame()
        ),
        "regiones": veredas_data_processed.get("regiones", {}),
        "validation_report": validation_report,
        "data_source": data_source,  # ✅ Esto será "hoja_veredas_simple" en lugar de "emergency_fallback"
    }

    # Agregar funciones de manejo simplificadas
    resultado["handle_empty_area"] = handle_empty_area_filter_simple
    resultado["validate_location"] = (
        lambda municipio, vereda: validate_location_exists_simple(
            municipio, vereda, resultado
        )
    )

    logger.info(f"✅ Estructura SIMPLIFICADA completada con {data_source}")
    logger.info(
        f"📊 {len(municipios_finales)} municipios, {sum(len(v) for v in veredas_por_municipio.values())} veredas"
    )

    return resultado


def validate_data_simple(casos_df, epizootias_df, municipios_authoritativos):
    """Validación simplificada de datos."""
    reporte = {
        "municipios_casos_invalidos": [],
        "municipios_epizootias_invalidos": [],
        "municipios_casos_validos": [],
        "municipios_epizootias_validos": [],
        "total_casos_validados": 0,
        "total_epizootias_validadas": 0,
    }

    # Validar municipios en casos
    if not casos_df.empty and "municipio" in casos_df.columns:
        municipios_casos = casos_df["municipio"].dropna().unique()

        for municipio in municipios_casos:
            if municipio in municipios_authoritativos:
                reporte["municipios_casos_validos"].append(municipio)
            else:
                reporte["municipios_casos_invalidos"].append(municipio)

        reporte["total_casos_validados"] = len(reporte["municipios_casos_validos"])

    # Validar municipios en epizootias
    if not epizootias_df.empty and "municipio" in epizootias_df.columns:
        municipios_epizootias = epizootias_df["municipio"].dropna().unique()

        for municipio in municipios_epizootias:
            if municipio in municipios_authoritativos:
                reporte["municipios_epizootias_validos"].append(municipio)
            else:
                reporte["municipios_epizootias_invalidos"].append(municipio)

        reporte["total_epizootias_validadas"] = len(
            reporte["municipios_epizootias_validos"]
        )

    return reporte


def get_unique_locations_simple(casos_df, epizootias_df):
    """Obtiene ubicaciones únicas SIMPLIFICADO - comparación directa."""
    locations = {"municipios": set(), "veredas_por_municipio": {}}

    # Obtener municipios únicos
    if "municipio" in casos_df.columns:
        municipios_casos = casos_df["municipio"].dropna().unique()
        locations["municipios"].update(municipios_casos)

    if "municipio" in epizootias_df.columns:
        municipios_epizootias = epizootias_df["municipio"].dropna().unique()
        locations["municipios"].update(municipios_epizootias)

    locations["municipios"] = sorted(list(locations["municipios"]))

    # Obtener veredas por municipio
    for municipio in locations["municipios"]:
        veredas = set()

        if "vereda" in casos_df.columns:
            veredas_casos = (
                casos_df[casos_df["municipio"] == municipio]["vereda"].dropna().unique()
            )
            veredas.update(veredas_casos)

        if "vereda" in epizootias_df.columns:
            veredas_epi = (
                epizootias_df[epizootias_df["municipio"] == municipio]["vereda"]
                .dropna()
                .unique()
            )
            veredas.update(veredas_epi)

        locations["veredas_por_municipio"][municipio] = sorted(list(veredas))

    return locations


def handle_empty_area_filter_simple(
    municipio=None, vereda=None, casos_df=None, epizootias_df=None
):
    """
    Maneja el filtrado de áreas sin datos SIMPLIFICADO - comparación directa
    """
    logger.info(f"🎯 Manejando filtro área sin datos SIMPLE: {municipio}, {vereda}")

    # Inicializar DataFrames vacíos si no se proporcionan
    if casos_df is None:
        casos_df = pd.DataFrame()
    if epizootias_df is None:
        epizootias_df = pd.DataFrame()

    # Aplicar filtros
    casos_filtrados = casos_df.copy() if not casos_df.empty else pd.DataFrame()
    epizootias_filtradas = (
        epizootias_df.copy() if not epizootias_df.empty else pd.DataFrame()
    )

    # Filtrar por municipio si se especifica
    if municipio and municipio != "Todos":
        if not casos_filtrados.empty and "municipio" in casos_filtrados.columns:
            casos_filtrados = casos_filtrados[casos_filtrados["municipio"] == municipio]
        else:
            casos_filtrados = pd.DataFrame()

        if (
            not epizootias_filtradas.empty
            and "municipio" in epizootias_filtradas.columns
        ):
            epizootias_filtradas = epizootias_filtradas[
                epizootias_filtradas["municipio"] == municipio
            ]
        else:
            epizootias_filtradas = pd.DataFrame()

    # Filtrar por vereda si se especifica
    if vereda and vereda != "Todas":
        if not casos_filtrados.empty and "vereda" in casos_filtrados.columns:
            casos_filtrados = casos_filtrados[casos_filtrados["vereda"] == vereda]
        else:
            casos_filtrados = pd.DataFrame()

        if not epizootias_filtradas.empty and "vereda" in epizootias_filtradas.columns:
            epizootias_filtradas = epizootias_filtradas[
                epizootias_filtradas["vereda"] == vereda
            ]
        else:
            epizootias_filtradas = pd.DataFrame()

    # Crear métricas con ceros para áreas sin datos
    metrics_with_zeros = create_zero_metrics_for_area(municipio, vereda)

    # Registrar resultado
    total_casos = len(casos_filtrados)
    total_epizootias = len(epizootias_filtradas)

    if total_casos == 0 and total_epizootias == 0:
        logger.info(f"📊 Área sin datos - mostrando métricas en cero")
    else:
        logger.info(
            f"📊 Área con datos: {total_casos} casos, {total_epizootias} epizootias"
        )

    return {
        "casos": casos_filtrados,
        "epizootias": epizootias_filtradas,
        "tiene_datos": total_casos > 0 or total_epizootias > 0,
        "metrics_zero": metrics_with_zeros,
        "area_info": {
            "municipio": municipio,
            "vereda": vereda,
            "tipo": (
                "con_datos"
                if (total_casos > 0 or total_epizootias > 0)
                else "sin_datos"
            ),
        },
    }


def validate_location_exists_simple(municipio, vereda, complete_data):
    """
    Valida que una ubicación existe SIMPLIFICADO - comparación directa
    """
    # Validar municipio
    municipio_exists = False
    if complete_data.get("municipios_authoritativos"):
        municipio_exists = municipio in complete_data["municipios_authoritativos"]

    # Validar vereda
    vereda_exists = False
    suggestions = []

    if vereda and municipio_exists:
        veredas_municipio = complete_data.get("veredas_por_municipio", {}).get(
            municipio, []
        )
        vereda_exists = vereda in veredas_municipio

        if not vereda_exists and veredas_municipio:
            suggestions = [
                v for v in veredas_municipio if municipio.lower() in v.lower()
            ][:5]

    elif not municipio_exists and municipio:
        municipios_completos = complete_data.get("municipios_authoritativos", [])
        suggestions = [
            m for m in municipios_completos if municipio.lower() in m.lower()
        ][:5]

    return {
        "municipio_exists": municipio_exists,
        "vereda_exists": vereda_exists or not vereda,
        "suggestions": suggestions,
    }


def create_zero_metrics_for_area(municipio, vereda):
    """Crea métricas en cero para áreas sin datos."""
    return {
        "total_casos": 0,
        "fallecidos": 0,
        "vivos": 0,
        "letalidad": 0.0,
        "total_epizootias": 0,
        "epizootias_positivas": 0,
        "epizootias_en_estudio": 0,
        "positividad": 0.0,
        "municipios_con_casos": 0,
        "municipios_con_epizootias": 0,
        "ultimo_caso": {
            "existe": False,
            "ubicacion": f"{vereda or municipio or 'Área'} - Sin casos",
        },
        "ultima_epizootia_positiva": {
            "existe": False,
            "ubicacion": f"{vereda or municipio or 'Área'} - Sin epizootias",
        },
    }


# ===== FUNCIONES DE CÁLCULO MEJORADAS =====


def calculate_basic_metrics(casos_df, epizootias_df, handle_empty=True):
    """Calcula métricas básicas con manejo mejorado de datos vacíos."""
    logger.info(
        f"Calculando métricas: {len(casos_df)} casos, {len(epizootias_df)} epizootias"
    )

    if not isinstance(casos_df, pd.DataFrame):
        casos_df = pd.DataFrame()
    if not isinstance(epizootias_df, pd.DataFrame):
        epizootias_df = pd.DataFrame()

    # Si no hay datos y handle_empty está activado, retornar métricas en cero
    if handle_empty and casos_df.empty and epizootias_df.empty:
        return create_zero_metrics_for_area(None, None)

    metrics = {}

    # Métricas de casos
    metrics["total_casos"] = len(casos_df)

    if "condicion_final" in casos_df.columns and not casos_df.empty:
        fallecidos = (casos_df["condicion_final"] == "Fallecido").sum()
        vivos = (casos_df["condicion_final"] == "Vivo").sum()
        metrics["fallecidos"] = fallecidos
        metrics["vivos"] = vivos
        metrics["letalidad"] = (
            (fallecidos / len(casos_df) * 100) if len(casos_df) > 0 else 0
        )
    else:
        metrics["fallecidos"] = 0
        metrics["vivos"] = 0
        metrics["letalidad"] = 0

    # Información del último caso
    if not casos_df.empty:
        ultimo_caso = get_latest_case_info(
            casos_df, "fecha_inicio_sintomas", ["vereda", "municipio"]
        )
        metrics["ultimo_caso"] = ultimo_caso
    else:
        metrics["ultimo_caso"] = {"existe": False, "ubicacion": "Sin casos registrados"}

    # Métricas de epizootias
    metrics["total_epizootias"] = len(epizootias_df)

    if "descripcion" in epizootias_df.columns and not epizootias_df.empty:
        positivos = (epizootias_df["descripcion"] == "POSITIVO FA").sum()
        en_estudio = (epizootias_df["descripcion"] == "EN ESTUDIO").sum()

        metrics["epizootias_positivas"] = positivos
        metrics["epizootias_en_estudio"] = en_estudio
        metrics["positividad"] = (
            (positivos / len(epizootias_df) * 100) if len(epizootias_df) > 0 else 0
        )
    else:
        metrics["epizootias_positivas"] = 0
        metrics["epizootias_en_estudio"] = 0
        metrics["positividad"] = 0

    # Información de la última epizootia positiva
    if not epizootias_df.empty:
        epizootias_positivas = (
            epizootias_df[epizootias_df["descripcion"] == "POSITIVO FA"]
            if "descripcion" in epizootias_df.columns
            else pd.DataFrame()
        )
        ultima_epizootia = get_latest_case_info(
            epizootias_positivas, "fecha_notificacion", ["vereda", "municipio"]
        )
        metrics["ultima_epizootia_positiva"] = ultima_epizootia
    else:
        metrics["ultima_epizootia_positiva"] = {
            "existe": False,
            "ubicacion": "Sin epizootias registradas",
        }

    # Métricas geográficas
    if "municipio" in casos_df.columns and not casos_df.empty:
        metrics["municipios_con_casos"] = casos_df["municipio"].nunique()
    else:
        metrics["municipios_con_casos"] = 0

    if "municipio" in epizootias_df.columns and not epizootias_df.empty:
        metrics["municipios_con_epizootias"] = epizootias_df["municipio"].nunique()
    else:
        metrics["municipios_con_epizootias"] = 0

    return metrics


def get_latest_case_info(df, date_column, location_columns=None):
    """Obtiene información del caso más reciente con manejo mejorado."""
    if df.empty or date_column not in df.columns:
        return {
            "existe": False,
            "fecha": None,
            "ubicacion": "Sin datos",
            "dias_transcurridos": None,
            "tiempo_transcurrido": "Sin datos",
        }

    df_with_dates = df.dropna(subset=[date_column])

    if df_with_dates.empty:
        return {
            "existe": False,
            "fecha": None,
            "ubicacion": "Sin fechas válidas",
            "dias_transcurridos": None,
            "tiempo_transcurrido": "Sin fechas válidas",
        }

    latest_idx = df_with_dates[date_column].idxmax()
    latest_record = df_with_dates.loc[latest_idx]

    fecha = latest_record[date_column]
    dias = calculate_days_since(fecha)
    tiempo_transcurrido = format_time_elapsed(dias)

    ubicacion_parts = []
    if location_columns:
        for col in location_columns:
            if col in latest_record and pd.notna(latest_record[col]):
                ubicacion_parts.append(str(latest_record[col]))

    ubicacion = (
        " - ".join(ubicacion_parts) if ubicacion_parts else "Ubicación no especificada"
    )

    return {
        "existe": True,
        "fecha": fecha,
        "ubicacion": ubicacion,
        "dias_transcurridos": dias,
        "tiempo_transcurrido": tiempo_transcurrido,
    }


# ===== FUNCIONES DE PROCESAMIENTO (mantener las existentes) =====


def create_age_groups(ages):
    """Crea grupos de edad a partir de una serie de edades."""
    GRUPOS_EDAD = [
        {"min": 0, "max": 14, "label": "0-14 años"},
        {"min": 15, "max": 29, "label": "15-29 años"},
        {"min": 30, "max": 44, "label": "30-44 años"},
        {"min": 45, "max": 59, "label": "45-59 años"},
        {"min": 60, "max": 120, "label": "60+ años"},
    ]

    def classify_age(age):
        if pd.isna(age):
            return "No especificado"

        age = int(age) if not pd.isna(age) else 0

        for grupo in GRUPOS_EDAD:
            if grupo["min"] <= age <= grupo["max"]:
                return grupo["label"]

        return "No especificado"

    return ages.apply(classify_age)


def process_casos_dataframe(casos_df):
    """Procesa el dataframe de casos."""
    df_processed = casos_df.copy()

    # Procesar fechas
    if "fecha_inicio_sintomas" in df_processed.columns:
        df_processed["fecha_inicio_sintomas"] = df_processed[
            "fecha_inicio_sintomas"
        ].apply(excel_date_to_datetime)

    # Crear grupos de edad
    if "edad" in df_processed.columns:
        df_processed["grupo_edad"] = create_age_groups(df_processed["edad"])

    # Normalizar sexo
    if "sexo" in df_processed.columns:
        df_processed["sexo"] = (
            df_processed["sexo"]
            .str.upper()
            .replace({"M": "Masculino", "F": "Femenino"})
        )

    # Agregar año de inicio de síntomas
    if "fecha_inicio_sintomas" in df_processed.columns:
        df_processed["año_inicio"] = df_processed["fecha_inicio_sintomas"].dt.year

    return df_processed


def process_epizootias_dataframe(epizootias_df):
    """Procesa el dataframe de epizootias."""
    df_processed = epizootias_df.copy()

    # Procesar fechas
    if "fecha_notificacion" in df_processed.columns:
        df_processed["fecha_notificacion"] = df_processed["fecha_notificacion"].apply(
            excel_date_to_datetime
        )

    # Limpiar descripción
    if "descripcion" in df_processed.columns:
        df_processed["descripcion"] = (
            df_processed["descripcion"].str.upper().str.strip()
        )

    # Limpiar proveniente
    if "proveniente" in df_processed.columns:
        df_processed["proveniente"] = df_processed["proveniente"].str.strip()

    # Agregar año de recolección
    if "fecha_notificacion" in df_processed.columns:
        df_processed["año_notificacion"] = df_processed["fecha_notificacion"].dt.year

    # Categorizar resultados
    if "descripcion" in df_processed.columns:
        df_processed["categoria_resultado"] = (
            df_processed["descripcion"]
            .map(
                {
                    "POSITIVO FA": "Positivo",
                    "NEGATIVO FA": "Negativo",
                    "NO APTA": "No apta",
                    "EN ESTUDIO": "En Estudio",
                }
            )
            .fillna("Otro")
        )

    return df_processed


def prepare_dataframe_for_display(df, date_columns=None):
    """Prepara DataFrame para mostrar."""
    if df.empty:
        return df

    df_display = df.copy()

    # Formatear columnas de fecha
    if date_columns:
        for col in date_columns:
            if col in df_display.columns:
                df_display[col] = df_display[col].apply(format_date_display)
    else:
        # Detectar automáticamente columnas de fecha
        for col in df_display.columns:
            if "fecha" in col.lower() and df_display[col].dtype == "datetime64[ns]":
                df_display[col] = df_display[col].apply(format_date_display)

    return df_display


# ===== FUNCIONES DE DEBUGGING SIMPLIFICADAS =====


def debug_data_flow(data_original, data_filtered, filters, stage="unknown"):
    """Debug simplificado del flujo de datos."""
    if isinstance(data_original, dict) and isinstance(data_filtered, dict):
        casos_orig = len(data_original.get("casos", []))
        epi_orig = len(data_original.get("epizootias", []))
        casos_filt = len(data_filtered.get("casos", []))
        epi_filt = len(data_filtered.get("epizootias", []))

        logger.info(
            f"Debug {stage}: Casos {casos_orig}→{casos_filt}, Epizootias {epi_orig}→{epi_filt}"
        )

        active_filters = (
            filters.get("active_filters", []) if isinstance(filters, dict) else []
        )
        if active_filters:
            logger.info(f"Filtros activos: {len(active_filters)}")


def verify_filtered_data_usage(data, context=""):
    """Verifica que se estén usando datos filtrados."""
    if data is None:
        logger.warning(f"⚠️ {context}: Datos nulos")
        return False

    total_rows = len(data)
    logger.debug(f"✅ {context}: {total_rows} registros")
    return True
