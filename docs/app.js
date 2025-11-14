function showScreen(screenId, clickedButton) {
    if (!screenId || !clickedButton) return;
    document.querySelector('.screen.active').classList.remove('active');
    document.getElementById(screenId).classList.add('active');
    document.querySelector('.header-buttons .button.active').classList.remove('active');
    clickedButton.classList.add('active');
}

// Отправка заявки с адресом, комментарием и данными Telegram
async function submitApplication() {
    const addressInput = document.querySelector('.adress-input');
    const commentInput = document.querySelector('.comment-textarea');
    const submitBtn = document.querySelector('.submit-btn');

    if (!addressInput || !commentInput) {
        console.error('Не найдены элементы формы');
        alert('Ошибка: элементы формы не найдены');
        return;
    }

    const address = addressInput.value;
    const comment = commentInput.value;

    if (!address || !comment) {
        alert('Пожалуйста, заполните адрес и комментарий');
        return;
    }

    // Блокируем кнопку на время отправки
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Отправка...';
    }

    // Получаем ФИАС данные из data-атрибута
    let fiasData = null;
    try {
        const fiasStr = addressInput.getAttribute('data-fias');
        if (fiasStr) {
            fiasData = JSON.parse(fiasStr);
        }
    } catch (e) {
        console.warn('Failed to parse FIAS data:', e);
    }

    // Отправляем JSON с данными пользователя Telegram и ФИАС
    const data = {
        raw_address: address,
        description: comment,
        telegram_username: telegramUser ? (telegramUser.username || null) : null,
        telegram_user_id: telegramUser ? (telegramUser.id || null) : null,
        telegram_first_name: telegramUser ? (telegramUser.first_name || null) : null,
        telegram_last_name: telegramUser ? (telegramUser.last_name || null) : null,
        // ФИАС данные (если есть)
        fias_id: fiasData ? fiasData.fias_id : null,
        latitude: fiasData ? fiasData.geo_lat : null,
        longitude: fiasData ? fiasData.geo_lon : null
    };

    console.log('Отправляю заявку:', data);

    try {
        const response = await fetch(`${API_URL}/api/apply`, {
            method: 'POST',
            mode: 'cors',
            cache: 'no-store',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        console.log('Ответ JSON:', result);

        if (!response.ok || !result.success) {
            throw new Error(result.error || 'Не удалось отправить заявку');
        }

        const reportId = result.report_id;
        const hasPhotos = selectedPhotos.some(photo => photo !== null);

        if (hasPhotos) {
            if (!reportId) {
                alert('Сервер не вернул номер заявки. Попробуйте ещё раз.');
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Отправить заявку';
                }
                return;
            }

            // Обновляем текст кнопки во время загрузки фото
            if (submitBtn) {
                submitBtn.textContent = 'Загрузка фото...';
            }

            try {
                const uploadedKeys = await uploadPhotos(reportId);
                alert(`Заявка отправлена! Загружено фото: ${uploadedKeys.length}`);
            } catch (uploadError) {
                console.error('Ошибка загрузки фото:', uploadError);
                alert('Заявка отправлена, но фото не загружены');
            }
        } else {
            alert('Заявка успешно отправлена!');
        }

        resetForm();
    } catch (error) {
        console.error('Ошибка при отправке заявки:', error);
        alert(error.message || 'Ошибка соединения с сервером');
    } finally {
        // Разблокируем кнопку в любом случае
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Отправить заявку';
        }
    }
}

// Сброс формы после отправки
function resetForm() {
    const addressInput = document.querySelector('.adress-input');
    const commentInput = document.querySelector('.comment-textarea');

    if (addressInput) {
        addressInput.value = '';
        addressInput.setAttribute('data-fias', '');
    }
    if (commentInput) {
        commentInput.value = '';
    }

    // Очищаем фото
    selectedPhotos = [null, null, null];
    for (let i = 0; i < 3; i++) {
        const slot = document.getElementById(`photo-slot-${i}`);
        const input = document.getElementById(`photo-input-${i}`);
        if (slot) {
            slot.style.backgroundImage = '';
            slot.innerHTML = '<div class="photo-icon"></div><div class="mini-text">Добавить</div>';
        }
        if (input) {
            input.value = '';
        }
    }

    // Переключаемся на экран заявок
    const homeBtn = document.querySelector('.header-buttons .button:first-child');
    if (homeBtn) {
        showScreen('home-applications', homeBtn);
        loadApplications();
    }
}

