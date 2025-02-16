# Eris Photo Bot

Телеграм-бот для отправки случайных фотографий с возможностью настройки автоматической рассылки по расписанию.
<img src="https://raw.githubusercontent.com/Am1rTl/Eris/main/eris_photo/01aad7e3d10f5d9236e7b7eb0afd013d.jpg" width="300">

## Основные возможности:

- Отправка случайной фотографии по команде
- Автоматическая рассылка фотографий по расписанию
- Удаление последних отправленных фотографий
- Управление временем рассылок
- Поддержка различных форматов изображений (jpg, jpeg, png, gif)

## Установка:

Создайте директорию для фотографий:```bash
mkdir eris_photo
```

Добавьте ваши фотографии в директорию `eris_photo`Установите зависимости:```bash
pip install python-telegram-bot telebot apscheduler pytz
```

Замените `TOKEN` в коде на ваш токен бота Telegram## Использование:

### Команды:

- `/start` - начать работу с ботом
- `/delete` - удалить последнюю отправленную фотографию

### Клавиатура меню:

- `Photo` - получить случайную фотографию
- `Настроить рассылку` - управление автоматической рассылкой

### Управление рассылкой:

Выберите "Настроить рассылку"Доступные опции:- Мои рассылки - просмотр активных рассылок
- Удалить рассылку - отмена существующей рассылки
- Добавить рассылку - создание новой рассылки
- Назад в меню - возврат в главное меню

## Технические детали:

- Язык программирования: Python 3.x
- Время работы: 24/7
- Временная зона: Europe/Moscow
- Хранение данных: JSON файл
- Планировщик задач: APScheduler

## Структура проекта:

```plaintext
project/
├── bot.py
├── eris_photo/
│   └── *.jpg/*.jpeg/*.png/*.gif
├── data.json
└── README.md
```

## Примечания по безопасности:

- Токен бота должен быть защищён и не выкладываться в публичный доступ
- Файлы фотографий должны иметь правильные разрешения для чтения
- При ошибке загрузки фотографии бот уведомит об этом пользователя

## Лицензия:

MIT License

Бот создан для автоматизации отправки фотографий в Telegram с возможностью гибкой настройки расписания рассылок. Все данные пользователей хранятся локально в JSON файле для обеспечения персонализации опыта использования.
