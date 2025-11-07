
let tgUsername = window.Telegram.WebApp.initDataUnsafe.user?.username;

// Переключение между экранами
function showScreen(screenId, clickedButton) {
    if (!screenId || !clickedButton) return;
    document.querySelector('.screen.active').classList.remove('active');
    document.getElementById(screenId).classList.add('active');
    document.querySelector('.header-buttons .button.active').classList.remove('active');
    clickedButton.classList.add('active');
}

// Отправка заявки (только адрес и комментарий)
function submitApplication() {
    const address = document.querySelector('.adress-input').value;
    const comment = document.querySelector('.comment-textarea').value;

    if (!address || !comment) {
        alert('Пожалуйста, заполните адрес и комментарий');
        return;
    }

    // Отправляем просто JSON
    const data = {
        location: address,
        comment: comment,
        username: tgUsername
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
            alert('Заявка успешно отправлена!', data);
            // Очищаем форму
            document.querySelector('.adress-input').value = '';
            document.querySelector('.comment-textarea').value = '';
            // Возвращаемся на экран "Мои заявки"
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

// Загрузка списка заявок
function loadApplications() {
    fetch('https://thefid.pythonanywhere.com/api/applications')
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
                        <p><b>Тг:</b> ${app.username || '-'}</p>
                        <p><b>Статус:</b> <span style="color: ${app.status === 'approved' ? 'green' : app.status === 'declined' ? 'red' : 'orange'};">${app.status || 'pending'}</span></p>
                    </div>
                `;
            });
            html += '</div>';
            container.innerHTML = html;
        })
        .catch(error => console.error('Ошибка загрузки:', error));
}

// Автораспирение для textarea
document.querySelectorAll('.auto-expand').forEach(function(textarea) {
    textarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 200) + 'px';
    });
});

// Инициализация при загрузке страницы
window.addEventListener('DOMContentLoaded', function() {
    // Загружаем список заявок
    loadApplications();

    // Привязываем обработчик к кнопке отправки
    const submitBtn = document.querySelector('.submit-btn');
    if (submitBtn) {
        submitBtn.addEventListener('click', submitApplication);
    }
});

// Обновляем список заявок каждые 10 секунд
setInterval(loadApplications, 10000);
