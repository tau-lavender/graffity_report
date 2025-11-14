// Загрузка фото на сервер (исправленная версия)
async function uploadPhotos(reportId) {
    console.log('📸 uploadPhotos вызван с reportId:', reportId);
    const uploadedKeys = [];

    for (let i = 0; i < selectedPhotos.length; i++) {
        const file = selectedPhotos[i];
        if (!file) continue;

        console.log(`📤 Загружаю фото ${i}:`, file.name, file.size, 'bytes');

        const formData = new FormData();
        formData.append('file', file);
        formData.append('report_id', reportId);

        // Попытки с ретраем (2 попытки)
        let success = false;
        for (let attempt = 1; attempt <= 2; attempt++) {
            try {
                console.log(`🌐 Попытка ${attempt}/2: POST на ${API_URL}/api/upload/photo`);
                const response = await fetch(`${API_URL}/api/upload/photo`, {
                    method: 'POST',
                    body: formData,
                    mode: 'cors'
                });

                console.log(`📥 Ответ получен, status: ${response.status}`);
                const result = await response.json();
                console.log(`📄 Ответ JSON:`, result);

                if (result.success) {
                    uploadedKeys.push(result.s3_key);
                    console.log(`✅ Фото ${i} загружено:`, result.s3_key);
                    success = true;
                    break;
                } else {
                    console.error(`❌ Сервер вернул ошибку:`, result.error);
                    if (attempt === 2) {
                        console.error(`Фото ${i} не загружено после 2 попыток`);
                    }
                }
            } catch (error) {
                console.error(`❌ Ошибка сети (попытка ${attempt}):`, error);
                if (attempt < 2) {
                    console.log('Жду 800ms перед повтором...');
                    await new Promise(resolve => setTimeout(resolve, 800));
                } else {
                    console.error(`Фото ${i} не загружено: сетевая ошибка`);
                }
            }
        }
    }

    console.log('✅ Все фото обработаны, загружено:', uploadedKeys.length);
    return uploadedKeys;
}
