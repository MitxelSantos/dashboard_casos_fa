"""
Extractor de nombres autoritativos desde shapefiles del IGAC
Para crear la tabla maestra de referencia
"""

import geopandas as gpd
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extraer_nombres_autoritativos_shapefiles():
    """
    Extrae todos los nombres de municipios y veredas desde shapefiles del IGAC
    para crear la tabla maestra autoritativa
    """

    # Rutas donde están los shapefiles
    shapefile_paths = [
        "E:\\Proyectos\\dashboard_casos_fa\\data\processed\\tolima_municipios.shp",
        "E:\\Proyectos\\dashboard_casos_fa\\data\processed\\tolima_veredas.shp",
        ".\\shapefiles\\tolima_municipios.shp",
        ".\\shapefiles\\tolima_veredas.shp",
        ".\\data\\shapefiles\\tolima_municipios.shp",
        ".\\data\\shapefiles\\tolima_veredas.shp",
    ]

    nombres_autoritativos = {"municipios": set(), "veredas_por_municipio": {}}

    # 1. Extraer municipios
    municipios_gdf = None
    for path in shapefile_paths:
        if "municipios" in path and Path(path).exists():
            try:
                municipios_gdf = gpd.read_file(path)
                logger.info(f"✅ Municipios cargados desde: {path}")
                break
            except Exception as e:
                logger.warning(f"⚠️ Error en {path}: {e}")
                continue

    if municipios_gdf is not None:
        # Detectar columna de nombres de municipios
        columnas_posibles = [
            "municipi_1",
            "MpNombre",
            "NOMBRE_MUN",
            "nombre",
            "MUNICIPIO",
        ]
        columna_municipio = None

        for col in columnas_posibles:
            if col in municipios_gdf.columns:
                columna_municipio = col
                break

        if columna_municipio:
            municipios_unicos = municipios_gdf[columna_municipio].dropna().unique()
            nombres_autoritativos["municipios"] = set(municipios_unicos)
            logger.info(
                f"📍 {len(municipios_unicos)} municipios extraídos usando columna '{columna_municipio}'"
            )

            # Mostrar primeros municipios para verificación
            print("\n🏛️ MUNICIPIOS EXTRAÍDOS (primeros 10):")
            for i, municipio in enumerate(sorted(municipios_unicos)[:10]):
                print(f"  {i+1:2d}. {municipio}")
            print(f"  ... y {len(municipios_unicos)-10} más")
        else:
            logger.error("❌ No se encontró columna de municipios")
            print("Columnas disponibles:", list(municipios_gdf.columns))

    # 2. Extraer veredas
    veredas_gdf = None
    for path in shapefile_paths:
        if "veredas" in path and Path(path).exists():
            try:
                veredas_gdf = gpd.read_file(path)
                logger.info(f"✅ Veredas cargadas desde: {path}")
                break
            except Exception as e:
                logger.warning(f"⚠️ Error en {path}: {e}")
                continue

    if veredas_gdf is not None:
        # Detectar columnas de nombres
        columnas_municipio_veredas = [
            "municipi_1",
            "MpNombre",
            "NOMBRE_MUN",
            "municipio",
        ]
        columnas_vereda = ["vereda_nor", "NOMBRE_VER", "vereda", "nombre_vereda"]

        col_mun = None
        col_ver = None

        for col in columnas_municipio_veredas:
            if col in veredas_gdf.columns:
                col_mun = col
                break

        for col in columnas_vereda:
            if col in veredas_gdf.columns:
                col_ver = col
                break

        if col_mun and col_ver:
            # Agrupar veredas por municipio
            for municipio in veredas_gdf[col_mun].dropna().unique():
                veredas_municipio = (
                    veredas_gdf[veredas_gdf[col_mun] == municipio][col_ver]
                    .dropna()
                    .unique()
                )
                nombres_autoritativos["veredas_por_municipio"][municipio] = sorted(
                    veredas_municipio
                )

            total_veredas = sum(
                len(veredas)
                for veredas in nombres_autoritativos["veredas_por_municipio"].values()
            )
            logger.info(
                f"🏘️ {total_veredas} veredas extraídas usando columnas '{col_mun}' y '{col_ver}'"
            )

            # Mostrar ejemplo de veredas
            print(f"\n🏘️ EJEMPLO DE VEREDAS POR MUNICIPIO:")
            for i, (municipio, veredas) in enumerate(
                list(nombres_autoritativos["veredas_por_municipio"].items())[:3]
            ):
                print(f"  📍 {municipio}: {len(veredas)} veredas")
                for j, vereda in enumerate(veredas[:3]):
                    print(f"    {j+1}. {vereda}")
                if len(veredas) > 3:
                    print(f"    ... y {len(veredas)-3} más")
                print()
        else:
            logger.error("❌ No se encontraron columnas de veredas")
            print("Columnas disponibles:", list(veredas_gdf.columns))

    return nombres_autoritativos


