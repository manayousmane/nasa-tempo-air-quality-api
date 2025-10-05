#!/usr/bin/env python3
"""
🚀 DÉMARRAGE SERVEUR NASA TEMPO API
================================================================================
Démarre le serveur FastAPI avec tous les endpoints
================================================================================
"""

import uvicorn
import sys
from pathlib import Path

def main():
    """Démarre le serveur"""
    print("🛰️ NASA TEMPO AIR QUALITY API")
    print("=" * 50)
    print("🚀 Démarrage serveur...")
    
    try:
        # Configuration serveur
        config = uvicorn.Config(
            app="app.main:app",
            host="127.0.0.1",
            port=8001,  # Port différent pour éviter les conflits
            reload=True,
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        
        print("\n📋 ENDPOINTS DISPONIBLES:")
        print("🌍 Location Search:")
        print("   GET /api/v1/location-search/available-locations")
        print("   GET /api/v1/location-search/suggest?q=new")
        print("   POST /api/v1/location-search/search")
        print("   POST /api/v1/location-search/search-multiple")
        
        print("🛰️ TEMPO Predictions:")
        print("   GET /api/v1/tempo/coverage")
        print("   POST /api/v1/tempo/predict")
        print("   POST /api/v1/tempo/batch")
        
        print("🌬️ Air Quality:")
        print("   GET /api/v1/air-quality/current")
        print("   POST /api/v1/air-quality/batch")
        
        print("\n📖 Documentation: http://127.0.0.1:8001/docs")
        print("🔧 Health Check: http://127.0.0.1:8001/health")
        print("\n" + "=" * 50)
        
        # Démarrage
        server.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Serveur arrêté par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur démarrage serveur: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()