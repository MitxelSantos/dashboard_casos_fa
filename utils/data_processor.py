"""
utils/data_processor.py
"""

import pandas as pd
import numpy as np
import unicodedata
import re
import logging
from datetime import datetime
from pathlib import Path

from utils.name_normalizer import (
    normalize_name_robust,
    normalize_name_with_accents,
    normalize_name_for_display,
    match_name_fuzzy,
    validate_municipio_name,
    get_canonical_municipio_name,
    create_cross_reference_map,
    validate_data_consistency,
    debug_name_matching,
    log_normalization_stats,
    find_equivalent_names,
)

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


# ===== NUEVAS FUNCIONES: CARGA DE LISTA COMPLETA =====


def load_complete_veredas_list_authoritative(data_dir=None):
    """
    Carga la lista completa de veredas desde BD_positivos.xlsx hoja "VEREDAS"
    como FUENTE AUTORITATIVA.

    Args:
        data_dir: Directorio donde buscar el archivo (opcional)

    Returns:
        dict: Estructura completa con mapeo bidireccional
    """
    logger.info("🗂️ Cargando hoja VEREDAS como fuente AUTORITATIVA")

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
        logger.error("❌ NO se pudo cargar hoja VEREDAS - CRÍTICO")
        return create_emergency_fallback()

    # Procesar DataFrame de veredas como FUENTE AUTORITATIVA
    return process_veredas_dataframe_authoritative(veredas_df)


def process_veredas_dataframe_authoritative(veredas_df):
    """
    Procesa el DataFrame de veredas como FUENTE AUTORITATIVA.

    Expected columns: CODIGO_VER, NOM_DEP, municipi_1, vereda_nor, region
    """
    logger.info(
        f"🔧 Procesando hoja VEREDAS como AUTORITATIVA: {len(veredas_df)} registros"
    )

    # Limpiar datos básicos
    veredas_df = veredas_df.dropna(how="all")

    # Limpiar nombres de columnas
    veredas_df.columns = veredas_df.columns.str.strip()

    # Verificar columnas requeridas
    required_columns = ["municipi_1", "vereda_nor"]
    missing_columns = [col for col in required_columns if col not in veredas_df.columns]

    if missing_columns:
        logger.error(
            f"❌ Columnas CRÍTICAS faltantes en hoja VEREDAS: {missing_columns}"
        )
        logger.info(f"📋 Columnas disponibles: {list(veredas_df.columns)}")
        return create_emergency_fallback()

    # LIMPIAR datos pero NO normalizar (mantener nombres exactos de shapefiles)
    veredas_df = veredas_df[
        (veredas_df["municipi_1"].notna())
        & (veredas_df["vereda_nor"].notna())
        & (veredas_df["municipi_1"].str.strip() != "")
        & (veredas_df["vereda_nor"].str.strip() != "")
    ]

    # Limpiar espacios pero NO cambiar case
    veredas_df["municipi_1"] = veredas_df["municipi_1"].str.strip()
    veredas_df["vereda_nor"] = veredas_df["vereda_nor"].str.strip()

    # Crear estructuras de datos USANDO NOMBRES EXACTOS
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
        regiones = get_regiones_from_dataframe_authoritative(veredas_df)

    logger.info(
        f"✅ HOJA VEREDAS procesada: {len(municipios_authoritativos)} municipios, {len(veredas_df)} veredas"
    )

    return {
        "veredas_por_municipio": veredas_por_municipio,
        "municipios_authoritativos": municipios_authoritativos,  # NUEVA KEY
        "veredas_completas": veredas_df,
        "municipio_display_map": municipio_display_map,
        "vereda_display_map": vereda_display_map,
        "regiones": regiones,
        "source": "hoja_veredas_autoritativa",
    }


