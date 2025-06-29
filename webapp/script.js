// JavaScript для веб-приложения вызова ветеринара

// Инициализация Telegram Web App
let tg = window.Telegram.WebApp;

// Настройка темы и интерфейса
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация Telegram Web App
    tg.ready();
    
    // Настройка главной кнопки
    tg.MainButton.text = "Отправить заявку";
    tg.MainButton.color = "#4CAF50";
    
    // Обработчики событий
    setupEventListeners();
    
    // Применение темы Telegram
    applyTelegramTheme();
    
    // Автозаполнение данных пользователя
    prefillUserData();
});

function setupEventListeners() {
    const form = document.getElementById('callForm');
    const submitBtn = document.getElementById('submitBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    
    // Обработчик отправки формы
    submitBtn.addEventListener('click', handleSubmit);
    
    // Обработчик отмены
    cancelBtn.addEventListener('click', handleCancel);
    
    // Валидация в реальном времени
    const requiredFields = form.querySelectorAll('[required]');
    requiredFields.forEach(field => {
        field.addEventListener('input', validateField);
        field.addEventListener('blur', validateField);
    });
    
    // Форматирование телефона
    const phoneInput = document.getElementById('phone');
    phoneInput.addEventListener('input', formatPhone);
    
    // Обработчик главной кнопки Telegram
    tg.MainButton.onClick(handleSubmit);
    
    // Обновление состояния главной кнопки при изменении формы
    form.addEventListener('input', updateMainButton);
}

function applyTelegramTheme() {
    // Применение цветовой схемы Telegram
    if (tg.colorScheme === 'dark') {
        document.body.classList.add('dark-theme');
    }
    
    // Установка CSS переменных из темы Telegram
    const root = document.documentElement;
    if (tg.themeParams) {
        root.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color || '#ffffff');
        root.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color || '#000000');
        root.style.setProperty('--tg-theme-hint-color', tg.themeParams.hint_color || '#999999');
        root.style.setProperty('--tg-theme-button-color', tg.themeParams.button_color || '#4CAF50');
        root.style.setProperty('--tg-theme-button-text-color', tg.themeParams.button_text_color || '#ffffff');
        root.style.setProperty('--tg-theme-secondary-bg-color', tg.themeParams.secondary_bg_color || '#f8f9fa');
    }
}

function prefillUserData() {
    // Автозаполнение данных пользователя из Telegram
    if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
        const user = tg.initDataUnsafe.user;
        const nameField = document.getElementById('name');
        
        if (user.first_name && !nameField.value) {
            nameField.value = user.first_name + (user.last_name ? ' ' + user.last_name : '');
        }
    }
}

function validateField(event) {
    const field = event.target;
    const value = field.value.trim();
    
    // Удаление предыдущих ошибок
    field.classList.remove('error');
    const existingError = field.parentNode.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
    
    let isValid = true;
    let errorMessage = '';
    
    // Валидация обязательных полей
    if (field.hasAttribute('required') && !value) {
        isValid = false;
        errorMessage = 'Это поле обязательно для заполнения';
    }
    
    // Специфическая валидация
    switch (field.id) {
        case 'phone':
            if (value && !isValidPhone(value)) {
                isValid = false;
                errorMessage = 'Введите корректный номер телефона';
            }
            break;
        case 'name':
            if (value && value.length < 2) {
                isValid = false;
                errorMessage = 'Имя должно содержать минимум 2 символа';
            }
            break;
        case 'address':
            if (value && value.length < 10) {
                isValid = false;
                errorMessage = 'Укажите полный адрес';
            }
            break;
        case 'problem':
            if (value && value.length < 10) {
                isValid = false;
                errorMessage = 'Опишите проблему более подробно';
            }
            break;
    }
    
    // Отображение ошибки
    if (!isValid) {
        field.classList.add('error');
        const errorElement = document.createElement('span');
        errorElement.className = 'error-message';
        errorElement.textContent = errorMessage;
        field.parentNode.appendChild(errorElement);
    }
    
    return isValid;
}

function isValidPhone(phone) {
    // Простая валидация телефона
    const phoneRegex = /^[\+]?[0-9\s\-\(\)]{10,}$/;
    return phoneRegex.test(phone);
}

function formatPhone(event) {
    let value = event.target.value.replace(/\D/g, '');
    
    if (value.length > 0) {
        if (value[0] === '8') {
            value = '7' + value.slice(1);
        }
        if (value[0] === '7') {
            value = '+7 (' + value.slice(1, 4) + ') ' + value.slice(4, 7) + '-' + value.slice(7, 9) + '-' + value.slice(9, 11);
        }
    }
    
    event.target.value = value;
}

function updateMainButton() {
    const form = document.getElementById('callForm');
    const isValid = validateForm(false);
    
    if (isValid) {
        tg.MainButton.show();
    } else {
        tg.MainButton.hide();
    }
}

function validateForm(showErrors = true) {
    const form = document.getElementById('callForm');
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (showErrors) {
            const fieldValid = validateField({ target: field });
            if (!fieldValid) isValid = false;
        } else {
            if (!field.value.trim()) isValid = false;
        }
    });
    
    return isValid;
}

function collectFormData() {
    const form = document.getElementById('callForm');
    const formData = new FormData(form);
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        data[key] = value.trim();
    }
    
    // Добавление метаданных
    data.timestamp = new Date().toISOString();
    data.user_id = tg.initDataUnsafe?.user?.id || null;
    data.username = tg.initDataUnsafe?.user?.username || null;
    
    return data;
}

function handleSubmit() {
    const submitBtn = document.getElementById('submitBtn');
    
    // Валидация формы
    if (!validateForm(true)) {
        tg.showAlert('Пожалуйста, заполните все обязательные поля корректно');
        return;
    }
    
    // Показать состояние загрузки
    submitBtn.disabled = true;
    submitBtn.classList.add('loading');
    submitBtn.textContent = '📤 Отправка...';
    
    try {
        // Сбор данных формы
        const formData = collectFormData();
        
        // Отправка данных в бот
        tg.sendData(JSON.stringify(formData));
        
        // Показать сообщение об успехе
        tg.showAlert('Заявка отправлена! Врач свяжется с вами в ближайшее время.');
        
        // Закрыть веб-приложение
        setTimeout(() => {
            tg.close();
        }, 1500);
        
    } catch (error) {
        console.error('Ошибка отправки:', error);
        tg.showAlert('Произошла ошибка при отправке заявки. Попробуйте еще раз.');
        
        // Восстановить кнопку
        submitBtn.disabled = false;
        submitBtn.classList.remove('loading');
        submitBtn.textContent = '📱 Вызвать врача';
    }
}

function handleCancel() {
    tg.showConfirm('Вы уверены, что хотите отменить заполнение формы?', (confirmed) => {
        if (confirmed) {
            tg.close();
        }
    });
}

// Обработка изменения ориентации устройства
window.addEventListener('orientationchange', function() {
    setTimeout(() => {
        tg.expand();
    }, 100);
});

// Обработка события закрытия веб-приложения
window.addEventListener('beforeunload', function(event) {
    const form = document.getElementById('callForm');
    const hasData = Array.from(form.elements).some(element => element.value.trim() !== '');
    
    if (hasData) {
        event.preventDefault();
        event.returnValue = '';
    }
});

// Расширение веб-приложения на весь экран
tg.expand();

// Включение закрывающего жеста
tg.enableClosingConfirmation();