//Создание карточек заявок
function createAppCard(app) {
    const STATUS_TEXTS = {
        'approved': 'Одобрено',
        'declined': 'Отклонено',
        'pending': 'Ожидает'
    };

    const status = STATUS_TEXTS[app.status] || 'Ожидает';

    // Создаем галерею фото, если есть
    let photoGallery = '';
    if (app.photos && app.photos.length > 0) {
        const photoItems = app.photos.map(photo =>
            `<img src="${photo.url}" class="card-photo" alt="Фото граффити">`
        ).join('');
        photoGallery = `<div class="card-photos">${photoItems}</div>`;
    }

    return `
        <div class="card" data-report-id="${app.id}">
            <div class="adress-slot">
                <div class="geo-icon"></div>
                <div class="title-text">${app.location || app.address || '-'}</div>
            </div>
            ${photoGallery}
            <div class="main-text">${app.comment || '-'}</div>
            <span class="mini-text status ${app.status || 'pending'}">${status}</span>
        </div>
    `;
}

// Загрузка списка заявок (для пользователя)
function loadApplications() {
    // Формируем URL с параметром telegram_user_id, если пользователь определен
    let url = `${API_URL}/api/applications`;
    if (telegramUser && telegramUser.id) {
        url += `?telegram_user_id=${telegramUser.id}`;
        console.log('Загружаю заявки для пользователя:', telegramUser.id);
    } else {
        console.log('Загружаю все заявки (пользователь не определен)');
    }

    fetch(url)
        .then(response => response.json())
        .then(apps => {
            const container = document.getElementById('home-applications');
            if (apps.length === 0) {
                container.innerHTML = '<p>У вас пока нет заявок</p>';
                return;
            }

            let html = '';
            apps.forEach(app => {
                html += createAppCard(app);
            });

            container.innerHTML = html;
        })
        .catch(error => console.error('Ошибка загрузки:', error));
}

// Автораспрямление для textarea
document.querySelectorAll('.auto-expand').forEach(function(textarea) {
    textarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 200) + 'px';
    });
});

// Глобальная переменная для хранения данных пользователя Telegram
let telegramUser = null;

// Массив для хранения выбранных фото
let selectedPhotos = [null, null, null];

// Триггер выбора фото
function triggerPhotoUpload(index) {
    const input = document.getElementById(`photo-input-${index}`);
    if (input) {
        input.click();
    }
}

// Обработка выбранного фото
function handlePhotoSelected(index) {
    const input = document.getElementById(`photo-input-${index}`);
    const slot = document.getElementById(`photo-slot-${index}`);

    if (!input || !input.files || !input.files[0]) return;

    const file = input.files[0];

    // Проверка размера (макс 10MB)
    if (file.size > 10 * 1024 * 1024) {
        alert('Файл слишком большой. Максимум 10 МБ');
        return;
    }

    // Проверка типа
    if (!file.type.startsWith('image/')) {
        alert('Пожалуйста, выберите изображение');
        return;
    }

    // Сохраняем файл
    selectedPhotos[index] = file;

    // Показываем превью
    const reader = new FileReader();
    reader.onload = function(e) {
        slot.style.backgroundImage = `url(${e.target.result})`;
        slot.style.backgroundSize = 'cover';
        slot.style.backgroundPosition = 'center';
        slot.innerHTML = '<div class="mini-text" style="background: rgba(0,0,0,0.5); color: white; padding: 4px;">Изменить</div>';
    };
    reader.readAsDataURL(file);

    console.log(`Фото ${index} выбрано:`, file.name);
}

async function uploadPhotos(reportId) {
    const uploadedKeys = [];

    for (let i = 0; i < selectedPhotos.length; i++) {
        const file = selectedPhotos[i];
        if (!file) continue;

        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('report_id', reportId);

            const response = await fetch(`${API_URL}/api/upload/photo`, {
                method: 'POST',
                mode: 'cors',
                cache: 'no-store',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const result = await response.json();

            if (result.success && result.s3_key) {
                uploadedKeys.push(result.s3_key);
            }
        } catch (error) {
            console.error('Photo upload error:', error);
        }
    }

    return uploadedKeys;
}

// Инициализация Telegram Web App
function initTelegramApp() {
    if (window.Telegram && window.Telegram.WebApp) {
        const tg = window.Telegram.WebApp;
        tg.ready();
        tg.expand();

        // Получаем данные пользователя
        if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
            telegramUser = tg.initDataUnsafe.user;
            console.log('Telegram User Data:', telegramUser);
            console.log('Username:', telegramUser.username || 'Не указан');
            console.log('First Name:', telegramUser.first_name || '');
            console.log('Last Name:', telegramUser.last_name || '');
            console.log('User ID:', telegramUser.id || '');

            // Можно отобразить приветствие пользователю
            displayUserGreeting();
        } else {
            console.warn('Telegram user data not available');
        }

        // Расширяем приложение на весь экран
        tg.expand();
    } else {
        console.warn('Not running in Telegram Web App environment');
    }
}

