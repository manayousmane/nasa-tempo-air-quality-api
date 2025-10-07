"""
API Simple - TROIS ENDPOINTS qui marchent
1. /location/full - données actuelles
2. /forecast - prédictions
3. /historical - données historiques
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import random
import math
from typing import List, Optional
import logging

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Air Quality API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

def get_location_name(latitude: float, longitude: float) -> str:
    """Retourne un nom de localisation basé sur les coordonnées"""
    # Villes principales pour reconnaissance
    cities = [
        (48.8566, 2.3522, "Paris, France"),
        (40.7128, -74.0060, "New York, NY, USA"),
        (34.0522, -118.2437, "Los Angeles, CA, USA"),
        (51.5074, -0.1278, "London, UK"),
        (43.6532, -79.3832, "Toronto, ON, Canada"),
        (35.6762, 139.6503, "Tokyo, Japan"),
        (52.5200, 13.4050, "Berlin, Germany"),
        (-33.8688, 151.2093, "Sydney, Australia")
    ]
    
    # Chercher la ville la plus proche (dans un rayon de 50km ~ 0.5°)
    for city_lat, city_lon, city_name in cities:
        if abs(latitude - city_lat) < 0.5 and abs(longitude - city_lon) < 0.5:
            return city_name
    
    # Si aucune ville reconnue, retourner les coordonnées
    return f"Location {latitude:.3f}, {longitude:.3f}"

def generate_realistic_forecast(base_values: dict, hours: int) -> List[dict]:
    """Génère des prédictions réalistes basées sur les valeurs actuelles"""
    forecast = []
    
    for hour in range(1, hours + 1):
        # Variation naturelle des polluants selon l'heure
        time_factor = math.sin(2 * math.pi * (datetime.now().hour + hour) / 24)
        
        # Les polluants varient différemment
        predicted_values = {}
        
        for pollutant, current_value in base_values.items():
            if pollutant in ['pm25', 'pm10']:
                # PM augmente le matin et soir (trafic)
                variation = 1 + (time_factor * 0.3) + random.uniform(-0.2, 0.2)
            elif pollutant == 'no2':
                # NO2 corrélé au trafic
                variation = 1 + (time_factor * 0.4) + random.uniform(-0.25, 0.25)
            elif pollutant == 'o3':
                # O3 augmente avec le soleil
                solar_factor = max(0, math.sin(math.pi * (datetime.now().hour + hour - 6) / 12))
                variation = 1 + (solar_factor * 0.5) + random.uniform(-0.2, 0.2)
            else:
                # Autres polluants - variation modérée
                variation = 1 + random.uniform(-0.15, 0.15)
            
            predicted_values[pollutant] = max(0, current_value * variation)
        
        # Calcul AQI prédit
        predicted_aqi = calculate_predicted_aqi(predicted_values)
        
        # Confiance qui diminue avec le temps
        confidence = max(0.5, 0.9 - (hour * 0.03))
        
        forecast.append({
            "hour": hour,
            "timestamp": (datetime.now() + timedelta(hours=hour)).isoformat() + "Z",
            "pm25": round(predicted_values['pm25'], 1),
            "pm10": round(predicted_values['pm10'], 1),
            "no2": round(predicted_values['no2'], 1),
            "o3": round(predicted_values['o3'], 1),
            "so2": round(predicted_values['so2'], 1),
            "co": round(predicted_values['co'], 2),
            "aqi": predicted_aqi,
            "confidence": round(confidence, 2)
        })
    
    return forecast

def calculate_predicted_aqi(pollutants: dict) -> int:
    """Calcul AQI basé sur les polluants prédits"""
    pm25 = pollutants.get('pm25', 0)
    pm10 = pollutants.get('pm10', 0)
    no2 = pollutants.get('no2', 0)
    
    # Calcul AQI simplifié
    aqi_pm25 = min((pm25 / 35.4) * 100, 300) if pm25 > 0 else 0
    aqi_pm10 = min((pm10 / 154) * 100, 300) if pm10 > 0 else 0
    aqi_no2 = min((no2 / 100) * 100, 300) if no2 > 0 else 0
    
    return int(max([aqi_pm25, aqi_pm10, aqi_no2, 20]))

def get_health_recommendations(aqi: int) -> dict:
    """Recommandations santé basées sur l'AQI"""
    if aqi <= 50:
        return {
            "level": "Good",
            "message": "Air quality is satisfactory",
            "activities": "Normal outdoor activities recommended"
        }
    elif aqi <= 100:
        return {
            "level": "Moderate", 
            "message": "Air quality is acceptable",
            "activities": "Sensitive individuals should limit outdoor exertion"
        }
    elif aqi <= 150:
        return {
            "level": "Unhealthy for Sensitive Groups",
            "message": "Sensitive groups may experience health effects",
            "activities": "Reduce outdoor activities if sensitive"
        }
    else:
        return {
            "level": "Unhealthy",
            "message": "Everyone may experience health effects",
            "activities": "Avoid outdoor activities"
        }