def create_emergency_fallback():
    """Fallback de emergencia si no se puede cargar hoja VEREDAS."""
    logger.error("🚨 USANDO FALLBACK DE EMERGENCIA - hoja VEREDAS no disponible")

    # Lista mínima de municipios (nombres como están en shapefiles)
    municipios_emergency = [
        "Ibague",
        "Alpujarra",
        "Alvarado",
        "Ambalema",
        "Anzoategui",
        "Armero",
        "Ataco",
        "Cajamarca",
        "Carmen de Apicala",
        "Casabianca",
        "Chaparral",
        "Coello",
        "Coyaima",
        "Cunday",
        "Dolores",
        "Espinal",
        "Falan",
        "Flandes",
        "Fresno",
        "Guamo",
        "Herveo",
        "Honda",
        "Icononzo",
        "Lerida",
        "Libano",
        "Mariquita",
        "Melgar",
        "Murillo",
        "Natagaima",
        "Ortega",
        "Palocabildo",
        "Piedras",
        "Planadas",
        "Prado",
        "Purificacion",
        "Rioblanco",
        "Roncesvalles",
        "Rovira",
        "Saldaña",
        "San Antonio",
        "San Luis",
        "Santa Isabel",
        "Suarez",
        "Valle de San Juan",
        "Venadillo",
        "Villahermosa",
        "Villarrica",
    ]

    veredas_por_municipio = {}
    municipio_display_map = {}

    for municipio in municipios_emergency:
        veredas_por_municipio[municipio] = [f"{municipio} Centro"]
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


def create_shapefile_to_veredas_mapping(shapefile_data, veredas_data):
    """
    Crea mapeo bidireccional entre nombres de shapefiles y hoja VEREDAS.

    Args:
        shapefile_data: GeoDataFrame con municipios del shapefile
        veredas_data: Dict con datos de hoja VEREDAS

    Returns:
        dict: Mapeo bidireccional
    """
    logger.info("🔗 Creando mapeo shapefile ↔ hoja VEREDAS")

    shapefile_names = []
    if "municipios" in shapefile_data and not shapefile_data["municipios"].empty:
        municipios_gdf = shapefile_data["municipios"]

        # Obtener nombres de municipios del shapefile
        if "municipi_1" in municipios_gdf.columns:
            shapefile_names = municipios_gdf["municipi_1"].dropna().unique().tolist()
        elif "MpNombre" in municipios_gdf.columns:
            shapefile_names = municipios_gdf["MpNombre"].dropna().unique().tolist()

    veredas_names = veredas_data.get("municipios_authoritativos", [])

    # Crear mapeo directo y detectar inconsistencias
    shapefile_to_veredas = {}
    veredas_to_shapefile = {}
    inconsistencias = []

    for shapefile_name in shapefile_names:
        shapefile_clean = shapefile_name.strip()

        # Buscar coincidencia exacta
        if shapefile_clean in veredas_names:
            shapefile_to_veredas[shapefile_clean] = shapefile_clean
            veredas_to_shapefile[shapefile_clean] = shapefile_clean
        else:
            # Buscar coincidencia similar (case-insensitive)
            found_match = False
            for veredas_name in veredas_names:
                if shapefile_clean.lower() == veredas_name.lower():
                    shapefile_to_veredas[shapefile_clean] = veredas_name
                    veredas_to_shapefile[veredas_name] = shapefile_clean
                    found_match = True
                    logger.info(
                        f"🔗 Mapeo automático: '{shapefile_clean}' → '{veredas_name}'"
                    )
                    break

            if not found_match:
                inconsistencias.append(
                    {
                        "shapefile": shapefile_clean,
                        "sugerencia": "Revisar hoja VEREDAS",
                        "tipo": "no_encontrado",
                    }
                )

    # Reportar inconsistencias
    if inconsistencias:
        logger.warning(f"⚠️ {len(inconsistencias)} inconsistencias detectadas:")
        for inconsistencia in inconsistencias:
            logger.warning(
                f"  - Shapefile: '{inconsistencia['shapefile']}' no encontrado en hoja VEREDAS"
            )

    logger.info(f"✅ Mapeo creado: {len(shapefile_to_veredas)} municipios mapeados")

    return {
        "shapefile_to_veredas": shapefile_to_veredas,
        "veredas_to_shapefile": veredas_to_shapefile,
        "inconsistencias": inconsistencias,
        "shapefile_names": shapefile_names,
        "veredas_names": veredas_names,
    }


