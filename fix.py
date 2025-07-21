"""
Estandarizador de datos usando la tabla maestra autoritativa
Corrige automáticamente los nombres en BD_positivos.xlsx e Información_Datos_FA.xlsx
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
import shutil
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataStandardizer:
    def __init__(self, tabla_maestra_path):
        """
        Inicializa el estandarizador con la tabla maestra

        Args:
            tabla_maestra_path: Ruta al archivo Excel con la tabla maestra
        """
        self.tabla_maestra_path = tabla_maestra_path
        self.mapeos = self._cargar_tabla_maestra()

    def _cargar_tabla_maestra(self):
        """Carga la tabla maestra y crea diccionarios de mapeo"""
        try:
            # Cargar las hojas
            municipios_df = pd.read_excel(
                self.tabla_maestra_path,
                sheet_name="MUNICIPIOS_AUTORITATIVOS",
                engine="openpyxl",
            )
            veredas_df = pd.read_excel(
                self.tabla_maestra_path,
                sheet_name="VEREDAS_AUTORITATIVAS",
                engine="openpyxl",
            )

            logger.info(
                f"✅ Tabla maestra cargada: {len(municipios_df)} municipios, {len(veredas_df)} veredas"
            )

            # Crear diccionarios de mapeo
            mapeos = {"municipios": {}, "veredas": {}}

            # Mapeo de municipios
            for _, row in municipios_df.iterrows():
                autoritativo = row["MUNICIPIO_AUTORITATIVO"]
                variantes = str(row.get("VARIANTES_COMUNES", "")).strip()

                # El nombre autoritativo se mapea a sí mismo
                mapeos["municipios"][autoritativo] = autoritativo

                # Agregar variantes si existen
                if variantes and variantes != "nan":
                    for variante in variantes.split(";"):
                        variante = variante.strip()
                        if variante:
                            mapeos["municipios"][variante] = autoritativo

            # Mapeo de veredas (incluye municipio para contexto)
            for _, row in veredas_df.iterrows():
                municipio = row["MUNICIPIO_AUTORITATIVO"]
                vereda_autoritativa = row["VEREDA_AUTORITATIVA"]
                variantes = str(row.get("VARIANTES_COMUNES", "")).strip()

                # Clave: municipio|vereda -> vereda autoritativa
                key_autoritativo = f"{municipio}|{vereda_autoritativa}"
                mapeos["veredas"][key_autoritativo] = vereda_autoritativa

                # Agregar variantes
                if variantes and variantes != "nan":
                    for variante in variantes.split(";"):
                        variante = variante.strip()
                        if variante:
                            key_variante = f"{municipio}|{variante}"
                            mapeos["veredas"][key_variante] = vereda_autoritativa

            logger.info(
                f"📊 Mapeos creados: {len(mapeos['municipios'])} municipios, {len(mapeos['veredas'])} veredas"
            )
            return mapeos

        except Exception as e:
            logger.error(f"❌ Error cargando tabla maestra: {e}")
            raise

    def _normalizar_nombre(self, nombre):
        """Normaliza un nombre para comparación"""
        if pd.isna(nombre):
            return ""
        return str(nombre).strip().upper()

    def _mapear_municipio(self, municipio_original):
        """Mapea un municipio a su versión autoritativa"""
        if pd.isna(municipio_original):
            return municipio_original

        municipio_norm = self._normalizar_nombre(municipio_original)

        # Buscar mapeo directo
        for variante, autoritativo in self.mapeos["municipios"].items():
            if self._normalizar_nombre(variante) == municipio_norm:
                if variante != autoritativo:
                    logger.debug(
                        f"🔄 Municipio: '{municipio_original}' -> '{autoritativo}'"
                    )
                return autoritativo

        # Si no se encuentra, devolver original
        logger.warning(
            f"⚠️ Municipio no encontrado en tabla maestra: '{municipio_original}'"
        )
        return municipio_original

    def _mapear_vereda(self, vereda_original, municipio_autoritativo):
        """Mapea una vereda a su versión autoritativa"""
        if pd.isna(vereda_original) or pd.isna(municipio_autoritativo):
            return vereda_original

        vereda_norm = self._normalizar_nombre(vereda_original)
        municipio_norm = self._normalizar_nombre(municipio_autoritativo)

        # Buscar mapeo con contexto de municipio
        for clave, vereda_autoritativa in self.mapeos["veredas"].items():
            municipio_clave, vereda_clave = clave.split("|", 1)

            if (
                self._normalizar_nombre(municipio_clave) == municipio_norm
                and self._normalizar_nombre(vereda_clave) == vereda_norm
            ):

                if vereda_clave != vereda_autoritativa:
                    logger.debug(
                        f"🔄 Vereda: '{vereda_original}' -> '{vereda_autoritativa}' ({municipio_autoritativo})"
                    )
                return vereda_autoritativa

        # Si no se encuentra, devolver original
        logger.warning(
            f"⚠️ Vereda no encontrada: '{vereda_original}' en '{municipio_autoritativo}'"
        )
        return vereda_original

    def estandarizar_casos(self, casos_path, backup=True):
        """
        Estandariza el archivo de casos

        Args:
            casos_path: Ruta al archivo BD_positivos.xlsx
            backup: Si crear backup antes de modificar
        """
        logger.info(f"🦠 Estandarizando casos: {casos_path}")

        if backup:
            backup_path = (
                f"{casos_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            shutil.copy2(casos_path, backup_path)
            logger.info(f"💾 Backup creado: {backup_path}")

        try:
            # Cargar todas las hojas
            excel_file = pd.ExcelFile(casos_path)
            hojas_modificadas = {}
            cambios_realizados = []

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(casos_path, sheet_name=sheet_name, engine="openpyxl")
                df_original = df.copy()

                # Detectar columnas de municipio y vereda
                col_municipio = None
                col_vereda = None

                municipio_cols = ["nmun_proce", "municipio", "MUNICIPIO", "municipi_1"]
                vereda_cols = ["vereda_", "vereda", "VEREDA", "vereda_nor"]

                for col in municipio_cols:
                    if col in df.columns:
                        col_municipio = col
                        break

                for col in vereda_cols:
                    if col in df.columns:
                        col_vereda = col
                        break

                # Estandarizar municipios
                if col_municipio:
                    df[col_municipio] = df[col_municipio].apply(self._mapear_municipio)

                    # Contar cambios
                    cambios_municipio = (
                        df_original[col_municipio] != df[col_municipio]
                    ).sum()
                    if cambios_municipio > 0:
                        cambios_realizados.append(
                            f"{sheet_name}: {cambios_municipio} municipios estandarizados"
                        )

                # Estandarizar veredas (después de municipios)
                if col_vereda and col_municipio:
                    for idx, row in df.iterrows():
                        municipio_autoritativo = row[col_municipio]
                        vereda_original = row[col_vereda]
                        vereda_estandarizada = self._mapear_vereda(
                            vereda_original, municipio_autoritativo
                        )
                        df.at[idx, col_vereda] = vereda_estandarizada

                    # Contar cambios en veredas
                    cambios_vereda = (df_original[col_vereda] != df[col_vereda]).sum()
                    if cambios_vereda > 0:
                        cambios_realizados.append(
                            f"{sheet_name}: {cambios_vereda} veredas estandarizadas"
                        )

                hojas_modificadas[sheet_name] = df

            # Guardar archivo modificado
            with pd.ExcelWriter(casos_path, engine="openpyxl") as writer:
                for sheet_name, df in hojas_modificadas.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

            logger.info(f"✅ Casos estandarizados exitosamente")
            for cambio in cambios_realizados:
                logger.info(f"  📊 {cambio}")

            return True, cambios_realizados

        except Exception as e:
            logger.error(f"❌ Error estandarizando casos: {e}")
            return False, [str(e)]

    def estandarizar_epizootias(self, epizootias_path, backup=True):
        """
        Estandariza el archivo de epizootias

        Args:
            epizootias_path: Ruta al archivo Información_Datos_FA.xlsx
            backup: Si crear backup antes de modificar
        """
        logger.info(f"🐒 Estandarizando epizootias: {epizootias_path}")

        if backup:
            backup_path = (
                f"{epizootias_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            shutil.copy2(epizootias_path, backup_path)
            logger.info(f"💾 Backup creado: {backup_path}")

        try:
            # Cargar todas las hojas
            excel_file = pd.ExcelFile(epizootias_path)
            hojas_modificadas = {}
            cambios_realizados = []

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(
                    epizootias_path, sheet_name=sheet_name, engine="openpyxl"
                )
                df_original = df.copy()

                # Detectar columnas
                col_municipio = None
                col_vereda = None

                municipio_cols = ["MUNICIPIO", "municipio", "municipi_1"]
                vereda_cols = ["VEREDA", "vereda", "vereda_nor"]

                for col in municipio_cols:
                    if col in df.columns:
                        col_municipio = col
                        break

                for col in vereda_cols:
                    if col in df.columns:
                        col_vereda = col
                        break

                # Estandarizar municipios
                if col_municipio:
                    df[col_municipio] = df[col_municipio].apply(self._mapear_municipio)

                    cambios_municipio = (
                        df_original[col_municipio] != df[col_municipio]
                    ).sum()
                    if cambios_municipio > 0:
                        cambios_realizados.append(
                            f"{sheet_name}: {cambios_municipio} municipios estandarizados"
                        )

                # Estandarizar veredas
                if col_vereda and col_municipio:
                    for idx, row in df.iterrows():
                        municipio_autoritativo = row[col_municipio]
                        vereda_original = row[col_vereda]
                        vereda_estandarizada = self._mapear_vereda(
                            vereda_original, municipio_autoritativo
                        )
                        df.at[idx, col_vereda] = vereda_estandarizada

                    cambios_vereda = (df_original[col_vereda] != df[col_vereda]).sum()
                    if cambios_vereda > 0:
                        cambios_realizados.append(
                            f"{sheet_name}: {cambios_vereda} veredas estandarizadas"
                        )

                hojas_modificadas[sheet_name] = df

            # Guardar archivo modificado
            with pd.ExcelWriter(epizootias_path, engine="openpyxl") as writer:
                for sheet_name, df in hojas_modificadas.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

            logger.info(f"✅ Epizootias estandarizadas exitosamente")
            for cambio in cambios_realizados:
                logger.info(f"  📊 {cambio}")

            return True, cambios_realizados

        except Exception as e:
            logger.error(f"❌ Error estandarizando epizootias: {e}")
            return False, [str(e)]

    def generar_reporte_estandarizacion(self, cambios_casos, cambios_epizootias):
        """Genera reporte de la estandarización realizada"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        reporte_path = f"reporte_estandarizacion_{timestamp}.txt"

        with open(reporte_path, "w", encoding="utf-8") as f:
            f.write("REPORTE DE ESTANDARIZACIÓN DE DATOS\n")
            f.write("=" * 50 + "\n")
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Tabla maestra utilizada: {self.tabla_maestra_path}\n\n")

            f.write("CAMBIOS EN CASOS:\n")
            f.write("-" * 20 + "\n")
            for cambio in cambios_casos:
                f.write(f"✅ {cambio}\n")
            if not cambios_casos:
                f.write("Sin cambios realizados\n")

            f.write("\nCAMBIOS EN EPIZOOTIAS:\n")
            f.write("-" * 20 + "\n")
            for cambio in cambios_epizootias:
                f.write(f"✅ {cambio}\n")
            if not cambios_epizootias:
                f.write("Sin cambios realizados\n")

            f.write(f"\nMAPEOS DISPONIBLES:\n")
            f.write("-" * 20 + "\n")
            f.write(f"Municipios: {len(self.mapeos['municipios'])} mapeos\n")
            f.write(f"Veredas: {len(self.mapeos['veredas'])} mapeos\n")

        logger.info(f"📄 Reporte generado: {reporte_path}")
        return reporte_path


