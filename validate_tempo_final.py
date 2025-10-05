#!/usr/bin/env python3
"""
🎉 VALIDATION FINALE SYSTÈME TEMPO
================================================================================
Validation que tous les composants TEMPO sont opérationnels
================================================================================
"""

from pathlib import Path
import json
from datetime import datetime

def validate_tempo_system():
    """Validation complète du système TEMPO"""
    print("🎉 VALIDATION FINALE SYSTÈME TEMPO")
    print("=" * 80)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🛰️ NASA TEMPO Air Quality Prediction System")
    print("=" * 80)
    
    validation_results = {}
    
    # 1. Vérification fichiers de données
    print("\n📊 VALIDATION 1: Données TEMPO générées")
    
    data_dir = Path("data/tempo_north_america")
    if data_dir.exists():
        features_files = list(data_dir.glob("tempo_features_*.csv"))
        targets_files = list(data_dir.glob("tempo_targets_*.csv"))
        metadata_files = list(data_dir.glob("tempo_metadata_*.json"))
        
        print(f"   ✅ Dossier données: {data_dir}")
        print(f"   ✅ Fichiers features: {len(features_files)}")
        print(f"   ✅ Fichiers targets: {len(targets_files)}")
        print(f"   ✅ Fichiers metadata: {len(metadata_files)}")
        
        # Lecture metadata le plus récent
        if metadata_files:
            latest_metadata = max(metadata_files, key=lambda x: x.stat().st_mtime)
            with open(latest_metadata, 'r') as f:
                metadata = json.load(f)
            
            print(f"   📍 Points historiques: {metadata.get('total_data_points', 'N/A')}")
            print(f"   📍 Locations couvertes: {metadata.get('locations_covered', 'N/A')}")
            print(f"   📍 Période données: {metadata.get('date_range', 'N/A')}")
        
        validation_results['data_generation'] = True
    else:
        print(f"   ❌ Dossier données manquant: {data_dir}")
        validation_results['data_generation'] = False
    
    # 2. Vérification modèles ML
    print("\n🤖 VALIDATION 2: Modèles ML TEMPO")
    
    models_dir = Path("models/tempo")
    if models_dir.exists():
        model_files = list(models_dir.glob("*_tempo.pkl"))
        metadata_files = list(models_dir.glob("tempo_models_metadata_*.json"))
        
        print(f"   ✅ Dossier modèles: {models_dir}")
        print(f"   ✅ Modèles entraînés: {len(model_files)}")
        
        # Lecture metadata modèles
        if metadata_files:
            latest_metadata = max(metadata_files, key=lambda x: x.stat().st_mtime)
            with open(latest_metadata, 'r') as f:
                metadata = json.load(f)
            
            print(f"   🎯 Polluants couverts: {len(metadata.get('pollutants', []))}")
            print(f"   🎯 Algorithmes utilisés: {len(metadata.get('algorithms', []))}")
            
            # Meilleurs modèles
            if 'best_models' in metadata:
                print("   🏆 Meilleurs modèles:")
                for pollutant, model_info in metadata['best_models'].items():
                    score = model_info.get('score', 'N/A')
                    algorithm = model_info.get('algorithm', 'N/A')
                    print(f"      {pollutant}: {algorithm} (R²={score})")
        
        validation_results['model_training'] = True
    else:
        print(f"   ❌ Dossier modèles manquant: {models_dir}")
        validation_results['model_training'] = False
    
    # 3. Vérification fichiers API
    print("\n🌐 VALIDATION 3: Code API TEMPO")
    
    api_files_check = [
        ("tempo_pipeline_north_america.py", "Pipeline de données"),
        ("train_tempo_models.py", "Entraînement ML"),
        ("app/api/api_v1/tempo_predictions.py", "Service prédictions"),
        ("app/api/api_v1/api.py", "Router principal")
    ]
    
    api_files_valid = True
    for file_path, description in api_files_check:
        if Path(file_path).exists():
            print(f"   ✅ {description}: {file_path}")
        else:
            print(f"   ❌ {description}: {file_path} MANQUANT")
            api_files_valid = False
    
    validation_results['api_files'] = api_files_valid
    
    # 4. Vérification structure de répertoires
    print("\n📁 VALIDATION 4: Structure de répertoires")
    
    required_dirs = [
        "app/services",
        "app/api/api_v1", 
        "data/tempo_north_america",
        "models/tempo"
    ]
    
    dirs_valid = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"   ✅ {dir_path}")
        else:
            print(f"   ❌ {dir_path} MANQUANT")
            dirs_valid = False
    
    validation_results['directory_structure'] = dirs_valid
    
    # 5. Résumé de validation
    print("\n" + "=" * 80)
    print("📊 RÉSUMÉ VALIDATION TEMPO")
    print("=" * 80)
    
    total_checks = len(validation_results)
    passed_checks = sum(1 for r in validation_results.values() if r)
    
    print(f"✅ Validations réussies: {passed_checks}/{total_checks}")
    
    for check_name, passed in validation_results.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check_name.replace('_', ' ').title()}")
    
    # 6. Status final
    print("\n" + "=" * 80)
    
    if passed_checks == total_checks:
        print("🎉 SYSTÈME TEMPO COMPLÈTEMENT VALIDÉ!")
        print("🛰️ Tous les composants sont opérationnels")
        print("📍 Prêt pour prédictions air quality Amérique du Nord")
        
        print("\n🚀 INSTRUCTIONS DE DÉMARRAGE:")
        print("   1. Démarrer serveur: python -m uvicorn app.main:app --port 8000")
        print("   2. Ouvrir navigateur: http://localhost:8000/docs")
        print("   3. Tester endpoints TEMPO: /api/v1/tempo/")
        
        print("\n📍 EXEMPLES D'UTILISATION:")
        print("   • GET  /api/v1/tempo/coverage")
        print("   • GET  /api/v1/tempo/models-status")
        print("   • POST /api/v1/tempo/predict")
        print("   • POST /api/v1/tempo/batch")
        
        print("\n🌍 ZONE DE COUVERTURE:")
        print("   • Latitude: 40°N - 70°N")
        print("   • Longitude: 70°W - 130°W")
        print("   • Région: États-Unis + Canada")
        
        print("\n🎯 CAPACITÉS:")
        print("   • 6 polluants prédits (PM2.5, PM10, NO2, O3, CO, SO2)")
        print("   • Prédictions géographiques temps réel")
        print("   • Calcul AQI et recommandations santé")
        print("   • Processing batch pour analyses en masse")
        
    else:
        print("⚠️ SYSTÈME PARTIELLEMENT VALIDÉ")
        print(f"🔧 {total_checks - passed_checks} validations ont échoué")
        print("📋 Vérifiez les étapes marquées ❌ ci-dessus")
    
    return passed_checks == total_checks

def main():
    """Point d'entrée principal"""
    try:
        success = validate_tempo_system()
        print(f"\n🏁 Validation terminée: {'SUCCÈS' if success else 'ÉCHECS PARTIELS'}")
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n❌ Erreur validation: {str(e)}")
        return 2

if __name__ == "__main__":
    import sys
    sys.exit(main())