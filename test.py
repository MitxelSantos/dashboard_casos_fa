#!/usr/bin/env python3
"""
Script para auditar y corregir el flujo de datos filtrados en el dashboard.
Identifica dónde se pierden los datos filtrados y aplica correcciones.
"""

import os
import re
from pathlib import Path

class FilterFlowAuditor:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.issues = []
        self.corrections = []
        
    def audit_file(self, file_path):
        """Audita un archivo Python en busca de problemas de filtrado."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
            issues = []
            
            # 1. Buscar funciones que recalculan métricas sin usar data_filtered
            metric_functions = [
                'calculate_basic_metrics',
                'get_latest_case_info', 
                'create_summary_by_location',
                'prepare_dataframe_for_display'
            ]
            
            for i, line in enumerate(lines):
                # Buscar llamadas a funciones de métricas
                for func in metric_functions:
                    if func in line and 'def ' not in line:
                        # Verificar si usa datos filtrados
                        if 'data_filtered' not in line and 'casos' in line and 'epizootias' in line:
                            issues.append({
                                'type': 'metric_recalc',
                                'line': i + 1,
                                'content': line.strip(),
                                'function': func,
                                'file': file_path
                            })
                
                # Buscar acceso directo a data original
                if re.search(r'data\["casos"\]|data\["epizootias"\]', line):
                    if 'data_filtered' not in line:
                        issues.append({
                            'type': 'direct_data_access',
                            'line': i + 1,
                            'content': line.strip(),
                            'file': file_path
                        })
                
                # Buscar funciones que no reciben data_filtered como parámetro
                if line.strip().startswith('def ') and '(' in line:
                    func_def = line.strip()
                    if any(keyword in func_def.lower() for keyword in ['metric', 'summary', 'analysis', 'chart']):
                        if 'data_filtered' not in func_def and ('casos' in func_def or 'epizootias' in func_def):
                            issues.append({
                                'type': 'missing_filtered_param',
                                'line': i + 1,
                                'content': line.strip(),
                                'file': file_path
                            })
            
            return issues
            
        except Exception as e:
            print(f"Error auditando {file_path}: {e}")
            return []
    
    def audit_project(self):
        """Audita todo el proyecto."""
        print("🔍 Iniciando auditoría del flujo de filtrado...")
        
        # Archivos a auditar
        files_to_audit = [
            'vistas/mapas.py',
            'vistas/tablas.py', 
            'vistas/comparativo.py',
            'utils/data_processor.py',
            'components/filters.py'
        ]
        
        all_issues = []
        
        for file_path in files_to_audit:
            full_path = self.project_root / file_path
            if full_path.exists():
                print(f"📄 Auditando {file_path}...")
                issues = self.audit_file(full_path)
                all_issues.extend(issues)
                
                if issues:
                    print(f"  ⚠️ {len(issues)} problemas encontrados")
                else:
                    print(f"  ✅ Sin problemas aparentes")
            else:
                print(f"  ❌ Archivo no encontrado: {file_path}")
        
        self.issues = all_issues
        return all_issues
    
    def generate_report(self):
        """Genera reporte detallado de problemas."""
        if not self.issues:
            print("✅ No se encontraron problemas de filtrado!")
            return
        
        print(f"\n📊 REPORTE DE AUDITORÍA - {len(self.issues)} problemas encontrados:")
        print("=" * 80)
        
        # Agrupar por tipo
        by_type = {}
        for issue in self.issues:
            issue_type = issue['type']
            if issue_type not in by_type:
                by_type[issue_type] = []
            by_type[issue_type].append(issue)
        
        for issue_type, issues in by_type.items():
            print(f"\n🔸 {issue_type.upper().replace('_', ' ')} ({len(issues)} casos):")
            print("-" * 50)
            
            for issue in issues[:5]:  # Mostrar solo primeros 5
                print(f"  📁 {issue['file']}")
                print(f"  📍 Línea {issue['line']}: {issue['content']}")
                if 'function' in issue:
                    print(f"  🔧 Función: {issue['function']}")
                print()
            
            if len(issues) > 5:
                print(f"  ... y {len(issues) - 5} más")
                print()
    
    def suggest_corrections(self):
        """Sugiere correcciones específicas."""
        print("\n🛠️ CORRECCIONES SUGERIDAS:")
        print("=" * 80)
        
        # Agrupar correcciones por archivo
        by_file = {}
        for issue in self.issues:
            file_path = issue['file']
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append(issue)
        
        for file_path, issues in by_file.items():
            print(f"\n📁 {file_path}:")
            print("-" * 40)
            
            # Agrupar por tipo de corrección
            corrections = {
                'metric_recalc': [],
                'direct_data_access': [],
                'missing_filtered_param': []
            }
            
            for issue in issues:
                corrections[issue['type']].append(issue)
            
            # Correcciones específicas por tipo
            if corrections['metric_recalc']:
                print("🔧 Corregir recálculos de métricas:")
                for issue in corrections['metric_recalc']:
                    func_name = issue['function']
                    print(f"  • Línea {issue['line']}: Usar data_filtered para {func_name}")
                    print(f"    Cambiar: {issue['content']}")
                    print(f"    Por: {func_name}(casos_filtrados, epizootias_filtradas)")
                print()
            
            if corrections['direct_data_access']:
                print("🔧 Eliminar acceso directo a datos no filtrados:")
                for issue in corrections['direct_data_access']:
                    print(f"  • Línea {issue['line']}: {issue['content']}")
                    print(f"    Usar data_filtered en lugar de data")
                print()
            
            if corrections['missing_filtered_param']:
                print("🔧 Agregar parámetro data_filtered:")
                for issue in corrections['missing_filtered_param']:
                    print(f"  • Línea {issue['line']}: {issue['content']}")
                    print(f"    Agregar data_filtered como parámetro")
                print()

def main():
    """Función principal."""
    print("🚀 Auditoría de Filtrado - Dashboard Fiebre Amarilla")
    print("=" * 60)
    
    auditor = FilterFlowAuditor()
    
    # Auditar proyecto
    issues = auditor.audit_project()
    
    # Generar reporte
    auditor.generate_report()
    
    # Sugerir correcciones
    auditor.suggest_corrections()
    
    print("\n" + "=" * 60)
    print("✅ Auditoría completada. Revisar correcciones sugeridas.")

if __name__ == "__main__":
    main()