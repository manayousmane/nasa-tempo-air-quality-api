# 🚀 GUIDE COMPLET : CONNEXIONS API RÉELLES 

## ❌ PROBLÈME ACTUEL

Votre API utilise des **données simulées** au lieu de vraies données ! Voici le problème :

### Dans `app/connectors/real_data_connector.py` :

```python
async def _get_nasa_tempo_data(self, latitude: float, longitude: float) -> Optional[Dict]:
    """Récupère les données NASA TEMPO (NO2, HCHO, O3)"""
    try:
        # Note: L'API TEMPO nécessite généralement des credentials Earthdata
        # Pour cette implémentation, nous utilisons des estimations basées sur les patterns régionaux
        logger.info("NASA TEMPO: Utilisation d'estimations basées sur les patterns de pollution")
        
        # Déterminer le type de région
        region_type = self._determine_region_type(latitude, longitude)
        
        # Estimations basées sur les données TEMPO typiques
        tempo_estimates = self._get_tempo_estimates(region_type, latitude, longitude)
```

**C'EST DU FAKE !** Il génère des estimations, pas de vraies données !

---

## ✅ SOLUTION : VRAIES CONNEXIONS API

### 1. NASA EARTHDATA (POUR TEMPO)

#### A. Créer un compte NASA Earthdata
```bash
# 1. Aller sur: https://urs.earthdata.nasa.gov/
# 2. Créer un compte
# 3. Obtenir vos credentials : username + password
```

#### B. Remplacer la méthode NASA TEMPO par une vraie :

```python
async def _get_nasa_tempo_data(self, latitude: float, longitude: float) -> Optional[Dict]:
    """VRAIE récupération des données NASA TEMPO"""
    try:
        # Authentification NASA Earthdata
        auth = aiohttp.BasicAuth(
            login="VOTRE_USERNAME_EARTHDATA",
            password="VOTRE_PASSWORD_EARTHDATA"
        )
        
        # URL de l'API TEMPO réelle
        base_url = "https://disc.gsfc.nasa.gov/service/opendap/hyrax/"
        
        # Paramètres pour la requête
        params = {
            'SERVICE': 'WCS',
            'VERSION': '2.0.1',
            'REQUEST': 'GetCoverage',
            'COVERAGEID': 'TEMPO_NO2_L2',
            'SUBSET': f'Lat({latitude-0.1},{latitude+0.1})',
            'SUBSET': f'Lon({longitude-0.1},{longitude+0.1})',
            'FORMAT': 'application/json'
        }
        
        async with self.session.get(
            base_url,
            params=params,
            auth=auth,
            timeout=30
        ) as response:
            if response.status == 200:
                data = await response.json()
                return self._parse_tempo_response(data, latitude, longitude)
            else:
                logger.error(f"NASA TEMPO API Error: {response.status}")
                return None
                
    except Exception as e:
        logger.error(f"Erreur NASA TEMPO réelle: {e}")
        return None

def _parse_tempo_response(self, data: Dict, lat: float, lon: float) -> Dict:
    """Parse les vraies données TEMPO"""
    # Parser les données NetCDF/JSON de TEMPO
    # Extraire NO2, HCHO, O3, etc.
    return {
        'name': f"NASA TEMPO {lat:.3f}, {lon:.3f}",
        'coordinates': [lat, lon],
        'no2': data.get('no2_column_density', 0),
        'hcho': data.get('hcho_column_density', 0),
        'o3': data.get('o3_column_density', 0),
        'data_source': 'NASA TEMPO Satellite (Real)',
        'last_updated': datetime.utcnow().isoformat() + "Z"
    }
```

### 2. OPENAQ v3 (NOUVELLE VERSION)

L'ancienne API OpenAQ v2 est deprecated (410). Utilisez v3 :

