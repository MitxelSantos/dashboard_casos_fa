#!/usr/bin/env python3
"""
Script de Diagnóstico para Dashboard Fiebre Amarilla
Analiza inconsistencias entre shapefiles IGAC y archivos Excel
Genera reportes detallados y sugerencias de mapeo
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path
import json
import re
import unicodedata
from collections import defaultdict, Counter
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NamesDiagnostic:
    """Clase principal para diagnosticar inconsistencias de nombres."""
    
    def __init__(self, data_dir="data", shapefiles_dir="C:/Users/Miguel Santos/Desktop/Tolima-Veredas/processed"):
        self.data_dir = Path(data_dir)
        self.shapefiles_dir = Path(shapefiles_dir)
        self.report = {
            'timestamp': datetime.now().isoformat(),
            'shapefiles_analysis': {},
            'excel_analysis': {},
            'inconsistencies': {},
            'mapping_suggestions': {},
            'statistics': {}
        }
        
    def normalize_text(self, text):
        """Normalización estándar de texto."""
        if pd.isna(text) or not isinstance(text, str):
            return ""
        
        # Remover tildes y diacríticos
        text = unicodedata.normalize("NFD", text)
        text = "".join(char for char in text if unicodedata.category(char) != "Mn")
        
        # Convertir a mayúsculas y limpiar
        text = text.upper().strip()
        text = re.sub(r"\s+", " ", text)
        
        return text
    
    def analyze_shapefiles(self):
        """Analiza los shapefiles y extrae información de campos y valores."""
        logger.info("🔍 Analizando shapefiles...")
        
        # Analizar municipios
        municipios_path = self.shapefiles_dir / "tolima_municipios.shp"
        if municipios_path.exists():
            try:
                municipios_gdf = gpd.read_file(municipios_path)
                self.report['shapefiles_analysis']['municipios'] = {
                    'file_found': True,
                    'columns': list(municipios_gdf.columns),
                    'total_records': len(municipios_gdf),
                    'sample_data': {}
                }
                
                # Analizar cada columna que podría contener nombres
                potential_name_cols = [col for col in municipios_gdf.columns 
                                     if any(keyword in col.lower() for keyword in 
                                           ['nombre', 'municipio', 'mun', 'mp'])]
                
                for col in potential_name_cols:
                    values = municipios_gdf[col].dropna().unique()
                    self.report['shapefiles_analysis']['municipios']['sample_data'][col] = {
                        'unique_count': len(values),
                        'samples': sorted(values)[:10],  # Primeros 10 como muestra
                        'all_values': sorted(values.tolist())  # Todos los valores
                    }
                
                logger.info(f"✅ Municipios shapefile: {len(municipios_gdf)} registros, columnas: {municipios_gdf.columns.tolist()}")
                
            except Exception as e:
                logger.error(f"❌ Error leyendo municipios shapefile: {e}")
                self.report['shapefiles_analysis']['municipios'] = {
                    'file_found': False,
                    'error': str(e)
                }
        else:
            logger.warning(f"⚠️ Shapefile de municipios no encontrado: {municipios_path}")
            self.report['shapefiles_analysis']['municipios'] = {'file_found': False}
        
        # Analizar veredas
        veredas_path = self.shapefiles_dir / "tolima_veredas.shp"
        if veredas_path.exists():
            try:
                veredas_gdf = gpd.read_file(veredas_path)
                self.report['shapefiles_analysis']['veredas'] = {
                    'file_found': True,
                    'columns': list(veredas_gdf.columns),
                    'total_records': len(veredas_gdf),
                    'sample_data': {}
                }
                
                # Analizar columnas potenciales
                potential_name_cols = [col for col in veredas_gdf.columns 
                                     if any(keyword in col.lower() for keyword in 
                                           ['nombre', 'vereda', 'ver', 'vda'])]
                
                potential_mun_cols = [col for col in veredas_gdf.columns 
                                    if any(keyword in col.lower() for keyword in 
                                          ['municipio', 'mun', 'mp'])]
                
                # Analizar nombres de veredas
                for col in potential_name_cols:
                    values = veredas_gdf[col].dropna().unique()
                    self.report['shapefiles_analysis']['veredas']['sample_data'][col] = {
                        'unique_count': len(values),
                        'samples': sorted(values)[:15],  # Más muestras para veredas
                        'all_values': sorted(values.tolist())
                    }
                
                # Analizar municipios en shapefile de veredas
                for col in potential_mun_cols:
                    values = veredas_gdf[col].dropna().unique()
                    self.report['shapefiles_analysis']['veredas']['sample_data'][col] = {
                        'unique_count': len(values),
                        'samples': sorted(values)[:10],
                        'all_values': sorted(values.tolist())
                    }
                
                logger.info(f"✅ Veredas shapefile: {len(veredas_gdf)} registros, columnas: {veredas_gdf.columns.tolist()}")
                
            except Exception as e:
                logger.error(f"❌ Error leyendo veredas shapefile: {e}")
                self.report['shapefiles_analysis']['veredas'] = {
                    'file_found': False,
                    'error': str(e)
                }
        else:
            logger.warning(f"⚠️ Shapefile de veredas no encontrado: {veredas_path}")
            self.report['shapefiles_analysis']['veredas'] = {'file_found': False}
    
    def analyze_excel_files(self):
        """Analiza los archivos Excel y extrae nombres de municipios y veredas."""
        logger.info("📊 Analizando archivos Excel...")
        
        # Analizar casos
        casos_path = self.data_dir / "BD_positivos.xlsx"
        if casos_path.exists():
            try:
                casos_df = pd.read_excel(casos_path, sheet_name="ACUMU", engine="openpyxl")
                self.report['excel_analysis']['casos'] = {
                    'file_found': True,
                    'total_records': len(casos_df),
                    'columns': list(casos_df.columns),
                    'municipios': {},
                    'veredas': {}
                }
                
                # Buscar columnas de municipios
                mun_cols = [col for col in casos_df.columns 
                           if any(keyword in col.lower() for keyword in 
                                 ['municipio', 'mun', 'nmun_proce'])]
                
                for col in mun_cols:
                    municipios = casos_df[col].dropna().unique()
                    municipios_norm = [self.normalize_text(m) for m in municipios]
                    self.report['excel_analysis']['casos']['municipios'][col] = {
                        'unique_count': len(municipios),
                        'samples': sorted(municipios)[:10],
                        'all_values': sorted(municipios.tolist()),
                        'normalized_values': sorted(list(set(municipios_norm)))
                    }
                
                # Buscar columnas de veredas
                ver_cols = [col for col in casos_df.columns 
                           if any(keyword in col.lower() for keyword in 
                                 ['vereda', 'ver'])]
                
                for col in ver_cols:
                    veredas = casos_df[col].dropna().unique()
                    veredas_norm = [self.normalize_text(v) for v in veredas]
                    self.report['excel_analysis']['casos']['veredas'][col] = {
                        'unique_count': len(veredas),
                        'samples': sorted(veredas)[:15],
                        'all_values': sorted(veredas.tolist()),
                        'normalized_values': sorted(list(set(veredas_norm)))
                    }
                
                logger.info(f"✅ Casos Excel: {len(casos_df)} registros analizados")
                
            except Exception as e:
                logger.error(f"❌ Error leyendo casos Excel: {e}")
                self.report['excel_analysis']['casos'] = {
                    'file_found': False,
                    'error': str(e)
                }
        else:
            logger.warning(f"⚠️ Archivo de casos no encontrado: {casos_path}")
            self.report['excel_analysis']['casos'] = {'file_found': False}
        
        # Analizar epizootias
        epizootias_path = self.data_dir / "Información_Datos_FA.xlsx"
        if epizootias_path.exists():
            try:
                epizootias_df = pd.read_excel(epizootias_path, sheet_name="Base de Datos", engine="openpyxl")
                self.report['excel_analysis']['epizootias'] = {
                    'file_found': True,
                    'total_records': len(epizootias_df),
                    'columns': list(epizootias_df.columns),
                    'municipios': {},
                    'veredas': {}
                }
                
                # Buscar columnas de municipios
                mun_cols = [col for col in epizootias_df.columns 
                           if any(keyword in col.lower() for keyword in 
                                 ['municipio', 'mun'])]
                
                for col in mun_cols:
                    municipios = epizootias_df[col].dropna().unique()
                    municipios_norm = [self.normalize_text(m) for m in municipios]
                    self.report['excel_analysis']['epizootias']['municipios'][col] = {
                        'unique_count': len(municipios),
                        'samples': sorted(municipios)[:10],
                        'all_values': sorted(municipios.tolist()),
                        'normalized_values': sorted(list(set(municipios_norm)))
                    }
                
                # Buscar columnas de veredas
                ver_cols = [col for col in epizootias_df.columns 
                           if any(keyword in col.lower() for keyword in 
                                 ['vereda', 'ver'])]
                
                for col in ver_cols:
                    veredas = epizootias_df[col].dropna().unique()
                    veredas_norm = [self.normalize_text(v) for v in veredas]
                    self.report['excel_analysis']['epizootias']['veredas'][col] = {
                        'unique_count': len(veredas),
                        'samples': sorted(veredas)[:15],
                        'all_values': sorted(veredas.tolist()),
                        'normalized_values': sorted(list(set(veredas_norm)))
                    }
                
                logger.info(f"✅ Epizootias Excel: {len(epizootias_df)} registros analizados")
                
            except Exception as e:
                logger.error(f"❌ Error leyendo epizootias Excel: {e}")
                self.report['excel_analysis']['epizootias'] = {
                    'file_found': False,
                    'error': str(e)
                }
        else:
            logger.warning(f"⚠️ Archivo de epizootias no encontrado: {epizootias_path}")
            self.report['excel_analysis']['epizootias'] = {'file_found': False}
    
    def find_inconsistencies(self):
        """Identifica inconsistencias entre las fuentes de datos."""
        logger.info("🔍 Identificando inconsistencias...")
        
        # Obtener datos de referencia (shapefiles)
        shp_municipios = set()
        shp_veredas = set()
        
        # Extraer municipios de referencia
        if self.report['shapefiles_analysis']['municipios'].get('file_found'):
            for col, data in self.report['shapefiles_analysis']['municipios']['sample_data'].items():
                if 'nombre' in col.lower() or 'mp' in col.lower():
                    shp_municipios.update([self.normalize_text(v) for v in data['all_values']])
        
        # Extraer veredas de referencia
        if self.report['shapefiles_analysis']['veredas'].get('file_found'):
            for col, data in self.report['shapefiles_analysis']['veredas']['sample_data'].items():
                if 'nombre' in col.lower() or 'ver' in col.lower():
                    shp_veredas.update([self.normalize_text(v) for v in data['all_values']])
        
        # Comparar con Excel
        self.report['inconsistencies'] = {
            'municipios': {'missing_in_shapefile': [], 'missing_in_excel': [], 'fuzzy_matches': []},
            'veredas': {'missing_in_shapefile': [], 'missing_in_excel': [], 'fuzzy_matches': []}
        }
        
        # Analizar municipios
        excel_municipios = set()
        for source in ['casos', 'epizootias']:
            if self.report['excel_analysis'][source].get('file_found'):
                for col, data in self.report['excel_analysis'][source]['municipios'].items():
                    excel_municipios.update(data['normalized_values'])
        
        # Inconsistencias de municipios
        self.report['inconsistencies']['municipios']['missing_in_shapefile'] = list(excel_municipios - shp_municipios)
        self.report['inconsistencies']['municipios']['missing_in_excel'] = list(shp_municipios - excel_municipios)
        
        # Analizar veredas
        excel_veredas = set()
        for source in ['casos', 'epizootias']:
            if self.report['excel_analysis'][source].get('file_found'):
                for col, data in self.report['excel_analysis'][source]['veredas'].items():
                    excel_veredas.update(data['normalized_values'])
        
        # Inconsistencias de veredas
        self.report['inconsistencies']['veredas']['missing_in_shapefile'] = list(excel_veredas - shp_veredas)
        self.report['inconsistencies']['veredas']['missing_in_excel'] = list(shp_veredas - excel_veredas)
        
        # Buscar coincidencias aproximadas (fuzzy matching)
        self.find_fuzzy_matches(shp_municipios, excel_municipios, 'municipios')
        self.find_fuzzy_matches(shp_veredas, excel_veredas, 'veredas')
        
        logger.info(f"✅ Inconsistencias encontradas: {len(self.report['inconsistencies']['municipios']['missing_in_shapefile'])} municipios, {len(self.report['inconsistencies']['veredas']['missing_in_shapefile'])} veredas")
    
    def find_fuzzy_matches(self, shp_names, excel_names, entity_type):
        """Encuentra coincidencias aproximadas usando similitud de cadenas."""
        try:
            from fuzzywuzzy import fuzz
            
            fuzzy_matches = []
            for excel_name in excel_names:
                if excel_name not in shp_names:  # Solo buscar para los que no coinciden exactamente
                    best_match = None
                    best_ratio = 0
                    
                    for shp_name in shp_names:
                        ratio = fuzz.ratio(excel_name, shp_name)
                        if ratio > best_ratio and ratio >= 80:  # Umbral de similitud
                            best_ratio = ratio
                            best_match = shp_name
                    
                    if best_match:
                        fuzzy_matches.append({
                            'excel_name': excel_name,
                            'shapefile_match': best_match,
                            'similarity': best_ratio
                        })
            
            self.report['inconsistencies'][entity_type]['fuzzy_matches'] = fuzzy_matches
            
        except ImportError:
            logger.warning("⚠️ fuzzywuzzy no disponible para coincidencias aproximadas")
            self.report['inconsistencies'][entity_type]['fuzzy_matches'] = []
    
    def generate_mapping_suggestions(self):
        """Genera sugerencias de mapeo basadas en el análisis."""
        logger.info("💡 Generando sugerencias de mapeo...")
        
        self.report['mapping_suggestions'] = {
            'municipios': {},
            'veredas': {},
            'patterns_found': [],
            'automatic_mappings': {}
        }
        
        # Analizar patrones comunes
        patterns = []
        
        # Buscar patrones en fuzzy matches
        for entity_type in ['municipios', 'veredas']:
            fuzzy_matches = self.report['inconsistencies'][entity_type]['fuzzy_matches']
            for match in fuzzy_matches:
                excel_name = match['excel_name']
                shp_name = match['shapefile_match']
                
                # Analizar diferencias comunes
                if 'VDA' in excel_name and 'VDA' not in shp_name:
                    patterns.append("Prefijo 'VDA' en Excel pero no en shapefile")
                
                if len(excel_name.split()) > len(shp_name.split()):
                    patterns.append("Nombres más largos en Excel")
        
        self.report['mapping_suggestions']['patterns_found'] = list(set(patterns))
        
        # Generar mapeos automáticos recomendados
        auto_mappings = {}
        for entity_type in ['municipios', 'veredas']:
            auto_mappings[entity_type] = {}
            fuzzy_matches = self.report['inconsistencies'][entity_type]['fuzzy_matches']
            
            for match in fuzzy_matches:
                if match['similarity'] >= 90:  # Alta confianza
                    auto_mappings[entity_type][match['excel_name']] = match['shapefile_match']
        
        self.report['mapping_suggestions']['automatic_mappings'] = auto_mappings
    
    def calculate_statistics(self):
        """Calcula estadísticas generales del diagnóstico."""
        logger.info("📊 Calculando estadísticas...")
        
        stats = {
            'total_files_analyzed': 0,
            'files_found': [],
            'files_missing': [],
            'total_inconsistencies': 0,
            'high_confidence_mappings': 0,
            'manual_review_needed': 0
        }
        
        # Contar archivos
        for source in ['municipios', 'veredas']:
            if self.report['shapefiles_analysis'][source].get('file_found'):
                stats['files_found'].append(f"shapefile_{source}")
                stats['total_files_analyzed'] += 1
            else:
                stats['files_missing'].append(f"shapefile_{source}")
        
        for source in ['casos', 'epizootias']:
            if self.report['excel_analysis'][source].get('file_found'):
                stats['files_found'].append(f"excel_{source}")
                stats['total_files_analyzed'] += 1
            else:
                stats['files_missing'].append(f"excel_{source}")
        
        # Contar inconsistencias
        for entity_type in ['municipios', 'veredas']:
            stats['total_inconsistencies'] += len(self.report['inconsistencies'][entity_type]['missing_in_shapefile'])
            
            # Contar mapeos de alta confianza
            for match in self.report['inconsistencies'][entity_type]['fuzzy_matches']:
                if match['similarity'] >= 90:
                    stats['high_confidence_mappings'] += 1
                else:
                    stats['manual_review_needed'] += 1
        
        self.report['statistics'] = stats
    
    def save_report(self, output_path="diagnostic_report.json"):
        """Guarda el reporte completo en JSON."""
        output_file = Path(output_path)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"📄 Reporte guardado en: {output_file.absolute()}")
        return output_file
    
    def print_summary(self):
        """Imprime un resumen del diagnóstico."""
        print("\n" + "="*60)
        print("📋 RESUMEN DEL DIAGNÓSTICO")
        print("="*60)
        
        stats = self.report['statistics']
        print(f"🗂️ Archivos analizados: {stats['total_files_analyzed']}")
        print(f"✅ Archivos encontrados: {len(stats['files_found'])}")
        print(f"❌ Archivos faltantes: {len(stats['files_missing'])}")
        
        if stats['files_missing']:
            print(f"   Faltantes: {', '.join(stats['files_missing'])}")
        
        print(f"\n🔍 Inconsistencias totales: {stats['total_inconsistencies']}")
        print(f"✅ Mapeos automáticos posibles: {stats['high_confidence_mappings']}")
        print(f"⚠️ Requieren revisión manual: {stats['manual_review_needed']}")
        
        # Mostrar algunas inconsistencias como ejemplo
        print(f"\n📍 EJEMPLOS DE INCONSISTENCIAS:")
        
        mun_missing = self.report['inconsistencies']['municipios']['missing_in_shapefile'][:5]
        if mun_missing:
            print(f"   Municipios en Excel pero no en shapefile: {mun_missing}")
        
        ver_missing = self.report['inconsistencies']['veredas']['missing_in_shapefile'][:5]
        if ver_missing:
            print(f"   Veredas en Excel pero no en shapefile: {ver_missing}")
        
        # Mostrar mapeos recomendados
        auto_mappings = self.report['mapping_suggestions']['automatic_mappings']
        if auto_mappings['municipios'] or auto_mappings['veredas']:
            print(f"\n💡 MAPEOS AUTOMÁTICOS RECOMENDADOS:")
            for entity_type in ['municipios', 'veredas']:
                if auto_mappings[entity_type]:
                    print(f"   {entity_type.capitalize()}:")
                    for excel_name, shp_name in list(auto_mappings[entity_type].items())[:3]:
                        print(f"     '{excel_name}' → '{shp_name}'")
        
        print("\n" + "="*60)
    
    def run_full_diagnostic(self):
        """Ejecuta el diagnóstico completo."""
        logger.info("🚀 Iniciando diagnóstico completo...")
        
        self.analyze_shapefiles()
        self.analyze_excel_files()
        self.find_inconsistencies()
        self.generate_mapping_suggestions()
        self.calculate_statistics()
        
        # Guardar reporte
        report_file = self.save_report()
        
        # Mostrar resumen
        self.print_summary()
        
        return report_file


def main():
    """Función principal para ejecutar el diagnóstico."""
    print("🔍 DIAGNÓSTICO DE INCONSISTENCIAS - DASHBOARD FIEBRE AMARILLA")
    print("="*60)
    
    # Crear instancia del diagnóstico
    diagnostic = NamesDiagnostic()
    
    # Ejecutar análisis completo
    try:
        report_file = diagnostic.run_full_diagnostic()
        
        print(f"\n✅ Diagnóstico completado exitosamente!")
        print(f"📄 Reporte detallado guardado en: {report_file}")
        print(f"\n💡 Próximos pasos recomendados:")
        print(f"   1. Revisar el archivo JSON para detalles completos")
        print(f"   2. Implementar mapeos automáticos de alta confianza")
        print(f"   3. Revisar manualmente inconsistencias restantes")
        print(f"   4. Actualizar sistema de normalización en el dashboard")
        
    except Exception as e:
        logger.error(f"❌ Error durante el diagnóstico: {e}")
        print(f"\n❌ Error: {e}")
        print(f"💡 Verifique que los archivos existan en las rutas especificadas")


if __name__ == "__main__":
    main()