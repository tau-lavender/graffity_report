// DaData Address Autocomplete
// Токен DaData (можно использовать публично для suggestions)
const DADATA_API_KEY = 'd8801ff08f6a1464d687ea026435b16c88ce64b4';

let dadataTimeout = null;
let selectedFiasData = null;

function initDadataAutocomplete() {
    const addressInput = document.querySelector('.adress-input');
    const suggestionsContainer = document.querySelector('.address-suggestions');

    if (!addressInput || !suggestionsContainer) return;

    addressInput.addEventListener('input', function(e) {
        const query = e.target.value.trim();

        // Очищаем ФИАС данные при ручном изменении адреса
        addressInput.removeAttribute('data-fias');
        selectedFiasData = null;

        // Очищаем предыдущий таймаут
        clearTimeout(dadataTimeout);

        if (query.length < 3) {
            suggestionsContainer.style.display = 'none';
            return;
        }

        // Делаем запрос с задержкой 300мс
        dadataTimeout = setTimeout(() => {
            fetchAddressSuggestions(query, suggestionsContainer, addressInput);
        }, 300);
    });

    // Закрытие подсказок при клике вне
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.address-autocomplete-wrapper')) {
            suggestionsContainer.style.display = 'none';
        }
    });
}

function fetchAddressSuggestions(query, container, input) {
    fetch('https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/address', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Token ' + DADATA_API_KEY
        },
        body: JSON.stringify({
            query: query,
            count: 5,
            locations: [{ country: 'Россия' }]
        })
    })
    .then(response => response.json())
    .then(data => {
        displaySuggestions(data.suggestions || [], container, input);
    })
    .catch(error => {
        console.error('DaData error:', error);
        container.style.display = 'none';
    });
}

function displaySuggestions(suggestions, container, input) {
    if (suggestions.length === 0) {
        container.style.display = 'none';
        return;
    }

    container.innerHTML = '';
    container.style.display = 'block';

    suggestions.forEach(suggestion => {
        const item = document.createElement('div');
        item.className = 'suggestion-item';
        item.textContent = suggestion.value;

        item.addEventListener('click', function() {
            const country = suggestion.data.country;
            if (country && country !== 'Россия' && country !== 'Russia' && country !== 'RU' && country !== 'RUS') {
                alert('Адрес должен находиться в Российской Федерации');
                return;
            }

            // Заполняем поле адресом
            input.value = suggestion.value;

            // Сохраняем данные ФИАС
            selectedFiasData = {
                fias_id: suggestion.data.fias_id,
                fias_code: suggestion.data.fias_code,
                fias_level: suggestion.data.fias_level,
                fias_actuality_state: suggestion.data.fias_actuality_state,
                kladr_id: suggestion.data.kladr_id,
                postal_code: suggestion.data.postal_code,
                country: suggestion.data.country,
                region: suggestion.data.region,
                city: suggestion.data.city,
                street: suggestion.data.street,
                house: suggestion.data.house,
                geo_lat: suggestion.data.geo_lat,
                geo_lon: suggestion.data.geo_lon
            };

            // Сохраняем ФИАС в data-атрибут
            input.setAttribute('data-fias', JSON.stringify(selectedFiasData));

            container.style.display = 'none';
        });

        container.appendChild(item);
    });
}
