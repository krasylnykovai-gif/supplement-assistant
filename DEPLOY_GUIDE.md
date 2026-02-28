# 🚀 Деплой Supplement Assistant в облако

## ✅ Текущая готовность к деплою

Бот уже **полностью готов к деплою**! У нас есть все необходимые файлы:

### 📁 Готовые файлы для деплоя:
- ✅ `Procfile` - для Heroku/Railway
- ✅ `railway.toml` - конфигурация Railway
- ✅ `requirements.txt` - зависимости Python
- ✅ `runtime.txt` - версия Python
- ✅ `.env` - переменные окружения (пример)

## 🔑 Необходимые переменные окружения

### Обязательные:
```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### Опциональные (для расширенного функционала):
```bash
# Для intelligent lookup (автоматический поиск новых БАДов)
BRAVE_SEARCH_API_KEY=your_brave_api_key

# Для AI-анализа (опционально)
OPENAI_API_KEY=your_openai_key
```

## 🌐 Варианты хостинга

### 1. 🚄 Railway.app (РЕКОМЕНДУЕТСЯ)
**Плюсы:** Бесплатно до $5/месяц, простой деплой, хорошо для ботов
**Цена:** Бесплатно → $5/месяц при превышении лимитов

**Деплой за 2 минуты:**
1. Зарегистрируйся на [railway.app](https://railway.app/)
2. Подключи GitHub репозиторий
3. Railway автоматически обнаружит `railway.toml`
4. Добавь переменную окружения `TELEGRAM_BOT_TOKEN`
5. Deploy! 🚀

### 2. 🟣 Heroku
**Плюсы:** Популярный, много документации
**Минусы:** Больше не бесплатный ($7+/месяц)

**Деплой:**
1. Создай app на [heroku.com](https://heroku.com/)
2. `git push heroku main`
3. `heroku config:set TELEGRAM_BOT_TOKEN=your_token`
4. `heroku ps:scale worker=1`

### 3. ☁️ Другие варианты
- **Render.com** - аналог Heroku, $7/месяц
- **DigitalOcean App Platform** - от $5/месяц
- **Google Cloud Run** - serverless, платишь за использование
- **AWS Lambda** - serverless, очень дешево

## 📦 Подготовка к деплою

### ✅ Все уже готово!

**Текущая конфигурация:**
- 🐍 Python 3.11.0 (runtime.txt)  
- 📦 Зависимости указаны (requirements.txt)
- ⚙️ Команда запуска готова (Procfile + railway.toml)
- 🔧 Переменные окружения документированы (.env)

### 🔧 Возможные улучшения перед деплоем:

1. **Обновить requirements.txt** (если нужны дополнительные библиотеки):
```bash
# Добавить если используется fuzzy search
fuzzywuzzy>=0.18.0
python-Levenshtein>=0.20.0

# Добавить если используется intelligent lookup  
aiohttp>=3.8.0
beautifulsoup4>=4.11.0
```

2. **Добавить healthcheck endpoint** (опционально):
```python
# В bot/telegram_bot.py можно добавить простой веб-сервер для healthcheck
```

## 🚀 Пошаговый деплой на Railway

### Шаг 1: Подготовка репозитория
```bash
# Убедись что все файлы коммитнуты
git add .
git commit -m "Ready for deployment"
git push origin main
```

### Шаг 2: Создание проекта Railway
1. Иди на [railway.app](https://railway.app/)
2. Авторизуйся через GitHub
3. Нажми "New Project" → "Deploy from GitHub repo"
4. Выбери репозиторий с supplement-assistant

### Шаг 3: Настройка переменных окружения
В Railway dashboard:
1. Перейди в Variables
2. Добавь `TELEGRAM_BOT_TOKEN` = твой токен
3. (Опционально) `BRAVE_SEARCH_API_KEY` для intelligent lookup

### Шаг 4: Деплой!
Railway автоматически:
- ✅ Обнаружит `railway.toml` 
- ✅ Установит зависимости из `requirements.txt`
- ✅ Запустит бота командой `python bot/telegram_bot.py`

## 📊 Мониторинг после деплоя

### Railway Dashboard покажет:
- 🟢 Статус сервиса (Running/Crashed)
- 📈 Использование CPU/RAM
- 📋 Логи бота в реальном времени
- 💰 Стоимость хостинга

### Проверка работы:
1. Открой бота в Telegram
2. Отправь `/start` 
3. Проверь что все команды работают
4. Попробуй добавить новый БАД

## 🔧 Troubleshooting

### Если бот не запускается:
1. **Проверь логи** в Railway dashboard
2. **Убедись что токен правильный** в Variables
3. **Проверь Python версию** в runtime.txt
4. **Убедись что Procfile корректный**

### Типичные ошибки:
```bash
# Если ошибка с зависимостями:
ModuleNotFoundError: No module named 'xyz'
# → Добавь в requirements.txt

# Если ошибка с токеном:
telegram.error.InvalidToken
# → Проверь TELEGRAM_BOT_TOKEN в Variables

# Если проблемы с памятью:
MemoryError or OOMKilled
# → Возможно нужен план повыше
```

## 💡 Оптимизация для продакшена

### 1. Логирование:
```python
# Настрой уровень логов для продакшена
logging.basicConfig(level=logging.WARNING)
```

### 2. Персистентное хранение:
```bash
# Если нужна база данных, добавь в Railway:
# PostgreSQL, MongoDB, Redis
```

### 3. Мониторинг:
```bash
# Добавь алерты на:
# - Ошибки в боте
# - Высокое использование ресурсов
# - Время ответа
```

## 🎯 Готов к деплою!

**Команда для быстрого деплоя:**
```bash
# Если все готово:
git add . && git commit -m "Deploy to production" && git push
# Затем просто подключи GitHub repo к Railway
```

**Время деплоя:** ~2-3 минуты  
**Результат:** Бот работает 24/7 в облаке! 🚀

---

*Если возникнут проблемы с деплоем, проверь Railway logs или создай issue в репозитории.*

<function_calls>
<invoke name="read">
<parameter name="path">supplement-assistant/runtime.txt