// Отображение приветствия пользователю
function displayUserGreeting() {
    if (telegramUser) {
        const username = telegramUser.username || telegramUser.first_name || 'Пользователь';
        console.log(`Добро пожаловать, @${username}!`);
        // Можно добавить визуальное приветствие в интерфейсе, если нужно
    }
}

// Инициализация при загрузке страницы
window.addEventListener('DOMContentLoaded', function() {
    // Инициализируем Telegram Mini App
    initTelegramApp();

    // Инициализируем DaData автоподсказки
    initDadataAutocomplete();

    loadApplications();
    const submitBtn = document.querySelector('.submit-btn');
    if (submitBtn) {
        submitBtn.addEventListener('click', submitApplication);
    }

    // Обработчик кнопки "Использовать текущее местоположение"
    const locationBtn = document.querySelector('.button-add-adress');
    if (locationBtn) {
        locationBtn.addEventListener('click', useCurrentLocation);
    }
});

// Функция для получения местоположения из Telegram
function useCurrentLocation() {
    if (!window.Telegram || !window.Telegram.WebApp) {
        alert('Telegram WebApp не доступен');
        return;
    }

    const tg = window.Telegram.WebApp;

    // Показываем индикатор загрузки
    const locationBtn = document.querySelector('.button-add-adress');
    const originalText = locationBtn ? locationBtn.textContent : '';
    if (locationBtn) {
        locationBtn.textContent = 'Получение местоположения...';
        locationBtn.disabled = true;
    }

    // Запрашиваем местоположение у Telegram
    // В Telegram WebApp API нет callback для requestLocation
    // Используем LocationManager или проверяем initDataUnsafe

    // Пытаемся получить из браузерной геолокации (работает и в Telegram WebView)
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;

                console.log('Location received:', { lat, lon });

                // Обратный геокодинг через DaData
                reverseGeocode(lat, lon).finally(() => {
                    if (locationBtn) {
                        locationBtn.textContent = originalText;
                        locationBtn.disabled = false;
                    }
                });
            },
            (error) => {
                console.error('Geolocation error:', error);
                alert('Не удалось получить местоположение. Проверьте разрешения.');
                if (locationBtn) {
                    locationBtn.textContent = originalText;
                    locationBtn.disabled = false;
                }
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    } else {
        alert('Геолокация не поддерживается');
        if (locationBtn) {
            locationBtn.textContent = originalText;
            locationBtn.disabled = false;
        }
    }
}

// Обратный геокодинг: координаты → адрес
async function reverseGeocode(lat, lon) {
    const addressInput = document.querySelector('.adress-input');

    try {
        console.log('Reverse geocoding for:', { lat, lon });
        console.log('Using DADATA_API_KEY:', DADATA_API_KEY ? 'Present' : 'Missing');

        const response = await fetch('https://suggestions.dadata.ru/suggestions/api/4_1/rs/geolocate/address', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': `Token ${DADATA_API_KEY}`
            },
            body: JSON.stringify({
                lat: lat,
                lon: lon,
                count: 1
            })
        });

        console.log('DaData response status:', response.status);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('DaData API error:', errorText);
            throw new Error(`API error: ${response.status}`);
        }

        const data = await response.json();
        console.log('DaData response:', data);

        if (data.suggestions && data.suggestions.length > 0) {
            const suggestion = data.suggestions[0];
            const address = suggestion.value;
            const fiasData = {
                fias_id: suggestion.data.fias_id,
                geo_lat: suggestion.data.geo_lat,
                geo_lon: suggestion.data.geo_lon
            };

            // Устанавливаем адрес в поле
            addressInput.value = address;
            addressInput.setAttribute('data-fias', JSON.stringify(fiasData));

            console.log('Address found:', address);
        } else {
            console.warn('No suggestions returned from DaData');
            alert('Не удалось определить адрес по координатам');
        }
    } catch (error) {
        console.error('Reverse geocoding error:', error);
        alert('Ошибка при определении адреса: ' + error.message);
    }
}

// Автообновление списка заявок каждые 10 секунд
setInterval(loadApplications, 10000);
