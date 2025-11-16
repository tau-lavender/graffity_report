import os
from typing import Optional, Dict, Any
from dadata import Dadata


def get_dadata_client() -> Optional[Dadata]:
    token = os.environ.get('DADATA_TOKEN')
    secret = os.environ.get('DADATA_SECRET')

    if not token or not secret:
        return None

    return Dadata(token, secret)


def normalize_address(raw_address: str) -> Dict[str, Any]:
    client = get_dadata_client()

    if not client:
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
            'qc_geo': result.get('qc_geo'),
            'qc': result.get('qc')
        }
    except Exception as e:
        print(f"DaData API error: {e}")
        return {
            'normalized_address': raw_address,
            'fias_id': None,
            'latitude': None,
            'longitude': None
        }
