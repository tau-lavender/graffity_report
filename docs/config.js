// Конфигурация API endpoint
// Для локальной разработки используйте 'local'
// Для production (Railway) используйте 'production'
const ENV = 'production';

const API_ENDPOINTS = {
    local: 'http://localhost:8080',
    production: 'https://graffityreport-production-cc37.up.railway.app'
};

const API_URL = API_ENDPOINTS[ENV];
