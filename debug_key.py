#!/usr/bin/env python3
"""
Script para debuggear específicamente el private_key
"""

import toml

def main():
    print("🔑 Debug del Private Key")
    print("=" * 40)
    
    try:
        with open('.streamlit/secrets.toml', 'r') as f:
            secrets = toml.load(f)
        
        private_key = secrets['gcp_service_account']['private_key']
        
        print(f"📏 Longitud total: {len(private_key)} caracteres")
        print(f"🏁 Primeros 50 caracteres: {private_key[:50]}")
        print(f"🔚 Últimos 50 caracteres: {private_key[-50:]}")
        
        # Verificaciones específicas
        if private_key.startswith('-----BEGIN PRIVATE KEY-----'):
            print("✅ Comienza correctamente")
        else:
            print("❌ NO comienza correctamente")
        
        if private_key.endswith('-----END PRIVATE KEY-----'):
            print("✅ Termina correctamente") 
        else:
            print("❌ NO termina correctamente")
            print(f"   Realmente termina con: '{private_key[-30:]}'")
        
        # Contar líneas
        lines = private_key.split('\\n')
        print(f"📊 Número de líneas: {len(lines)}")
        
        if len(lines) >= 25:
            print("✅ Número de líneas parece correcto")
        else:
            print("⚠️ Pocas líneas, puede estar truncado")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()