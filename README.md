# HH Vacancy Monitor 🚀

Скрипт отслеживает новые вакансии работодателя на HH.ru и отправляет уведомления в Telegram.

---

## 📁 Структура проекта

```
hh_monitor/
├── hh_monitor.py      # основной скрипт
├── requirements.txt   # зависимости
├── .env               # секреты (создать вручную)
├── .env.example       # шаблон .env
├── vacancies.json     # создаётся автоматически
└── app.log            # создаётся автоматически
```

---

## 1️⃣ Установка Python

Убедитесь, что установлен **Python 3.10+**:
```
python --version
```
Скачать: https://www.python.org/downloads/

---

## 2️⃣ Создание .env файла

Скопируйте шаблон и заполните:
```
copy .env.example .env
```

Откройте `.env` в блокноте и укажите:
```
TELEGRAM_BOT_TOKEN=1234567890:AAH...ваш_токен
TELEGRAM_CHAT_ID=123456789
```

### Как получить токен бота:
1. Напишите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot` и следуйте инструкциям
3. Скопируйте полученный токен

### Как получить Chat ID:
1. Напишите вашему боту любое сообщение
2. Откройте в браузере:
   `https://api.telegram.org/bot<ВАШ_ТОКЕН>/getUpdates`
3. Найдите `"chat":{"id": ...}` — это и есть ваш Chat ID

---

## 3️⃣ Установка зависимостей

```
pip install -r requirements.txt
```

---

## 4️⃣ Запуск вручную

```
python hh_monitor.py
```

При первом запуске скрипт считает все текущие вакансии как "уже отправленные"
и запишет их в `vacancies.json`. Новые уведомления придут только при следующих запусках.

---

## 5️⃣ Автозапуск каждые 5 минут (Windows Task Scheduler)

### Шаг 1 — Найдите полный путь к python.exe
```
where python
```
Например: `C:\Users\User\AppData\Local\Programs\Python\Python311\python.exe`

### Шаг 2 — Откройте Task Scheduler
Нажмите `Win + R` → введите `taskschd.msc` → ОК

### Шаг 3 — Создайте новое задание
1. В правой панели нажмите **"Create Basic Task..."**
2. Введите имя: `HH Vacancy Monitor`
3. Триггер: **Daily** (мы настроим повтор вручную)
4. Действие: **Start a program**

### Шаг 4 — Настройте действие
- **Program/script:**
  ```
  C:\Users\User\AppData\Local\Programs\Python\Python311\python.exe
  ```
- **Add arguments:**
  ```
  hh_monitor.py
  ```
- **Start in** (обязательно!):
  ```
  C:\путь\к\папке\hh_monitor
  ```

### Шаг 5 — Настройте повтор каждые 5 минут
1. После создания найдите задание в списке → **Properties**
2. Вкладка **Triggers** → выберите триггер → **Edit**
3. Включите **Repeat task every:** `5 minutes`
4. **For a duration of:** `Indefinitely`
5. Нажмите **OK**

### Шаг 6 — Проверьте задание
Щёлкните по заданию правой кнопкой → **Run**. Проверьте, пришло ли сообщение в Telegram.

---

## 📋 Логи

Все события записываются в `app.log` и выводятся в консоль:
```
2024-05-01 10:00:00 [INFO] HH Vacancy Monitor запущен.
2024-05-01 10:00:01 [INFO] Получено вакансий с HH: 5
2024-05-01 10:00:01 [INFO] Новая вакансия: [12345678] Python Developer
2024-05-01 10:00:02 [INFO] Сообщение отправлено в Telegram.
```

---

## ⚠️ Частые проблемы

| Проблема | Решение |
|---|---|
| `TELEGRAM_BOT_TOKEN не задан` | Проверьте файл `.env` рядом со скриптом |
| `HTTP 401 Telegram` | Неверный токен бота |
| `HTTP 400 Telegram` | Неверный Chat ID |
| `ConnectionError HH API` | Нет интернета или HH недоступен |
| Скрипт не запускается в Task Scheduler | Проверьте поле **"Start in"** — должен быть путь к папке скрипта |