def process_complete_data_structure_authoritative(
    casos_df, epizootias_df, shapefile_data=None, data_dir=None
):
    """
    Función principal que procesa datos usando hoja VEREDAS como AUTORITATIVA.
    ACTUALIZADA con normalización robusta para tildes.
    """
    logger.info("🚀 Procesando estructura con normalización robusta CORREGIDA")

    # Procesar DataFrames básicos
    casos_processed = process_casos_dataframe(casos_df)
    epizootias_processed = process_epizootias_dataframe(epizootias_df)

    # Cargar datos AUTHORITATIVOS de hoja VEREDAS
    veredas_data = load_complete_veredas_list_authoritative(data_dir)

    # NUEVA: Validar consistencia de datos
    validation_report = validate_data_consistency(
        casos_processed,
        epizootias_processed,
        veredas_data.get("municipios_authoritativos", []),
    )

    # Log de validación
    if validation_report["municipios_casos_invalidos"]:
        logger.warning(
            f"⚠️ Municipios problemáticos en casos: {validation_report['municipios_casos_invalidos']}"
        )

    if validation_report["municipios_epizootias_invalidos"]:
        logger.warning(
            f"⚠️ Municipios problemáticos en epizootias: {validation_report['municipios_epizootias_invalidos']}"
        )

    # Crear mapeo con shapefiles si están disponibles
    shapefile_mapping = {}
    if shapefile_data and veredas_data.get("municipios_authoritativos"):
        shapefile_mapping = create_enhanced_shapefile_mapping(
            shapefile_data, veredas_data
        )

    # Obtener ubicaciones de los datos actuales CON NORMALIZACIÓN ROBUSTA
    ubicaciones_actuales = get_unique_locations_normalized(
        casos_processed, epizootias_processed
    )

    # USAR HOJA VEREDAS como base, complementar con datos actuales
    municipios_authoritativos = veredas_data["municipios_authoritativos"]
    veredas_por_municipio = veredas_data["veredas_por_municipio"].copy()

    # NUEVO: Mapear municipios de datos actuales a nombres canónicos
    municipios_adicionales = []
    for municipio in ubicaciones_actuales["municipios"]:
        canonical = get_canonical_municipio_name(municipio)
        if canonical and canonical not in municipios_authoritativos:
            municipios_adicionales.append(canonical)
            if canonical not in veredas_por_municipio:
                veredas_por_municipio[canonical] = [f"{canonical} Centro"]
        elif not canonical:
            # Municipio no reconocido, mantener como está pero con warning
            logger.warning(
                f"⚠️ Municipio no reconocido: '{municipio}' - manteniendo como está"
            )
            municipios_adicionales.append(municipio)
            if municipio not in veredas_por_municipio:
                veredas_por_municipio[municipio] = [f"{municipio} Centro"]

    if municipios_adicionales:
        logger.info(f"➕ Municipios adicionales agregados: {municipios_adicionales}")

    # NUEVO: Mapear veredas con normalización robusta
    for municipio, veredas_data_current in ubicaciones_actuales[
        "veredas_por_municipio"
    ].items():
        canonical_municipio = get_canonical_municipio_name(municipio)
        target_municipio = canonical_municipio or municipio

        if target_municipio in veredas_por_municipio:
            veredas_existentes = set(veredas_por_municipio[target_municipio])
            veredas_nuevas = set(veredas_data_current)
            veredas_adicionales = veredas_nuevas - veredas_existentes

            if veredas_adicionales:
                logger.info(
                    f"➕ Veredas adicionales para {target_municipio}: {list(veredas_adicionales)}"
                )
                veredas_por_municipio[target_municipio].extend(
                    sorted(veredas_adicionales)
                )

    # Crear lista final de municipios
    municipios_finales = sorted(set(municipios_authoritativos + municipios_adicionales))

    # Crear mapeos display CON NORMALIZACIÓN PARA DISPLAY
    municipio_display_map = veredas_data["municipio_display_map"].copy()
    for municipio in municipios_adicionales:
        municipio_display_map[municipio] = normalize_name_for_display(municipio)

    # Resultado final
    resultado = {
        "casos": casos_processed,
        "epizootias": epizootias_processed,
        "municipios_normalizados": municipios_finales,
        "municipios_authoritativos": municipios_authoritativos,
        "veredas_por_municipio": veredas_por_municipio,
        "municipio_display_map": municipio_display_map,
        "vereda_display_map": veredas_data["vereda_display_map"],
        "veredas_completas": veredas_data["veredas_completas"],
        "regiones": veredas_data.get("regiones", {}),
        "shapefile_mapping": shapefile_mapping,
        "validation_report": validation_report,  # NUEVO: Incluir reporte de validación
        "data_source": "hoja_veredas_autoritativa_normalized",
    }

    # Agregar funciones de manejo mejoradas
    resultado["handle_empty_area"] = handle_empty_area_filter_normalized
    resultado["validate_location"] = (
        lambda municipio, vereda: validate_location_exists_normalized(
            municipio, vereda, resultado
        )
    )

    # NUEVO: Log de estadísticas de normalización
    log_normalization_stats(
        {"casos": casos_processed, "epizootias": epizootias_processed}
    )

    logger.info(f"✅ Estructura AUTORITATIVA con normalización robusta completada")
    logger.info(
        f"📊 {len(municipios_finales)} municipios, {sum(len(v) for v in veredas_por_municipio.values())} veredas"
    )

    return resultado


