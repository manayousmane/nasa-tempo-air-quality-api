# NASA TEMPO Air Quality API - Instructions Copilot

## Projet Description
API FastAPI pour les prédictions de qualité de l'air utilisant les données du satellite NASA TEMPO.

## Architecture
- **Backend**: FastAPI avec modèles ML
- **Données**: NASA TEMPO + sources ouvertes
- **Couverture**: Amérique du Nord (37 locations)

## Endpoint Principal
`GET /api/v1/location/location/{location_name}` - Retourne toutes les données LocationDataType pour une location donnée.

## Fonctionnalités Complétées
- ✅ Service de géocodage (37 locations NA)
- ✅ Endpoint location data simplifié
- ✅ Intégration TEMPO ML
- ✅ API documentation
- ✅ Tests validés