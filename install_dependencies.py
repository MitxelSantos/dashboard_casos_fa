#!/usr/bin/env python3
"""
Instalador automático para el Dashboard de Fiebre Amarilla - Tolima v2.1
Simplificado para profesionales médicos.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
import pkg_resources

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Definir rutas
ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
ASSETS_DIR = ROOT_DIR / "assets"
IMAGES_DIR = ASSETS_DIR / "images"

# Dependencias requeridas
REQUIRED_PACKAGES = [
    "streamlit>=1.28.0",
    "pandas>=2.0.0",
    "numpy>=1.24.0",
    "plotly>=5.17.0",
    "openpyxl>=3.1.0",
    "Pillow>=10.0.0",
    "requests>=2.31.0",
]

# Archivos requeridos para funcionamiento
REQUIRED_FILES = {
    "BD_positivos.xlsx": "Archivo de casos confirmados (hoja: ACUMU)",
    "Información_Datos_FA.xlsx": "Archivo de epizootias (hoja: Base de Datos)",
}

# Archivos opcionales
OPTIONAL_FILES = {"Gobernacion.png": "Logo de la Gobernación del Tolima"}


def print_header():
    """Muestra el encabezado del instalador."""
    print("=" * 70)
    print("🏥 DASHBOARD FIEBRE AMARILLA - TOLIMA")
    print("    Instalador Automático v2.1")
    print("    Para Profesionales de la Salud")
    print("=" * 70)
    print()


def check_python_version():
    """Verifica la versión de Python."""
    logger.info("🔍 Verificando versión de Python...")

    if sys.version_info < (3, 8):
        logger.error("❌ Se requiere Python 3.8 o superior")
        logger.error(f"   Versión actual: {sys.version}")
        return False

    logger.info(f"✅ Python {sys.version.split()[0]} detectado")
    return True


def create_directories():
    """Crea las carpetas necesarias."""
    logger.info("📁 Creando estructura de carpetas...")

    directories = [DATA_DIR, ASSETS_DIR, IMAGES_DIR]

    for directory in directories:
        try:
            directory.mkdir(exist_ok=True)
            logger.info(f"✅ Carpeta creada/verificada: {directory.name}/")
        except Exception as e:
            logger.error(f"❌ Error creando {directory}: {e}")
            return False

    return True


def check_installed_packages():
    """Verifica qué paquetes están instalados."""
    logger.info("📦 Verificando dependencias instaladas...")

    installed = []
    missing = []

    for package in REQUIRED_PACKAGES:
        package_name = package.split(">=")[0]
        try:
            pkg_resources.get_distribution(package_name)
            installed.append(package_name)
            logger.info(f"✅ {package_name}")
        except pkg_resources.DistributionNotFound:
            missing.append(package)
            logger.warning(f"❌ {package_name} (no instalado)")

    return installed, missing


def install_missing_packages(missing_packages):
    """Instala los paquetes faltantes."""
    if not missing_packages:
        logger.info("✅ Todas las dependencias están instaladas")
        return True

    logger.info(f"📥 Instalando {len(missing_packages)} paquetes faltantes...")

    try:
        cmd = [sys.executable, "-m", "pip", "install"] + missing_packages

        logger.info("🔄 Ejecutando instalación...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            logger.info("✅ Todas las dependencias instaladas correctamente")
            return True
        else:
            logger.error("❌ Error en la instalación:")
            logger.error(result.stderr)
            return False

    except Exception as e:
        logger.error(f"❌ Error ejecutando pip: {e}")
        return False


def check_data_files():
    """Verifica la presencia de archivos de datos."""
    logger.info("📋 Verificando archivos de datos...")

    # Verificar archivos requeridos
    found_files = []
    missing_files = []

    for filename, description in REQUIRED_FILES.items():
        # Buscar en directorio raíz primero
        root_path = ROOT_DIR / filename
        data_path = DATA_DIR / filename

        if root_path.exists():
            found_files.append((filename, "raíz", description))
            logger.info(f"✅ {filename} (encontrado en raíz)")
        elif data_path.exists():
            found_files.append((filename, "data/", description))
            logger.info(f"✅ {filename} (encontrado en data/)")
        else:
            missing_files.append((filename, description))
            logger.warning(f"❌ {filename} (no encontrado)")

    # Verificar archivos opcionales
    for filename, description in OPTIONAL_FILES.items():
        root_path = ROOT_DIR / filename
        data_path = DATA_DIR / filename
        assets_path = IMAGES_DIR / filename

        if root_path.exists():
            logger.info(f"✅ {filename} (encontrado en raíz) - OPCIONAL")
        elif data_path.exists():
            logger.info(f"✅ {filename} (encontrado en data/) - OPCIONAL")
        elif assets_path.exists():
            logger.info(f"✅ {filename} (encontrado en assets/images/) - OPCIONAL")
        else:
            logger.info(f"ℹ️ {filename} (no encontrado) - OPCIONAL")

    return found_files, missing_files


def show_file_instructions(missing_files):
    """Muestra instrucciones para archivos faltantes."""
    if not missing_files:
        return

    print()
    print("📋 ARCHIVOS REQUERIDOS FALTANTES:")
    print("-" * 50)

    for filename, description in missing_files:
        print(f"❌ {filename}")
        print(f"   📝 {description}")
        print(f"   📁 Colocar en: {ROOT_DIR}/")
        print(f"        O en: {DATA_DIR}/")
        print()

    print("🎯 ESTRUCTURA RECOMENDADA:")
    print(
        f"""
    {ROOT_DIR.name}/
    ├── data/                          ← CREAR ESTA CARPETA
    │   ├── BD_positivos.xlsx         ← Casos confirmados
    │   ├── Información_Datos_FA.xlsx ← Epizootias  
    │   └── Gobernacion.png           ← Logo (opcional)
    ├── app.py
    └── requirements.txt
    """
    )


def test_imports():
    """Prueba las importaciones principales."""
    logger.info("🧪 Probando importaciones...")

    test_modules = [
        ("streamlit", "st"),
        ("pandas", "pd"),
        ("numpy", "np"),
        ("plotly.express", "px"),
        ("openpyxl", None),
        ("PIL", "Image"),
    ]

    failed_imports = []

    for module_name, alias in test_modules:
        try:
            if alias:
                exec(f"import {module_name} as {alias}")
            else:
                exec(f"import {module_name}")
            logger.info(f"✅ {module_name}")
        except ImportError as e:
            failed_imports.append(module_name)
            logger.error(f"❌ {module_name}: {e}")

    return len(failed_imports) == 0


def show_next_steps(found_files, missing_files):
    """Muestra los próximos pasos."""
    print()
    print("🚀 PRÓXIMOS PASOS:")
    print("-" * 30)

    if missing_files:
        print("1. ❌ Coloque los archivos de datos faltantes")
        print("2. 🔄 Ejecute nuevamente este instalador")
        print("3. ▶️ Ejecute: streamlit run app.py")
    else:
        print("1. ✅ Todos los archivos están listos")
        print("2. ▶️ Ejecute: streamlit run app.py")
        print("3. 🌐 Abra el navegador en: http://localhost:8501")

    print()
    print("💡 COMANDOS ÚTILES:")
    print("   🔄 Actualizar datos: python install_dependencies.py")
    print("   ▶️ Ejecutar dashboard: streamlit run app.py")
    print("   🛑 Detener dashboard: Ctrl+C")


def main():
    """Función principal del instalador."""
    print_header()

    # Verificar Python
    if not check_python_version():
        return False

    print()

    # Crear directorios
    if not create_directories():
        logger.error("❌ Error creando carpetas")
        return False

    print()

    # Verificar e instalar dependencias
    installed, missing = check_installed_packages()

    if missing:
        print()
        install_success = install_missing_packages(missing)
        if not install_success:
            logger.error("❌ Error instalando dependencias")
            return False

    print()

    # Probar importaciones
    if not test_imports():
        logger.error("❌ Error en las importaciones")
        return False

    print()

    # Verificar archivos de datos
    found_files, missing_files = check_data_files()

    # Mostrar instrucciones si faltan archivos
    if missing_files:
        show_file_instructions(missing_files)

    # Mostrar próximos pasos
    show_next_steps(found_files, missing_files)

    print()
    print("=" * 70)
    if missing_files:
        print("⚠️  INSTALACIÓN PARCIAL COMPLETADA")
        print("   Coloque los archivos de datos y ejecute nuevamente")
    else:
        print("✅ INSTALACIÓN COMPLETADA EXITOSAMENTE")
        print("   Dashboard listo para usar")
    print("=" * 70)

    return len(missing_files) == 0


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Instalación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        sys.exit(1)
