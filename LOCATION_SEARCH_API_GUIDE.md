# 🌍 API LOCATION SEARCH - Guide d'Utilisation

## ✅ **ENDPOINT CRÉÉ AVEC SUCCÈS**

L'endpoint pour rechercher la qualité de l'air par nom de lieu est maintenant opérationnel !

## 🚀 **Démarrage Rapide**

```bash
# Démarrer le serveur
python start_server.py

# Ou alternativement:
python -m uvicorn app.main:app --port 8001
```

**Serveur disponible sur:** `http://127.0.0.1:8001`  
**Documentation interactive:** `http://127.0.0.1:8001/docs`

---

## 📋 **ENDPOINTS DISPONIBLES**

### **Base URL:** `/api/v1/location-search`

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/available-locations` | Liste toutes les locations (37 disponibles) |
| `GET` | `/suggest?q=new` | Suggestions auto-complete |
| `POST` | `/search` | **PRINCIPAL** - Recherche par nom |
| `POST` | `/search-multiple` | Recherche batch (max 10) |
| `GET` | `/health` | Santé du service |

---

## 🎯 **UTILISATION PRINCIPALE** 

### **Recherche par nom de lieu:**

```bash
curl -X POST "http://127.0.0.1:8001/api/v1/location-search/search" \
  -H "Content-Type: application/json" \
  -d '{
    "location_name": "New York", 
    "include_predictions": true
  }'
```

### **Réponse (selon LocationDataType):**
```json
{
  "success": true,
  "location_found": true,
  "location_info": {
    "name": "New York",
    "latitude": 40.7128,
    "longitude": -74.0060,
    "country": "United States",
    "state": "New York"
  },
  "air_quality_data": {
    "name": "New York",
    "coordinates": [40.7128, -74.0060],
    "aqi": 105,
    "pm25": 29.5,
    "pm10": 58.8,
    "no2": 52.3,
    "o3": 56.4,
    "so2": 9.5,
    "co": 1.4,
    "temperature": 15.0,
    "humidity": 65.0,
    "wind_speed": 5.0,
    "wind_direction": "SW",
    "pressure": 1013.25,
    "visibility": 10.0,
    "last_updated": "2025-10-05T..."
  }
}
```

---

## 🗺️ **TYPES DE RECHERCHE SUPPORTÉS**

### **37 Locations Disponibles:**

#### **🇺🇸 États-Unis (24 locations)**
- **Pays:** "United States", "USA"
- **États:** "California", "Texas", "Florida", "New York State", etc.
- **Villes:** "New York", "Los Angeles", "Chicago", "Houston", "Miami", etc.

#### **🇨🇦 Canada (13 locations)**
- **Pays:** "Canada"
- **Provinces:** "Ontario", "Quebec", "British Columbia", "Alberta"
- **Villes:** "Toronto", "Montreal", "Vancouver", "Calgary", "Ottawa", etc.

---

## 💡 **EXEMPLES D'UTILISATION**

### **1. Recherche par ville:**
```bash
curl -X POST "http://127.0.0.1:8001/api/v1/location-search/search" \
  -H "Content-Type: application/json" \
  -d '{"location_name": "Toronto", "include_predictions": true}'
```

### **2. Recherche par état/province:**
```bash
curl -X POST "http://127.0.0.1:8001/api/v1/location-search/search" \
  -H "Content-Type: application/json" \
  -d '{"location_name": "California", "include_predictions": true}'
```

### **3. Suggestions auto-complete:**
```bash
curl "http://127.0.0.1:8001/api/v1/location-search/suggest?q=los"
# Retourne: ["Los Angeles"]
```

### **4. Recherche multiple:**
```bash
curl -X POST "http://127.0.0.1:8001/api/v1/location-search/search-multiple" \
  -H "Content-Type: application/json" \
  -d '{
    "location_names": ["New York", "Toronto", "Los Angeles"],
    "include_predictions": true
  }'
```

### **5. Liste complète des locations:**
```bash
curl "http://127.0.0.1:8001/api/v1/location-search/available-locations"
```

---

## 📊 **DONNÉES RETOURNÉES**

Conforme au type `LocationDataType` que vous avez spécifié :

```typescript
interface LocationDataType {
  name: string;
  coordinates: [number, number];
  aqi?: number;
  pm25?: number;
  pm10?: number;
  no2?: number;
  o3?: number;
  so2?: number;
  co?: number;
  temperature?: number;
  humidity?: number;
  windSpeed?: number;
  windDirection?: string;
  pressure?: number;
  visibility?: number;
  lastUpdated: string;
}
```

---

## ✅ **VALIDATION**

- ✅ **Endpoint créé:** `/api/v1/location-search/search`
- ✅ **Entrée:** Nom du pays/état/province/ville
- ✅ **Sortie:** Coordonnées + données air quality complètes
- ✅ **37 locations** Amérique du Nord supportées
- ✅ **Prédictions TEMPO** intégrées
- ✅ **Auto-complete** disponible
- ✅ **Batch processing** jusqu'à 10 locations

## 🎉 **API LOCATION SEARCH OPÉRATIONNELLE !**

L'endpoint répond exactement à votre demande basée sur l'image `LocationDataType` fournie.