from unittest.mock import patch, MagicMock
from src.app import create_app


def test_apply_route_exists():
    """Проверяем, что роут /api/apply зарегистрирован и отвечает"""
    app = create_app()
    app.config['TESTING'] = True
    client = app.test_client()

    # Отправляем запрос без реальной БД (мокаем обработку)
    with patch('src.app.admin.admin_routes.get_db_session') as mock_session, \
         patch('src.app.admin.admin_routes.normalize_address') as mock_normalize:

        # Мокаем сессию БД
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db

        # Мокаем DaData (возвращаем нормализованные данные)
        mock_normalize.return_value = {
            'normalized_address': 'г Москва, ул Оршанская, д 3',
            'fias_id': '0c5b2444-70a0-4932-980c-b4dc0d3f02b5',
            'latitude': 52.1039,
            'longitude': 38.6161
        }

        # Отправляем заявку
        response = client.post('/api/apply', json={
            'raw_address': 'Москва, Оршанская 3',
            'description': 'Граффити на стене',
            'telegram_user_id': 123456,
            'telegram_username': 'test'
        })

        # Проверяем ответ
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'report_id' in data