def create_enhanced_shapefile_mapping(shapefile_data, veredas_data):
    """
    Crea mapeo mejorado entre shapefiles y hoja VEREDAS usando normalización robusta.
    """
    logger.info("🔗 Creando mapeo mejorado shapefile ↔ hoja VEREDAS")

    shapefile_names = []
    if "municipios" in shapefile_data and not shapefile_data["municipios"].empty:
        municipios_gdf = shapefile_data["municipios"]

        # Obtener nombres de municipios del shapefile
        if "municipi_1" in municipios_gdf.columns:
            shapefile_names = municipios_gdf["municipi_1"].dropna().unique().tolist()
        elif "MpNombre" in municipios_gdf.columns:
            shapefile_names = municipios_gdf["MpNombre"].dropna().unique().tolist()

    veredas_names = veredas_data.get("municipios_authoritativos", [])

    # Usar función de mapeo robusta
    shapefile_mapping = create_cross_reference_map(shapefile_names, veredas_names)

    # Crear mapeo bidireccional
    veredas_to_shapefile = {v: k for k, v in shapefile_mapping.items()}

    # Agregar debug info
    inconsistencias = []
    for shapefile_name in shapefile_names:
        if shapefile_name not in shapefile_mapping:
            inconsistencias.append(
                {
                    "shapefile": shapefile_name,
                    "debug_info": debug_name_matching(
                        shapefile_name, veredas_names[0] if veredas_names else ""
                    ),
                    "tipo": "no_mapeado",
                }
            )

    resultado = {
        "shapefile_to_veredas": shapefile_mapping,
        "veredas_to_shapefile": veredas_to_shapefile,
        "inconsistencias": inconsistencias,
        "shapefile_names": shapefile_names,
        "veredas_names": veredas_names,
        "mapping_success_rate": (
            len(shapefile_mapping) / len(shapefile_names) if shapefile_names else 0
        ),
    }

    logger.info(
        f"✅ Mapeo mejorado: {len(shapefile_mapping)}/{len(shapefile_names)} éxito ({resultado['mapping_success_rate']:.1%})"
    )

    return resultado


def get_unique_locations_normalized(casos_df, epizootias_df):
    """
    Obtiene ubicaciones únicas usando normalización robusta.
    """
    locations = {"municipios": set(), "veredas_por_municipio": {}}

    # Obtener municipios únicos con normalización
    if "municipio" in casos_df.columns:
        municipios_casos = casos_df["municipio"].dropna().unique()
        for municipio in municipios_casos:
            canonical = get_canonical_municipio_name(municipio)
            if canonical:
                locations["municipios"].add(canonical)
            else:
                locations["municipios"].add(
                    municipio
                )  # Mantener original si no se encuentra canónico

    if "municipio" in epizootias_df.columns:
        municipios_epizootias = epizootias_df["municipio"].dropna().unique()
        for municipio in municipios_epizootias:
            canonical = get_canonical_municipio_name(municipio)
            if canonical:
                locations["municipios"].add(canonical)
            else:
                locations["municipios"].add(municipio)

    locations["municipios"] = sorted(list(locations["municipios"]))

    # Obtener veredas por municipio con normalización
    for municipio in locations["municipios"]:
        veredas = set()

        # Buscar veredas usando equivalencias
        equivalent_names = find_equivalent_names(municipio)

        if "vereda" in casos_df.columns:
            for equiv_name in equivalent_names:
                veredas_casos = (
                    casos_df[
                        casos_df["municipio"].apply(
                            lambda x: normalize_name_robust(x)
                            == normalize_name_robust(equiv_name)
                        )
                    ]["vereda"]
                    .dropna()
                    .unique()
                )
                veredas.update(veredas_casos)

        if "vereda" in epizootias_df.columns:
            for equiv_name in equivalent_names:
                veredas_epi = (
                    epizootias_df[
                        epizootias_df["municipio"].apply(
                            lambda x: normalize_name_robust(x)
                            == normalize_name_robust(equiv_name)
                        )
                    ]["vereda"]
                    .dropna()
                    .unique()
                )
                veredas.update(veredas_epi)

        locations["veredas_por_municipio"][municipio] = sorted(list(veredas))

    return locations