def crear_tabla_maestra_referencia(nombres_autoritativos):
    """
    Crea tabla maestra de referencia para estandarización
    """

    print("\n" + "=" * 50)
    print("📋 CREANDO TABLA MAESTRA DE REFERENCIA")
    print("=" * 50)

    # 1. Tabla de municipios
    municipios_df = pd.DataFrame(
        {
            "MUNICIPIO_AUTORITATIVO": sorted(nombres_autoritativos["municipios"]),
            "VARIANTES_COMUNES": [""] * len(nombres_autoritativos["municipios"]),
            "NOTAS": [""] * len(nombres_autoritativos["municipios"]),
        }
    )

    # 2. Tabla de veredas
    veredas_rows = []
    for municipio, veredas in nombres_autoritativos["veredas_por_municipio"].items():
        for vereda in veredas:
            veredas_rows.append(
                {
                    "MUNICIPIO_AUTORITATIVO": municipio,
                    "VEREDA_AUTORITATIVA": vereda,
                    "VARIANTES_COMUNES": "",
                    "NOTAS": "",
                }
            )

    veredas_df = pd.DataFrame(veredas_rows)

    # 3. Guardar en Excel
    timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M")
    filename = f"tabla_maestra_autoritativa_{timestamp}.xlsx"

    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        municipios_df.to_excel(
            writer, sheet_name="MUNICIPIOS_AUTORITATIVOS", index=False
        )
        veredas_df.to_excel(writer, sheet_name="VEREDAS_AUTORITATIVAS", index=False)

        # Hoja de instrucciones
        instrucciones = pd.DataFrame(
            {
                "INSTRUCCIONES": [
                    "1. Esta es la TABLA MAESTRA AUTORITATIVA basada en shapefiles del IGAC",
                    "2. Los nombres en MUNICIPIO_AUTORITATIVO y VEREDA_AUTORITATIVA son los EXACTOS del shapefile",
                    "3. En VARIANTES_COMUNES anote las versiones que aparecen en los datos (separadas por ;)",
                    "4. Use esta tabla para estandarizar BD_positivos.xlsx e Información_Datos_FA.xlsx",
                    "5. SIEMPRE use los nombres autoritativos en futuras entradas de datos",
                    "",
                    "EJEMPLOS DE VARIANTES COMUNES:",
                    "IBAGUE -> IBAGUÉ",
                    "PURIFICACION -> PURIFICACIÓN",
                    "CARMEN DE APICALA -> CARMEN DE APICALÁ",
                    "",
                    f"Generado: {pd.Timestamp.now()}",
                    f"Total municipios: {len(municipios_df)}",
                    f"Total veredas: {len(veredas_df)}",
                ]
            }
        )
        instrucciones.to_excel(writer, sheet_name="INSTRUCCIONES", index=False)

    print(f"✅ Tabla maestra guardada en: {filename}")
    print(f"📊 {len(municipios_df)} municipios, {len(veredas_df)} veredas")

    return filename, municipios_df, veredas_df


