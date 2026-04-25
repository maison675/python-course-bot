# Python Course Telegram Bot

Личный Telegram-бот для прохождения курса Python с автопроверкой решений.

## Структура

```
python_course_bot/
├── bot/                      — код бота (aiogram 3)
│   ├── main.py               — точка входа
│   ├── handlers.py           — обработчики команд и кнопок
│   ├── content.py            — загрузка тем/задач из content/
│   ├── progress.py           — SQLite для прогресса
│   └── ui.py                 — клавиатуры
├── sandbox/                  — изолированный запуск кода
│   ├── runner.py             — subprocess с лимитами CPU/память/время
│   └── grader.py             — проверка решений (stdout / function tests)
├── content/                  — задачи в структурированном формате
│   ├── topics.yaml           — список тем с теорией
│   └── tasks/
│       ├── 01_hello.yaml     — задачи темы 01 с тестами
│       └── …
├── tests/                    — pytest тесты для самого бота
├── requirements.txt
├── Dockerfile                — для деплоя на Railway
└── railway.json
```

## Локальный запуск

```bash
pip install -r requirements.txt
export BOT_TG_TOKEN=...
export OWNER_TG_ID=...
python -m bot.main
```

## Деплой

Railway автоматически собирает Dockerfile и запускает.
