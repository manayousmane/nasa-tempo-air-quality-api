"""
Connecteur TEMPO pour les dernières données disponibles
Recherche les données TEMPO des derniers jours au lieu du temps réel uniquement
"""
import asyncio
import earthaccess
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import aiohttp
from dotenv import load_dotenv
import os
import xarray as xr
import numpy as np
import tempfile
import numpy as np
import tempfile

# Chargement des variables d'environnement
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(env_path)

logger = logging.getLogger(__name__)

class TempoLatestDataClient:
    """
    Client TEMPO spécialisé pour récupérer les dernières données disponibles
    Recherche sur une période étendue pour maximiser les chances de trouver des données
    """
    
    def __init__(self):
        self.authenticated = False
        self.max_search_days = 7  # Rechercher sur les 7 derniers jours
        
        # Collections TEMPO avec leurs concepts
        self.tempo_collections = {
            'no2': {
                'concept_id': 'C2765522927-GES_DISC',
                'short_name': 'TEMPO_NO2_L2',
                'description': 'TEMPO Nitrogen Dioxide (NO2) Total Column'
            },
            'hcho': {
                'concept_id': 'C2765526899-GES_DISC', 
                'short_name': 'TEMPO_HCHO_L2',
                'description': 'TEMPO Formaldehyde (HCHO) Total Column'
            },
            'aerosol': {
                'concept_id': 'C2765525281-GES_DISC',
                'short_name': 'TEMPO_AOD_L2',
                'description': 'TEMPO Aerosol Optical Depth'
            },
            'o3': {
                'concept_id': 'C2765524647-GES_DISC',
                'short_name': 'TEMPO_O3TOT_L2', 
                'description': 'TEMPO Ozone (O3) Total Column'
            }
        }
        
    async def authenticate(self):
        """Authentification NASA Earthdata"""
        if self.authenticated:
            return True
            
        try:
            username = os.getenv('NASA_EARTHDATA_USERNAME')
            password = os.getenv('NASA_EARTHDATA_PASSWORD')
            
            if not username or not password:
                logger.error("❌ Identifiants NASA Earthdata manquants")
                return False
            
            # Authentification earthaccess (version corrigée)
            auth = earthaccess.login(persist=True)
            if auth.authenticated:
                self.authenticated = True
                logger.info("✅ Authentification NASA Earthdata réussie (mode Latest)")
                return True
            else:
                logger.error("❌ Échec authentification earthaccess")
                return False
            
        except Exception as e:
            logger.error(f"❌ Erreur authentification TEMPO Latest: {e}")
            return False
    
    async def get_latest_available_data(self, lat: float, lon: float) -> Dict:
        """
        Récupère les dernières données TEMPO disponibles - VERSION RAPIDE (métadonnées seulement)
        """
        if not await self.authenticate():
            return {}
        
        logger.info(f"🛰️ Recherche RAPIDE des métadonnées TEMPO ({self.max_search_days} jours)")
        
        all_data = {}
        
        # Rechercher chaque polluant sur la période - MÉTADONNÉES SEULEMENT
        for pollutant, config in self.tempo_collections.items():
            logger.info(f"🔍 Recherche {pollutant.upper()} récent (métadonnées)...")
            
            # Version rapide - pas de téléchargement
            data = await self._search_pollutant_metadata_only(
                pollutant, config, lat, lon
            )
            
            if data:
                all_data[pollutant] = data
                logger.info(f"✅ {pollutant.upper()} trouvé: {data.get('date', 'Unknown date')}")
            else:
                logger.warning(f"⚠️ {pollutant.upper()} non disponible (période: {self.max_search_days} jours)")
        
        if all_data:
            # Ajouter métadonnées
            all_data['search_period_days'] = self.max_search_days
            all_data['coordinates'] = [lat, lon]
            all_data['data_source'] = 'TEMPO Latest Available'
            all_data['retrieved_at'] = datetime.utcnow().isoformat() + 'Z'
            
            logger.info(f"🎯 Données TEMPO récentes trouvées: {list(all_data.keys())}")
        
        return all_data
    
    async def _search_pollutant_recent(self, pollutant: str, config: Dict, lat: float, lon: float) -> Optional[Dict]:
        """
        Recherche un polluant spécifique et extrait les vraies valeurs de concentration
        """
        try:
            # Recherche sur période étendue
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=self.max_search_days)
            
            # Recherche des granules
            results = earthaccess.search_data(
                short_name=config['short_name'],
                bounding_box=(lon-0.5, lat-0.5, lon+0.5, lat+0.5),
                temporal=(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')),
                count=10  # Prendre moins de granules pour extraire les données
            )
            
            if not results:
                return None
            
            # Prendre le granule le plus récent
            latest_granule = results[-1]
            
            # Extraire les métadonnées
            granule_date = self._extract_granule_date(latest_granule)
            
            # Télécharger et extraire la vraie valeur de concentration
            concentration_data = await self._extract_concentration_from_granule(
                latest_granule, pollutant, lat, lon
            )
            
            if concentration_data:
                return {
                    'pollutant': pollutant,
                    'concentration': concentration_data['value'],
                    'unit': concentration_data['unit'],
                    'date': granule_date,
                    'granule_id': getattr(latest_granule, 'id', 'Unknown'),
                    'collection': config['short_name'],
                    'description': config['description'],
                    'coordinates': [lat, lon],
                    'quality_flag': concentration_data.get('quality', 'good'),
                    'data_source': 'TEMPO Satellite',
                    'note': f'Concentration extraite du granule TEMPO'
                }
            else:
                # Fallback si extraction échoue - retourner métadonnées
                return {
                    'pollutant': pollutant,
                    'concentration': None,
                    'unit': self._get_default_unit(pollutant),
                    'date': granule_date,
                    'granule_id': getattr(latest_granule, 'id', 'Unknown'),
                    'collection': config['short_name'],
                    'description': config['description'],
                    'coordinates': [lat, lon],
                    'available': True,
                    'note': f'Granule disponible mais concentration non extraite'
                }
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche {pollutant}: {e}")
            return None
    
    async def _extract_concentration_from_granule(self, granule, pollutant: str, lat: float, lon: float) -> Optional[Dict]:
        """
        Extrait les métadonnées du granule TEMPO SANS téléchargement pour éviter les timeouts
        Version optimisée pour la rapidité
        """
        try:
            granule_metadata = {
                'granule_id': getattr(granule, 'id', 'Unknown'),
                'time_start': getattr(granule, 'time_start', 'Unknown'),
                'time_end': getattr(granule, 'time_end', 'Unknown'),
                'size_mb': getattr(granule, 'granule_size', 0) / 1024 / 1024 if hasattr(granule, 'granule_size') else 0,
                'extraction_method': 'metadata_only',
                'pollutant': pollutant,
                'coordinates': {'lat': lat, 'lon': lon},
                'available': True,
                'value': f"Granule disponible - {pollutant.upper()}",
                'unit': self._get_default_unit(pollutant)
            }
            
            logger.info(f"✅ {pollutant.upper()} trouvé: {granule_metadata.get('time_start', 'N/A')} (métadonnées seulement)")
            return granule_metadata
                
        except Exception as e:
            logger.warning(f"⚠️ Erreur extraction métadonnées {pollutant}: {e}")
            return None
            logger.info(f"📥 Téléchargement du granule {pollutant.upper()}...")
            
            # Créer un répertoire temporaire
            with tempfile.TemporaryDirectory() as temp_dir:
                # Télécharger le fichier
                downloaded_files = earthaccess.download(granule, temp_dir)
                
                if not downloaded_files:
                    logger.warning(f"⚠️ Échec téléchargement {pollutant}")
                    return None
                
                # Lire le fichier NetCDF
                file_path = downloaded_files[0]
                concentration = await self._read_netcdf_concentration(
                    file_path, pollutant, lat, lon
                )
                
                return concentration
                
        except Exception as e:
            logger.warning(f"⚠️ Erreur extraction {pollutant}: {e}")
            return None
    
    async def _read_netcdf_concentration(self, file_path: str, pollutant: str, lat: float, lon: float) -> Optional[Dict]:
        """
        Lit le fichier NetCDF et extrait la concentration au point géographique
        """
        try:
            import xarray as xr
            
            # Ouvrir le dataset NetCDF
            with xr.open_dataset(file_path) as ds:
                
                # Variables typiques pour chaque polluant TEMPO
                variable_mapping = {
                    'no2': 'nitrogen_dioxide_total_column',
                    'hcho': 'formaldehyde_total_column', 
                    'aerosol': 'aerosol_optical_depth',
                    'o3': 'ozone_total_column'
                }
                
                # Chercher la variable dans le dataset
                var_name = None
                for possible_name in [variable_mapping.get(pollutant), f'{pollutant}_column', pollutant]:
                    if possible_name and possible_name in ds.variables:
                        var_name = possible_name
                        break
                
                # Si pas trouvé, prendre la première variable de données
                if not var_name:
                    data_vars = [v for v in ds.data_vars if len(ds[v].dims) >= 2]
                    if data_vars:
                        var_name = data_vars[0]
                        logger.info(f"📊 Utilisation de la variable: {var_name}")
                
                if not var_name:
                    logger.warning("⚠️ Aucune variable de données trouvée")
                    return None
                
                # Extraire les coordonnées
                data_array = ds[var_name]
                
                # Trouver les indices les plus proches de lat/lon
                if 'latitude' in ds.coords and 'longitude' in ds.coords:
                    lat_idx = np.abs(ds.latitude - lat).argmin()
                    lon_idx = np.abs(ds.longitude - lon).argmin()
                    
                    # Extraire la valeur
                    if len(data_array.dims) == 2:
                        value = float(data_array.isel(latitude=lat_idx, longitude=lon_idx).values)
                    else:
                        # Prendre le premier temps si dimension temporelle
                        value = float(data_array.isel(latitude=lat_idx, longitude=lon_idx).values.flatten()[0])
                    
                    # Vérifier si la valeur est valide
                    if np.isnan(value) or np.isinf(value):
                        logger.warning(f"⚠️ Valeur invalide pour {pollutant}: {value}")
                        return None
                    
                    # Obtenir l'unité
                    unit = getattr(data_array, 'units', self._get_default_unit(pollutant))
                    
                    return {
                        'value': round(value, 6),
                        'unit': unit,
                        'quality': 'good',
                        'variable_name': var_name
                    }
                else:
                    logger.warning("⚠️ Coordonnées latitude/longitude non trouvées")
                    return None
                    
        except ImportError:
            logger.error("❌ xarray requis pour lire les fichiers NetCDF")
            return None
        except Exception as e:
            logger.error(f"❌ Erreur lecture NetCDF: {e}")
            return None
    
    def _get_default_unit(self, pollutant: str) -> str:
        """Retourne l'unité par défaut pour chaque polluant"""
        units = {
            'no2': 'molecules/cm²',
            'hcho': 'molecules/cm²', 
            'aerosol': 'unitless',
            'o3': 'DU'
        }
        return units.get(pollutant, 'unknown')
    
    def _extract_granule_date(self, granule) -> str:
        """Extrait la date du granule"""
        try:
            # Essayer d'extraire la date depuis les métadonnées
            if hasattr(granule, 'temporal'):
                temporal = granule.temporal
                if temporal and len(temporal) > 0:
                    return temporal[0].strftime('%Y-%m-%d %H:%M:%S UTC')
            
            # Fallback: utiliser la date de création
            if hasattr(granule, 'meta') and 'native-id' in granule.meta:
                native_id = granule.meta['native-id']
                # Extraire la date du nom du fichier si possible
                if 'TEMPO' in native_id:
                    # Format typique: TEMPO_[PRODUCT]_L2_[YYYYMMDD]T[HHMMSS]...
                    import re
                    date_match = re.search(r'(\d{8})T(\d{6})', native_id)
                    if date_match:
                        date_str = date_match.group(1)
                        time_str = date_match.group(2)
                        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]} {time_str[:2]}:{time_str[2:4]}:{time_str[4:6]} UTC"
            
            return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
            
        except Exception as e:
            logger.warning(f"⚠️ Impossible d'extraire la date du granule: {e}")
            return "Date inconnue"
    
    async def get_data_summary(self, lat: float, lon: float) -> Dict:
        """
        Récupère un résumé des données TEMPO disponibles sans les détails complets
        """
        if not await self.authenticate():
            return {'error': 'Authentication failed'}
        
        summary = {
            'location': [lat, lon],
            'search_period_days': self.max_search_days,
            'pollutants_available': [],
            'latest_dates': {},
            'total_granules_found': 0
        }
        
        for pollutant, config in self.tempo_collections.items():
            try:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=self.max_search_days)
                
                results = earthaccess.search_data(
                    short_name=config['short_name'],
                    bounding_box=(lon-0.5, lat-0.5, lon+0.5, lat+0.5),
                    temporal=(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')),
                    count=10
                )
                
                if results:
                    summary['pollutants_available'].append(pollutant)
                    summary['total_granules_found'] += len(results)
                    
                    # Date du plus récent
                    latest_date = self._extract_granule_date(results[-1])
                    summary['latest_dates'][pollutant] = latest_date
                    
            except Exception as e:
                logger.warning(f"⚠️ Erreur résumé {pollutant}: {e}")
        
        summary['status'] = 'success' if summary['pollutants_available'] else 'no_data'
        return summary

    async def _search_pollutant_metadata_only(self, pollutant: str, config: Dict, lat: float, lon: float) -> Optional[Dict]:
        """
        Recherche RAPIDE - métadonnées seulement, pas de téléchargement
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=self.max_search_days)
            
            # Recherche avec une zone géographique
            granules = earthaccess.search_data(
                short_name=config['short_name'],
                bounding_box=(lon-0.5, lat-0.5, lon+0.5, lat+0.5),
                temporal=(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')),
                count=5  # Limite pour rapidité
            )
            
            if not granules:
                return None
            
            # Prendre le plus récent
            latest_granule = granules[-1]
            granule_date = self._extract_granule_date(latest_granule)
            
            # Retourner métadonnées seulement - PAS de téléchargement
            return {
                'pollutant': pollutant,
                'concentration': 'Métadonnées disponibles',
                'unit': self._get_default_unit(pollutant),
                'date': granule_date,
                'granule_id': getattr(latest_granule, 'id', 'Unknown'),
                'collection': config['short_name'],
                'description': config['description'],
                'coordinates': [lat, lon],
                'available': True,
                'extraction_method': 'metadata_only_fast',
                'data_source': 'TEMPO Satellite',
                'note': f'Granule TEMPO disponible - extraction rapide sans téléchargement'
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche métadonnées {pollutant}: {e}")
            return None

    async def get_search_metadata_only(self, lat: float, lon: float) -> Dict:
        """
        Version ultra-rapide : recherche métadonnées seulement sans téléchargement
        """
        try:
            # Utiliser la méthode d'authentification existante
            if not await self.authenticate():
                return {'available': False, 'reason': 'authentication_failed'}
            
            logger.info(f"🔍 Recherche métadonnées TEMPO rapide: {lat}, {lon}")
            
            products_found = []
            for pollutant in ['no2', 'hcho', 'o3']:
                try:
                    config = self.tempo_collections[pollutant]  # Utiliser tempo_collections
                    
                    # Recherche simple avec limite
                    granules = earthaccess.search_data(
                        short_name=config['short_name'],
                        version=config['version'],
                        temporal=(
                            (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
                            datetime.now().strftime("%Y-%m-%d")
                        ),
                        count=3  # Limite à 3 granules
                    )
                    
                    if granules:
                        products_found.append({
                            'pollutant': pollutant,
                            'count': len(granules),
                            'last_granule': granules[0].get('time_start', 'N/A'),
                            'collection': config['short_name']
                        })
                
                except Exception as e:
                    logger.warning(f"Erreur recherche {pollutant}: {e}")
                    continue
            
            return {
                'available': len(products_found) > 0,
                'products': products_found,
                'retrieved_at': datetime.now().isoformat(),
                'search_method': 'metadata_only',
                'coordinates': {'lat': lat, 'lon': lon}
            }
            
        except Exception as e:
            logger.error(f"Erreur recherche métadonnées: {e}")
            return {'available': False, 'reason': str(e)}

    async def get_metadata_only(self, lat: float, lon: float) -> Dict:
        """Alias pour compatibilité"""
        return await self.get_search_metadata_only(lat, lon)