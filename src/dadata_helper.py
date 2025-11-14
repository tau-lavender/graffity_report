"""
DaData API integration for address normalization.
"""
import os
from typing import Optional, Dict, Any
from dadata import Dadata  # type: ignore


def get_dadata_client() -> Optional[Dadata]:
    """Get DaData API client if credentials are available."""
    token = os.environ.get('DADATA_TOKEN')
    secret = os.environ.get('DADATA_SECRET')

    if not token or not secret:
        return None

    return Dadata(token, secret)


def normalize_address(raw_address: str) -> Dict[str, Any]:
    """
    Normalize address using DaData API.

    Returns dict with:
    - normalized_address: str - полный нормализованный адрес
    - fias_id: str - ФИАС ID
    - latitude: float - широта
    - longitude: float - долгота
    - postal_code: str - почтовый индекс
    - ...other ФИАС fields
    """
    client = get_dadata_client()

    if not client:
        # Fallback: return raw address if DaData not configured
        return {
            'normalized_address': raw_address,
            'fias_id': None,
            'latitude': None,
            'longitude': None
        }

    try:
        result = client.clean("address", raw_address)

        return {
            'normalized_address': result.get('result') or raw_address,
            'fias_id': result.get('fias_id'),
            'fias_code': result.get('fias_code'),
            'fias_level': result.get('fias_level'),
            'kladr_id': result.get('kladr_id'),
            'postal_code': result.get('postal_code'),
            'country': result.get('country'),
            'region': result.get('region'),
            'city': result.get('city'),
            'street': result.get('street'),
            'house': result.get('house'),
            'latitude': float(result['geo_lat']) if result.get('geo_lat') else None,
            'longitude': float(result['geo_lon']) if result.get('geo_lon') else None,
            'qc_geo': result.get('qc_geo'),  # Quality code for coordinates
            'qc': result.get('qc')  # Quality code for address
        }
    except Exception as e:
        print(f"DaData API error: {e}")
        return {
            'normalized_address': raw_address,
            'fias_id': None,
            'latitude': None,
            'longitude': None
        }
