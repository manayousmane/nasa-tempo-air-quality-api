# Script PowerShell pour recréer l'environnement Python 3.11
# setup-py311.ps1

Write-Host "🐍 Configuration environnement Python 3.11 pour NASA TEMPO API" -ForegroundColor Green

# Désactiver l'environnement actuel si activé
if ($env:VIRTUAL_ENV) {
    Write-Host "Désactivation de l'environnement actuel..." -ForegroundColor Yellow
    deactivate
}

# Supprimer l'ancien environnement
if (Test-Path ".venv") {
    Write-Host "Suppression de l'ancien environnement..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force .venv
}

# Vérifier Python 3.11
Write-Host "Vérification de Python 3.11..." -ForegroundColor Blue
$python311 = $null
if (Get-Command "python3.11" -ErrorAction SilentlyContinue) {
    $python311 = "python3.11"
} elseif (Get-Command "py" -ErrorAction SilentlyContinue) {
    $python311 = "py -3.11"
} else {
    Write-Host "❌ Python 3.11 non trouvé. Installez-le depuis python.org" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Python 3.11 trouvé: $python311" -ForegroundColor Green

# Créer le nouvel environnement
Write-Host "Création de l'environnement virtuel..." -ForegroundColor Blue
& $python311 -m venv .venv

# Activer l'environnement
Write-Host "Activation de l'environnement..." -ForegroundColor Blue
& .venv\Scripts\Activate.ps1

# Mettre à jour pip et outils
Write-Host "Mise à jour des outils de base..." -ForegroundColor Blue
python -m pip install --upgrade pip setuptools wheel

# Installer les dépendances
Write-Host "Installation des dépendances..." -ForegroundColor Blue
pip install -r requirements.txt

# Vérifications
Write-Host "Vérifications finales..." -ForegroundColor Blue
python --version
pip list | Select-String "fastapi|pandas|numpy"

Write-Host "🎉 Environnement Python 3.11 prêt !" -ForegroundColor Green
Write-Host "Pour tester: python start_server.py" -ForegroundColor Cyan