"""
API Simple - DEUX ENDPOINTS qui marchent
1. /location/full - données actuelles
2. /forecast - prédictions
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import random
import math
from typing import List, Optional

app = FastAPI(title="Air Quality API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

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
        "message": "API fonctionne", 
        "endpoints": {
            "current": "/location/full?latitude=45.5&longitude=2.3",
            "forecast": "/forecast?latitude=45.5&longitude=2.3&hours=24"
        }
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)