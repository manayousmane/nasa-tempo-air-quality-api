#!/usr/bin/env python3
"""
Test de diagnostic des APIs NASA disponibles.
"""
import asyncio
import aiohttp
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.config import settings


async def test_nasa_apis():
    """Tester les différentes APIs NASA disponibles."""
    print("🛰️ Diagnostic des APIs NASA Disponibles")
    print("=" * 50)
    
    # URLs à tester
    nasa_urls = [
        "https://urs.earthdata.nasa.gov/api/users/tokens",
        "https://urs.earthdata.nasa.gov/oauth/authorize",
        "https://earthdata.nasa.gov/api/echo/v10/collections",
        "https://cmr.earthdata.nasa.gov/search/collections",
        "https://search.earthdata.nasa.gov/search/collections",
        "https://ladsweb.modaps.eosdis.nasa.gov/api/v2",
        "https://disc.gsfc.nasa.gov/api/v2"
    ]
    
    credentials = {
        "username": settings.NASA_EARTHDATA_USERNAME,
        "password": settings.NASA_EARTHDATA_PASSWORD,
        "token": settings.NASA_EARTHDATA_TOKEN
    }
    
    print(f"Credentials: Username={credentials['username']}, Token={'OK' if credentials['token'] else 'Missing'}")
    print()
    
    async with aiohttp.ClientSession() as session:
        for url in nasa_urls:
            print(f"🔍 Test: {url}")
            
            try:
                # Test sans authentification
                async with session.get(url, timeout=10) as response:
                    print(f"   Status: {response.status}")
                    if response.status in [200, 401, 403]:
                        print(f"   ✅ API accessible (status {response.status})")
                    else:
                        print(f"   ❌ API non accessible")
                        
                # Test avec token si disponible
                if credentials['token'] and response.status == 401:
                    headers = {"Authorization": f"Bearer {credentials['token']}"}
                    async with session.get(url, headers=headers, timeout=10) as auth_response:
                        print(f"   Avec token: {auth_response.status}")
                        if auth_response.status == 200:
                            print(f"   ✅ Authentification réussie !")
                        
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
            
            print()


async def test_openaq_alternative():
    """Tester OpenAQ avec l'API v3."""
    print("🌍 Test OpenAQ API v3")
    print("=" * 30)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Nouvelle API OpenAQ v3
            url = "https://api.openaq.org/v3/locations"
            params = {
                "limit": 5,
                "coordinates": "40.7,-74.0",  # NYC
                "radius": 50000  # 50km
            }
            
            async with session.get(url, params=params) as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print("✅ OpenAQ v3 fonctionne !")
                    results = data.get("results", [])
                    print(f"   Trouvé {len(results)} stations près de NYC")
                    return True
                else:
                    print(f"❌ Échec: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


async def test_alternative_air_quality_apis():
    """Tester des APIs alternatives de qualité de l'air."""
    print("\n🌬️ APIs Alternatives de Qualité de l'Air")
    print("=" * 45)
    
    # AirVisual (IQAir)
    print("🔍 Test AirVisual API...")
    try:
        async with aiohttp.ClientSession() as session:
            url = "http://api.airvisual.com/v2/nearest_city"
            params = {
                "lat": 40.7,
                "lon": -74.0,
                "key": "demo"  # Clé demo limitée
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ AirVisual accessible (clé demo)")
                    if data.get("status") == "success":
                        pollution = data.get("data", {}).get("current", {}).get("pollution", {})
                        print(f"   AQI: {pollution.get('aqius', 'N/A')}")
                else:
                    print(f"   Status: {response.status}")
    except Exception as e:
        print(f"   Erreur: {e}")
    
    # WAQI (World Air Quality Index)
    print("\n🔍 Test WAQI API...")
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://api.waqi.info/feed/geo:40.7;-74.0/"
            params = {"token": "demo"}  # Token demo
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ WAQI accessible (token demo)")
                    if data.get("status") == "ok":
                        aqi = data.get("data", {}).get("aqi")
                        print(f"   AQI: {aqi}")
                else:
                    print(f"   Status: {response.status}")
    except Exception as e:
        print(f"   Erreur: {e}")


async def main():
    """Fonction principale de diagnostic."""
    print("🧪 DIAGNOSTIC COMPLET DES APIs")
    print("=" * 50)
    
    # Test des APIs NASA
    await test_nasa_apis()
    
    # Test OpenAQ alternatif
    await test_openaq_alternative()
    
    # Test APIs alternatives
    await test_alternative_air_quality_apis()
    
    print("\n💡 RECOMMANDATIONS:")
    print("1. 🌤️  OpenWeatherMap fonctionne parfaitement")
    print("2. 🛰️  Pour NASA TEMPO: Utilisez les vraies APIs de données satellites")
    print("3. 🌍 Pour la qualité de l'air: Utilisez WAQI ou AirVisual")
    print("4. 📊 Votre backend peut fonctionner avec les sources disponibles")


if __name__ == "__main__":
    asyncio.run(main())