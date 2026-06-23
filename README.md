# 🚀 FB Multi-Account Automation System v2.0

Полная система создания и управления мультиаккаунтами на Facebook/Instagram с поддержкой автоматизации, кампаний и взаимодействий.

## 📋 Возможности

### Создание Аккаунтов
- ✅ Массовое создание аккаунтов с реалистичными профилями
- ✅ Поддержка множества стран (US, DE, FR, IL, RU, UA)
- ✅ Автоматическое заполнение профиля (имя, город, работа, ВУЗ)
- ✅ Генерация аватаров и биографии
- ✅ Сохранение куки и сессий

### База Данных
- 📊 SQLite БД с полной статистикой
- 💾 Сохранение всех данных аккаунтов
- 🔍 Поиск и фильтрация по различным критериям
- 📈 Отслеживание истории действий

### Прокси
- 🌐 Автоматическое обновление БД прокси
- ✅ Проверка прокси по странам
- 📊 Статистика и рейтинг прокси
- ⚡ Быстрая выборка рабочих прокси

### Кампании
- 🎯 Создание и управление кампаниями
- 👥 Назначение аккаунтов на кампании
- 🔗 Создание сетей взаимодействий
- ⚙️ Автоматизация действий

### Действия
- ❤️ Автолайкер
- 💬 Автокомментатор
- 👥 Автоподписка
- 💌 Автопостинг
- 📬 Автоответчик в мессенджерах

### Веб-Дашборд
- 🌐 REST API
- 📊 Реал-тайм статистика
- 👨‍💼 Управление аккаунтами
- 🎯 Управление кампаниями
- 📈 Аналитика и отчеты

## 🛠️ Установка

```bash
# Клонировать репозиторий
git clone https://github.com/batoniyoni-hub/1.git
cd 1

# Установить зависимости
pip install -r requirements.txt
```

## 🚀 Запуск

### Интерактивный режим
```bash
python main.py --mode interactive
```

### Создание аккаунтов
```bash
python main.py --mode create --geo US --count 50 --threads 10 --proxy
```

### Веб-Дашборд
```bash
python main.py --mode api
```

## 📚 Структура проекта

```
.
├── main.py                    # Главный скрипт
├── api_dashboard.py          # Flask API
├── account_database.py       # БД аккаунтов
├── proxy_manager.py          # Менеджер прокси
├── campaign_automation.py    # Автоматизация кампаний
├── multi_account_manager.py  # Менеджер аккаунтов
├── profile_generator.py      # Генератор профилей
├── FB_Multi_Creator_v17.py   # Основной создатель
└── requirements.txt          # Зависимости
```

## 🔌 API Endpoints

### Аккаунты
- `GET /api/accounts` - Получить список аккаунтов
- `GET /api/accounts/<id>` - Получить детали
- `PUT /api/accounts/<id>` - Обновить аккаунт
- `POST /api/create-accounts` - Создать новые

### Кампании
- `GET /api/campaigns` - Список кампаний
- `POST /api/campaigns` - Создать кампанию
- `POST /api/campaigns/<id>/start` - Запустить
- `POST /api/campaigns/<id>/stop` - Остановить
- `GET /api/campaigns/<id>/stats` - Статистика

### Действия
- `POST /api/actions/schedule` - Запланировать
- `POST /api/actions/execute` - Выполнить

### Экспорт
- `GET /api/export/accounts?format=xlsx` - Экспортировать

## 📊 Примеры использования

### Создание 50 аккаунтов США
```python
from main import FBMultiCreator

creator = FBMultiCreator()
creator.create_accounts_bulk('US', 50, 'facebook', 10, use_proxy=True)
```

### Запуск кампании
```python
campaign_id = creator.run_campaign(
    'Summer2024',
    'organic',
    'instagram',
    'US',
    20
)
```

### Работа с БД
```python
from account_database import AccountDatabase

db = AccountDatabase()

# Получить валидные аккаунты
accounts = db.get_accounts_by_status('valid')

# Получить по стране
us_accounts = db.get_accounts_by_country('US')

# Получить статистику
stats = db.get_stats()
print(stats)
```

## ⚙️ Конфигурация

Отредактируйте `config.json`:

```json
{
  "settings": {
    "max_threads": 10,
    "default_country": "US",
    "min_age": 18,
    "max_age": 45
  }
}
```

## 📝 Функциональность

### ✅ Реализовано
- Массовое создание аккаунтов
- SQLite БД со всеми данными
- Проверка и менеджмент прокси
- Система кампаний
- Автоматизация действий
- REST API дашборд
- Многопоточность
- Экспорт в различные форматы

### 🔜 Планируется
- Фронтенд на React/Vue
- ML модель для определения трастовых аккаунтов
- Интеграция с Telegram для оповещений
- Система прокси ротации
- Backup и восстановление БД

## ⚠️ Дисклеймер

Эта система предназначена только для образовательных целей. Использование для несанкционированного доступа к аккаунтам или нарушения ToS социальных сетей запрещено.

## 📞 Поддержка

Если у вас есть вопросы или проблемы, откройте issue на GitHub.

## 📄 Лицензия

MIT License

---

**Создано с ❤️ для автоматизации**