def handle_empty_area_filter_normalized(
    municipio=None, vereda=None, casos_df=None, epizootias_df=None
):
    """
    Maneja el filtrado de áreas sin datos con normalización robusta.
    """
    logger.info(
        f"🎯 Manejando filtro área sin datos con normalización: {municipio}, {vereda}"
    )

    # Inicializar DataFrames vacíos si no se proporcionan
    if casos_df is None:
        casos_df = pd.DataFrame()
    if epizootias_df is None:
        epizootias_df = pd.DataFrame()

    # Aplicar filtros usando normalización robusta
    casos_filtrados = casos_df.copy() if not casos_df.empty else pd.DataFrame()
    epizootias_filtradas = (
        epizootias_df.copy() if not epizootias_df.empty else pd.DataFrame()
    )

    # Filtrar por municipio si se especifica
    if municipio and municipio != "Todos":
        if not casos_filtrados.empty and "municipio" in casos_filtrados.columns:
            casos_filtrados = casos_filtrados[
                casos_filtrados["municipio"].apply(
                    lambda x: normalize_name_robust(x)
                    == normalize_name_robust(municipio)
                )
            ]
        else:
            casos_filtrados = pd.DataFrame()

        if (
            not epizootias_filtradas.empty
            and "municipio" in epizootias_filtradas.columns
        ):
            epizootias_filtradas = epizootias_filtradas[
                epizootias_filtradas["municipio"].apply(
                    lambda x: normalize_name_robust(x)
                    == normalize_name_robust(municipio)
                )
            ]
        else:
            epizootias_filtradas = pd.DataFrame()

    # Filtrar por vereda si se especifica
    if vereda and vereda != "Todas":
        if not casos_filtrados.empty and "vereda" in casos_filtrados.columns:
            casos_filtrados = casos_filtrados[
                casos_filtrados["vereda"].apply(
                    lambda x: normalize_name_robust(x) == normalize_name_robust(vereda)
                )
            ]
        else:
            casos_filtrados = pd.DataFrame()

        if not epizootias_filtradas.empty and "vereda" in epizootias_filtradas.columns:
            epizootias_filtradas = epizootias_filtradas[
                epizootias_filtradas["vereda"].apply(
                    lambda x: normalize_name_robust(x) == normalize_name_robust(vereda)
                )
            ]
        else:
            epizootias_filtradas = pd.DataFrame()

    # Crear métricas con ceros para áreas sin datos
    metrics_with_zeros = create_zero_metrics_for_area(municipio, vereda)

    # Registrar resultado
    total_casos = len(casos_filtrados)
    total_epizootias = len(epizootias_filtradas)

    if total_casos == 0 and total_epizootias == 0:
        logger.info(f"📊 Área sin datos (normalizado) - mostrando métricas en cero")
    else:
        logger.info(
            f"📊 Área con datos (normalizado): {total_casos} casos, {total_epizootias} epizootias"
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
            "normalization": "robust",
        },
    }


def validate_location_exists_normalized(municipio, vereda, complete_data):
    """
    Valida que una ubicación (municipio/vereda) existe usando normalización robusta.
    """
    # Validar municipio usando normalización robusta
    municipio_exists = validate_municipio_name(municipio) if municipio else True

    # Validar vereda usando normalización robusta
    vereda_exists = False
    suggestions = []

    if vereda and municipio_exists:
        veredas_municipio = complete_data.get("veredas_por_municipio", {})

        # Buscar municipio canónico
        canonical_municipio = get_canonical_municipio_name(municipio)
        target_municipio = canonical_municipio or municipio

        if target_municipio in veredas_municipio:
            veredas_disponibles = veredas_municipio[target_municipio]
            vereda_match = match_name_fuzzy(vereda, veredas_disponibles)
            vereda_exists = vereda_match is not None

            if not vereda_exists:
                # Sugerir veredas similares
                suggestions = find_similar_names_normalized(vereda, veredas_disponibles)

    elif not municipio_exists and municipio:
        # Sugerir municipios similares
        municipios_completos = complete_data.get("municipios_authoritativos", [])
        suggestions = find_similar_names_normalized(municipio, municipios_completos)

    return {
        "municipio_exists": municipio_exists,
        "vereda_exists": vereda_exists or not vereda,
        "suggestions": suggestions[:5],
        "normalization_used": True,
    }


