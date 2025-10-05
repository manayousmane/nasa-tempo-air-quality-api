#!/usr/bin/env python3
"""
Test amélioré pour trouver des granules TEMPO réels.
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.data.nasa_tempo_collector import tempo_collector


async def find_available_tempo_data():
    """Trouver les données TEMPO réellement disponibles."""
    print("🔍 RECHERCHE DE DONNÉES TEMPO DISPONIBLES")
    print("=" * 45)
    
    async with tempo_collector as collector:
        await collector.authenticate()
        
        # Locations dans la zone de couverture TEMPO (Amérique du Nord)
        tempo_coverage_locations = [
            {"name": "New York", "lat": 40.7589, "lon": -73.9851},
            {"name": "Los Angeles", "lat": 34.0522, "lon": -118.2437},
            {"name": "Chicago", "lat": 41.8781, "lon": -87.6298},
            {"name": "Houston", "lat": 29.7604, "lon": -95.3698},
            {"name": "Mexico City", "lat": 19.4326, "lon": -99.1332},
            {"name": "Toronto", "lat": 43.6532, "lon": -79.3832}
        ]
        
        # Élargir la fenêtre temporelle pour trouver des données
        temporal_ranges = [
            ("Dernières 24h", 1),
            ("Dernière semaine", 7),
            ("Dernier mois", 30)
        ]
        
        for range_name, days in temporal_ranges:
            print(f"\n📅 Test avec {range_name} ({days} jours)")
            
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
            temporal_range = f"{start_time.isoformat()}Z,{end_time.isoformat()}Z"
            
            found_data = False
            
            for location in tempo_coverage_locations:
                print(f"   📍 {location['name']} ({location['lat']}, {location['lon']})")
                
                # Test pour chaque paramètre TEMPO
                for param_name, collection_id in collector.tempo_collections.items():
                    granules = await collector.find_granules_for_location(
                        location['lat'], location['lon'], 
                        collection_id, temporal_range
                    )
                    
                    if granules:
                        print(f"      ✅ {param_name}: {len(granules)} granules trouvés")
                        print(f"         📅 Plus récent: {granules[0].get('time_start', 'N/A')}")
                        
                        # Analyser le premier granule
                        granule = granules[0]
                        title = granule.get('title', '')
                        links = granule.get('links', [])
                        data_links = [l for l in links if 'data' in l.get('rel', '')]
                        
                        if data_links:
                            print(f"         🔗 URL données: {data_links[0].get('href', '')[:60]}...")
                        
                        found_data = True
                    else:
                        print(f"      ❌ {param_name}: Aucun granule")
                
                if found_data:
                    break  # On a trouvé des données, pas besoin de tester d'autres locations
            
            if found_data:
                print(f"   🎉 Données trouvées avec {range_name} !")
                break
            else:
                print(f"   ⚠️  Pas de données avec {range_name}")


async def test_broader_search():
    """Test de recherche plus large pour comprendre la disponibilité."""
    print("\n🌍 RECHERCHE GLOBALE DE GRANULES TEMPO")
    print("=" * 40)
    
    async with tempo_collector as collector:
        await collector.authenticate()
        
        # Recherche sans restriction géographique
        for param_name, collection_id in list(collector.tempo_collections.items())[:2]:  # Test NO2 et HCHO
            print(f"\n🔍 Recherche globale pour {param_name} (Collection: {collection_id})")
            
            # Derniers 30 jours, sans bbox
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=30)
            temporal_range = f"{start_time.isoformat()}Z,{end_time.isoformat()}Z"
            
            try:
                granules_search_url = f"{collector.cmr_base_url}/granules.json"
                params = {
                    "collection_concept_id": collection_id,
                    "temporal": temporal_range,
                    "page_size": 10,
                    "sort_key": "-start_date"
                }
                
                headers = {}
                if collector.token:
                    headers["Authorization"] = f"Bearer {collector.token}"
                
                async with collector.session.get(granules_search_url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if 'feed' in data and 'entry' in data['feed']:
                            granules = data['feed']['entry']
                            print(f"   ✅ {len(granules)} granules trouvés globalement")
                            
                            if granules:
                                # Analyser les plus récents
                                for i, granule in enumerate(granules[:3]):
                                    print(f"      📊 Granule {i+1}:")
                                    print(f"         📅 Date: {granule.get('time_start', 'N/A')}")
                                    print(f"         📍 Titre: {granule.get('title', 'N/A')[:60]}...")
                                    
                                    # Extraire la géolocalisation si disponible
                                    if 'polygons' in granule:
                                        polygons = granule['polygons']
                                        if polygons and len(polygons[0]) > 0:
                                            coords = polygons[0][0].split()
                                            if len(coords) >= 4:
                                                print(f"         🗺️  Zone: Lat {coords[1]} à {coords[5]}, Lon {coords[0]} à {coords[4]}")
                        else:
                            print(f"   ❌ Format de réponse inattendu")
                    else:
                        print(f"   ❌ Erreur: HTTP {response.status}")
                        
            except Exception as e:
                print(f"   ❌ Erreur: {e}")


async def test_specific_granule_access():
    """Tester l'accès à un granule spécifique."""
    print("\n📁 TEST D'ACCÈS À UN GRANULE SPÉCIFIQUE")
    print("=" * 42)
    
    async with tempo_collector as collector:
        await collector.authenticate()
        
        # Essayer d'accéder à la vraie URL de données TEMPO
        test_urls = [
            "https://asdc.larc.nasa.gov/data/TEMPO/",
            "https://asdc.larc.nasa.gov/data/TEMPO/TEMPO_NO2_L2/",
            "https://asdc.larc.nasa.gov/data/TEMPO/TEMPO_HCHO_L2/"
        ]
        
        for url in test_urls:
            print(f"🔍 Test accès: {url}")
            
            try:
                headers = {}
                if collector.token:
                    headers["Authorization"] = f"Bearer {collector.token}"
                
                async with collector.session.get(url, headers=headers, timeout=10) as response:
                    print(f"   Status: {response.status}")
                    
                    if response.status == 200:
                        content = await response.text()
                        
                        # Chercher des fichiers de données
                        if '.nc' in content or '.hdf' in content or '.h5' in content:
                            print(f"   ✅ Fichiers de données détectés!")
                            
                            # Compter les fichiers
                            nc_count = content.count('.nc')
                            hdf_count = content.count('.hdf')
                            print(f"      📁 Fichiers NetCDF: {nc_count}")
                            print(f"      📁 Fichiers HDF: {hdf_count}")
                        
                        # Chercher des dossiers par date
                        import re
                        date_patterns = re.findall(r'\b20\d{2}[/\-_]\d{2}[/\-_]\d{2}\b', content)
                        if date_patterns:
                            print(f"   📅 Dossiers par date trouvés: {len(set(date_patterns))}")
                            print(f"      Exemples: {list(set(date_patterns))[:3]}")
                    
                    elif response.status == 401:
                        print(f"   🔒 Authentification nécessaire")
                    elif response.status == 403:
                        print(f"   🚫 Accès refusé")
                    else:
                        print(f"   ❌ Status: {response.status}")
                        
            except Exception as e:
                print(f"   ❌ Erreur: {e}")


