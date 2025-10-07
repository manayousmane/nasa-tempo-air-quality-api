"""
API Simple - UN SEUL ENDPOINT qui marche
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import random
import math

app = FastAPI(title="Air Quality API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "API fonctionne", "endpoint": "/location/full?latitude=45.5&longitude=2.3"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/location/full")
def get_location_full(latitude: float, longitude: float):
    """L'UNIQUE endpoint demandé"""
    
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)