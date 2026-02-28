# 💊 Supplement Assistant Bot

**Науковий Telegram-бот для персонального планування прийому БАДів**

*Базується виключно на даних від Harvard Health, NIH, Mayo Clinic, PubMed та інших провідних медичних джерел*

## 🎯 Можливості

- **Перевірка сумісності** — аналіз взаємодій між обраними добавками
- **Meal-based планування** — розподіл БАДів по сніданку/обіду/вечері  
- **Часові інтервали** — автоматичне рознесення несумісних добавок
- **Розумний пошук** — автоматичний пошук інформації про нові БАДи
- **Наукова база** — Harvard Health, NIH ODS, Mayo Clinic, PubMed, Examine.com

## 🏛️ Наукові джерела

Вся інформація береться виключно з авторитетних медичних джерел:
- **NIH Office of Dietary Supplements** - Національний інститут здоров'я США
- **Harvard Health Publishing** - Гарвардська медична школа  
- **Mayo Clinic** - Одна з провідних клінік світу
- **PubMed** - Національна медична бібліотека США
- **Examine.com** - Незалежні огляди наукових досліджень БАДів

## 📦 Встановлення

```bash
# Клонувати / перейти в папку
cd supplement-assistant

# Створити віртуальне середовище
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Встановити залежності
pip install -r requirements.txt
```

## ⚙️ Налаштування

1. Створіть `.env` файл (або використайте існуючий):
```
TELEGRAM_BOT_TOKEN=your_token_here
```

2. Отримайте токен у [@BotFather](https://t.me/BotFather)

## 🚀 Запуск

```bash
python bot/telegram_bot.py
```

## 📁 Структура

```
supplement-assistant/
├── data/
│   ├── supplement_catalog.json    # Каталог БАДів
│   ├── supplement_interactions.json # Взаємодії
│   └── red_flags.json             # Застереження
├── core/
│   ├── normalizer.py              # Нормалізація назв
│   ├── compatibility.py           # Перевірка сумісності
│   └── planner.py                 # Планувальник
├── bot/
│   └── telegram_bot.py            # Telegram інтерфейс
├── requirements.txt
└── README.md
```

## 📊 Оновлення даних

JSON файли в `data/` можна оновлювати вручну або автоматично.
Кожен запис містить посилання на джерело (`source`).

### Джерела
- [NIH Office of Dietary Supplements](https://ods.od.nih.gov/)
- [Harvard Health](https://www.health.harvard.edu/)
- [Examine.com](https://examine.com/)
- [PubMed](https://pubmed.ncbi.nlm.nih.gov/)

## ⚠️ Застереження

Цей бот надає **науково обґрунтовану** інформаційну підтримку на основі рецензованих медичних джерел і **не замінює консультацію лікаря**.

- БАДи не є лікарськими засобами
- Інформація базується на наукових дослідженнях, але індивідуальна реакція може відрізнятися  
- Завжди консультуйтеся з лікарем перед початком прийому нових БАДів
- Особливо важливо при прийомі ліків або наявності захворювань

**Науковий підхід:** Кожна рекомендація містить посилання на джерело та рівень достовірності (0-1.0).

## 🔜 Roadmap

- [ ] Нагадування про прийом
- [ ] Персистентне зберігання (Redis/SQLite)
- [ ] Автооновлення knowledge base
- [ ] Інтеграція з календарем
- [ ] Трекінг прийому

---

Made with 🦝 by OpenClaw
