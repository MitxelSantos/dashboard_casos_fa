#!/usr/bin/env python3
"""
Generador de Mapeos Automáticos para Dashboard Fiebre Amarilla
Basado en el análisis de diagnóstico, genera archivos de mapeo para usar en el dashboard
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MappingGenerator:
    """Genera archivos de mapeo basados en el diagnóstico."""
    
    def __init__(self, diagnostic_report_path="diagnostic_report.json"):
        self.diagnostic_path = Path(diagnostic_report_path)
        self.report = None
        self.load_diagnostic_report()
    
    def load_diagnostic_report(self):
        """Carga el reporte de diagnóstico."""
        if not self.diagnostic_path.exists():
            raise FileNotFoundError(f"Reporte de diagnóstico no encontrado: {self.diagnostic_path}")
        
        with open(self.diagnostic_path, 'r', encoding='utf-8') as f:
            self.report = json.load(f)
        
        logger.info(f"✅ Reporte de diagnóstico cargado: {self.diagnostic_path}")
    
    def extract_shapefile_reference_data(self):
        """Extrae los datos de referencia de los shapefiles."""
        reference_data = {
            'municipios_shapefile': set(),
            'veredas_shapefile': set(),
            'municipios_field': None,
            'veredas_field': None
        }
        
        # Extraer municipios de referencia
        if self.report['shapefiles_analysis']['municipios'].get('file_found'):
            shp_data = self.report['shapefiles_analysis']['municipios']['sample_data']
            
            # Identificar el mejor campo para municipios
            best_mun_field = None
            max_count = 0
            
            for field, data in shp_data.items():
                if any(keyword in field.lower() for keyword in ['nombre', 'mp']):
                    if data['unique_count'] > max_count:
                        max_count = data['unique_count']
                        best_mun_field = field
                        reference_data['municipios_shapefile'] = set(data['all_values'])
            
            reference_data['municipios_field'] = best_mun_field
            logger.info(f"📍 Campo de municipios identificado: {best_mun_field} ({max_count} municipios)")
        
        # Extraer veredas de referencia
        if self.report['shapefiles_analysis']['veredas'].get('file_found'):
            shp_data = self.report['shapefiles_analysis']['veredas']['sample_data']
            
            # Identificar el mejor campo para veredas
            best_ver_field = None
            max_count = 0
            
            for field, data in shp_data.items():
                if any(keyword in field.lower() for keyword in ['nombre', 'ver']):
                    if data['unique_count'] > max_count:
                        max_count = data['unique_count']
                        best_ver_field = field
                        reference_data['veredas_shapefile'] = set(data['all_values'])
            
            reference_data['veredas_field'] = best_ver_field
            logger.info(f"🏘️ Campo de veredas identificado: {best_ver_field} ({max_count} veredas)")
        
        return reference_data
    
    def generate_comprehensive_mapping(self):
        """Genera mapeo completo basado en todos los datos disponibles."""
        reference_data = self.extract_shapefile_reference_data()
        
        mapping = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'diagnostic_report': str(self.diagnostic_path),
                'municipios_source_field': reference_data['municipios_field'],
                'veredas_source_field': reference_data['veredas_field'],
                'total_municipios_shapefile': len(reference_data['municipios_shapefile']),
                'total_veredas_shapefile': len(reference_data['veredas_shapefile'])
            },
            'municipios_mapping': {},
            'veredas_mapping': {},
            'normalization_rules': {},
            'problematic_cases': {}
        }
        
        # Generar mapeos de municipios
        mun_mapping = self._generate_entity_mapping(
            'municipios', 
            reference_data['municipios_shapefile']
        )
        mapping['municipios_mapping'] = mun_mapping
        
        # Generar mapeos de veredas
        ver_mapping = self._generate_entity_mapping(
            'veredas', 
            reference_data['veredas_shapefile']
        )
        mapping['veredas_mapping'] = ver_mapping
        
        # Generar reglas de normalización
        mapping['normalization_rules'] = self._generate_normalization_rules()
        
        # Identificar casos problemáticos
        mapping['problematic_cases'] = self._identify_problematic_cases()
        
        return mapping
    
    def _generate_entity_mapping(self, entity_type, shapefile_reference):
        """Genera mapeo para un tipo de entidad específico."""
        mapping = {
            'automatic_high_confidence': {},  # Mapeos automáticos de alta confianza (>=95%)
            'automatic_medium_confidence': {},  # Mapeos automáticos de confianza media (85-94%)
            'manual_review_required': {},  # Requieren revisión manual (<85%)
            'exact_matches': {},  # Coincidencias exactas
            'missing_in_shapefile': [],  # Están en Excel pero no en shapefile
            'missing_in_excel': []  # Están en shapefile pero no en Excel
        }
        
        # Obtener datos de coincidencias aproximadas del reporte
        fuzzy_matches = self.report['inconsistencies'][entity_type]['fuzzy_matches']
        
        # Clasificar por nivel de confianza
        for match in fuzzy_matches:
            excel_name = match['excel_name']
            shapefile_name = match['shapefile_match']
            similarity = match['similarity']
            
            if similarity >= 95:
                mapping['automatic_high_confidence'][excel_name] = shapefile_name
            elif similarity >= 85:
                mapping['automatic_medium_confidence'][excel_name] = shapefile_name
            else:
                mapping['manual_review_required'][excel_name] = {
                    'suggested_match': shapefile_name,
                    'confidence': similarity
                }
        
        # Agregar casos faltantes
        mapping['missing_in_shapefile'] = self.report['inconsistencies'][entity_type]['missing_in_shapefile']
        mapping['missing_in_excel'] = self.report['inconsistencies'][entity_type]['missing_in_excel']
        
        # Buscar coincidencias exactas (normalizadas)
        excel_names = set()
        for source in ['casos', 'epizootias']:
            if self.report['excel_analysis'][source].get('file_found'):
                for field, data in self.report['excel_analysis'][source][entity_type].items():
                    excel_names.update(data['normalized_values'])
        
        # Normalizar nombres de shapefile para comparación
        shapefile_normalized = {self._normalize_for_comparison(name): name for name in shapefile_reference}
        
        for excel_name in excel_names:
            excel_normalized = self._normalize_for_comparison(excel_name)
            if excel_normalized in shapefile_normalized:
                mapping['exact_matches'][excel_name] = shapefile_normalized[excel_normalized]
        
        return mapping
    
    def _normalize_for_comparison(self, text):
        """Normalización estricta para comparaciones exactas."""
        if not text:
            return ""
        
        import unicodedata
        import re
        
        # Normalización completa
        text = unicodedata.normalize("NFD", text)
        text = "".join(char for char in text if unicodedata.category(char) != "Mn")
        text = text.upper().strip()
        text = re.sub(r"\s+", " ", text)
        
        # Remover prefijos comunes
        prefixes_to_remove = ['VDA ', 'VEREDA ', 'MUNICIPIO ', 'MUN ']
        for prefix in prefixes_to_remove:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
        
        # Remover conectores comunes
        text = re.sub(r'\s+(DE|DEL|LA|LAS|EL|LOS|Y|E)\s+', ' ', text)
        
        return text
    
    def _generate_normalization_rules(self):
        """Genera reglas de normalización basadas en patrones encontrados."""
        rules = {
            'prefix_removal': [
                'VDA ', 'VEREDA ', 'MUNICIPIO ', 'MUN '
            ],
            'connector_normalization': [
                {'pattern': r'\s+(DE|DEL|LA|LAS|EL|LOS|Y|E)\s+', 'replacement': ' '}
            ],
            'special_cases': {},
            'common_abbreviations': {
                'VDA': 'VEREDA',
                'MUN': 'MUNICIPIO',
                'SAN': 'SAN',
                'STA': 'SANTA'
            }
        }
        
        # Analizar patrones específicos encontrados
        patterns = self.report['mapping_suggestions'].get('patterns_found', [])
        for pattern in patterns:
            if 'VDA' in pattern:
                rules['special_cases']['vereda_prefix'] = "Remover prefijo 'VDA' de nombres de veredas"
        
        return rules
    
    def _identify_problematic_cases(self):
        """Identifica casos que requieren atención especial."""
        problematic = {
            'duplicate_names': [],
            'ambiguous_mappings': [],
            'encoding_issues': [],
            'structural_differences': []
        }
        
        # Buscar nombres duplicados en shapefile
        for entity_type in ['municipios', 'veredas']:
            if self.report['shapefiles_analysis'][entity_type].get('file_found'):
                for field, data in self.report['shapefiles_analysis'][entity_type]['sample_data'].items():
                    values = data['all_values']
                    value_counts = {}
                    for value in values:
                        normalized = self._normalize_for_comparison(value)
                        if normalized in value_counts:
                            value_counts[normalized].append(value)
                        else:
                            value_counts[normalized] = [value]
                    
                    # Identificar duplicados
                    for normalized, original_values in value_counts.items():
                        if len(original_values) > 1:
                            problematic['duplicate_names'].append({
                                'entity_type': entity_type,
                                'normalized_name': normalized,
                                'variations': original_values
                            })
        
        return problematic
    
    def save_mapping_files(self, mapping, output_dir="mapping_outputs"):
        """Guarda los archivos de mapeo en diferentes formatos."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        
        # 1. Guardar mapeo completo en JSON
        json_file = output_path / f"mapping_complete_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, indent=2, ensure_ascii=False)
        logger.info(f"📄 Mapeo completo guardado: {json_file}")
        
        # 2. Generar archivo Python para usar en el dashboard
        py_file = output_path / f"automatic_mappings_{timestamp}.py"
        self._generate_python_mapping_file(mapping, py_file)
        logger.info(f"🐍 Archivo Python generado: {py_file}")
        
        # 3. Generar archivo Excel para revisión manual
        excel_file = output_path / f"mapping_review_{timestamp}.xlsx"
        self._generate_excel_review_file(mapping, excel_file)
        logger.info(f"📊 Archivo Excel para revisión: {excel_file}")
        
        # 4. Generar reporte de implementación
        report_file = output_path / f"implementation_guide_{timestamp}.md"
        self._generate_implementation_guide(mapping, report_file)
        logger.info(f"📋 Guía de implementación: {report_file}")
        
        return {
            'json_file': json_file,
            'python_file': py_file,
            'excel_file': excel_file,
            'report_file': report_file
        }
    
    def _generate_python_mapping_file(self, mapping, output_file):
        """Genera archivo Python con mapeos listos para usar."""
        content = f'''"""
Mapeos Automáticos para Dashboard Fiebre Amarilla
Generado automáticamente el {mapping['metadata']['generated_at']}

IMPORTANTE: Este archivo contiene mapeos basados en análisis automático.
Revise los mapeos de confianza media antes de usar en producción.
"""

from typing import Dict, Set

# Metadatos de generación
MAPPING_METADATA = {mapping['metadata']}

# =============================================================================
# MAPEOS DE MUNICIPIOS
# =============================================================================

# Mapeos de alta confianza (>=95% similitud) - USAR DIRECTAMENTE
MUNICIPIOS_HIGH_CONFIDENCE: Dict[str, str] = {mapping['municipios_mapping']['automatic_high_confidence']}

# Mapeos de confianza media (85-94% similitud) - REVISAR ANTES DE USAR
MUNICIPIOS_MEDIUM_CONFIDENCE: Dict[str, str] = {mapping['municipios_mapping']['automatic_medium_confidence']}

# Coincidencias exactas (después de normalización)
MUNICIPIOS_EXACT_MATCHES: Dict[str, str] = {mapping['municipios_mapping']['exact_matches']}

# =============================================================================
# MAPEOS DE VEREDAS
# =============================================================================

# Mapeos de alta confianza (>=95% similitud) - USAR DIRECTAMENTE
VEREDAS_HIGH_CONFIDENCE: Dict[str, str] = {mapping['veredas_mapping']['automatic_high_confidence']}

# Mapeos de confianza media (85-94% similitud) - REVISAR ANTES DE USAR
VEREDAS_MEDIUM_CONFIDENCE: Dict[str, str] = {mapping['veredas_mapping']['automatic_medium_confidence']}

# Coincidencias exactas (después de normalización)
VEREDAS_EXACT_MATCHES: Dict[str, str] = {mapping['veredas_mapping']['exact_matches']}

# =============================================================================
# MAPEO CONSOLIDADO PARA USAR EN EL DASHBOARD
# =============================================================================

def get_municipio_mapping(include_medium_confidence: bool = False) -> Dict[str, str]:
    """
    Obtiene mapeo consolidado de municipios.
    
    Args:
        include_medium_confidence: Si incluir mapeos de confianza media
    
    Returns:
        Diccionario con mapeos excel_name -> shapefile_name
    """
    mapping = {{}}
    mapping.update(MUNICIPIOS_EXACT_MATCHES)
    mapping.update(MUNICIPIOS_HIGH_CONFIDENCE)
    
    if include_medium_confidence:
        mapping.update(MUNICIPIOS_MEDIUM_CONFIDENCE)
    
    return mapping

def get_vereda_mapping(include_medium_confidence: bool = False) -> Dict[str, str]:
    """
    Obtiene mapeo consolidado de veredas.
    
    Args:
        include_medium_confidence: Si incluir mapeos de confianza media
    
    Returns:
        Diccionario con mapeos excel_name -> shapefile_name
    """
    mapping = {{}}
    mapping.update(VEREDAS_EXACT_MATCHES)
    mapping.update(VEREDAS_HIGH_CONFIDENCE)
    
    if include_medium_confidence:
        mapping.update(VEREDAS_MEDIUM_CONFIDENCE)
    
    return mapping

# =============================================================================
# FUNCIÓN PRINCIPAL PARA INTEGRAR EN EL DASHBOARD
# =============================================================================

def apply_shapefile_mapping(df, entity_column: str, entity_type: str = 'municipios', 
                          include_medium_confidence: bool = False):
    """
    Aplica mapeo automático a un DataFrame usando shapefiles como referencia.
    
    Args:
        df: DataFrame a procesar
        entity_column: Nombre de la columna con entidades (municipios/veredas)
        entity_type: 'municipios' o 'veredas'
        include_medium_confidence: Si incluir mapeos de confianza media
    
    Returns:
        DataFrame con columna adicional '_mapped' con nombres del shapefile
    """
    if entity_type == 'municipios':
        mapping = get_municipio_mapping(include_medium_confidence)
    elif entity_type == 'veredas':
        mapping = get_vereda_mapping(include_medium_confidence)
    else:
        raise ValueError("entity_type debe ser 'municipios' o 'veredas'")
    
    # Crear columna mapeada
    df_result = df.copy()
    df_result[f'{{entity_column}}_mapped'] = df_result[entity_column].map(mapping).fillna(df_result[entity_column])
    
    return df_result

# =============================================================================
# CASOS QUE REQUIEREN REVISIÓN MANUAL
# =============================================================================

MANUAL_REVIEW_REQUIRED = {mapping['municipios_mapping']['manual_review_required']}

PROBLEMATIC_CASES = {mapping['problematic_cases']}

# =============================================================================
# ESTADÍSTICAS DE MAPEO
# =============================================================================

MAPPING_STATS = {{
    'municipios': {{
        'high_confidence': len(MUNICIPIOS_HIGH_CONFIDENCE),
        'medium_confidence': len(MUNICIPIOS_MEDIUM_CONFIDENCE),
        'exact_matches': len(MUNICIPIOS_EXACT_MATCHES),
        'manual_review': len([k for k in {mapping['municipios_mapping']['manual_review_required']}]),
        'missing_in_shapefile': len({mapping['municipios_mapping']['missing_in_shapefile']}),
    }},
    'veredas': {{
        'high_confidence': len(VEREDAS_HIGH_CONFIDENCE),
        'medium_confidence': len(VEREDAS_MEDIUM_CONFIDENCE),
        'exact_matches': len(VEREDAS_EXACT_MATCHES),
        'manual_review': len([k for k in {mapping['veredas_mapping']['manual_review_required']}]),
        'missing_in_shapefile': len({mapping['veredas_mapping']['missing_in_shapefile']}),
    }}
}}

if __name__ == "__main__":
    # Mostrar estadísticas cuando se ejecuta directamente
    print("📊 ESTADÍSTICAS DE MAPEO AUTOMÁTICO")
    print("=" * 50)
    
    for entity_type, stats in MAPPING_STATS.items():
        print(f"\\n{{entity_type.upper()}}:")
        for stat_name, count in stats.items():
            print(f"  {{stat_name.replace('_', ' ').title()}}: {{count}}")
    
    print(f"\\n✅ Mapeos listos para usar en el dashboard")
    print(f"📄 Generado desde: {{MAPPING_METADATA['diagnostic_report']}}")
'''
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _generate_excel_review_file(self, mapping, output_file):
        """Genera archivo Excel para revisión manual."""
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Hoja 1: Mapeos de alta confianza
            high_conf_data = []
            for excel_name, shp_name in mapping['municipios_mapping']['automatic_high_confidence'].items():
                high_conf_data.append({
                    'Tipo': 'Municipio',
                    'Excel': excel_name,
                    'Shapefile': shp_name,
                    'Confianza': '>=95%',
                    'Estado': 'Listo para usar'
                })
            
            for excel_name, shp_name in mapping['veredas_mapping']['automatic_high_confidence'].items():
                high_conf_data.append({
                    'Tipo': 'Vereda',
                    'Excel': excel_name,
                    'Shapefile': shp_name,
                    'Confianza': '>=95%',
                    'Estado': 'Listo para usar'
                })
            
            if high_conf_data:
                pd.DataFrame(high_conf_data).to_excel(writer, sheet_name='Alta_Confianza', index=False)
            
            # Hoja 2: Mapeos que requieren revisión
            review_data = []
            for excel_name, shp_name in mapping['municipios_mapping']['automatic_medium_confidence'].items():
                review_data.append({
                    'Tipo': 'Municipio',
                    'Excel': excel_name,
                    'Shapefile': shp_name,
                    'Confianza': '85-94%',
                    'Estado': 'Revisar antes de usar',
                    'Aprobado': ''
                })
            
            for excel_name, shp_name in mapping['veredas_mapping']['automatic_medium_confidence'].items():
                review_data.append({
                    'Tipo': 'Vereda',
                    'Excel': excel_name,
                    'Shapefile': shp_name,
                    'Confianza': '85-94%',
                    'Estado': 'Revisar antes de usar',
                    'Aprobado': ''
                })
            
            if review_data:
                pd.DataFrame(review_data).to_excel(writer, sheet_name='Revisar', index=False)
            
            # Hoja 3: Casos problemáticos
            problem_data = []
            for excel_name, data in mapping['municipios_mapping']['manual_review_required'].items():
                problem_data.append({
                    'Tipo': 'Municipio',
                    'Excel': excel_name,
                    'Sugerencia': data.get('suggested_match', ''),
                    'Confianza': f"{data.get('confidence', 0)}%",
                    'Estado': 'Revisión manual requerida',
                    'Mapeo_Correcto': ''
                })
            
            if problem_data:
                pd.DataFrame(problem_data).to_excel(writer, sheet_name='Manual', index=False)
    
    def _generate_implementation_guide(self, mapping, output_file):
        """Genera guía de implementación en Markdown."""
        stats = {
            'municipios_auto': len(mapping['municipios_mapping']['automatic_high_confidence']),
            'veredas_auto': len(mapping['veredas_mapping']['automatic_high_confidence']),
            'municipios_review': len(mapping['municipios_mapping']['automatic_medium_confidence']),
            'veredas_review': len(mapping['veredas_mapping']['automatic_medium_confidence']),
        }
        
        content = f"""# Guía de Implementación - Mapeos Automáticos

**Generado:** {mapping['metadata']['generated_at']}
**Fuente:** {mapping['metadata']['diagnostic_report']}

## 📊 Resumen Ejecutivo

- ✅ **Mapeos automáticos listos:** {stats['municipios_auto']} municipios + {stats['veredas_auto']} veredas
- ⚠️ **Requieren revisión:** {stats['municipios_review']} municipios + {stats['veredas_review']} veredas
- 📍 **Campo fuente municipios:** `{mapping['metadata']['municipios_source_field']}`
- 🏘️ **Campo fuente veredas:** `{mapping['metadata']['veredas_source_field']}`

## 🚀 Pasos de Implementación

### 1. Backup de Datos Actuales
```bash
# Crear respaldo antes de implementar cambios
cp -r data/ data_backup_{datetime.now().strftime("%Y%m%d")}/
```

### 2. Integrar Archivo de Mapeos
1. Copiar `automatic_mappings_YYYYMMDD_HHMM.py` a la carpeta `utils/`
2. Importar en `utils/data_processor.py`:
```python
from utils.automatic_mappings_YYYYMMDD_HHMM import (
    apply_shapefile_mapping,
    get_municipio_mapping,
    get_vereda_mapping
)
```

### 3. Modificar Función de Carga de Datos
En `app.py`, función `load_enhanced_datasets()`:

```python
# Después de cargar y normalizar los datos
if not casos_df.empty:
    casos_df = apply_shapefile_mapping(
        casos_df, 
        'municipio_normalizado', 
        'municipios', 
        include_medium_confidence=False  # Solo alta confianza inicialmente
    )
    # Usar la columna mapeada
    casos_df['municipio_normalizado'] = casos_df['municipio_normalizado_mapped']

if not epizootias_df.empty:
    epizootias_df = apply_shapefile_mapping(
        epizootias_df, 
        'municipio_normalizado', 
        'municipios',
        include_medium_confidence=False
    )
    epizootias_df['municipio_normalizado'] = epizootias_df['municipio_normalizado_mapped']
```

### 4. Testing Gradual
1. **Fase 1:** Solo mapeos de alta confianza (`include_medium_confidence=False`)
2. **Fase 2:** Después de validación, incluir confianza media
3. **Fase 3:** Implementar mapeos manuales revisados

### 5. Validación
- [ ] Verificar que los mapas muestren datos correctamente
- [ ] Confirmar que los filtros funcionen sin loops infinitos
- [ ] Validar que las métricas sean consistentes
- [ ] Probar navegación entre niveles del mapa

## ⚠️ Casos que Requieren Atención

### Mapeos de Confianza Media
{len(mapping['municipios_mapping']['automatic_medium_confidence']) + len(mapping['veredas_mapping']['automatic_medium_confidence'])} mapeos requieren revisión antes de implementar.

### Casos Problemáticos Identificados
{len(mapping['problematic_cases']['duplicate_names'])} nombres duplicados encontrados en shapefiles.

## 🔧 Troubleshooting

### Si aparecen loops infinitos:
1. Verificar que los nombres en el mapeo sean exactamente iguales a los del shapefile
2. Revisar logs para identificar nombres problemáticos
3. Agregar mapeos manuales para casos específicos

### Si faltan datos en el mapa:
1. Verificar que el mapeo incluya todos los municipios/veredas necesarios
2. Revisar la lista `missing_in_shapefile` en el archivo de mapeos
3. Considerar agregar estos nombres al shapefile o crear mapeos alternativos

## 📝 Monitoreo Post-Implementación

1. **Logs a revisar:**
   - Nombres que no se pudieron mapear
   - Clics en el mapa que causan errores
   - Filtros que no se sincronizan correctamente

2. **Métricas a validar:**
   - Número total de casos/epizootias debe mantenerse
   - Distribución geográfica debe ser consistente
   - Mapas deben mostrar todos los datos esperados

## 🆘 Rollback Plan

Si hay problemas críticos:
```bash
# Restaurar backup
rm -rf data/
mv data_backup_YYYYMMDD/ data/

# Revertir cambios en código
git checkout HEAD~1 utils/data_processor.py
```

---
**Contacto:** Revisar diagnostic_report.json para detalles técnicos completos.
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def run_full_generation(self):
        """Ejecuta la generación completa de mapeos."""
        logger.info("🚀 Iniciando generación de mapeos automáticos...")
        
        # Generar mapeo completo
        mapping = self.generate_comprehensive_mapping()
        
        # Guardar archivos
        output_files = self.save_mapping_files(mapping)
        
        # Mostrar resumen
        self._print_generation_summary(mapping, output_files)
        
        return output_files
    
    def _print_generation_summary(self, mapping, output_files):
        """Imprime resumen de la generación."""
        print("\n" + "="*60)
        print("📋 RESUMEN DE GENERACIÓN DE MAPEOS")
        print("="*60)
        
        stats = mapping['metadata']
        print(f"📊 Shapefile de municipios: {stats['total_municipios_shapefile']} registros")
        print(f"🏘️ Shapefile de veredas: {stats['total_veredas_shapefile']} registros")
        
        mun_stats = mapping['municipios_mapping']
        ver_stats = mapping['veredas_mapping']
        
        print(f"\n🗺️ MUNICIPIOS:")
        print(f"   ✅ Alta confianza: {len(mun_stats['automatic_high_confidence'])}")
        print(f"   ⚠️ Confianza media: {len(mun_stats['automatic_medium_confidence'])}")
        print(f"   📝 Revisión manual: {len(mun_stats['manual_review_required'])}")
        
        print(f"\n🏘️ VEREDAS:")
        print(f"   ✅ Alta confianza: {len(ver_stats['automatic_high_confidence'])}")
        print(f"   ⚠️ Confianza media: {len(ver_stats['automatic_medium_confidence'])}")
        print(f"   📝 Revisión manual: {len(ver_stats['manual_review_required'])}")
        
        print(f"\n📄 ARCHIVOS GENERADOS:")
        for name, path in output_files.items():
            print(f"   {name}: {path}")
        
        total_auto = (len(mun_stats['automatic_high_confidence']) + 
                     len(ver_stats['automatic_high_confidence']))
        total_review = (len(mun_stats['automatic_medium_confidence']) + 
                       len(ver_stats['automatic_medium_confidence']))
        
        print(f"\n💡 RECOMENDACIONES:")
        print(f"   1. Implementar {total_auto} mapeos de alta confianza inmediatamente")
        print(f"   2. Revisar {total_review} mapeos de confianza media en Excel")
        print(f"   3. Seguir guía de implementación paso a paso")
        print(f"   4. Hacer backup antes de implementar cambios")
        
        print("\n" + "="*60)


def main():
    """Función principal."""
    print("🔧 GENERADOR DE MAPEOS AUTOMÁTICOS - DASHBOARD FIEBRE AMARILLA")
    print("="*60)
    
    try:
        # Verificar que existe el reporte de diagnóstico
        diagnostic_file = "diagnostic_report.json"
        if not Path(diagnostic_file).exists():
            print(f"❌ Error: No se encuentra {diagnostic_file}")
            print(f"💡 Ejecute primero el script de diagnóstico")
            return
        
        # Crear generador y ejecutar
        generator = MappingGenerator(diagnostic_file)
        output_files = generator.run_full_generation()
        
        print(f"\n✅ Generación completada exitosamente!")
        print(f"📂 Archivos guardados en: mapping_outputs/")
        print(f"\n🚀 Próximos pasos:")
        print(f"   1. Revisar archivo Excel para validar mapeos")
        print(f"   2. Seguir guía de implementación (archivo .md)")
        print(f"   3. Integrar archivo Python en el dashboard")
        print(f"   4. Probar funcionamiento paso a paso")
        
    except Exception as e:
        logger.error(f"❌ Error durante la generación: {e}")
        print(f"\n❌ Error: {e}")
        print(f"💡 Revise el reporte de diagnóstico y verifique las rutas")


if __name__ == "__main__":
    main()