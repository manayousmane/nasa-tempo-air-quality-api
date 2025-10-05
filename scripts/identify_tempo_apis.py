#!/usr/bin/env python3
"""
Recherche et identification des vraies APIs NASA TEMPO.
"""
import asyncio
import aiohttp
import sys
import os
import json
from datetime import datetime

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.config import settings


async def identify_nasa_tempo_apis():
    """Identifier les vraies APIs NASA TEMPO disponibles."""
    print("🛰️ IDENTIFICATION DES APIs NASA TEMPO")
    print("=" * 50)
    
    # URLs potentielles pour TEMPO
    tempo_endpoints = [
        # NASA Earthdata Search
        "https://cmr.earthdata.nasa.gov/search/collections.json?provider=LARC_CLOUD&keyword=TEMPO",
        "https://cmr.earthdata.nasa.gov/search/collections.json?provider=GES_DISC&keyword=TEMPO", 
        "https://cmr.earthdata.nasa.gov/search/collections.json?short_name=TEMPO*",
        
        # NASA LARC (Langley Research Center)
        "https://eosweb.larc.nasa.gov/api/v1/collections",
        "https://asdc.larc.nasa.gov/api/collections",
        
        # NASA GES DISC
        "https://disc.gsfc.nasa.gov/api/collections",
        "https://giovanni.gsfc.nasa.gov/giovanni/",
        
        # TEMPO spécifiques
        "https://tempo.si.edu/api",
        "https://tempo-data.si.edu/api",
        "https://search.earthdata.nasa.gov/search/collections?q=TEMPO",
        
        # OPeNDAP pour données TEMPO
        "https://opendap.larc.nasa.gov/opendap/TEMPO/",
        "https://opendap.gesdisc.eosdis.nasa.gov/opendap/TEMPO/",
    ]
    
    credentials = {
        "username": settings.NASA_EARTHDATA_USERNAME,
        "password": settings.NASA_EARTHDATA_PASSWORD,
        "token": settings.NASA_EARTHDATA_TOKEN
    }
    
    print(f"🔑 Credentials: {credentials['username']} / Token: {'✅' if credentials['token'] else '❌'}")
    print()
    
    headers = {}
    if credentials['token']:
        headers["Authorization"] = f"Bearer {credentials['token']}"
    
    async with aiohttp.ClientSession() as session:
        for url in tempo_endpoints:
            print(f"🔍 Test: {url}")
            
            try:
                # Test avec timeout
                async with session.get(url, headers=headers, timeout=15) as response:
                    print(f"   Status: {response.status}")
                    
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        
                        if 'json' in content_type:
                            try:
                                data = await response.json()
                                print(f"   ✅ JSON Response - Keys: {list(data.keys()) if isinstance(data, dict) else 'Array'}")
                                
                                # Analyser le contenu pour TEMPO
                                if isinstance(data, dict):
                                    if 'feed' in data and 'entry' in data['feed']:
                                        entries = data['feed']['entry']
                                        tempo_collections = [e for e in entries if 'TEMPO' in str(e)]
                                        if tempo_collections:
                                            print(f"   🎯 TEMPO collections trouvées: {len(tempo_collections)}")
                                            for collection in tempo_collections[:2]:  # Première 2
                                                title = collection.get('title', 'No title')
                                                print(f"      - {title}")
                                
                            except Exception as e:
                                print(f"   ⚠️  JSON parse error: {e}")
                        
                        elif 'html' in content_type:
                            text = await response.text()
                            if 'TEMPO' in text.upper():
                                print(f"   ✅ HTML contient 'TEMPO'")
                            else:
                                print(f"   📄 HTML response (no TEMPO found)")
                        
                        else:
                            print(f"   📄 Content type: {content_type}")
                    
                    elif response.status == 401:
                        print(f"   🔒 Requires authentication")
                        
                        # Test avec auth basique si pas de token
                        if not credentials['token'] and credentials['username'] and credentials['password']:
                            auth = aiohttp.BasicAuth(credentials['username'], credentials['password'])
                            async with session.get(url, auth=auth, timeout=15) as auth_response:
                                print(f"   🔑 With basic auth: {auth_response.status}")
                    
                    elif response.status == 403:
                        print(f"   🚫 Forbidden - Permissions insuffisantes")
                    
                    elif response.status == 404:
                        print(f"   ❌ Not found")
                    
                    else:
                        print(f"   ⚠️  Status: {response.status}")
                
            except asyncio.TimeoutError:
                print(f"   ⏱️  Timeout")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            print()


