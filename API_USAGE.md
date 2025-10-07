# API Air Quality - Guide d'utilisation

## 🚀 Démarrage rapide

```bash
# Démarrer l'API
python app/main.py

# L'API sera disponible sur http://localhost:8000
```

## 📋 Endpoints disponibles

### 1. `/location/full` - Données actuelles

Récupère les données actuelles de qualité de l'air pour une localisation.

**Paramètres:**
- `latitude` (float): Latitude (-90 à 90)
- `longitude` (float): Longitude (-180 à 180)

**Exemple:**
```bash
curl "http://localhost:8000/location/full?latitude=48.8566&longitude=2.3522"
```

**Réponse:**
```json
{
  "name": "Paris, France",
  "coordinates": [48.8566, 2.3522],
  "aqi": 85,
  "pm25": 18.5,
  "pm10": 28.3,
  "no2": 35.2,
  "o3": 52.1,
  "so2": 7.8,
  "co": 1.45,
  "temperature": 15.2,
  "humidity": 67.3,
  "windSpeed": 8.5,
  "windDirection": "SW",
  "pressure": 1015.2,
  "visibility": 12.5,
  "lastUpdated": "2025-10-07T15:30:00Z"
}
```

### 2. `/forecast` - Prédictions

Récupère les prédictions de qualité de l'air (inspiré de tempo_predictions.py).

**Paramètres:**
- `latitude` (float): Latitude (-90 à 90)
- `longitude` (float): Longitude (-180 à 180)
- `hours` (int): Nombre d'heures de prédiction (1 à 72, défaut: 24)

**Exemple:**
```bash
curl "http://localhost:8000/forecast?latitude=48.8566&longitude=2.3522&hours=12"
```

**Réponse:**
```json
{
  "location": {
    "name": "Paris, France",
    "coordinates": [48.8566, 2.3522]
  },
  "current": {
    "aqi": 78,
    "pm25": 16.2,
    "pm10": 24.8,
    "no2": 32.1,
    "o3": 48.5,
    "so2": 6.9,
    "co": 1.32,
    "timestamp": "2025-10-07T15:30:00Z"
  },
  "forecast": [
    {
      "hour": 1,
      "timestamp": "2025-10-07T16:30:00Z",
      "pm25": 17.3,
      "pm10": 26.1,
      "no2": 34.8,
      "o3": 51.2,
      "so2": 7.2,
      "co": 1.38,
      "aqi": 82,
      "confidence": 0.87
    }
    // ... plus de prédictions
  ],
  "summary": {
    "forecast_hours": 12,
    "avg_aqi": 85.3,
    "max_aqi": 95,
    "min_aqi": 72,
    "trend": "stable"
  },
  "health": {
    "level": "Moderate",
    "message": "Air quality is acceptable",
    "activities": "Sensitive individuals should limit outdoor exertion"
  },
  "metadata": {
    "model": "Statistical Forecast Model",
    "confidence": "Medium",
    "last_updated": "2025-10-07T15:30:00Z",
    "note": "Predictions based on historical patterns and current conditions"
  }
}
```

## 🧪 Tests

```bash
# Tester les deux endpoints
python test_both_endpoints.py
```

## 📚 Documentation interactive

- **Swagger UI**: http://localhost:8000/docs
- **Root endpoint**: http://localhost:8000/

## 🏗️ Architecture

L'endpoint `/forecast` est basé sur la structure de `tempo_predictions.py` mais utilise des données simulées réalistes qui:

1. **Varient selon l'heure**: Les polluants suivent des patterns naturels
2. **Considèrent la location**: Urbain vs rural
3. **Incluent la confiance**: Diminue avec le temps
4. **Calculent l'AQI**: Formules EPA simplifiées
5. **Fournissent des recommandations**: Santé publique

## ✅ Fonctionnalités

- ✅ Deux endpoints fonctionnels
- ✅ Validation des paramètres
- ✅ Données réalistes simulées
- ✅ Gestion d'erreurs
- ✅ Documentation Swagger
- ✅ Prédictions avec tendances
- ✅ Recommandations santé
- ✅ Calculs AQI