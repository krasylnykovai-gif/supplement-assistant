# 🚀 СРОЧНЫЙ ДЕПЛОЙ - Med Bot (@med11007_bot)

## ✅ Бот готов к деплою!

**Bot info:**
- Name: med
- Username: @med11007_bot  
- Token: 8355609545:AAFUdwoaBeu0epPN9gj32aPxkh7lqqxZzbI
- Admin: 383087326 (Ірина)

## 📋 БЫСТРЫЕ ШАГИ:

### 1. Railway.app (БЕСПЛАТНО)
1. Иди на [railway.app](https://railway.app)
2. Sign up with GitHub
3. New Project → Deploy from GitHub repo
4. Выбери supplement-assistant папку/repo
5. Add Environment Variable:
   - `TELEGRAM_BOT_TOKEN` = `8355609545:AAFUdwoaBeu0epPN9gj32aPxkh7lqqxZzbI`
6. Deploy!

### 2. Heroku ($7/месяц)
1. Иди на [heroku.com](https://heroku.com)
2. Create new app: `med-supplement-bot`
3. Connect GitHub repo
4. Settings → Config Vars:
   - `TELEGRAM_BOT_TOKEN` = `8355609545:AAFUdwoaBeu0epPN9gj32aPxkh7lqqxZzbI`
5. Deploy branch: main

## 🧪 После деплоя:

### Проверка:
1. Открой [@med11007_bot](https://t.me/med11007_bot) в Telegram
2. Напиши `/start` → должен ответить
3. Напиши `/users` → покажет "1 пользователь" (ты)

### Команды для проверки:
- `/start` - регистрация пользователя
- `/help` - список команд  
- `/users` - статистика (только админ)
- Добавь любой БАД для теста

## 📊 Ожидаемый результат /users:
```
📊 Аналітика користувачів

📈 Загальна статистика:
👥 Всього унікальних користувачів: 1

📅 Сьогодні (2026-03-02):
🆕 Нових користувачів: 1
👤 Активних користувачів: 1

🏆 Топ-5 найактивніших:
1. Ірина (@your_username) - 1 раз
```

## 🔧 Если проблемы:

**Бот не отвечает:**
- Проверь токен в Environment Variables
- Проверь логи в Railway/Heroku dashboard

**Команда /users не работает:**
- Убедись что твой ID = 383087326
- Проверь что ты пишешь команду в приватном чате с ботом

## ⏱️ Время деплоя: 2-3 минуты

**Готово! Бот будет работать 24/7 и собирать реальную статистику пользователей.**