async def search_tempo_collections():
    """Rechercher spécifiquement les collections TEMPO dans CMR."""
    print("🔍 RECHERCHE SPÉCIFIQUE COLLECTIONS TEMPO")
    print("=" * 45)
    
    cmr_search_url = "https://cmr.earthdata.nasa.gov/search/collections.json"
    
    # Différentes requêtes de recherche pour TEMPO
    search_queries = [
        {"keyword": "TEMPO"},
        {"keyword": "Tropospheric Emissions"},
        {"short_name": "*TEMPO*"},
        {"provider": "LARC_CLOUD", "keyword": "air quality"},
        {"provider": "GES_DISC", "keyword": "atmospheric"},
        {"instrument": "TEMPO"},
        {"platform": "TEMPO"},
    ]
    
    async with aiohttp.ClientSession() as session:
        for i, params in enumerate(search_queries, 1):
            print(f"🔍 Requête {i}: {params}")
            
            try:
                async with session.get(cmr_search_url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if 'feed' in data and 'entry' in data['feed']:
                            entries = data['feed']['entry']
                            print(f"   ✅ {len(entries)} collections trouvées")
                            
                            # Filtrer pour TEMPO
                            tempo_entries = []
                            for entry in entries:
                                title = entry.get('title', '').upper()
                                summary = str(entry.get('summary', '')).upper()
                                if 'TEMPO' in title or 'TEMPO' in summary:
                                    tempo_entries.append(entry)
                            
                            if tempo_entries:
                                print(f"   🎯 {len(tempo_entries)} collections TEMPO:")
                                for entry in tempo_entries[:3]:  # Première 3
                                    title = entry.get('title', 'No title')
                                    concept_id = entry.get('id', 'No ID')
                                    print(f"      - {title}")
                                    print(f"        ID: {concept_id}")
                                    
                                    # Chercher les liens de données
                                    if 'links' in entry:
                                        data_links = [l for l in entry['links'] if l.get('rel') == 'http://esipfed.org/ns/fedsearch/1.1/data#']
                                        if data_links:
                                            print(f"        Data URL: {data_links[0].get('href', 'N/A')}")
                            else:
                                print(f"   ℹ️  Pas de collections TEMPO spécifiques")
                        else:
                            print(f"   ❌ Format de réponse inattendu")
                    else:
                        print(f"   ❌ Status: {response.status}")
                        
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            print()


async def test_tempo_data_access():
    """Tester l'accès aux données TEMPO réelles."""
    print("🌍 TEST D'ACCÈS AUX DONNÉES TEMPO")
    print("=" * 40)
    
    # URLs d'accès direct aux données TEMPO
    tempo_data_urls = [
        # OPeNDAP
        "https://opendap.larc.nasa.gov/opendap/TEMPO/",
        "https://opendap.gesdisc.eosdis.nasa.gov/opendap/",
        
        # HTTPS direct
        "https://asdc.larc.nasa.gov/data/TEMPO/",
        "https://disc.gsfc.nasa.gov/datasets/",
        
        # Nouveaux endpoints potentiels
        "https://tempodata.org/api/",
        "https://tempo.si.edu/data/",
    ]
    
    headers = {}
    if settings.NASA_EARTHDATA_TOKEN:
        headers["Authorization"] = f"Bearer {settings.NASA_EARTHDATA_TOKEN}"
    
    async with aiohttp.ClientSession() as session:
        for url in tempo_data_urls:
            print(f"🔍 Test accès: {url}")
            
            try:
                async with session.get(url, headers=headers, timeout=10) as response:
                    print(f"   Status: {response.status}")
                    
                    if response.status == 200:
                        content = await response.text()
                        if 'TEMPO' in content.upper() or 'NO2' in content.upper() or 'O3' in content.upper():
                            print(f"   ✅ Contient des données atmosphériques")
                            
                            # Chercher des patterns de fichiers de données
                            if '.nc' in content or '.hdf' in content or '.h5' in content:
                                print(f"   📁 Fichiers de données détectés")
                        else:
                            print(f"   📄 Contenu générique")
                    
                    elif response.status == 401:
                        print(f"   🔒 Authentification requise")
                    elif response.status == 403:
                        print(f"   🚫 Accès refusé")
                    else:
                        print(f"   ❌ Status: {response.status}")
                        
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            print()


async def main():
    """Fonction principale d'identification."""
    print("🎯 IDENTIFICATION COMPLÈTE DES APIs NASA TEMPO")
    print("=" * 60)
    
    print("Phase 1: Test des endpoints généraux")
    await identify_nasa_tempo_apis()
    
    print("\nPhase 2: Recherche spécifique TEMPO")
    await search_tempo_collections()
    
    print("\nPhase 3: Test d'accès aux données")
    await test_tempo_data_access()
    
    print("\n📋 RÉSULTATS ET RECOMMANDATIONS")
    print("=" * 35)
    print("1. 🔍 Utiliser CMR (Common Metadata Repository) pour chercher les collections TEMPO")
    print("2. 📊 Accéder aux données via OPeNDAP ou HTTPS direct")
    print("3. 🔑 Votre token NASA Earthdata est nécessaire pour l'accès")
    print("4. 📁 Les données sont probablement en format NetCDF (.nc) ou HDF5")
    print("\n🎯 PROCHAINE ÉTAPE: Créer un collecteur TEMPO spécialisé")


if __name__ == "__main__":
    asyncio.run(main())