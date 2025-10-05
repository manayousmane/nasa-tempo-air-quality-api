#!/usr/bin/env python3
"""
🔍 ANALYSE DES DONNÉES COLLECTÉES
================================================================================
Analyse la structure des données pour définir le pipeline ML
================================================================================
"""

import asyncio
import sys
import json
from datetime import datetime

sys.path.append('.')

from app.services.air_quality_service import AirQualityService

async def analyze_data_structure():
    """Analyse complète des données collectées"""
    print("🔍 ANALYSE DES DONNÉES POUR PIPELINE ML")
    print("=" * 80)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    try:
        service = AirQualityService()
        
        # Test locations diverses pour voir la variété des données
        locations = [
            (40.7128, -74.0060, "New York"),
            (34.0522, -118.2437, "Los Angeles"), 
            (48.8566, 2.3522, "Paris"),
            (35.6762, 139.6503, "Tokyo")
        ]
        
        all_data = []
        
        for lat, lon, city in locations:
            print(f"\n📍 Analyse données: {city}")
            print("-" * 50)
            
            # Collecte données AQI
            aqi_data = await service.get_air_quality_indices(lat, lon)
            
            if aqi_data:
                print(f"✅ Données reçues pour {city}")
                print(f"   Structure: {list(aqi_data.keys())}")
                
                # Analyse measurements
                if 'measurements' in aqi_data:
                    measurements = aqi_data['measurements']
                    print(f"   📊 Polluants: {len(measurements)}")
                    
                    for measurement in measurements:
                        pollutant = measurement.get('pollutant', 'Unknown')
                        value = measurement.get('value', 'N/A')
                        unit = measurement.get('unit', 'N/A')
                        source = measurement.get('source', 'N/A')
                        timestamp = measurement.get('timestamp', 'N/A')
                        
                        print(f"      • {pollutant}: {value} {unit} (source: {source})")
                
                # Analyse metadata
                if 'metadata' in aqi_data:
                    meta = aqi_data['metadata']
                    print(f"   🕐 Timestamp: {meta.get('timestamp', 'N/A')}")
                    print(f"   📡 Sources: {meta.get('sources_used', [])}")
                    print(f"   ⏱️ Collection time: {meta.get('collection_time_ms', 'N/A')}ms")
                
                # Analyse indices
                if 'indices' in aqi_data:
                    indices = aqi_data['indices']
                    print(f"   📈 Indices calculés: {list(indices.keys())}")
                    
                    for index_name, index_data in indices.items():
                        overall_aqi = index_data.get('overall_aqi', 'N/A')
                        category = index_data.get('category', 'N/A')
                        print(f"      • {index_name}: {overall_aqi} ({category})")
                
                all_data.append({
                    'location': city,
                    'coordinates': (lat, lon),
                    'data': aqi_data
                })
            else:
                print(f"❌ Aucune donnée pour {city}")
        
        # Analyse globale
        print("\n" + "=" * 80)
        print("📊 ANALYSE GLOBALE POUR PIPELINE ML")
        print("=" * 80)
        
        if all_data:
            # Polluants disponibles
            all_pollutants = set()
            all_sources = set()
            
            for location_data in all_data:
                data = location_data['data']
                if 'measurements' in data:
                    for measurement in data['measurements']:
                        all_pollutants.add(measurement.get('pollutant', 'Unknown'))
                        all_sources.add(measurement.get('source', 'Unknown'))
            
            print(f"🌡️ Polluants disponibles ({len(all_pollutants)}):")
            for pollutant in sorted(all_pollutants):
                print(f"   • {pollutant}")
            
            print(f"\n📡 Sources de données ({len(all_sources)}):")
            for source in sorted(all_sources):
                print(f"   • {source}")
            
            # Structure pour ML
            print(f"\n🤖 RECOMMANDATIONS PIPELINE ML:")
            print("   ✅ Features disponibles: Coordonnées + polluants + météo")
            print("   ✅ Targets possibles: AQI futur, concentrations polluants")
            print("   ✅ Données temporelles: Timestamps disponibles")
            print("   ✅ Données géospatiales: Coordonnées précises")
            
            # Prochaines étapes
            print(f"\n🎯 PROCHAINES ÉTAPES PIPELINE:")
            print("   1. Création du data collector pour historique")
            print("   2. Feature engineering (temporal, spatial, météo)")
            print("   3. Preprocessing et normalisation")
            print("   4. Modèles ML (LSTM, XGBoost, Random Forest)")
            print("   5. Pipeline de prédiction temps réel")
            
        else:
            print("❌ Aucune donnée collectée - problème d'intégration API")
        
        return all_data
        
    except Exception as e:
        print(f"❌ Erreur analyse: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    data = await analyze_data_structure()
    if data:
        print(f"\n🎉 Analyse terminée - {len(data)} locations analysées")
    else:
        print(f"\n⚠️ Analyse échouée")

if __name__ == "__main__":
    asyncio.run(main())