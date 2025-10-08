"""
SCRIPT D'AIDE POUR OBTENIR LES CLÉS API RÉELLES
"""

import os
import asyncio
import aiohttp
from datetime import datetime

def print_header(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_step(step, description):
    print(f"\n{step}. {description}")
    print("-" * 40)

def check_environment_variables():
    """Vérifie quelles variables d'environnement sont définies"""
    print_header("VÉRIFICATION DES CLÉS API ACTUELLES")
    
    api_keys = {
        'OpenAQ v3': 'OPENAQ_API_KEY',
        'PurpleAir': 'PURPLEAIR_API_KEY', 
        'AirNow EPA': 'AIRNOW_API_KEY',
        'IQAir': 'IQAIR_API_KEY',
        'NASA Earthdata Username': 'NASA_EARTHDATA_USERNAME',
        'NASA Earthdata Password': 'NASA_EARTHDATA_PASSWORD'
    }
    
    configured = []
    missing = []
    
    for service, env_var in api_keys.items():
        value = os.getenv(env_var)
        if value:
            configured.append(f"✅ {service}: {'*' * (len(value)-4) + value[-4:] if len(value) > 4 else '*' * len(value)}")
        else:
            missing.append(f"❌ {service}: Variable {env_var} manquante")
    
    if configured:
        print("\n🟢 CLÉS CONFIGURÉES:")
        for item in configured:
            print(f"   {item}")
    
    if missing:
        print("\n🔴 CLÉS MANQUANTES:")
        for item in missing:
            print(f"   {item}")
        print(f"\n💡 Total à configurer: {len(missing)} sur {len(api_keys)}")
    else:
        print("\n🎉 TOUTES LES CLÉS SONT CONFIGURÉES!")
    
    return len(missing) == 0

def guide_openaq_v3():
    """Guide pour obtenir la clé OpenAQ v3"""
    print_header("🌐 OPENAQ V3 - GRATUIT (RECOMMANDÉ)")
    
    print_step("1", "Aller sur le site OpenAQ")
    print("   URL: https://openaq.org/")
    print("   📧 Créer un compte gratuit")
    
    print_step("2", "Demander l'accès API")
    print("   📩 Contact: https://openaq.org/contact")
    print("   📝 Mentionner: 'Demande d'accès API v3 pour projet de recherche air quality'")
    print("   ⏱️ Délai: 1-3 jours ouvrables")
    
    print_step("3", "Récupérer la clé")
    print("   📧 Vous recevrez la clé par email")
    print("   🔐 Format: 'openaq_api_key_xxxxxxxxxxxxx'")
    
    print_step("4", "Configurer la variable d'environnement")
    print("   Windows PowerShell:")
    print("   $env:OPENAQ_API_KEY='votre_cle_ici'")
    print("   ")
    print("   Linux/Mac:")
    print("   export OPENAQ_API_KEY='votre_cle_ici'")
    
    print("\n💡 AVANTAGES:")
    print("   ✅ Gratuit pour usage raisonnable")
    print("   ✅ Données mondiales")
    print("   ✅ Très fiable")
    print("   ✅ API moderne et bien documentée")

def guide_purpleair():
    """Guide pour obtenir la clé PurpleAir"""
    print_header("🟣 PURPLEAIR - PAYANT (~10€/mois)")
    
    print_step("1", "Créer un compte")
    print("   URL: https://develop.purpleair.com/")
    print("   📧 Inscription gratuite")
    
    print_step("2", "Souscrire à un plan API")
    print("   💰 Prix: ~$10/mois (≈10€)")
    print("   📊 Limites: 1000 requêtes/jour (plan de base)")
    print("   🔄 Upgrade possible")
    
    print_step("3", "Obtenir la clé")
    print("   🔐 Disponible dans votre dashboard")
    print("   📋 Format: UUID (ex: 12345678-1234-5678-9012-123456789012)")
    
    print_step("4", "Configurer")
    print("   $env:PURPLEAIR_API_KEY='votre_uuid_ici'")
    
    print("\n💡 AVANTAGES:")
    print("   ✅ Excellent pour PM2.5/PM10")
    print("   ✅ Réseau dense aux USA")
    print("   ✅ Données temps réel")
    print("   ✅ API stable et rapide")

def guide_airnow():
    """Guide pour obtenir la clé AirNow EPA"""
    print_header("🇺🇸 AIRNOW EPA - GRATUIT (USA seulement)")
    
    print_step("1", "Demander une clé")
    print("   URL: https://docs.airnowapi.org/account")
    print("   📧 Remplir le formulaire")
    print("   ⏱️ Délai: 1-2 jours")
    
    print_step("2", "Recevoir la clé")
    print("   📧 Envoyée par email")
    print("   🔐 Format: UUID")
    
    print_step("3", "Configurer")
    print("   $env:AIRNOW_API_KEY='votre_cle_ici'")
    
    print("\n💡 AVANTAGES:")
    print("   ✅ Gratuit")
    print("   ✅ Données officielles EPA")
    print("   ✅ Très fiable")
    print("   ❌ USA seulement")

def guide_iqair():
    """Guide pour obtenir la clé IQAir"""
    print_header("🌍 IQAIR - PREMIUM (~30€/mois)")
    
    print_step("1", "Créer un compte")
    print("   URL: https://www.iqair.com/air-pollution-data-api")
    print("   📧 Inscription")
    
    print_step("2", "Choisir un plan")
    print("   💰 Prix: $29-199/mois (≈30-200€)")
    print("   📊 Community: 10,000 calls/mois")
    print("   🏢 Startup: 100,000 calls/mois")
    
    print_step("3", "Obtenir la clé")
    print("   🔐 Dans votre dashboard")
    print("   📋 Format: UUID")
    
    print_step("4", "Configurer")
    print("   $env:IQAIR_API_KEY='votre_cle_ici'")
    
    print("\n💡 AVANTAGES:")
    print("   ✅ Couverture mondiale excellent")
    print("   ✅ Données météo incluses")
    print("   ✅ API très stable")
    print("   ✅ Support commercial")

def guide_nasa_earthdata():
    """Guide pour obtenir les credentials NASA Earthdata"""
    print_header("🛰️ NASA EARTHDATA - GRATUIT")
    
    print_step("1", "Créer un compte NASA Earthdata")
    print("   URL: https://urs.earthdata.nasa.gov/")
    print("   📧 Inscription gratuite")
    print("   📋 Remplir le profil")
    
    print_step("2", "Activer l'accès aux applications")
    print("   🔐 Approuver l'accès aux données TEMPO")
    print("   📊 Applications -> Authorize")
    
    print_step("3", "Configurer les credentials")
    print("   $env:NASA_EARTHDATA_USERNAME='votre_username'")
    print("   $env:NASA_EARTHDATA_PASSWORD='votre_password'")
    
    print("\n💡 AVANTAGES:")
    print("   ✅ Gratuit")
    print("   ✅ Données satellitaires officielles")
    print("   ✅ Accès à TEMPO, AIRS, etc.")
    print("   ❌ API complexe (NetCDF/HDF5)")

def create_env_file_template():
    """Crée un fichier .env template"""
    print_header("📄 CRÉATION DU FICHIER .ENV")
    
    env_content = """# Clés API pour sources de données réelles
# Obtenez ces clés en suivant le guide

# OpenAQ v3 (Gratuit - Recommandé)
# https://openaq.org/contact
OPENAQ_API_KEY=

# PurpleAir (~10€/mois)
# https://develop.purpleair.com/
PURPLEAIR_API_KEY=

# AirNow EPA (Gratuit - USA seulement)
# https://docs.airnowapi.org/account
AIRNOW_API_KEY=

# IQAir (~30€/mois - Premium)
# https://www.iqair.com/air-pollution-data-api
IQAIR_API_KEY=

# NASA Earthdata (Gratuit)
# https://urs.earthdata.nasa.gov/
NASA_EARTHDATA_USERNAME=
NASA_EARTHDATA_PASSWORD=

# Configuration optionnelle
API_CACHE_DURATION=300
API_TIMEOUT=30
API_MAX_RETRIES=3
"""
    
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("✅ Fichier .env créé avec succès!")
        print("📝 Éditez le fichier .env pour ajouter vos clés API")
        print("🔐 Ne commitez JAMAIS ce fichier dans git!")
        
        # Créer aussi .env.example
        with open('.env.example', 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("✅ Fichier .env.example créé pour référence")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création du fichier .env: {e}")

def create_powershell_script():
    """Crée un script PowerShell pour configurer les variables"""
    print_header("⚡ SCRIPT POWERSHELL DE CONFIGURATION")
    
    ps_content = """# Script PowerShell pour configurer les variables d'environnement
# Exécutez ce script après avoir obtenu vos clés API

Write-Host "🔧 Configuration des variables d'environnement API" -ForegroundColor Green

# Demander les clés à l'utilisateur
$openaq = Read-Host "OpenAQ API Key (optionnel, appuyez sur Entrée pour ignorer)"
$purpleair = Read-Host "PurpleAir API Key (optionnel, appuyez sur Entrée pour ignorer)"
$airnow = Read-Host "AirNow EPA API Key (optionnel, appuyez sur Entrée pour ignorer)"
$iqair = Read-Host "IQAir API Key (optionnel, appuyez sur Entrée pour ignorer)"
$nasa_user = Read-Host "NASA Earthdata Username (optionnel, appuyez sur Entrée pour ignorer)"
$nasa_pass = Read-Host "NASA Earthdata Password (optionnel, appuyez sur Entrée pour ignorer)" -AsSecureString

# Configurer les variables (session actuelle)
if ($openaq) { $env:OPENAQ_API_KEY = $openaq }
if ($purpleair) { $env:PURPLEAIR_API_KEY = $purpleair }
if ($airnow) { $env:AIRNOW_API_KEY = $airnow }
if ($iqair) { $env:IQAIR_API_KEY = $iqair }
if ($nasa_user) { $env:NASA_EARTHDATA_USERNAME = $nasa_user }
if ($nasa_pass) { 
    $nasa_pass_plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($nasa_pass))
    $env:NASA_EARTHDATA_PASSWORD = $nasa_pass_plain 
}

Write-Host "✅ Variables configurées pour cette session" -ForegroundColor Green
Write-Host "💡 Pour les rendre permanentes, ajoutez-les aux Variables Système Windows" -ForegroundColor Yellow

# Afficher les variables configurées
Write-Host "`n📊 Variables configurées:" -ForegroundColor Cyan
if ($env:OPENAQ_API_KEY) { Write-Host "   ✅ OPENAQ_API_KEY" -ForegroundColor Green }
if ($env:PURPLEAIR_API_KEY) { Write-Host "   ✅ PURPLEAIR_API_KEY" -ForegroundColor Green }
if ($env:AIRNOW_API_KEY) { Write-Host "   ✅ AIRNOW_API_KEY" -ForegroundColor Green }
if ($env:IQAIR_API_KEY) { Write-Host "   ✅ IQAIR_API_KEY" -ForegroundColor Green }
if ($env:NASA_EARTHDATA_USERNAME) { Write-Host "   ✅ NASA_EARTHDATA_USERNAME" -ForegroundColor Green }
if ($env:NASA_EARTHDATA_PASSWORD) { Write-Host "   ✅ NASA_EARTHDATA_PASSWORD" -ForegroundColor Green }
"""
    
    try:
        with open('setup_api_keys.ps1', 'w', encoding='utf-8') as f:
            f.write(ps_content)
        print("✅ Script setup_api_keys.ps1 créé!")
        print("📝 Exécutez: ./setup_api_keys.ps1")
        print("🔐 Le script vous demandera vos clés de manière sécurisée")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création du script: {e}")

async def test_api_connectivity():
    """Test la connectivité aux APIs (sans clés)"""
    print_header("🧪 TEST DE CONNECTIVITÉ DES APIS")
    
    apis_to_test = [
        ("OpenAQ v3", "https://api.openaq.org/v3/locations?limit=1"),
        ("PurpleAir", "https://api.purpleair.com/v1/keys"),
        ("AirNow EPA", "https://www.airnowapi.org/"),
        ("IQAir", "https://api.airvisual.com/v2/"),
        ("NASA Earthdata", "https://urs.earthdata.nasa.gov/")
    ]
    
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        for name, url in apis_to_test:
            try:
                print(f"\n📡 Test {name}...")
                async with session.get(url) as response:
                    status = response.status
                    if status in [200, 401, 403]:  # 401/403 = API accessible mais auth requise
                        print(f"   ✅ {name}: Accessible (Status {status})")
                    else:
                        print(f"   ⚠️ {name}: Status {status}")
                        
            except Exception as e:
                print(f"   ❌ {name}: Erreur de connexion - {str(e)[:50]}...")

def show_cost_summary():
    """Affiche un résumé des coûts"""
    print_header("💰 RÉSUMÉ DES COÛTS")
    
    costs = [
        ("🌐 OpenAQ v3", "GRATUIT", "Données mondiales, excellent choix"),
        ("🇺🇸 AirNow EPA", "GRATUIT", "USA seulement, données officielles"),
        ("🛰️ NASA Earthdata", "GRATUIT", "Données satellitaires, complexe"),
        ("🟣 PurpleAir", "~10€/mois", "Excellent pour PM2.5/PM10"),
        ("🌍 IQAir", "~30€/mois", "Premium, couverture mondiale")
    ]
    
    print("\n📊 OPTIONS PAR COÛT:")
    for service, cost, description in costs:
        print(f"   {service:<20} {cost:<15} - {description}")
    
    print("\n🎯 RECOMMANDATIONS:")
    print("   🆓 BUDGET ZÉRO: OpenAQ v3 + AirNow EPA + NASA Earthdata")
    print("   💰 BUDGET LIMITÉ: + PurpleAir (10€/mois)")
    print("   🏢 PROFESSIONNEL: + IQAir (40€/mois total)")
    
    print("\n⏱️ DÉLAIS D'OBTENTION:")
    print("   🚀 Immédiat: NASA Earthdata")
    print("   📧 1-3 jours: OpenAQ v3, AirNow EPA")
    print("   💳 Immédiat (payant): PurpleAir, IQAir")

def main():
    """Fonction principale du guide"""
    print("🚀 GUIDE COMPLET POUR OBTENIR DES DONNÉES RÉELLES")
    print("=" * 60)
    print("Ce guide va vous aider à obtenir les clés API pour remplacer")
    print("les données simulées par de VRAIES données de qualité de l'air!")
    
    # Vérification initiale
    all_configured = check_environment_variables()
    
    if all_configured:
        print("\n🎉 Toutes vos clés sont déjà configurées!")
        print("✅ Vous pouvez utiliser le connecteur API réel")
        return
    
    print("\n📋 MENU DES GUIDES:")
    print("1. 🌐 OpenAQ v3 (GRATUIT - Recommandé)")
    print("2. 🟣 PurpleAir (~10€/mois)")
    print("3. 🇺🇸 AirNow EPA (GRATUIT - USA)")
    print("4. 🌍 IQAir (~30€/mois - Premium)")
    print("5. 🛰️ NASA Earthdata (GRATUIT)")
    print("6. 📄 Créer fichier .env template")
    print("7. ⚡ Créer script PowerShell")
    print("8. 🧪 Tester connectivité APIs")
    print("9. 💰 Résumé des coûts")
    print("0. 🔄 Vérifier variables actuelles")
    
    while True:
        try:
            choice = input("\n👉 Choisissez une option (ou 'q' pour quitter): ").strip()
            
            if choice.lower() == 'q':
                break
            elif choice == '1':
                guide_openaq_v3()
            elif choice == '2':
                guide_purpleair()
            elif choice == '3':
                guide_airnow()
            elif choice == '4':
                guide_iqair()
            elif choice == '5':
                guide_nasa_earthdata()
            elif choice == '6':
                create_env_file_template()
            elif choice == '7':
                create_powershell_script()
            elif choice == '8':
                asyncio.run(test_api_connectivity())
            elif choice == '9':
                show_cost_summary()
            elif choice == '0':
                check_environment_variables()
            else:
                print("❌ Option invalide. Choisissez 1-9 ou 'q'")
                
        except KeyboardInterrupt:
            print("\n\n👋 Au revoir!")
            break

if __name__ == "__main__":
    main()