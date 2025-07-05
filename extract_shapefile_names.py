#!/usr/bin/env python3
"""
Extractor de Nombres de Shapefiles - Dashboard Fiebre Amarilla Tolima
Extrae todos los nombres de municipios y veredas de los shapefiles para análisis de referencia.

Ejecutar desde la raíz del proyecto:
python extract_shapefile_names.py
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path
import unicodedata
import re
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def normalize_text_like_dashboard(text):
    """
    Normaliza texto igual que en el dashboard para comparación.
    Copiado de utils/data_processor.py
    """
    if pd.isna(text) or not isinstance(text, str):
        return ""

    if text.strip() == "" or text.lower() in ['nan', 'none', 'null']:
        return ""

    try:
        # Remover tildes y diacríticos
        text = unicodedata.normalize("NFD", text)
        text = "".join(char for char in text if unicodedata.category(char) != "Mn")

        # Convertir a mayúsculas y limpiar espacios
        text = text.upper().strip()
        text = re.sub(r"\s+", " ", text)

        # Reemplazos específicos detectados en el código
        replacements = {
            "VILLARICA": "VILLARRICA",
            "PURIFICACION": "PURIFICACION",
        }

        for old, new in replacements.items():
            if text == old:
                text = new
                break

        return text
        
    except Exception as e:
        logger.warning(f"Error normalizando texto '{text}': {e}")
        return ""

def extract_shapefile_info(shapefile_path, layer_name):
    """
    Extrae información completa de un shapefile.
    
    Args:
        shapefile_path (Path): Ruta al shapefile
        layer_name (str): Nombre de la capa (municipios/veredas)
    
    Returns:
        pd.DataFrame: DataFrame con información extraída
    """
    try:
        logger.info(f"📂 Leyendo shapefile: {shapefile_path}")
        gdf = gpd.read_file(shapefile_path)
        
        # Información básica
        logger.info(f"   ✅ {len(gdf)} registros encontrados")
        logger.info(f"   📊 Columnas disponibles: {list(gdf.columns)}")
        
        # Extraer información de todas las columnas que podrían contener nombres
        extracted_data = []
        
        for idx, row in gdf.iterrows():
            row_info = {
                'capa': layer_name,
                'indice': idx,
                'geometry_type': str(row.geometry.geom_type) if row.geometry else 'Sin geometría'
            }
            
            # Extraer TODAS las columnas del shapefile
            for col in gdf.columns:
                if col != 'geometry':  # Excluir geometría
                    value = row[col]
                    row_info[f'campo_{col}'] = value
                    
                    # Si parece ser un nombre (texto no vacío)
                    if isinstance(value, str) and value.strip():
                        row_info[f'campo_{col}_normalizado'] = normalize_text_like_dashboard(value)
            
            extracted_data.append(row_info)
        
        return pd.DataFrame(extracted_data)
        
    except Exception as e:
        logger.error(f"❌ Error leyendo {shapefile_path}: {str(e)}")
        return pd.DataFrame()

def analyze_name_patterns(df, layer_name):
    """
    Analiza patrones en los nombres para identificar columnas principales.
    
    Args:
        df (pd.DataFrame): DataFrame con datos extraídos
        layer_name (str): Nombre de la capa
    
    Returns:
        dict: Análisis de patrones
    """
    analysis = {
        'layer': layer_name,
        'total_records': len(df),
        'potential_name_columns': [],
        'unique_values_per_column': {},
        'most_likely_name_column': None
    }
    
    if df.empty:
        return analysis
    
    # Buscar columnas que contengan nombres
    name_columns = []
    
    for col in df.columns:
        if col.startswith('campo_') and not col.endswith('_normalizado'):
            # Verificar si la columna tiene valores de texto únicos
            values = df[col].dropna()
            if len(values) > 0:
                unique_count = values.nunique()
                total_count = len(values)
                
                # Si tiene muchos valores únicos y son strings, probablemente sea nombres
                if isinstance(values.iloc[0], str) and unique_count / total_count > 0.7:
                    name_columns.append({
                        'column': col,
                        'unique_values': unique_count,
                        'total_values': total_count,
                        'completeness': unique_count / total_count,
                        'sample_values': values.unique()[:5].tolist()
                    })
                    
                    analysis['unique_values_per_column'][col] = {
                        'unique_count': unique_count,
                        'sample_values': values.unique()[:10].tolist()
                    }
    
    analysis['potential_name_columns'] = name_columns
    
    # Determinar la columna más probable para nombres
    if name_columns:
        # Ordenar por completeness y número de valores únicos
        best_column = max(name_columns, 
                         key=lambda x: (x['completeness'], x['unique_values']))
        analysis['most_likely_name_column'] = best_column['column']
    
    return analysis

def create_comparison_table(municipios_df, veredas_df):
    """
    Crea tabla de comparación con datos de casos/epizootias si están disponibles.
    
    Args:
        municipios_df (pd.DataFrame): Datos de municipios
        veredas_df (pd.DataFrame): Datos de veredas
    
    Returns:
        dict: Tablas de comparación
    """
    comparison_data = {}
    
    # Tabla de municipios únicos
    if not municipios_df.empty:
        municipios_unique = []
        
        # Intentar extraer nombres de las columnas más probables
        possible_name_cols = [col for col in municipios_df.columns 
                             if 'nombre' in col.lower() or 'municipio' in col.lower() or 'mp' in col.lower()]
        
        if not possible_name_cols:
            possible_name_cols = [col for col in municipios_df.columns if col.startswith('campo_')]
        
        for col in possible_name_cols[:3]:  # Tomar las 3 primeras columnas
            if col in municipios_df.columns:
                unique_values = municipios_df[col].dropna().unique()
                for value in unique_values:
                    if isinstance(value, str) and value.strip():
                        municipios_unique.append({
                            'municipio_original': value,
                            'municipio_normalizado': normalize_text_like_dashboard(value),
                            'fuente_columna': col,
                            'tipo': 'Municipio'
                        })
        
        comparison_data['municipios'] = pd.DataFrame(municipios_unique).drop_duplicates()
    
    # Tabla de veredas únicas
    if not veredas_df.empty:
        veredas_unique = []
        
        possible_name_cols = [col for col in veredas_df.columns 
                             if 'nombre' in col.lower() or 'vereda' in col.lower() or 'ver' in col.lower()]
        
        if not possible_name_cols:
            possible_name_cols = [col for col in veredas_df.columns if col.startswith('campo_')]
        
        for col in possible_name_cols[:3]:
            if col in veredas_df.columns:
                unique_values = veredas_df[col].dropna().unique()
                for value in unique_values:
                    if isinstance(value, str) and value.strip():
                        # Intentar extraer municipio si está en el mismo registro
                        municipio_cols = [c for c in veredas_df.columns if 'municipio' in c.lower()]
                        municipio = ""
                        if municipio_cols:
                            municipio_data = veredas_df[veredas_df[col] == value][municipio_cols[0]].iloc[0] if len(veredas_df[veredas_df[col] == value]) > 0 else ""
                            municipio = str(municipio_data) if pd.notna(municipio_data) else ""
                        
                        veredas_unique.append({
                            'vereda_original': value,
                            'vereda_normalizada': normalize_text_like_dashboard(value),
                            'municipio_asociado': municipio,
                            'fuente_columna': col,
                            'tipo': 'Vereda'
                        })
        
        comparison_data['veredas'] = pd.DataFrame(veredas_unique).drop_duplicates()
    
    return comparison_data

def export_to_excel(municipios_df, veredas_df, municipios_analysis, veredas_analysis, comparison_data, output_path):
    """
    Exporta toda la información a Excel con múltiples hojas.
    
    Args:
        municipios_df (pd.DataFrame): Datos completos de municipios
        veredas_df (pd.DataFrame): Datos completos de veredas
        municipios_analysis (dict): Análisis de municipios
        veredas_analysis (dict): Análisis de veredas
        comparison_data (dict): Tablas de comparación
        output_path (Path): Ruta del archivo de salida
    """
    try:
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            
            # Hoja 1: Resumen ejecutivo
            summary_data = []
            summary_data.append({
                'Aspecto': 'Fecha de Extracción',
                'Valor': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Descripción': 'Fecha y hora de generación del archivo'
            })
            summary_data.append({
                'Aspecto': 'Total Municipios',
                'Valor': len(municipios_df) if not municipios_df.empty else 0,
                'Descripción': 'Número total de registros de municipios en shapefile'
            })
            summary_data.append({
                'Aspecto': 'Total Veredas', 
                'Valor': len(veredas_df) if not veredas_df.empty else 0,
                'Descripción': 'Número total de registros de veredas en shapefile'
            })
            summary_data.append({
                'Aspecto': 'Columna Principal Municipios',
                'Valor': municipios_analysis.get('most_likely_name_column', 'No detectada'),
                'Descripción': 'Columna más probable que contiene nombres de municipios'
            })
            summary_data.append({
                'Aspecto': 'Columna Principal Veredas',
                'Valor': veredas_analysis.get('most_likely_name_column', 'No detectada'),
                'Descripción': 'Columna más probable que contiene nombres de veredas'
            })
            
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='🏠 Resumen', index=False)
            
            # Hoja 2: Municipios únicos para referencia
            if 'municipios' in comparison_data and not comparison_data['municipios'].empty:
                comparison_data['municipios'].to_excel(writer, sheet_name='📍 Municipios Únicos', index=False)
            
            # Hoja 3: Veredas únicas para referencia
            if 'veredas' in comparison_data and not comparison_data['veredas'].empty:
                comparison_data['veredas'].to_excel(writer, sheet_name='🏘️ Veredas Únicas', index=False)
            
            # Hoja 4: Datos completos de municipios
            if not municipios_df.empty:
                municipios_df.to_excel(writer, sheet_name='🏛️ Municipios Completo', index=False)
            
            # Hoja 5: Datos completos de veredas
            if not veredas_df.empty:
                veredas_df.to_excel(writer, sheet_name='🏘️ Veredas Completo', index=False)
            
            # Hoja 6: Análisis de patrones de municipios
            if municipios_analysis.get('potential_name_columns'):
                municipios_patterns = []
                for col_info in municipios_analysis['potential_name_columns']:
                    municipios_patterns.append({
                        'Columna': col_info['column'],
                        'Valores Únicos': col_info['unique_values'],
                        'Total Valores': col_info['total_values'],
                        'Completitud (%)': round(col_info['completeness'] * 100, 2),
                        'Muestra Valores': ' | '.join(map(str, col_info['sample_values']))
                    })
                pd.DataFrame(municipios_patterns).to_excel(writer, sheet_name='📊 Análisis Municipios', index=False)
            
            # Hoja 7: Análisis de patrones de veredas
            if veredas_analysis.get('potential_name_columns'):
                veredas_patterns = []
                for col_info in veredas_analysis['potential_name_columns']:
                    veredas_patterns.append({
                        'Columna': col_info['column'],
                        'Valores Únicos': col_info['unique_values'],
                        'Total Valores': col_info['total_values'],
                        'Completitud (%)': round(col_info['completeness'] * 100, 2),
                        'Muestra Valores': ' | '.join(map(str, col_info['sample_values']))
                    })
                pd.DataFrame(veredas_patterns).to_excel(writer, sheet_name='📊 Análisis Veredas', index=False)
            
            # Hoja 8: Metadatos técnicos
            metadata = []
            metadata.append({
                'Categoría': 'Archivos Procesados',
                'Detalle': 'tolima_municipios.shp',
                'Estado': 'OK' if not municipios_df.empty else 'No encontrado',
                'Registros': len(municipios_df) if not municipios_df.empty else 0
            })
            metadata.append({
                'Categoría': 'Archivos Procesados',
                'Detalle': 'tolima_veredas.shp',
                'Estado': 'OK' if not veredas_df.empty else 'No encontrado',
                'Registros': len(veredas_df) if not veredas_df.empty else 0
            })
            metadata.append({
                'Categoría': 'Función de Normalización',
                'Detalle': 'normalize_text_like_dashboard()',
                'Estado': 'Implementada',
                'Registros': 'Compatible con dashboard'
            })
            
            pd.DataFrame(metadata).to_excel(writer, sheet_name='🔧 Metadatos', index=False)
        
        logger.info(f"✅ Archivo Excel generado exitosamente: {output_path}")
        
    except Exception as e:
        logger.error(f"❌ Error generando Excel: {str(e)}")
        raise

def main():
    """
    Función principal del extractor.
    """
    print("🗺️ EXTRACTOR DE NOMBRES DE SHAPEFILES - TOLIMA")
    print("=" * 60)
    
    # Configurar rutas (ajustar según tu configuración)
    base_path = Path("C:/Users/Miguel Santos/Desktop/Tolima-Veredas/processed")
    municipios_path = base_path / "tolima_municipios.shp"
    veredas_path = base_path / "tolima_veredas.shp"
    
    # Ruta de salida
    output_path = Path.cwd() / f"shapefile_names_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    print(f"📂 Buscando shapefiles en: {base_path}")
    print(f"📄 Archivo de salida: {output_path}")
    print()
    
    # Verificar que las rutas existen
    if not base_path.exists():
        logger.error(f"❌ Directorio no encontrado: {base_path}")
        print(f"\n💡 INSTRUCCIONES:")
        print(f"   1. Ajusta la variable 'base_path' en el script")
        print(f"   2. Asegúrate de que los archivos .shp estén en la ruta correcta")
        print(f"   3. Verifica que tengas instalado: geopandas, pandas, openpyxl")
        return
    
    # Extraer información de municipios
    logger.info("🏛️ Procesando shapefile de municipios...")
    municipios_df = extract_shapefile_info(municipios_path, "municipios")
    municipios_analysis = analyze_name_patterns(municipios_df, "municipios")
    
    # Extraer información de veredas
    logger.info("🏘️ Procesando shapefile de veredas...")
    veredas_df = extract_shapefile_info(veredas_path, "veredas")
    veredas_analysis = analyze_name_patterns(veredas_df, "veredas")
    
    # Crear tablas de comparación
    logger.info("📊 Creando tablas de comparación...")
    comparison_data = create_comparison_table(municipios_df, veredas_df)
    
    # Exportar a Excel
    logger.info("📥 Exportando resultados a Excel...")
    export_to_excel(municipios_df, veredas_df, municipios_analysis, veredas_analysis, comparison_data, output_path)
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE EXTRACCIÓN:")
    print(f"   🏛️ Municipios encontrados: {len(municipios_df)}")
    print(f"   🏘️ Veredas encontradas: {len(veredas_df)}")
    
    if municipios_analysis.get('most_likely_name_column'):
        print(f"   📍 Columna principal municipios: {municipios_analysis['most_likely_name_column']}")
    
    if veredas_analysis.get('most_likely_name_column'):
        print(f"   🏘️ Columna principal veredas: {veredas_analysis['most_likely_name_column']}")
    
    print(f"   📁 Archivo generado: {output_path.name}")
    print("\n💡 Abra el archivo Excel para revisar todos los nombres extraídos")
    print("   Úselo como referencia para mapear datos de casos y epizootias")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ Proceso cancelado por el usuario")
    except Exception as e:
        logger.error(f"💥 Error crítico: {str(e)}")
        print(f"\n❌ Error: {str(e)}")
        print("\n🔧 Verifica que tengas instaladas las dependencias:")
        print("   pip install geopandas pandas openpyxl")