def main():
    """Función principal de estandarización"""
    print("🚀 INICIANDO ESTANDARIZACIÓN DE DATOS")
    print("=" * 50)

    # 1. Buscar tabla maestra
    tabla_maestra_path = None
    posibles_tablas = list(Path(".").glob("tabla_maestra_autoritativa_*.xlsx"))

    if posibles_tablas:
        # Usar la más reciente
        tabla_maestra_path = max(posibles_tablas, key=lambda p: p.stat().st_mtime)
        print(f"📋 Tabla maestra encontrada: {tabla_maestra_path}")
    else:
        print(
            "❌ No se encontró tabla maestra. Ejecute primero el extractor de nombres."
        )
        return

    # 2. Inicializar estandarizador
    try:
        estandarizador = DataStandardizer(tabla_maestra_path)
    except Exception as e:
        print(f"❌ Error inicializando estandarizador: {e}")
        return

    # 3. Buscar archivos de datos
    archivos_datos = {"casos": None, "epizootias": None}

    # Buscar casos
    casos_paths = ["data/BD_positivos.xlsx", "BD_positivos.xlsx"]
    for path in casos_paths:
        if Path(path).exists():
            archivos_datos["casos"] = path
            break

    # Buscar epizootias
    epi_paths = ["data/Información_Datos_FA.xlsx", "Información_Datos_FA.xlsx"]
    for path in epi_paths:
        if Path(path).exists():
            archivos_datos["epizootias"] = path
            break

    if not archivos_datos["casos"]:
        print("⚠️ No se encontró BD_positivos.xlsx")
    if not archivos_datos["epizootias"]:
        print("⚠️ No se encontró Información_Datos_FA.xlsx")

    if not any(archivos_datos.values()):
        print("❌ No se encontraron archivos de datos para estandarizar")
        return

    # 4. Realizar estandarización
    cambios_casos = []
    cambios_epizootias = []

    if archivos_datos["casos"]:
        exito, cambios = estandarizador.estandarizar_casos(archivos_datos["casos"])
        if exito:
            cambios_casos = cambios
        else:
            print(f"❌ Error estandarizando casos: {cambios}")

    if archivos_datos["epizootias"]:
        exito, cambios = estandarizador.estandarizar_epizootias(
            archivos_datos["epizootias"]
        )
        if exito:
            cambios_epizootias = cambios
        else:
            print(f"❌ Error estandarizando epizootias: {cambios}")

    # 5. Generar reporte
    reporte_path = estandarizador.generar_reporte_estandarizacion(
        cambios_casos, cambios_epizootias
    )

    print("\n🎯 ESTANDARIZACIÓN COMPLETADA")
    print("=" * 30)
    print("✅ Sus datos ahora usan los nombres EXACTOS de los shapefiles del IGAC")
    print("✅ El sistema de normalización complejo ya no será necesario")
    print(f"📄 Revise el reporte: {reporte_path}")
    print("\n🔧 SIGUIENTES PASOS:")
    print("1. Simplifique el código eliminando el sistema de normalización")
    print("2. Para futuras entradas, use SIEMPRE los nombres de la tabla maestra")
    print("3. Si necesita agregar nuevas veredas, consúltelas en los shapefiles")


if __name__ == "__main__":
    main()