```python
async def _get_openaq_current(self, latitude: float, longitude: float) -> Optional[Dict]:
    """VRAIE connexion OpenAQ v3"""
    try:
        # Nouvelle URL v3
        url = "https://api.openaq.org/v3/locations"
        
        # Obtenir une clé API : https://openaq.org/contact
        headers = {
            'X-API-Key': 'VOTRE_CLE_OPENAQ_V3',
            'Content-Type': 'application/json'
        }
        
        params = {
            'coordinates': f"{latitude},{longitude}",
            'radius': 25000,  # 25km
            'limit': 10,
            'order_by': 'distance'
        }
        
        async with self.session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                locations = data.get('results', [])
                
                if locations:
                    # Prendre la station la plus proche
                    closest_location = locations[0]
                    location_id = closest_location['id']
                    
                    # Récupérer les mesures actuelles
                    measurements_url = f"https://api.openaq.org/v3/locations/{location_id}/latest"
                    
                    async with self.session.get(measurements_url, headers=headers) as measurements_response:
                        if measurements_response.status == 200:
                            measurements_data = await measurements_response.json()
                            return self._format_openaq_v3_data(measurements_data, latitude, longitude)
                            
            logger.warning(f"OpenAQ v3: Pas de données pour {latitude}, {longitude}")
            return None
            
    except Exception as e:
        logger.error(f"Erreur OpenAQ v3: {e}")
        return None

def _format_openaq_v3_data(self, data: Dict, lat: float, lon: float) -> Dict:
    """Format les données OpenAQ v3"""
    measurements = data.get('results', [])
    
    # Organiser par polluant
    pollutants = {}
    for measurement in measurements:
        parameter = measurement.get('parameter')
        value = measurement.get('value')
        if parameter and value:
            pollutants[parameter.lower()] = value
    
    # Calculer AQI
    aqi = self._calculate_aqi(
        pollutants.get('pm25', 0),
        pollutants.get('pm10', 0),
        pollutants.get('no2', 0),
        pollutants.get('o3', 0)
    )
    
    return {
        'name': data.get('location', {}).get('name', 'Unknown'),
        'coordinates': [lat, lon],
        'aqi': aqi,
        'pm25': pollutants.get('pm25', 0),
        'pm10': pollutants.get('pm10', 0),
        'no2': pollutants.get('no2', 0),
        'o3': pollutants.get('o3', 0),
        'so2': pollutants.get('so2', 0),
        'co': pollutants.get('co', 0),
        'data_source': 'OpenAQ v3 (Real)',
        'station_distance_km': data.get('distance', 0),
        'last_updated': datetime.utcnow().isoformat() + "Z"
    }
```

### 3. PURPLEAIR (VRAIE ALTERNATIVE)

```python
async def _get_purpleair_data(self, latitude: float, longitude: float) -> Optional[Dict]:
    """Récupération PurpleAir (vraie alternative)"""
    try:
        # Obtenir clé API : https://develop.purpleair.com/
        headers = {
            'X-API-Key': 'VOTRE_CLE_PURPLEAIR'
        }
        
        # Chercher les capteurs dans un rayon
        url = "https://api.purpleair.com/v1/sensors"
        params = {
            'nwlat': latitude + 0.1,
            'nwlng': longitude - 0.1,
            'selat': latitude - 0.1,
            'selng': longitude + 0.1,
            'fields': 'pm2.5_atm,pm2.5_cf_1,pm10.0_atm,temperature,humidity'
        }
        
        async with self.session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                sensors = data.get('data', [])
                
                if sensors:
                    # Prendre le premier capteur
                    sensor_data = sensors[0]
                    return self._format_purpleair_data(sensor_data, latitude, longitude)
                    
        return None
        
    except Exception as e:
        logger.error(f"Erreur PurpleAir: {e}")
        return None
```

### 4. NOAA (VRAIE MÉTÉO)

```python
async def _get_noaa_weather(self, latitude: float, longitude: float) -> Optional[Dict]:
    """Vraie connexion NOAA"""
    try:
        # API NOAA gratuite (avec limitation)
        url = f"https://api.weather.gov/points/{latitude},{longitude}"
        
        headers = {
            'User-Agent': 'NASA-TEMPO-API/2.0 contact@votre-domaine.com'
        }
        
        async with self.session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                forecast_url = data['properties']['forecastHourly']
                
                # Récupérer les données horaires
                async with self.session.get(forecast_url, headers=headers) as forecast_response:
                    if forecast_response.status == 200:
                        forecast_data = await forecast_response.json()
                        return self._format_noaa_data(forecast_data)
                        
        return None
        
    except Exception as e:
        logger.error(f"Erreur NOAA: {e}")
        return None
```

### 5. CONFIGURATION DES CLÉS API

Créez un fichier `app/config.py` :

```python
import os
from typing import Optional

class APIConfig:
    """Configuration des clés API réelles"""
    
    # NASA Earthdata
    NASA_EARTHDATA_USERNAME: Optional[str] = os.getenv('NASA_EARTHDATA_USERNAME')
    NASA_EARTHDATA_PASSWORD: Optional[str] = os.getenv('NASA_EARTHDATA_PASSWORD')
    
    # OpenAQ v3
    OPENAQ_API_KEY: Optional[str] = os.getenv('OPENAQ_API_KEY')
    
    # PurpleAir
    PURPLEAIR_API_KEY: Optional[str] = os.getenv('PURPLEAIR_API_KEY')
    
    # AirNow (EPA)
    AIRNOW_API_KEY: Optional[str] = os.getenv('AIRNOW_API_KEY')
    
    # IQAir
    IQAIR_API_KEY: Optional[str] = os.getenv('IQAIR_API_KEY')
    
    @classmethod
    def validate_keys(cls) -> Dict[str, bool]:
        """Vérifie quelles clés sont configurées"""
        return {
            'nasa_earthdata': bool(cls.NASA_EARTHDATA_USERNAME and cls.NASA_EARTHDATA_PASSWORD),
            'openaq': bool(cls.OPENAQ_API_KEY),
            'purpleair': bool(cls.PURPLEAIR_API_KEY),
            'airnow': bool(cls.AIRNOW_API_KEY),
            'iqair': bool(cls.IQAIR_API_KEY)
        }
```