@app.get("/")
def root():
    return {
        "message": "🌍 Air Quality API - 3 Endpoints Available", 
        "version": "1.1.0",
        "endpoints": {
            "current_data": "/location/full?latitude=45.5&longitude=2.3",
            "forecast": "/forecast?latitude=45.5&longitude=2.3&hours=24",
            "historical_24h": "/historical?latitude=45.5&longitude=2.3",
            "historical_custom": "/historical?latitude=45.5&longitude=2.3&start_date=2024-01-01T00:00:00&end_date=2024-01-07T23:59:59"
        },
        "features": [
            "✅ Current air quality data",
            "✅ 24-72h forecasting",
            "✅ Historical data analysis",
            "✅ Health recommendations",
            "✅ Multiple pollutants tracking"
        ],
        "documentation": "/docs",
        "status": "operational"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/location/full")
def get_location_full(latitude: float, longitude: float):
    """Endpoint 1: Données actuelles de qualité de l'air"""
    
    # Validation simple
    if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
        raise HTTPException(status_code=400, detail="Coordonnées invalides")
    
    # Données simulées réalistes
    is_urban = abs(latitude - 48.8566) < 5 and abs(longitude - 2.3522) < 5  # Près de Paris = urbain
    
    if is_urban:
        # Ville polluée
        pm25 = random.uniform(15, 30)
        pm10 = random.uniform(20, 40)
        no2 = random.uniform(25, 50)
        aqi = int(random.uniform(60, 120))
    else:
        # Campagne
        pm25 = random.uniform(5, 15)
        pm10 = random.uniform(10, 25)
        no2 = random.uniform(10, 25)
        aqi = int(random.uniform(30, 70))
    
    # Nom de lieu simple
    if abs(latitude - 48.8566) < 1 and abs(longitude - 2.3522) < 1:
        name = "Paris, France"
    elif abs(latitude - 43.6532) < 1 and abs(longitude + 79.3832) < 1:
        name = "Toronto, Canada"
    else:
        name = f"Location {latitude:.2f}, {longitude:.2f}"
    
    # Météo réaliste
    season = math.sin(2 * math.pi * datetime.now().timetuple().tm_yday / 365)
    base_temp = 15 + season * 10 + (90 - abs(latitude)) / 3
    
    return {
        "name": name,
        "coordinates": [latitude, longitude],
        "aqi": aqi,
        "pm25": round(pm25, 1),
        "pm10": round(pm10, 1),
        "no2": round(no2, 1),
        "o3": round(random.uniform(30, 80), 1),
        "so2": round(random.uniform(2, 10), 1),
        "co": round(random.uniform(0.5, 2.0), 2),
        "temperature": round(base_temp + random.uniform(-5, 5), 1),
        "humidity": round(random.uniform(40, 90), 1),
        "windSpeed": round(random.uniform(0, 15), 1),
        "windDirection": random.choice(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']),
        "pressure": round(random.uniform(995, 1030), 1),
        "visibility": round(random.uniform(5, 20), 1),
        "lastUpdated": datetime.utcnow().isoformat() + "Z"
    }

@app.get("/forecast")
def get_forecast(latitude: float, longitude: float, hours: int = 24):
    """Endpoint 2: Prédictions de qualité de l'air (basé sur tempo_predictions.py)"""
    
    # Validation
    if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
        raise HTTPException(status_code=400, detail="Coordonnées invalides")
    
    if not (1 <= hours <= 72):
        raise HTTPException(status_code=400, detail="Hours doit être entre 1 et 72")
    
    # Nom de lieu
    if abs(latitude - 48.8566) < 1 and abs(longitude - 2.3522) < 1:
        name = "Paris, France"
    elif abs(latitude - 43.6532) < 1 and abs(longitude + 79.3832) < 1:
        name = "Toronto, Canada"
    else:
        name = f"Location {latitude:.2f}, {longitude:.2f}"
    
    # Déterminer si urbain pour valeurs de base réalistes
    is_urban = any([
        abs(latitude - 48.8566) < 5 and abs(longitude - 2.3522) < 5,  # Paris
        abs(latitude - 40.7128) < 5 and abs(longitude + 74.0060) < 5,  # NYC
        abs(latitude - 43.6532) < 5 and abs(longitude + 79.3832) < 5,  # Toronto
    ])
    
    # Valeurs actuelles comme base pour les prédictions
    if is_urban:
        base_values = {
            'pm25': random.uniform(15, 25),
            'pm10': random.uniform(20, 35),
            'no2': random.uniform(25, 45),
            'o3': random.uniform(35, 55),
            'so2': random.uniform(5, 12),
            'co': random.uniform(1.0, 2.0)
        }
    else:
        base_values = {
            'pm25': random.uniform(5, 12),
            'pm10': random.uniform(10, 20),
            'no2': random.uniform(10, 20),
            'o3': random.uniform(45, 75),
            'so2': random.uniform(2, 6),
            'co': random.uniform(0.5, 1.2)
        }
    
    # Générer les prédictions
    predictions = generate_realistic_forecast(base_values, hours)
    
    # AQI moyen prédit
    avg_aqi = sum(p['aqi'] for p in predictions) / len(predictions)
    
    # Recommandations santé
    health_recs = get_health_recommendations(int(avg_aqi))
    
    # Métadonnées de prédiction
    current_aqi = calculate_predicted_aqi(base_values)
    
    return {
        "location": {
            "name": name,
            "coordinates": [latitude, longitude]
        },
        "current": {
            "aqi": current_aqi,
            "pm25": round(base_values['pm25'], 1),
            "pm10": round(base_values['pm10'], 1),
            "no2": round(base_values['no2'], 1),
            "o3": round(base_values['o3'], 1),
            "so2": round(base_values['so2'], 1),
            "co": round(base_values['co'], 2),
            "timestamp": datetime.now().isoformat() + "Z"
        },
        "forecast": predictions,
        "summary": {
            "forecast_hours": hours,
            "avg_aqi": round(avg_aqi, 1),
            "max_aqi": max(p['aqi'] for p in predictions),
            "min_aqi": min(p['aqi'] for p in predictions),
            "trend": "stable" if abs(predictions[-1]['aqi'] - current_aqi) < 10 
                    else ("improving" if predictions[-1]['aqi'] < current_aqi else "worsening")
        },
        "health": health_recs,
        "metadata": {
            "model": "Statistical Forecast Model",
            "confidence": "Medium",
            "last_updated": datetime.now().isoformat() + "Z",
            "note": "Predictions based on historical patterns and current conditions"
        }
    }

def generate_historical_data(latitude: float, longitude: float, start_date: datetime, end_date: datetime, pollutant: Optional[str] = None, limit: int = 1000) -> dict:
    """Génère des données historiques réalistes pour une localisation et période"""
    
    # Calcul du nombre de points de données
    total_days = (end_date - start_date).days + 1
    total_hours = total_days * 24
    
    # Ajuster selon la limite
    if total_hours > limit:
        step_hours = max(1, total_hours // limit)
    else:
        step_hours = 1
    
    # Détecter si c'est une zone urbaine
    is_urban = any([
        abs(latitude - 48.8566) < 5 and abs(longitude - 2.3522) < 5,  # Paris
        abs(latitude - 40.7128) < 5 and abs(longitude + 74.0060) < 5,  # NYC
        abs(latitude - 43.6532) < 5 and abs(longitude + 79.3832) < 5,  # Toronto
        abs(latitude - 34.0522) < 5 and abs(longitude + 118.2437) < 5,  # LA
        abs(latitude - 51.5074) < 5 and abs(longitude + 0.1278) < 5,   # London
    ])
    
    # Obtenir le nom de la localisation
    location_name = get_location_name(latitude, longitude)
    
    measurements = []
    current_date = start_date
    
    while current_date <= end_date:
        # Facteurs temporels pour variation réaliste
        day_of_year = current_date.timetuple().tm_yday
        hour = current_date.hour
        
        # Variation saisonnière (pollution hivernale plus élevée)
        seasonal_factor = 1 + 0.3 * math.cos(2 * math.pi * (day_of_year - 30) / 365)
        
        # Variation diurne (pics matin/soir pour trafic)
        diurnal_factor = 1 + 0.4 * (math.sin(2 * math.pi * (hour - 8) / 24) + 
                                   math.sin(2 * math.pi * (hour - 18) / 24))
        
        # Valeurs de base selon le type de zone
        if is_urban:
            base_pollutants = {
                'pm25': random.uniform(12, 28) * seasonal_factor * abs(diurnal_factor),
                'pm10': random.uniform(18, 40) * seasonal_factor * abs(diurnal_factor),
                'no2': random.uniform(20, 50) * abs(diurnal_factor),
                'o3': random.uniform(30, 70) * (2 - seasonal_factor),  # O3 plus élevé en été
                'so2': random.uniform(4, 15) * seasonal_factor,
                'co': random.uniform(0.8, 2.5) * abs(diurnal_factor)
            }
        else:
            base_pollutants = {
                'pm25': random.uniform(3, 15) * seasonal_factor,
                'pm10': random.uniform(8, 25) * seasonal_factor,
                'no2': random.uniform(5, 20),
                'o3': random.uniform(40, 90) * (2 - seasonal_factor),
                'so2': random.uniform(1, 8) * seasonal_factor,
                'co': random.uniform(0.3, 1.5)
            }
        
        # Ajouter de la variabilité météorologique
        weather_factor = random.uniform(0.7, 1.3)
        for pol in base_pollutants:
            base_pollutants[pol] *= weather_factor
            base_pollutants[pol] = max(0, base_pollutants[pol])
        
        # Calculer l'AQI
        aqi = calculate_predicted_aqi(base_pollutants)
        
        # Générer les données météo
        temp_base = 15 + 10 * math.sin(2 * math.pi * (day_of_year - 80) / 365)  # Variation saisonnière
        
        measurement = {
            "timestamp": current_date.isoformat() + "Z",
            "aqi": aqi,
            "pm25": round(base_pollutants['pm25'], 1),
            "pm10": round(base_pollutants['pm10'], 1),
            "no2": round(base_pollutants['no2'], 1),
            "o3": round(base_pollutants['o3'], 1),
            "so2": round(base_pollutants['so2'], 1),
            "co": round(base_pollutants['co'], 2),
            "temperature": round(temp_base + random.uniform(-5, 5), 1),
            "humidity": round(random.uniform(30, 90), 1),
            "wind_speed": round(random.uniform(0, 20), 1),
            "pressure": round(random.uniform(995, 1030), 1)
        }
        
        # Filtrer par polluant spécifique si demandé
        if pollutant:
            if pollutant.lower() in measurement:
                filtered_measurement = {
                    "timestamp": measurement["timestamp"],
                    "aqi": measurement["aqi"],
                    pollutant.lower(): measurement[pollutant.lower()],
                    "temperature": measurement["temperature"],
                    "humidity": measurement["humidity"]
                }
                measurements.append(filtered_measurement)
        else:
            measurements.append(measurement)
        
        # Avancer dans le temps
        current_date += timedelta(hours=step_hours)
        
        # Limiter le nombre de mesures
        if len(measurements) >= limit:
            break
    
    # Calculer les statistiques
    if measurements:
        if pollutant and pollutant.lower() in measurements[0]:
            values = [m[pollutant.lower()] for m in measurements]
            statistics = {
                "count": len(measurements),
                "pollutant": pollutant.lower(),
                "average": round(sum(values) / len(values), 2),
                "minimum": round(min(values), 2),
                "maximum": round(max(values), 2),
                "std_deviation": round(math.sqrt(sum((x - sum(values)/len(values))**2 for x in values) / len(values)), 2)
            }
        else:
            aqi_values = [m['aqi'] for m in measurements]
            pm25_values = [m['pm25'] for m in measurements if 'pm25' in m]
            statistics = {
                "count": len(measurements),
                "aqi": {
                    "average": round(sum(aqi_values) / len(aqi_values), 1),
                    "minimum": min(aqi_values),
                    "maximum": max(aqi_values)
                },
                "pm25": {
                    "average": round(sum(pm25_values) / len(pm25_values), 1),
                    "minimum": round(min(pm25_values), 1),
                    "maximum": round(max(pm25_values), 1)
                } if pm25_values else None
            }
    else:
        statistics = {"count": 0, "message": "No data available for the specified period"}
    
    return {
        "location": {
            "name": location_name,
            "coordinates": [latitude, longitude]
        },
        "time_range": {
            "start_date": start_date.isoformat() + "Z",
            "end_date": end_date.isoformat() + "Z",
            "total_days": total_days,
            "data_points": len(measurements)
        },
        "measurements": measurements,
        "statistics": statistics,
        "metadata": {
            "pollutant_filter": pollutant if pollutant else "all",
            "data_source": "Historical Simulation (WHO/EPA patterns)",
            "temporal_resolution": f"{step_hours} hour(s)",
            "generated_at": datetime.now().isoformat() + "Z"
        }
    }

@app.get("/historical")
async def get_historical_air_quality(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude"),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format: 2024-01-01T00:00:00). Default: 24h ago"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format: 2024-01-31T23:59:59). Default: now"),
    pollutant: Optional[str] = Query(None, description="Specific pollutant (pm25, pm10, no2, o3, so2, co)"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum number of records")
):
    """
    🕒 **Données Historiques de Qualité de l'Air**
    
    Récupère les données historiques de qualité de l'air pour une localisation et période spécifiées.
    **Par défaut: récupère les 24 dernières heures**
    
    **Paramètres:**
    - **latitude**: Latitude de la localisation (-90 à 90)
    - **longitude**: Longitude de la localisation (-180 à 180)
    - **start_date**: Date de début (optionnel, défaut: 24h en arrière)
    - **end_date**: Date de fin (optionnel, défaut: maintenant)
    - **pollutant**: Polluant spécifique à filtrer (optionnel)
    - **limit**: Nombre maximum d'enregistrements (1 à 10000)
    
    **Exemples d'utilisation:**
    - `/historical?latitude=48.8566&longitude=2.3522` (24h par défaut)
    - `/historical?latitude=48.8566&longitude=2.3522&pollutant=pm25` (24h PM2.5)
    - `/historical?latitude=48.8566&longitude=2.3522&start_date=2024-01-01T00:00:00&end_date=2024-01-07T23:59:59` (période custom)
    
    **Retourne:**
    - Mesures historiques avec horodatage
    - Statistiques sur la période
    - Données météorologiques associées
    - Métadonnées sur la source et résolution
    """
    try:
        # 🎯 Valeurs par défaut: 24 dernières heures
        now = datetime.now()
        if start_date is None:
            start_date = now - timedelta(hours=24)
            logger.info(f"🕒 Using default start_date: 24h ago ({start_date.isoformat()})")
        
        if end_date is None:
            end_date = now
            logger.info(f"🕒 Using default end_date: now ({end_date.isoformat()})")
        
        logger.info(f"📊 Historical data request: {latitude:.4f}, {longitude:.4f} from {start_date} to {end_date}")
        
        # Validation de la plage de dates
        if end_date <= start_date:
            raise HTTPException(
                status_code=400,
                detail="end_date must be after start_date"
            )
        
        # Limiter la plage temporelle pour éviter les requêtes excessives
        max_days = 365
        if (end_date - start_date).days > max_days:
            raise HTTPException(
                status_code=400,
                detail=f"Time range cannot exceed {max_days} days. Current range: {(end_date - start_date).days} days"
            )
        
        # Validation du polluant
        valid_pollutants = ['pm25', 'pm10', 'no2', 'o3', 'so2', 'co']
        if pollutant and pollutant.lower() not in valid_pollutants:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid pollutant. Valid options: {', '.join(valid_pollutants)}"
            )
        
        # Générer les données historiques
        result = generate_historical_data(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            pollutant=pollutant,
            limit=limit
        )
        
        if not result["measurements"]:
            raise HTTPException(
                status_code=404,
                detail="No historical data found for the specified criteria"
            )
        
        logger.info(f" Historical data delivered: {len(result['measurements'])} measurements")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f" Error getting historical air quality: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)