def find_similar_names_normalized(target_name, name_list, max_suggestions=5):
    """
    Encuentra nombres similares usando normalización robusta.
    """
    if not target_name or not name_list:
        return []

    # Usar match_name_fuzzy para encontrar la mejor coincidencia
    best_match = match_name_fuzzy(target_name, name_list)

    if best_match:
        return [best_match]

    # Si no hay coincidencia fuzzy, usar distancia de edición simple
    return find_similar_names(target_name, name_list, max_suggestions)


# ===== PARTE 5: FUNCIÓN DE DEBUGGING =====


def debug_normalization_issue(municipio_input, veredas_data, shapefile_data=None):
    """
    Función de debugging específica para problemas de normalización.
    """
    logger.info(f"🔍 DEBUGGING NORMALIZACIÓN PARA: '{municipio_input}'")

    # Análisis del municipio de entrada
    normalized_input = normalize_name_robust(municipio_input)
    with_accents_input = normalize_name_with_accents(municipio_input)
    equivalents_input = find_equivalent_names(municipio_input)

    logger.info(f"  Input original: '{municipio_input}'")
    logger.info(f"  Normalizado sin tildes: '{normalized_input}'")
    logger.info(f"  Normalizado con tildes: '{with_accents_input}'")
    logger.info(f"  Equivalencias encontradas: {equivalents_input}")

    # Análisis contra hoja VEREDAS
    municipios_veredas = veredas_data.get("municipios_authoritativos", [])
    logger.info(f"  Municipios en hoja VEREDAS: {len(municipios_veredas)}")

    for municipio_vereda in municipios_veredas:
        if any(
            eq in find_equivalent_names(municipio_vereda) for eq in equivalents_input
        ):
            logger.info(
                f"  ✅ COINCIDENCIA ENCONTRADA: '{municipio_input}' ↔ '{municipio_vereda}'"
            )

            # Mostrar debug detallado
            debug_info = debug_name_matching(municipio_input, municipio_vereda)
            logger.info(f"  Debug detallado: {debug_info}")

            return municipio_vereda

    # Análisis contra shapefile si disponible
    if shapefile_data and "municipios" in shapefile_data:
        logger.info(f"  Analizando también contra shapefile...")
        # Agregar lógica similar para shapefile

    logger.warning(f"  ❌ NO SE ENCONTRÓ COINCIDENCIA PARA: '{municipio_input}'")
    return None


def get_regiones_from_dataframe_authoritative(veredas_df):
    """Extrae información de regiones del DataFrame AUTORITATIVO."""
    if "region" not in veredas_df.columns:
        return {}

    regiones = {}

    for region in veredas_df["region"].dropna().unique():
        municipios_region = veredas_df[veredas_df["region"] == region][
            "municipi_1"
        ].unique()
        regiones[region] = sorted(municipios_region)  # NO normalizar

    logger.info(f"🗺️ Regiones extraídas: {list(regiones.keys())}")
    return regiones


def create_fallback_veredas_structure():
    """Crea estructura de fallback cuando no se puede cargar la lista completa."""
    logger.warning("⚠️ Usando estructura de fallback para veredas")

    # Lista básica de municipios del Tolima
    municipios_tolima = [
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
        "SALDAÑA",
        "SAN ANTONIO",
        "SAN LUIS",
        "SANTA ISABEL",
        "SUAREZ",
        "VALLE DE SAN JUAN",
        "VENADILLO",
        "VILLAHERMOSA",
        "VILLARRICA",
    ]

    # Crear veredas básicas (placeholder)
    veredas_por_municipio = {}
    municipio_display_map = {}

    for municipio in municipios_tolima:
        veredas_por_municipio[municipio] = [f"{municipio} CENTRO"]
        municipio_display_map[municipio] = municipio

    return {
        "veredas_por_municipio": veredas_por_municipio,
        "municipios_completos": municipios_tolima,
        "veredas_completas": pd.DataFrame(),
        "municipio_display_map": municipio_display_map,
        "vereda_display_map": {},
        "regiones": {},
    }


