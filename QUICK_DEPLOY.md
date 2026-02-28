# ⚡ Быстрый деплой за 2 минуты

## 🎯 Что нужно (минимум):

### 1. ✅ Telegram Bot Token 
Получи у [@BotFather](https://t.me/BotFather) - **у тебя уже есть!**

### 2. ☁️ Аккаунт Railway.app
Бесплатная регистрация на [railway.app](https://railway.app/)

## 🚀 Деплой (2 минуты):

### Шаг 1: Railway
1. Иди на [railway.app](https://railway.app/)
2. "Sign in with GitHub"
3. "New Project" → "Deploy from GitHub repo"
4. Выбери репозиторий supplement-assistant

### Шаг 2: Токен
В Railway dashboard:
1. Вкладка "Variables" 
2. Добавь `TELEGRAM_BOT_TOKEN` = `8355609545:AAFUdwoaBeu0epPN9gj32aPxkh7lqqxZzbI`

### Шаг 3: Готово! 🎉
Railway автоматически развернет бота. Через 30 секунд проверь в Telegram - `/start`

---

## 🔧 Альтернативы Railway:

### Heroku ($7+/месяц):
```bash
heroku create supplement-assistant-bot
heroku config:set TELEGRAM_BOT_TOKEN=твой_токен
git push heroku main
heroku ps:scale worker=1
```

### Render.com ($7/месяц):
1. Подключи GitHub repo
2. Service Type: "Web Service" 
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `python bot/telegram_bot.py`

### VPS (DigitalOcean $5/месяц):
```bash
# На сервере:
git clone репозиторий
cd supplement-assistant  
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN=твой_токен
nohup python bot/telegram_bot.py &
```

---

## 💡 Дополнительно (опционально):

### Brave Search API (для intelligent lookup):
1. Получи API key на [brave.com/search/api/](https://brave.com/search/api/) (бесплатно)
2. Добавь в Railway Variables: `BRAVE_SEARCH_API_KEY`

### Мониторинг:
Railway Dashboard показывает логи и статистику в реальном времени.

---

**Результат: Бот работает 24/7 в облаке! 🤖☁️**