def analizar_inconsistencias_actuales():
    """
    Analiza las inconsistencias en los datos actuales para facilitar la estandarización
    """

    print("\n" + "=" * 50)
    print("🔍 ANALIZANDO INCONSISTENCIAS ACTUALES")
    print("=" * 50)

    inconsistencias = {
        "municipios_casos": set(),
        "municipios_epizootias": set(),
        "veredas_casos": set(),
        "veredas_epizootias": set(),
    }

    # Cargar datos actuales
    data_paths = [
        ("data/BD_positivos.xlsx", "ACUMU"),
        ("BD_positivos.xlsx", "ACUMU"),
        ("data/Información_Datos_FA.xlsx", "Base de Datos"),
        ("Información_Datos_FA.xlsx", "Base de Datos"),
    ]

    casos_df = None
    epizootias_df = None

    # Cargar casos
    for path, sheet in data_paths[:2]:
        if Path(path).exists():
            try:
                casos_df = pd.read_excel(path, sheet_name=sheet, engine="openpyxl")
                print(f"✅ Casos cargados desde: {path}")
                break
            except Exception as e:
                print(f"⚠️ Error cargando {path}: {e}")

    # Cargar epizootias
    for path, sheet in data_paths[2:]:
        if Path(path).exists():
            try:
                epizootias_df = pd.read_excel(path, sheet_name=sheet, engine="openpyxl")
                print(f"✅ Epizootias cargadas desde: {path}")
                break
            except Exception as e:
                print(f"⚠️ Error cargando {path}: {e}")

    # Extraer nombres únicos
    if casos_df is not None:
        # Mapear columnas comunes
        municipio_cols = ["nmun_proce", "municipio", "MUNICIPIO"]
        vereda_cols = ["vereda_", "vereda", "VEREDA"]

        for col in municipio_cols:
            if col in casos_df.columns:
                municipios_unicos = casos_df[col].dropna().unique()
                inconsistencias["municipios_casos"].update(municipios_unicos)
                print(f"📋 Municipios en casos ({col}): {len(municipios_unicos)}")
                break

        for col in vereda_cols:
            if col in casos_df.columns:
                veredas_unicas = casos_df[col].dropna().unique()
                inconsistencias["veredas_casos"].update(veredas_unicas)
                print(f"📋 Veredas en casos ({col}): {len(veredas_unicas)}")
                break

    if epizootias_df is not None:
        municipio_cols = ["MUNICIPIO", "municipio"]
        vereda_cols = ["VEREDA", "vereda"]

        for col in municipio_cols:
            if col in epizootias_df.columns:
                municipios_unicos = epizootias_df[col].dropna().unique()
                inconsistencias["municipios_epizootias"].update(municipios_unicos)
                print(f"📋 Municipios en epizootias ({col}): {len(municipios_unicos)}")
                break

        for col in vereda_cols:
            if col in epizootias_df.columns:
                veredas_unicas = epizootias_df[col].dropna().unique()
                inconsistencias["veredas_epizootias"].update(veredas_unicas)
                print(f"📋 Veredas en epizootias ({col}): {len(veredas_unicas)}")
                break

    return inconsistencias


if __name__ == "__main__":
    print("🚀 INICIANDO EXTRACCIÓN DE NOMBRES AUTORITATIVOS")
    print("=" * 60)

    # Paso 1: Extraer nombres de shapefiles
    nombres_autoritativos = extraer_nombres_autoritativos_shapefiles()

    if not nombres_autoritativos["municipios"]:
        print(
            "❌ No se pudieron extraer municipios. Verifique las rutas de shapefiles."
        )
        exit(1)

    # Paso 2: Crear tabla maestra
    filename, municipios_df, veredas_df = crear_tabla_maestra_referencia(
        nombres_autoritativos
    )

    # Paso 3: Analizar inconsistencias actuales
    inconsistencias = analizar_inconsistencias_actuales()

    print("\n" + "🎯 SIGUIENTES PASOS:")
    print("1. Abra el archivo:", filename)
    print(
        "2. Complete la columna VARIANTES_COMUNES con las versiones que encuentra en sus datos"
    )
    print("3. Use esta tabla para estandarizar sus archivos Excel")
    print("4. Ejecute el script de estandarización que proporcionaré a continuación")