# ===== NUEVAS FUNCIONES: MANEJO DE ÁREAS SIN DATOS =====


def handle_empty_area_filter(
    municipio=None, vereda=None, casos_df=None, epizootias_df=None
):
    """
    Maneja el filtrado de áreas sin datos, evitando bucles infinitos.

    Args:
        municipio: Nombre del municipio filtrado
        vereda: Nombre de la vereda filtrada
        casos_df: DataFrame de casos
        epizootias_df: DataFrame de epizootias

    Returns:
        dict: Datos filtrados con estructura consistente
    """
    logger.info(f"🎯 Manejando filtro área sin datos: {municipio}, {vereda}")

    def normalize_name(name):
        """
        Función de compatibilidad que usa el nuevo normalizador robusto.
        """
        return normalize_name_robust(name)

    # Inicializar DataFrames vacíos si no se proporcionan
    if casos_df is None:
        casos_df = pd.DataFrame()
    if epizootias_df is None:
        epizootias_df = pd.DataFrame()

    # Aplicar filtros y crear estructura consistente
    casos_filtrados = casos_df.copy() if not casos_df.empty else pd.DataFrame()
    epizootias_filtradas = (
        epizootias_df.copy() if not epizootias_df.empty else pd.DataFrame()
    )

    # Filtrar por municipio si se especifica
    if municipio and municipio != "Todos":
        municipio_norm = normalize_name(municipio)

        if not casos_filtrados.empty and "municipio" in casos_filtrados.columns:
            casos_filtrados = casos_filtrados[
                casos_filtrados["municipio"].apply(normalize_name) == municipio_norm
            ]
        else:
            casos_filtrados = pd.DataFrame()

        if (
            not epizootias_filtradas.empty
            and "municipio" in epizootias_filtradas.columns
        ):
            epizootias_filtradas = epizootias_filtradas[
                epizootias_filtradas["municipio"].apply(normalize_name)
                == municipio_norm
            ]
        else:
            epizootias_filtradas = pd.DataFrame()

    # Filtrar por vereda si se especifica
    if vereda and vereda != "Todas":
        vereda_norm = normalize_name(vereda)

        if not casos_filtrados.empty and "vereda" in casos_filtrados.columns:
            casos_filtrados = casos_filtrados[
                casos_filtrados["vereda"].apply(normalize_name) == vereda_norm
            ]
        else:
            casos_filtrados = pd.DataFrame()

        if not epizootias_filtradas.empty and "vereda" in epizootias_filtradas.columns:
            epizootias_filtradas = epizootias_filtradas[
                epizootias_filtradas["vereda"].apply(normalize_name) == vereda_norm
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


def validate_location_exists(municipio, vereda, complete_data):
    """
    Valida que una ubicación (municipio/vereda) existe en la lista completa.

    Args:
        municipio: Nombre del municipio
        vereda: Nombre de la vereda (opcional)
        complete_data: Datos completos de ubicaciones

    Returns:
        dict: {
            'municipio_exists': bool,
            'vereda_exists': bool,
            'suggestions': [lista_sugerencias]
        }
    """

    def normalize_name(name):
        """
        Función de compatibilidad que usa el nuevo normalizador robusto.
        """
        return normalize_name_robust(name)

    municipio_norm = normalize_name(municipio) if municipio else ""
    vereda_norm = normalize_name(vereda) if vereda else ""

    # Validar municipio
    municipio_exists = False
    if complete_data.get("municipios_completos"):
        municipio_exists = municipio_norm in complete_data["municipios_completos"]

    # Validar vereda
    vereda_exists = False
    suggestions = []

    if vereda and municipio_exists:
        veredas_municipio = complete_data.get("veredas_por_municipio", {}).get(
            municipio_norm, []
        )
        vereda_exists = vereda_norm in veredas_municipio

        if not vereda_exists and veredas_municipio:
            # Sugerir veredas similares
            suggestions = find_similar_names(vereda_norm, veredas_municipio)

    elif not municipio_exists and municipio:
        # Sugerir municipios similares
        municipios_completos = complete_data.get("municipios_completos", [])
        suggestions = find_similar_names(municipio_norm, municipios_completos)

    return {
        "municipio_exists": municipio_exists,
        "vereda_exists": vereda_exists or not vereda,  # True si no se especificó vereda
        "suggestions": suggestions[:5],  # Máximo 5 sugerencias
    }


def find_similar_names(target_name, name_list, max_suggestions=5):
    """Encuentra nombres similares usando distancia de edición simple."""
    if not target_name or not name_list:
        return []

    def simple_distance(s1, s2):
        """Distancia de edición simple."""
        if len(s1) < len(s2):
            return simple_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    # Calcular distancias y ordenar
    similarities = []
    for name in name_list:
        distance = simple_distance(target_name.lower(), name.lower())
        similarities.append((name, distance))

    # Ordenar por distancia y retornar los mejores
    similarities.sort(key=lambda x: x[1])
    return [
        name
        for name, distance in similarities[:max_suggestions]
        if distance < len(target_name)
    ]


# ===== FUNCIONES CORE DE CÁLCULO MEJORADAS =====


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
            epizootias_positivas, "fecha_recoleccion", ["vereda", "municipio"]
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


# ===== FUNCIONES DE INTEGRACIÓN =====


def integrate_complete_data_structure(casos_df, epizootias_df, data_dir=None):
    """
    Integra la estructura completa de datos con listas de municipios/veredas.

    Args:
        casos_df: DataFrame de casos
        epizootias_df: DataFrame de epizootias
        data_dir: Directorio para buscar archivos adicionales

    Returns:
        dict: Estructura de datos completa
    """
    logger.info("🔗 Integrando estructura completa de datos")

    # Cargar lista completa de veredas
    complete_veredas = load_complete_veredas_list_authoritative(data_dir)

    # Obtener ubicaciones de los datos actuales
    ubicaciones_actuales = get_unique_locations(casos_df, epizootias_df)

    # Combinar datos
    municipios_combinados = list(
        set(
            complete_veredas["municipios_completos"]
            + ubicaciones_actuales["municipios"]
        )
    )

    # Combinar veredas por municipio
    veredas_combinadas = complete_veredas["veredas_por_municipio"].copy()

    for municipio, veredas_actuales in ubicaciones_actuales[
        "veredas_por_municipio"
    ].items():
        if municipio in veredas_combinadas:
            # Combinar con veredas existentes
            veredas_existentes = set(veredas_combinadas[municipio])
            veredas_nuevas = set(veredas_actuales)
            veredas_combinadas[municipio] = sorted(
                veredas_existentes.union(veredas_nuevas)
            )
        else:
            # Municipio no estaba en lista completa
            veredas_combinadas[municipio] = sorted(veredas_actuales)

    # Asegurar que todos los municipios tengan al menos una vereda
    for municipio in municipios_combinados:
        if municipio not in veredas_combinadas or not veredas_combinadas[municipio]:
            veredas_combinadas[municipio] = [f"{municipio} CENTRO"]

    # Crear mapeos display
    municipio_display_map = complete_veredas["municipio_display_map"].copy()
    vereda_display_map = complete_veredas["vereda_display_map"].copy()

    # Agregar mapeos faltantes
    for municipio in municipios_combinados:
        if municipio not in municipio_display_map:
            municipio_display_map[municipio] = municipio

    resultado = {
        "casos": casos_df,
        "epizootias": epizootias_df,
        "municipios_normalizados": sorted(municipios_combinados),
        "veredas_por_municipio": veredas_combinadas,
        "municipio_display_map": municipio_display_map,
        "vereda_display_map": vereda_display_map,
        "veredas_completas": complete_veredas["veredas_completas"],
        "regiones": complete_veredas.get("regiones", {}),
        "data_source": "integrated",
    }

    logger.info(
        f"✅ Estructura integrada: {len(municipios_combinados)} municipios, {sum(len(v) for v in veredas_combinadas.values())} veredas"
    )

    return resultado


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
    if "fecha_recoleccion" in df_processed.columns:
        df_processed["fecha_recoleccion"] = df_processed["fecha_recoleccion"].apply(
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
    if "fecha_recoleccion" in df_processed.columns:
        df_processed["año_recoleccion"] = df_processed["fecha_recoleccion"].dt.year

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


def get_unique_locations(casos_df, epizootias_df):
    """Obtiene ubicaciones únicas de los datos."""
    locations = {"municipios": set(), "veredas_por_municipio": {}}

    # Obtener municipios únicos
    if "municipio" in casos_df.columns:
        locations["municipios"].update(casos_df["municipio"].dropna().unique())

    if "municipio" in epizootias_df.columns:
        locations["municipios"].update(epizootias_df["municipio"].dropna().unique())

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
