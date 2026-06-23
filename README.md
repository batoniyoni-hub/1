# FB Multi-Creator v17

Мульти-аккаунт создатель и фармер для различных платформ (Facebook, Instagram, Telegram и т.д.)

## Функциональность

- 🔧 Создание профилей с реалистичными данными
- 📧 Автоматическое получение временных email через Mail.tm API
- 🌍 Поддержка ГЕО-прокси (IL, US, GB, DE, FR)
- 💼 Создание Business Manager аккаунтов для Facebook
- 📊 Экспорт всех данных в Excel
- 🔐 Генерация 2FA секретов
- ⚡ Многопоточная обработка

## Установка

```bash
pip install -r requirements.txt
```

## Использование

```bash
python FB_Multi_Creator_v17.py
```

### Интерактивное меню

1. Выберите ГЕО (IL/US/GB/DE/FR)
2. Укажите количество профилей
3. Выберите платформы (FB, IG, TG, WA, TW, GOOGLE)
4. Выберите опции (Business Manager, Прокси)

## Результат

Все данные сохраняются в Excel файл с форматом:
`Accounts_{GEO}_{COUNT}acc_{DATETIME}.xlsx`

## Требования

- Python 3.7+
- requests
- faker
- tqdm
- openpyxl
- pyotp

## Лицензия

MIT
