function showScreen(screenId, clickedButton) {
    if (!screenId || !clickedButton) return;
    document.querySelector('.screen.active').classList.remove('active');
    document.getElementById(screenId).classList.add('active');
    document.querySelector('.header-buttons .button.active').classList.remove('active');
    clickedButton.classList.add('active');
}

// Отправка заявки с адресом, комментарием и данными Telegram
function submitApplication() {
    const addressInput = document.querySelector('.adress-input');
    const commentInput = document.querySelector('.comment-textarea');
    
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
    
    // Отправляем JSON с данными пользователя Telegram
    const data = {
        location: address,
        comment: comment,
        telegram_username: telegramUser ? (telegramUser.username || null) : null,
        telegram_user_id: telegramUser ? (telegramUser.id || null) : null,
        telegram_first_name: telegramUser ? (telegramUser.first_name || null) : null,
        telegram_last_name: telegramUser ? (telegramUser.last_name || null) : null
    };

    console.log('Отправляю заявку:', data);

    fetch('https://thefid.pythonanywhere.com/api/apply', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        console.log('Ответ статус:', response.status);
        return response.json();
    })
    .then(result => {
        console.log('Ответ JSON:', result);
        if (result.success) {
            alert('Заявка успешно отправлена!');
            const addressInput = document.querySelector('.adress-input');
            const commentInput = document.querySelector('.comment-textarea');
            if (addressInput) addressInput.value = '';
            if (commentInput) commentInput.value = '';
            const homeBtn = document.querySelector('.header-buttons .button:first-child');
            if (homeBtn) {
                showScreen('home-applications', homeBtn);
                loadApplications();
            }
        } else {
            alert('Ошибка: ' + (result.error || 'Не удалось отправить заявку'));
        }
    })
    .catch(error => {
        console.error('Ошибка сети:', error);
        alert('Ошибка соединения с сервером: ' + error.message);
    });
}

// Загрузка списка заявок (в админке и для пользователя)
function loadApplications() {
    // Формируем URL с параметром telegram_user_id, если пользователь определен
    let url = 'https://thefid.pythonanywhere.com/api/applications';
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
                container.innerHTML = '<h2>Мои заявки</h2><p>У вас пока нет заявок</p>';
                return;
            }

            let html = '<h2>Мои заявки</h2><div style="display: flex; flex-direction: column; gap: 10px;">';
            apps.forEach((app, index) => {
                html += `
                    <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #ddd;">
                        <p><b>Адрес:</b> ${app.location || app.address || '-'}</p>
                        <p><b>Комментарий:</b> ${app.comment || '-'}</p>
                        <p><b>Статус:</b> <span style="color: ${app.status === 'approved' ? 'green' : app.status === 'declined' ? 'red' : 'orange'};">${app.status || 'pending'}</span></p>
                    </div>
                `;
            });
            html += '</div>';
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

// Инициализация Telegram Web App
function initTelegramApp() {
    if (window.Telegram && window.Telegram.WebApp) {
        const tg = window.Telegram.WebApp;
        tg.ready();
        
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
    
    loadApplications();
    const submitBtn = document.querySelector('.submit-btn');
    if (submitBtn) {
        submitBtn.addEventListener('click', submitApplication);
    }
});

// Автообновление списка заявок каждые 10 секунд
setInterval(loadApplications, 10000);
