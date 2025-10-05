# 🛰️ NASA TEMPO Air Quality Prediction API

Une API FastAPI avancée pour les prédictions de qualité de l'air utilisant les données du satellite NASA TEMPO et des modèles de machine learning.

*Projet développé pour le NASA Space Apps Challenge : From Data to Action*

## 🌟 Fonctionnalités principales

### 🔍 **Endpoint Location Data**
- **Endpoint principal** : `GET /api/v1/location/location/{location_name}`
- **Fonctionnalité** : Prend un nom de location et retourne toutes les données de qualité d'air
- **Couverture** : 37 locations en Amérique du Nord (États-Unis + Canada)

### 🛰️ **Prédictions TEMPO**
- Modèles ML spécialisés pour l'Amérique du Nord
- Prédictions de PM2.5, PM10, NO2, O3, SO2, CO
- Intégration des données satellitaires NASA TEMPO

### 🌍 **Géolocalisation intelligente**
- Base de données locale des principales villes nord-américaines
- Mapping automatique nom → coordonnées
- Support des États/Provinces et villes principales

## 🚀 Installation rapide

```bash
# Cloner le repository
git clone <VOTRE_REPO_URL>
cd NASA_Space

# Créer l'environnement virtuel
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Installer les dépendances
pip install -r requirements.txt

# Démarrer le serveur
python start_server.py
```

## 📋 Usage

### Exemple d'utilisation de l'endpoint principal

```bash
# Obtenir les données pour Toronto
GET http://localhost:8001/api/v1/location/location/Toronto

# Réponse
{
  "name": "Toronto",
  "coordinates": {
    "latitude": 43.65,
    "longitude": -79.38
  },
  "aqi": 45.2,
  "pm25": 12.8,
  "pm10": 18.5,
  "no2": 22.1,
  "o3": 65.3,
  "so2": 3.2,
  "co": 0.8,
  "temperature": 15.2,
  "humidity": 68.5,
  "windSpeed": 12.3,
  "windDirection": 245,
  "pressure": 1013.2,
  "visibility": 10.0,
  "lastUpdated": "2024-01-20T15:30:00Z"
}
```

### Autres endpoints disponibles

```bash
# Lister toutes les locations disponibles
GET /api/v1/location/locations/available

# Prédictions TEMPO
POST /api/v1/tempo/predict

# Documentation interactive
GET http://localhost:8001/docs
```

## 🌍 Locations supportées

### 🇺🇸 États-Unis
- **Villes** : New York, Los Angeles, Chicago, Houston, Phoenix, Philadelphia, etc.
- **États** : California, Texas, Florida, New York, Illinois, Pennsylvania, etc.

### 🇨🇦 Canada  
- **Villes** : Toronto, Montreal, Vancouver, Calgary, Edmonton, Ottawa, etc.
- **Provinces** : Ontario, Quebec, British Columbia, Alberta

**Total** : 37 locations pré-configurées
- **Geospatial Support**: Location-based predictions and visualizations

## Project Structure

```
nasa-tempo-air-quality-api/
├── app/
│   ├── api/                 # API routes and endpoints
│   ├── core/                # Core configuration and settings
│   ├── data/                # Data collection and processing
│   ├── models/              # Database and ML models
│   ├── services/            # Business logic services
│   └── main.py              # FastAPI application entry point
├── tests/                   # Test files
├── alembic/                 # Database migrations
├── scripts/                 # Utility scripts
├── docs/                    # Documentation
└── requirements.txt         # Python dependencies
```

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run Database Migrations**:
   ```bash
   alembic upgrade head
   ```

4. **Start the Server**:
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Access API Documentation**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Data Sources

### NASA TEMPO
- **Real-time satellite data** for air quality monitoring
- **Coverage**: North America
- **Parameters**: NO2, HCHO, O3, aerosols

### Ground Stations
- **Pandora Network**: Ground-based spectrometers
- **OpenAQ**: Global air quality data
- **EPA AirNow**: US air quality monitoring

### Weather Data
- **OpenWeatherMap API**: Current and forecast weather
- **NOAA**: Historical weather data
- **Integration**: Weather impact on air quality

## API Endpoints

### Air Quality
- `GET /api/v1/air-quality/current` - Current air quality data
- `GET /api/v1/air-quality/forecast` - Air quality predictions
- `GET /api/v1/air-quality/historical` - Historical data

### Locations
- `GET /api/v1/locations` - Available monitoring locations
- `GET /api/v1/locations/{id}` - Location details

### Alerts
- `POST /api/v1/alerts/subscribe` - Subscribe to alerts
- `GET /api/v1/alerts/active` - Current active alerts

## Machine Learning Models

### Forecasting Models
- **XGBoost**: Primary prediction model
- **LSTM Neural Networks**: Time series forecasting
- **Random Forest**: Ensemble predictions

### Model Features
- Satellite measurements (TEMPO)
- Ground station data
- Weather conditions
- Temporal patterns
- Geographical factors

## Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black app/
isort app/
```

### Type Checking
```bash
mypy app/
```

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/nasa_tempo
REDIS_URL=redis://localhost:6379

# APIs
NASA_EARTHDATA_TOKEN=your_token_here
OPENWEATHER_API_KEY=your_key_here
EPA_API_KEY=your_key_here

# Application
DEBUG=True
LOG_LEVEL=INFO
SECRET_KEY=your_secret_key
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Contact

For questions about this project, please contact the NASA TEMPO team.

---

⭐ **N'hésitez pas à star ce projet si vous le trouvez utile !**