### 6. VARIABLES D'ENVIRONNEMENT

Créez un fichier `.env` :

```bash
# Clés API réelles
NASA_EARTHDATA_USERNAME=votre_username
NASA_EARTHDATA_PASSWORD=votre_password
OPENAQ_API_KEY=votre_cle_openaq
PURPLEAIR_API_KEY=votre_cle_purpleair
AIRNOW_API_KEY=votre_cle_airnow
IQAIR_API_KEY=votre_cle_iqair
```

---

## 🔧 ÉTAPES POUR IMPLÉMENTER

### 1. Obtenir les clés API

| Service | Lien | Type | Coût |
|---------|------|------|------|
| NASA Earthdata | https://urs.earthdata.nasa.gov/ | Gratuit | 0€ |
| OpenAQ v3 | https://openaq.org/contact | Gratuit/Payant | 0-50€/mois |
| PurpleAir | https://develop.purpleair.com/ | Payant | 10€/mois |
| AirNow (EPA) | https://docs.airnowapi.org/ | Gratuit | 0€ |
| IQAir | https://www.iqair.com/air-pollution-data-api | Payant | 30€/mois |

### 2. Modifier le connector

Remplacez **tout** le contenu de `app/connectors/real_data_connector.py` par les vraies connexions API.

### 3. Tester les connexions

```python
# Script de test des vraies connexions
async def test_real_apis():
    connector = RealDataConnector()
    
    # Test NASA TEMPO réel
    tempo_data = await connector._get_nasa_tempo_data(48.8566, 2.3522)
    print(f"NASA TEMPO: {tempo_data}")
    
    # Test OpenAQ v3 réel
    openaq_data = await connector._get_openaq_current(48.8566, 2.3522)
    print(f"OpenAQ v3: {openaq_data}")
    
    # Test PurpleAir réel
    purpleair_data = await connector._get_purpleair_data(48.8566, 2.3522)
    print(f"PurpleAir: {purpleair_data}")
```

### 4. Gestion des erreurs réelles

```python
async def get_current_air_quality(self, latitude: float, longitude: float) -> Dict:
    """Service avec vraies sources en cascade"""
    
    # 1. Essayer OpenAQ v3 (le plus fiable)
    try:
        data = await self.connector._get_openaq_current(latitude, longitude)
        if data:
            logger.info("✅ Données OpenAQ v3 récupérées")
            return data
    except Exception as e:
        logger.warning(f"OpenAQ v3 failed: {e}")
    
    # 2. Essayer PurpleAir
    try:
        data = await self.connector._get_purpleair_data(latitude, longitude)
        if data:
            logger.info("✅ Données PurpleAir récupérées")
            return data
    except Exception as e:
        logger.warning(f"PurpleAir failed: {e}")
    
    # 3. Essayer NASA TEMPO réel
    try:
        data = await self.connector._get_nasa_tempo_data(latitude, longitude)
        if data:
            logger.info("✅ Données NASA TEMPO réelles récupérées")
            return data
    except Exception as e:
        logger.warning(f"NASA TEMPO failed: {e}")
    
    # 4. Derniers recours : AirNow, IQAir
    # ... autres sources réelles
    
    # 5. Si tout échoue, retourner erreur (PAS de simulation)
    raise ValueError("Aucune source de données réelle disponible")
```

---

## ⚠️ POURQUOI ÇA N'A PAS ÉTÉ FAIT

1. **Clés API payantes** : La plupart des services nécessitent des abonnements
2. **Limites de taux** : Les APIs gratuites sont limitées
3. **Complexité** : Parser les vrais formats de données (NetCDF, HDF5, etc.)
4. **Authentification** : OAuth, tokens, credentials
5. **Gestion d'erreurs** : Services qui tombent, quotas dépassés

---

## 🎯 RECOMMANDATION FINALE

**Pour avoir de VRAIES données dès maintenant :**

1. Commencez par **OpenAQ v3** (contact pour clé gratuite)
2. Ajoutez **PurpleAir** (10€/mois, excellent ROI)
3. Implémentez **NASA Earthdata** (gratuit mais complexe)
4. Complétez avec **AirNow EPA** (gratuit, USA seulement)

**Coût total : ~20€/mois pour des données mondiales réelles.**

Voulez-vous que je vous aide à implémenter une de ces connexions réelles ?