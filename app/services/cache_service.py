"""
Cache service for optimizing API performance.
Implements in-memory caching with TTL for air quality data.
"""
import asyncio
import time
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from app.core.logging import get_logger

logger = get_logger(__name__)


class AirQualityCacheService:
    """Service de cache pour optimiser les performances de l'API"""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes par défaut
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.hit_count = 0
        self.miss_count = 0
        logger.info(f"💾 Cache service initialisé (TTL: {default_ttl}s)")
    
    def _generate_key(self, endpoint: str, **params) -> str:
        """Génère une clé unique pour le cache"""
        # Trier les paramètres pour une clé consistante
        sorted_params = sorted(params.items())
        param_str = "&".join(f"{k}={v}" for k, v in sorted_params)
        return f"{endpoint}:{param_str}"
    
    def _is_expired(self, cache_entry: Dict[str, Any]) -> bool:
        """Vérifie si une entrée de cache a expiré"""
        return time.time() > cache_entry["expires_at"]
    
    async def get(self, endpoint: str, **params) -> Optional[Any]:
        """Récupère une valeur du cache"""
        key = self._generate_key(endpoint, **params)
        
        if key in self.cache:
            entry = self.cache[key]
            if not self._is_expired(entry):
                self.hit_count += 1
                logger.debug(f"💾 Cache HIT: {key}")
                return entry["data"]
            else:
                # Supprimer l'entrée expirée
                del self.cache[key]
                logger.debug(f"💾 Cache EXPIRED: {key}")
        
        self.miss_count += 1
        logger.debug(f"💾 Cache MISS: {key}")
        return None
    
    async def set(self, endpoint: str, data: Any, ttl: Optional[int] = None, **params):
        """Met une valeur en cache"""
        key = self._generate_key(endpoint, **params)
        expires_at = time.time() + (ttl or self.default_ttl)
        
        self.cache[key] = {
            "data": data,
            "expires_at": expires_at,
            "created_at": time.time()
        }
        
        logger.debug(f"💾 Cache SET: {key} (expire dans {ttl or self.default_ttl}s)")
    
    async def clear_expired(self):
        """Nettoie les entrées expirées du cache"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time > entry["expires_at"]
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.info(f"💾 Cache nettoyé: {len(expired_keys)} entrées expirées supprimées")
    
    async def clear_all(self):
        """Vide complètement le cache"""
        cleared_count = len(self.cache)
        self.cache.clear()
        self.hit_count = 0
        self.miss_count = 0
        logger.info(f"💾 Cache vidé: {cleared_count} entrées supprimées")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du cache"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cache_size": len(self.cache),
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests
        }
    
    async def get_cached_or_fetch(self, endpoint: str, fetch_func, ttl: Optional[int] = None, **params):
        """
        Pattern cache-aside: récupère du cache ou exécute la fonction si pas en cache
        """
        # Essayer de récupérer du cache
        cached_data = await self.get(endpoint, **params)
        if cached_data is not None:
            return cached_data
        
        # Pas en cache, exécuter la fonction
        try:
            data = await fetch_func(**params)
            if data is not None:
                await self.set(endpoint, data, ttl, **params)
            return data
        except Exception as e:
            logger.error(f"❌ Erreur lors du fetch pour {endpoint}: {str(e)}")
            return None


# Instance globale du cache
cache_service = AirQualityCacheService()


# Décorateur pour mise en cache automatique
def cached(endpoint: str, ttl: int = 300):
    """
    Décorateur pour mettre en cache automatiquement les résultats des méthodes
    
    Args:
        endpoint: Nom de l'endpoint pour la clé de cache
        ttl: Time to live en secondes
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Générer les paramètres pour la clé de cache
            cache_params = {}
            
            # Ajouter les arguments positionnels (sauf self)
            if len(args) > 1:  # Skip self
                cache_params.update({f"arg_{i}": arg for i, arg in enumerate(args[1:])})
            
            # Ajouter les arguments nommés
            cache_params.update(kwargs)
            
            # Utiliser le cache-aside pattern
            return await cache_service.get_cached_or_fetch(
                endpoint=endpoint,
                fetch_func=lambda **params: func(*args, **kwargs),
                ttl=ttl,
                **cache_params
            )
        
        return wrapper
    return decorator