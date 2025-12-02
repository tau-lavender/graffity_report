from unittest.mock import patch, MagicMock
from src.dadata_helper import normalize_address


def test_dadata_normalize():
    """Мокаем get_dadata_client и проверяем обработку адреса"""
    mock_client = MagicMock()
    mock_client.clean.return_value = {
        'result': 'г Москва, ул Оршанская, д 3',
        'fias_id': '0c5b2444-70a0-4932-980c-b4dc0d3f02b5',
        'geo_lat': '52.1039',
        'geo_lon': '38.6161'
    }

    with patch('src.dadata_helper.get_dadata_client', return_value=mock_client):
        result = normalize_address("мск, Оршанская 3")

        assert result['normalized_address'] == 'г Москва, ул Оршанская, д 3'
        assert result['fias_id'] == '0c5b2444-70a0-4932-980c-b4dc0d3f02b5'
        assert result['latitude'] == 52.1039
        assert result['longitude'] == 38.6161