# 🚀 Guide de publication sur GitHub avec un autre compte

## 1. Configuration d'un nouveau compte GitHub

### Étape 1 : Créer/Configurer le compte GitHub
1. Créez un nouveau compte sur https://github.com (si pas déjà fait)
2. Confirmez l'email du nouveau compte

### Étape 2 : Configuration Git locale pour ce projet
```bash
# Aller dans le dossier du projet
cd "C:\Users\Utilisateur\Documents\NASA_Space"

# Configurer Git pour ce projet spécifiquement
git config user.name "NOUVEAU_NOM_UTILISATEUR"
git config user.email "NOUVEAU_EMAIL@example.com"

# Vérifier la configuration
git config user.name
git config user.email
```

## 2. Initialisation du repository Git

```bash
# Initialiser le repository Git
git init

# Ajouter tous les fichiers (respectera le .gitignore)
git add .

# Premier commit
git commit -m "🛰️ Initial commit: NASA TEMPO Air Quality API"
```

## 3. Création du repository sur GitHub

### Option A : Via l'interface GitHub
1. Allez sur https://github.com
2. Connectez-vous avec le nouveau compte
3. Cliquez sur "New repository"
4. Nom suggéré : `nasa-tempo-air-quality-api`
5. Description : "🛰️ NASA TEMPO Air Quality Prediction API with FastAPI and ML models"
6. Repository public ou privé (votre choix)
7. **NE PAS** initialiser avec README, .gitignore, ou license (déjà créés)

### Option B : Via GitHub CLI (si installé)
```bash
# Installer GitHub CLI si pas déjà fait
winget install GitHub.cli

# Se connecter avec le nouveau compte
gh auth login

# Créer le repository
gh repo create nasa-tempo-air-quality-api --public --description "🛰️ NASA TEMPO Air Quality Prediction API"
```

## 4. Connexion et push vers GitHub

```bash
# Ajouter l'origin remote (remplacer USERNAME par le nom du nouveau compte)
git remote add origin https://github.com/USERNAME/nasa-tempo-air-quality-api.git

# Push du code
git branch -M main
git push -u origin main
```

## 5. Authentication alternatives

### Option A : Personal Access Token (Recommandé)
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token avec les scopes : `repo`, `workflow`
3. Utiliser le token comme mot de passe lors du push

### Option B : SSH (Plus sécurisé)
```bash
# Générer une nouvelle clé SSH pour ce compte
ssh-keygen -t ed25519 -C "NOUVEAU_EMAIL@example.com" -f ~/.ssh/id_ed25519_nouveau_compte

# Ajouter la clé à l'agent SSH
ssh-add ~/.ssh/id_ed25519_nouveau_compte

# Afficher la clé publique pour l'ajouter sur GitHub
cat ~/.ssh/id_ed25519_nouveau_compte.pub
```

Puis ajouter cette clé dans GitHub → Settings → SSH and GPG keys

## 6. Structure finale du repository

```
nasa-tempo-air-quality-api/
├── README.md                    ✅ Créé
├── LICENSE                      ✅ Créé  
├── .gitignore                   ✅ Créé
├── requirements.txt             ✅ Existant
├── start_server.py              ✅ Existant
├── app/                         ✅ Code principal
├── models/                      ✅ Modèles ML
├── config/                      ✅ Configuration
└── .github/                     ✅ Métadonnées
```

## 7. Commandes finales

```bash
# Vérifier que tout est prêt
git status
git log --oneline

# Si des modifications supplémentaires
git add .
git commit -m "📝 Update documentation and configuration"
git push
```

## 🎯 Nom suggéré pour le repository
`nasa-tempo-air-quality-api`

## 🔧 Étapes suivantes après le push
1. Activer GitHub Pages (si souhaité)
2. Configurer les GitHub Actions (CI/CD)
3. Ajouter des badges au README
4. Créer des releases

---
**✅ Votre projet sera maintenant accessible publiquement et prêt pour la collaboration !**