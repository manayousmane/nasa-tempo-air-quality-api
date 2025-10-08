"""
Analyse détaillée des sources de données réelles utilisées dans l'API
"""

import sys
import asyncio
import aiohttp
sys.path.append('.')

from app.connectors.real_data_connector import RealDataConnector

async def analyze_data_sources():
    print("🔍 ANALYSE DÉTAILLÉE DES SOURCES DE DONNÉES")
    print("="*60)
    
    connector = RealDataConnector()
    
    # Test 1: OpenAQ API
    print("\n1️⃣ TEST OpenAQ API")
    print("-" * 30)
    
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://api.openaq.org/v2/latest"
            params = {
                'coordinates': '48.8566,2.3522',
                'radius': 25000,
                'limit': 5
            }
            
            async with session.get(url, params=params, timeout=10) as response:
                print(f"📡 URL: {url}")
                print(f"📊 Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    results = data.get('results', [])
                    print(f"✅ OPENAQ FONCTIONNE: {len(results)} stations trouvées")
                    
                    if results:
                        print("📍 Stations disponibles:")
                        for i, result in enumerate(results[:3]):
                            location = result.get('location', 'Unknown')
                            city = result.get('city', 'Unknown')
                            measurements = result.get('measurements', [])
                            print(f"   Station {i+1}: {location} à {city}")
                            print(f"   Mesures: {len(measurements)} paramètres")
                    else:
                        print("⚠️ Pas de stations dans la zone")
                        
                elif response.status == 410:
                    print("❌ OPENAQ API DEPRECATED (410 Gone)")
                    print("🔄 Service potentiellement migré vers nouvelle version")
                else:
                    print(f"❌ OPENAQ ERROR: Status {response.status}")
                    
    except Exception as e:
        print(f"❌ OPENAQ EXCEPTION: {e}")
    
    # Test 2: NASA TEMPO (méthode actuelle)
    print("\n2️⃣ TEST NASA TEMPO")
    print("-" * 30)
    
    async with connector:
        try:
            result = await connector._get_nasa_tempo_data(48.8566, 2.3522)
            if result:
                data_source = result.get('data_source', 'Unknown')
                print(f"✅ NASA TEMPO: {data_source}")
                print(f"📊 Type: {result.get('region_type', 'Unknown')}")
                print(f"🎯 AQI généré: {result.get('aqi', 'N/A')}")
                
                # Vérifier si c'est vraiment des données TEMPO ou des estimations
                if 'Estimation' in data_source:
                    print("⚠️ ATTENTION: Ce sont des ESTIMATIONS, pas de vraies données TEMPO")
                else:
                    print("✅ Données NASA TEMPO authentiques")
            else:
                print("❌ NASA TEMPO: Aucune donnée")
        except Exception as e:
            print(f"❌ NASA TEMPO ERROR: {e}")
    
    # Test 3: Autres APIs mentionnées
    print("\n3️⃣ TEST AUTRES APIS MENTIONNÉES")
    print("-" * 30)
    
    apis_to_test = [
        ("NOAA", "https://api.weather.gov"),
        ("NASA Earthdata", "https://cmr.earthdata.nasa.gov"),
        ("NASA AIRS", "https://airs.jpl.nasa.gov"),
    ]
    
    async with aiohttp.ClientSession() as session:
        for name, url in apis_to_test:
            try:
                async with session.get(url, timeout=5) as response:
                    print(f"📡 {name}: Status {response.status}")
                    if response.status == 200:
                        print(f"   ✅ {name} accessible")
                    else:
                        print(f"   ⚠️ {name} status {response.status}")
            except Exception as e:
                print(f"   ❌ {name}: {str(e)[:50]}...")

async def analyze_current_data_flow():
    print("\n🔄 ANALYSE DU FLUX DE DONNÉES ACTUEL")
    print("="*60)
    
    connector = RealDataConnector()
    
    # Test avec coordonnées de Paris
    lat, lon = 48.8566, 2.3522
    
    async with connector:
        print(f"\n📍 Test avec Paris ({lat}, {lon})")
        print("-" * 40)
        
        # Suivre le flux de données tel qu'implémenté
        print("1. Tentative OpenAQ...")
        openaq_result = await connector._get_openaq_current(lat, lon)
        
        if openaq_result:
            print("   ✅ OpenAQ a fourni des données")
            print(f"   📊 Source: {openaq_result.get('data_source')}")
        else:
            print("   ❌ OpenAQ a échoué, passage à NASA TEMPO...")
            
            tempo_result = await connector._get_nasa_tempo_data(lat, lon)
            if tempo_result:
                print("   ✅ NASA TEMPO a fourni des données")
                print(f"   📊 Source: {tempo_result.get('data_source')}")
                
                # Analyser si c'est vraiment du TEMPO
                if 'Estimation' in tempo_result.get('data_source', ''):
                    print("   ⚠️ ATTENTION: Données estimées, pas réelles")
                    print("   🔍 Méthode: Patterns basés sur type de région")
                    print(f"   🏙️ Type région: {tempo_result.get('region_type')}")
            else:
                print("   ❌ NASA TEMPO a aussi échoué")
                
                print("   🔄 Passage aux estimations régionales...")
                fallback_result = await connector._get_regional_estimation(lat, lon)
                print(f"   📊 Fallback source: {fallback_result.get('data_source')}")

def analyze_code_reality():
    print("\n💻 ANALYSE DU CODE RÉEL")
    print("="*60)
    
    print("\n🔍 Lecture du code source...")
    
    # Analyser ce qui est vraiment implémenté
    print("\n📋 SOURCES DÉCLARÉES vs IMPLÉMENTÉES:")
    print("-" * 40)
    
    declared_sources = [
        "🛰️ NASA TEMPO Satellite",
        "🌐 OpenAQ Ground Stations", 
        "🌤️ NOAA Weather Data",
        "🏥 WHO Air Quality Standards",
        "📡 NASA AIRS Atmospheric Sounder"
    ]
    
    print("Sources annoncées dans l'API:")
    for source in declared_sources:
        print(f"   {source}")
    
    print("\nSources réellement implémentées:")
    print("   ✅ OpenAQ - Tentative d'appel (mais API deprecated)")
    print("   ⚠️ NASA TEMPO - Estimations locales, pas vraies données")
    print("   ❌ NOAA - Non implémenté (juste URL définie)")
    print("   ❌ WHO - Non implémenté (juste standards)")
    print("   ❌ NASA AIRS - Non implémenté (juste URL définie)")
    
    print("\nCe qui fonctionne vraiment:")
    print("   🎯 Estimations basées sur types de régions")
    print("   🗺️ Base de données de villes codée en dur")
    print("   🎲 Génération de valeurs dans des plages réalistes")
    print("   🔄 Variations temporelles simulées")

async def main():
    await analyze_data_sources()
    await analyze_current_data_flow()
    analyze_code_reality()
    
    print("\n" + "="*60)
    print("🎯 VERDICT FINAL")
    print("="*60)
    
    print("\n❌ PROBLÈMES IDENTIFIÉS:")
    print("   • OpenAQ API retourne 410 (Gone) - Service deprecated")
    print("   • NASA TEMPO utilise des estimations, pas de vraies données")
    print("   • NOAA, AIRS, WHO ne sont pas vraiment implémentés")
    print("   • Données majoritairement simulées/estimées")
    
    print("\n✅ CE QUI FONCTIONNE:")
    print("   • Estimations intelligentes basées sur géographie")
    print("   • Variations temporelles réalistes")
    print("   • Géolocalisation performante")
    print("   • Structure API robuste avec fallbacks")
    
    print("\n🔧 RECOMMANDATIONS:")
    print("   • Implémenter de vraies sources de données")
    print("   • Obtenir clés API pour services payants")
    print("   • Clarifier dans docs que ce sont des estimations")
    print("   • Ajouter disclaimer sur fiabilité des données")

if __name__ == "__main__":
    asyncio.run(main())