# Guide de Configuration des Vraies Données

Ce guide vous explique exactement comment configurer les vraies données pour le backend NASA TEMPO.

## 🔑 Étape 1: Configuration des Clés API

### 1.1 Créer le fichier .env
```bash
# Copier le fichier exemple
cp .env.example .env
```

### 1.2 Obtenir les Clés API Nécessaires

#### NASA Earthdata (OBLIGATOIRE)
1. **S'inscrire** sur https://earthdata.nasa.gov/
2. **Créer une application** dans le profil utilisateur
3. **Obtenir les credentials**:
   - `NASA_EARTHDATA_USERNAME`
   - `NASA_EARTHDATA_PASSWORD` 
   - `NASA_EARTHDATA_TOKEN`

#### OpenWeatherMap (RECOMMANDÉ)
1. **S'inscrire** sur https://openweathermap.org/api
2. **Plan gratuit** : 1000 calls/jour
3. **Obtenir** : `OPENWEATHER_API_KEY`

#### EPA AirNow (OPTIONNEL - USA uniquement)
1. **S'inscrire** sur https://www.airnow.gov/index.cfm?action=aqibasics.aqi
2. **Demander accès API** : `EPA_API_KEY`

#### OpenAQ (OPTIONNEL - Données globales)
1. **S'inscrire** sur https://openaq.org/
2. **Obtenir** : `OPENAQ_API_KEY`

## 🗄️ Étape 2: Configuration Base de Données

### 2.1 Installer PostgreSQL
```bash
# Windows (avec Chocolatey)
choco install postgresql

# Ou télécharger depuis https://www.postgresql.org/download/windows/
```

### 2.2 Créer la Base de Données
```sql
-- Se connecter à PostgreSQL
psql -U postgres

-- Créer la base de données
CREATE DATABASE nasa_tempo_db;
CREATE USER nasa_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE nasa_tempo_db TO nasa_user;
```

### 2.3 Configurer l'URL de Base de Données
```bash
# Dans .env
DATABASE_URL=postgresql://nasa_user:your_password@localhost:5432/nasa_tempo_db
```

## 📊 Étape 3: Initialiser les Données

### 3.1 Créer les Tables
```bash
# Migrations avec Alembic
alembic upgrade head
```

### 3.2 Peupler les Locations Initiales
```bash
# Exécuter le script d'initialisation
python scripts/init_database.py
```

## 🚀 Étape 4: Tester la Configuration

### 4.1 Test des Connexions API
```bash
# Tester toutes les connexions
python scripts/test_connections.py
```

### 4.2 Test de Collecte de Données
```bash
# Collecter des données réelles
python scripts/collect_sample_data.py
```

## 📍 Locations par Défaut

Le système démarre avec ces locations principales :
- New York City (40.7589, -73.9851)
- Los Angeles (34.0522, -118.2437)
- Paris (48.8566, 2.3522)
- Londres (51.5074, -0.1278)
- Tokyo (35.6762, 139.6503)
- Mexico City (19.4326, -99.1332)
- São Paulo (-23.5505, -46.6333)
- Le Caire (30.0444, 31.2357)

## ⚠️ Points d'Attention

1. **Limites API** : Respecter les quotas des services externes
2. **Cache** : Utiliser Redis pour éviter les appels répétitifs
3. **Monitoring** : Surveiller les erreurs de connexion
4. **Fallback** : Le système fonctionne même si certaines sources sont indisponibles

## 🔧 Dépannage

### Problème: NASA TEMPO ne répond pas
```python
# Vérifier l'authentification
async def test_tempo():
    async with tempo_collector as collector:
        success = await collector.authenticate()
        print(f"Auth: {success}")
```

### Problème: Base de données inaccessible
```bash
# Vérifier la connexion
python -c "from app.core.config import settings; print(settings.DATABASE_URL)"
```

### Problème: API météo en erreur
```bash
# Tester la clé OpenWeatherMap
curl "http://api.openweathermap.org/data/2.5/weather?q=Paris&appid=YOUR_API_KEY"
```