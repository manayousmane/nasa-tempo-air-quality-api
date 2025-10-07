# Configuration Render.com pour NASA TEMPO API

## Variables d'environnement requises

Pour que votre API fonctionne correctement sur Render.com, vous devez configurer les variables d'environnement suivantes dans l'interface Render :

### 1. Accédez aux paramètres du service

1. Connectez-vous à votre dashboard Render.com
2. Sélectionnez votre service "nasa-tempo-air-quality-api"
3. Cliquez sur "Environment" dans le menu de gauche

### 2. Ajoutez les variables d'environnement

Cliquez sur "Add Environment Variable" et ajoutez ces variables une par une :

#### Variables NASA (OBLIGATOIRES)
```
NASA_EARTHDATA_USERNAME = Charmant
NASA_EARTHDATA_PASSWORD = WaHz2k05kis$
NASA_EARTHDATA_TOKEN = eyJ0eXAiOiJKV1QiLCJvcmlnaW4iOiJFYXJ0aGRhdGEgTG9naW4iLCJzaWciOiJlZGxqd3RwdWJrZXlfb3BzIiwiYWxnIjoiUlMyNTYifQ.eyJ0eXBlIjoiVXNlciIsInVpZCI6ImNoYXJtYW50IiwiZXhwIjoxNzY1MDIzNTY3LCJpYXQiOjE3NTk4Mzk1NjcsImlzcyI6Imh0dHBzOi8vdXJzLmVhcnRoZGF0YS5uYXNhLmdvdiIsImlkZW50aXR5X3Byb3ZpZGVyIjoiZWRsX29wcyIsImFjciI6ImVkbCIsImFzc3VyYW5jZV9sZXZlbCI6M30.15cH4mfAx-8cF4EJ8n2LQwlxIs_ebEu8q5a8xXmt2iy4SfpkgnGh_u14azwEUYIn9P8XuxEn-WpzufncLTf0qyKVcJdBwlCFVQ-2bmd9muvB3d56rvWwgfMaapu6iZk1H3lWOZdsFv_jypp4M7VV_fEsONh_Kuk2dvx7vUI8FnhlndUqI6nTYdHtUleuMrGIJsFXEdOUTa3xrgCCREXLY5hnH0DpZCesaV_gen3jkWYjsbxsJdQ-WhlZbAi3wY-LH6PjpMaxd736ZmL_lKHWoz4TudwDqnQ7-H9gXSGUxRkTr8_SrxRP0K7naZ6uLOk4myXdA3Elr-41QBzwgZn93Q
```

#### Variables optionnelles pour optimisation
```
HOST = 0.0.0.0
PORT = 8000
DEBUG = False
LOG_LEVEL = INFO
```

### 3. Variables déjà configurées automatiquement

Ces variables sont automatiquement configurées par Render :
- `PORT` (généralement 10000)
- `RENDER` (défini automatiquement par Render)

### 4. Redéployez le service

Après avoir ajouté toutes les variables :
1. Cliquez sur "Save Changes"
2. Render redéployera automatiquement votre service
3. Le déploiement devrait maintenant réussir

## Vérification du déploiement

### Endpoints à tester après déploiement

1. **Health Check** : `https://votre-app.onrender.com/health`
2. **Documentation API** : `https://votre-app.onrender.com/docs`
3. **Test API** : `https://votre-app.onrender.com/api/v1/location/full?lat=40.7589&lon=-73.9851&radius=25`

### Logs à surveiller

Les logs devraient maintenant afficher :
```
2025-10-07 XX:XX:XX - __main__ - INFO - Starting NASA TEMPO Air Quality API
2025-10-07 XX:XX:XX - __main__ - INFO - Environment variables configured
2025-10-07 XX:XX:XX - __main__ - INFO - All required dependencies available
2025-10-07 XX:XX:XX - __main__ - INFO - NASA authentication: True
2025-10-07 XX:XX:XX - __main__ - INFO - Starting server on http://0.0.0.0:8000
```

## Dépannage

### Si les variables sont toujours manquantes

1. Vérifiez l'orthographe exacte des noms de variables
2. Assurez-vous qu'il n'y a pas d'espaces avant/après les valeurs
3. Redéployez manuellement si nécessaire

### Si l'authentification NASA échoue

1. Vérifiez que votre token NASA n'a pas expiré
2. Testez vos credentials localement d'abord
3. Régénérez un nouveau token si nécessaire

### Commandes utiles pour les logs

Dans l'interface Render, utilisez l'onglet "Logs" pour surveiller :
- Messages de démarrage
- Erreurs d'authentification
- Requêtes API

## URL de votre API déployée

Une fois configuré correctement, votre API sera accessible à :
`https://nasa-tempo-air-quality-api-xxxx.onrender.com`

Remplacez `xxxx` par l'identifiant unique généré par Render.