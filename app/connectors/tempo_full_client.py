# tempo_full_client.py
import earthaccess
import xarray as xr
import asyncio
import aiohttp
from datetime import datetime, timedelta
import logging
import tempfile
import os
import numpy as np
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class TempoFullClient:
    """Client TEMPO pour tous les polluants disponibles"""
    
    def __init__(self):
        self.authenticated = False
        self.temp_dir = tempfile.mkdtemp()
        
        # Mapping des produits TEMPO et leurs variables
        self.tempo_products = {
            'NO2': {
                'short_name': 'TEMPO_NO2_L2',
                'variable': 'nitrogendioxide_tropospheric_column',
                'group': 'PRODUCT'
            },
            'HCHO': {
                'short_name': 'TEMPO_HCHO_L2', 
                'variable': 'formaldehyde_tropospheric_column',
                'group': 'PRODUCT'
            },
            'Aerosol': {
                'short_name': 'TEMPO_Aerosol_L2',
                'variable': 'aerosol_index_340_380',
                'group': 'PRODUCT'
            },
            'O3': {
                'short_name': 'TEMPO_O3_L2',
                'variable': 'ozone_total_column',
                'group': 'PRODUCT'
            }
        }
        
        self.unit_conversions = {
            'NO2': lambda x: x * 46000 * 0.1,  # mol/m² → μg/m³
            'HCHO': lambda x: x * 30000 * 0.1,  # mol/m² → μg/m³  
            'Aerosol': lambda x: x,  # Pas de conversion
            'O3': lambda x: x * 2.0  # DU → μg/m³ approximatif
        }

    async def authenticate(self):
        """Authentification Earthdata"""
        try:
            auth = earthaccess.login(strategy="interactive", persist=True)
            self.authenticated = True
            logger.info("✅ Authentification NASA Earthdata réussie")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur authentification: {e}")
            return False

    async def get_all_pollutants(self, lat: float, lon: float) -> Dict:
        """
        Récupère TOUS les polluants TEMPO disponibles
        Retourne un dict avec toutes les données TEMPO
        """
        if not self.authenticated:
            await self.authenticate()

        results = {}
        
        for pollutant, config in self.tempo_products.items():
            try:
                logger.info(f"🛰️ Recherche {pollutant}...")
                data = await self._get_single_pollutant(lat, lon, pollutant, config)
                if data:
                    results[pollutant.lower()] = data
                    logger.info(f"✅ {pollutant} trouvé: {data['value']:.2f} {data['unit']}")
                else:
                    logger.warning(f"⚠️ {pollutant} non disponible")
                    
            except Exception as e:
                logger.error(f"❌ Erreur {pollutant}: {e}")
                continue

        return results

    async def _get_single_pollutant(self, lat: float, lon: float, pollutant: str, config: Dict) -> Optional[Dict]:
        """Récupère un polluant spécifique de TEMPO"""
        try:
            # Recherche des données
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=6)  # Dernières 6 heures
            
            granules = earthaccess.search_data(
                short_name=config['short_name'],
                temporal=(start_time, end_time),
                bounding_box=(lon-2, lat-2, lon+2, lat+2),  # Zone large
                count=5
            )
            
            if not granules:
                return None

            # Téléchargement et traitement
            files = earthaccess.download(granules[:1], self.temp_dir)
            if not files:
                return None

            return await self._process_tempo_file(files[0], lat, lon, pollutant, config)
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération {pollutant}: {e}")
            return None

    async def _process_tempo_file(self, file_path: str, target_lat: float, target_lon: float, 
                                pollutant: str, config: Dict) -> Optional[Dict]:
        """Traite un fichier TEMPO pour un polluant spécifique"""
        try:
            group = config.get('group', 'PRODUCT')
            variable = config['variable']
            
            with xr.open_dataset(file_path, group=group) as ds:
                if variable not in ds.variables:
                    logger.warning(f"⚠️ Variable {variable} non trouvée dans {file_path}")
                    return None
                
                data_var = ds[variable]
                lat_var = ds['latitude']
                lon_var = ds['longitude']
                time_var = ds['time']
                
                # QA value si disponible
                qa_var = ds['qa_value'] if 'qa_value' in ds.variables else None
                
                # Trouver le point le plus proche avec données valides
                valid_mask = ~np.isnan(data_var.values)
                if qa_var is not None:
                    valid_mask = valid_mask & (qa_var.values > 0.3)
                
                lat_diff = np.abs(lat_var.values - target_lat)
                lon_diff = np.abs(lon_var.values - target_lon)
                total_diff = lat_diff + lon_diff
                total_diff[~valid_mask] = np.inf
                
                if np.all(total_diff == np.inf):
                    return None
                
                # Index du meilleur point
                y_idx, x_idx = np.unravel_index(np.argmin(total_diff), total_diff.shape)
                
                # Extraction des valeurs
                raw_value = float(data_var.values[y_idx, x_idx])
                converted_value = self.unit_conversions[pollutant](raw_value)
                
                # Métadonnées
                actual_lat = float(lat_var.values[y_idx, x_idx])
                actual_lon = float(lon_var.values[y_idx, x_idx])
                
                return {
                    'value': converted_value,
                    'value_original': raw_value,
                    'unit': self._get_unit(pollutant),
                    'unit_original': self._get_original_unit(pollutant),
                    'latitude': actual_lat,
                    'longitude': actual_lon,
                    'quality': float(qa_var.values[y_idx, x_idx]) if qa_var is not None else 0.8,
                    'distance_km': self._calculate_distance(target_lat, target_lon, actual_lat, actual_lon),
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur traitement {pollutant}: {e}")
            return None

    def _get_unit(self, pollutant: str) -> str:
        """Retourne l'unité convertie"""
        units = {
            'NO2': 'μg/m³',
            'HCHO': 'μg/m³', 
            'Aerosol': 'index',
            'O3': 'μg/m³'
        }
        return units.get(pollutant, 'unknown')

    def _get_original_unit(self, pollutant: str) -> str:
        """Retourne l'unité originale TEMPO"""
        units = {
            'NO2': 'mol/m²',
            'HCHO': 'mol/m²',
            'Aerosol': 'unitless', 
            'O3': 'DU'
        }
        return units.get(pollutant, 'unknown')

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcule la distance en km entre deux points"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat, dlon = lat2 - lat1, lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        return R * 2 * atan2(sqrt(a), sqrt(1-a))