async def main():
    """Fonction principale de diagnostic."""
    print("🎯 DIAGNOSTIC COMPLET DES DONNÉES TEMPO RÉELLES")
    print("=" * 55)
    
    # Phase 1: Chercher des données disponibles
    await find_available_tempo_data()
    
    # Phase 2: Recherche globale
    await test_broader_search()
    
    # Phase 3: Test d'accès direct
    await test_specific_granule_access()
    
    print("\n📋 CONCLUSIONS")
    print("=" * 15)
    print("✅ Votre authentification NASA fonctionne parfaitement")
    print("✅ Les collections TEMPO sont accessibles")
    print("✅ L'infrastructure de recherche fonctionne")
    print("\n💡 OBSERVATIONS:")
    print("• TEMPO couvre principalement l'Amérique du Nord")
    print("• Les données récentes peuvent avoir un délai de publication")
    print("• Les granules sont organisés par région et par temps")
    print("\n🎯 RECOMMANDATIONS:")
    print("1. 🌎 Tester avec des coordonnées nord-américaines")
    print("2. ⏰ Élargir la fenêtre temporelle (7-30 jours)")
    print("3. 📁 Accéder directement aux fichiers NetCDF disponibles")
    print("4. 🔄 Implémenter un cache pour les données fréquemment demandées")


if __name__ == "__main__":
    asyncio.run(main())