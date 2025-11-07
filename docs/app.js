// Переключение между экранами
function showScreen(screenId, clickedButton) {
    if (!screenId || !clickedButton) return;
    document.querySelector('.screen.active').classList.remove('active');
    document.getElementById(screenId).classList.add('active');
    document.querySelector('.header-buttons .button.active').classList.remove('active');
    clickedButton.classList.add('active');
}

// Хранилище выбранных фотографий
let selectedPhotos = {};

// Открытие диалога загрузки фото
function triggerPhotoUpload(slotNumber) {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = (e) => handlePhotoSelect(e, slotNumber);
    input.click();
}

// Обработка выбора фото
function handlePhotoSelect(event, slotNumber) {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        selectedPhotos[slotNumber] = {
            data: e.target.result,
            file: file
        };
        updatePhotoSlot(slotNumber, e.target.result);
    };
    reader.readAsDataURL(file);
}

// Обновление слота с фото
function updatePhotoSlot(slotNumber, dataUrl) {
    const slots = document.querySelectorAll('.photo-slot');
    if (slots[slotNumber - 1]) {
        slots[slotNumber - 1].innerHTML = `
            <img src="${dataUrl}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 8px;">
            <div class="delete-btn" onclick="deletePhoto(${slotNumber}, event)" style="position: absolute; top: 5px; right: 5px; background: rgba(0,0,0,0.7); color: white; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; font-weight: bold; z-index: 10;">×</div>
        `;
        slots[slotNumber - 1].style.position = 'relative';
    }
}

// Удаление фото
function deletePhoto(slotNumber, event) {
    event.stopPropagation();
    delete selectedPhotos[slotNumber];
    const slots = document.querySelectorAll('.photo-slot');
    if (slots[slotNumber - 1]) {
        slots[slotNumber - 1].innerHTML = `
            <div class="photo-icon"></div>
            <div class="mini-text">Добавить</div>
        `;
        slots[slotNumber - 1].onclick = () => triggerPhotoUpload(slotNumber);
        slots[slotNumber - 1].style.position = 'relative';
    }
}

// Отправка заявки
function submitApplication() {
    const address = document.querySelector('.adress-input').value;
    const comment = document.querySelector('.comment-textarea').value;
    
    if (!address || !comment) {
        alert('Пожалуйста, заполните адрес и комментарий');
        return;
    }
    
    const formData = new FormData();
    formData.append('location', address);
    formData.append('comment', comment);
    
    // Добавляем фото в FormData
    Object.keys(selectedPhotos).forEach(slotNumber => {
        formData.append('photos', selectedPhotos[slotNumber].file);
    });
    
    // Отправляем на backend
    fetch('https://thefid.pythonanywhere.com/api/apply', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Заявка успешно отправлена!');
            // Очищаем форму
            document.querySelector('.adress-input').value = '';
            document.querySelector('.comment-textarea').value = '';
            selectedPhotos = {};
            // Сбрасываем слоты с фото
            document.querySelectorAll('.photo-slot').forEach((slot, index) => {
                slot.innerHTML = `
                    <div class="photo-icon"></div>
                    <div class="mini-text">Добавить</div>
                `;
                slot.onclick = () => triggerPhotoUpload(index + 1);
            });
            // Возвращаемся на экран "Мои заявки"
            const homeBtn = document.querySelector('.header-buttons .button:first-child');
            if (homeBtn) {
                showScreen('home-applications', homeBtn);
                loadApplications();
            }
        } else {
            alert('Ошибка: ' + (data.error || 'Не удалось отправить заявку'));
        }
    })
    .catch(error => {
        console.error('Ошибка:', error);
        alert('Ошибка соединения с сервером');
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
    
    // Привязываем click для всех слотов фото
    document.querySelectorAll('.photo-slot').forEach((slot, index) => {
        slot.onclick = () => triggerPhotoUpload(index + 1);
    });
});

// Обновляем список заявок каждые 10 секунд
setInterval(loadApplications, 10000);
