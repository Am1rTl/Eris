import os
import random
import telebot
from telebot import types
import json
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
import pytz

TOKEN = 'token'
PHOTO_DIR = 'eris_photo'

bot = telebot.TeleBot(TOKEN)

moscow_tz = pytz.timezone('Europe/Moscow')
scheduler = BackgroundScheduler(timezone=moscow_tz)
scheduler.start()

try:
    with open('data.json') as f:
        user_data = json.load(f)
    # Конвертация старых данных и инициализация last_photo
    for user_id, data in user_data.items():
        if "last_photo_id" in data:
            del data["last_photo_id"]
        if "last_photo" not in data:
            data["last_photo"] = None
except FileNotFoundError:
    user_data = {}

def save_data():
    with open('data.json', 'w') as f:
        json.dump(user_data, f, indent=4)

# Восстановление задач
for user_id, data in user_data.items():
    valid_jobs = {}
    for job_id, time_str in data.get("jobs", {}).items():
        try:
            hour, minute = map(int, time_str.split(':'))
            scheduler.add_job(
                send_mailing,
                'cron',
                hour=hour,
                minute=minute,
                args=[user_id],
                id=job_id,
                timezone=moscow_tz
            )
            valid_jobs[job_id] = time_str
        except Exception:
            continue
    data["jobs"] = valid_jobs

save_data()

def show_keyboard(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("Photo"), types.KeyboardButton("Настроить рассылку"))
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=keyboard)

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = str(message.chat.id)
    if user_id not in user_data:
        user_data[user_id] = {"mailing_times": [], "jobs": {}, "last_photo": None}
        save_data()
    show_keyboard(message)

@bot.message_handler(func=lambda message: message.text == "Photo")
def send_random_photo(message):
    user_id = str(message.chat.id)
    photos = [f for f in os.listdir(PHOTO_DIR) if f.endswith(('jpg', 'jpeg', 'png', 'gif'))]
    if not photos:
        bot.send_message(message.chat.id, "Нет доступных фотографий.")
        return

    random_photo = random.choice(photos)
    with open(os.path.join(PHOTO_DIR, random_photo), 'rb') as photo:
        sent_photo = bot.send_photo(message.chat.id, photo)
        user_data[user_id]["last_photo"] = {
            "message_id": sent_photo.message_id,
            "file_name": random_photo
        }
        save_data()

@bot.message_handler(commands=['delete'])
def handle_delete_command(message):
    user_id = str(message.chat.id)
    user_info = user_data.get(user_id)
    if not user_info or not user_info.get("last_photo"):
        bot.reply_to(message, "Нет последней фотографии для удаления.")
        return

    last_photo = user_info["last_photo"]
    file_path = os.path.join(PHOTO_DIR, last_photo["file_name"])
    file_deleted = False
    msg_deleted = False

    # Удаление файла
    if last_photo["file_name"] and os.path.exists(file_path):
        try:
            os.remove(file_path)
            file_deleted = True
        except Exception as e:
            bot.reply_to(message, f"Ошибка при удалении файла: {e}")

    # Удаление сообщения
    try:
        bot.delete_message(chat_id=message.chat.id, message_id=last_photo["message_id"])
        msg_deleted = True
    except telebot.apihelper.ApiTelegramException as e:
        error_msg = "Сообщение уже удалено или недоступно."
        bot.reply_to(message, error_msg)

    # Формирование ответа
    response = []
    if msg_deleted:
        response.append("Сообщение удалено из чата.")
    if file_deleted:
        response.append("Фотография удалена из датасета.")
    if not response:
        response.append("Действия не выполнены.")
    bot.reply_to(message, "\n".join(response))

    # Сброс последней фотографии
    user_info["last_photo"] = None
    save_data()

@bot.message_handler(func=lambda message: message.text == "Настроить рассылку")
def configure_mailing(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("Мои рассылки"), types.KeyboardButton("Удалить рассылку"), types.KeyboardButton("Добавить рассылку"), types.KeyboardButton("Назад в меню"))
    bot.send_message(message.chat.id, "Выберите опцию:", reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text == "Мои рассылки")
def show_mailing_times(message):
    user_id = str(message.chat.id)
    if user_id not in user_data or not user_data[user_id]["mailing_times"]:
        bot.send_message(message.chat.id, "Нет активных рассылок.")
    else:
        bot.send_message(message.chat.id, "Ваши рассылки:\n" + "\n".join(user_data[user_id]["mailing_times"]))

@bot.message_handler(func=lambda message: message.text == "Удалить рассылку")
def delete_mailing(message):
    user_id = str(message.chat.id)
    if user_id not in user_data or not user_data[user_id]["mailing_times"]:
        bot.send_message(message.chat.id, "Нет рассылок для удаления.")
        return

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for time in user_data[user_id]["mailing_times"]:
        keyboard.add(types.KeyboardButton(time))
    keyboard.add(types.KeyboardButton("Назад в меню"))
    bot.send_message(message.chat.id, "Выберите время для удаления:", reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text in user_data.get(str(message.chat.id), {}).get("mailing_times", []))
def confirm_delete_mailing(message):
    user_id = str(message.chat.id)
    target_time = message.text

    jobs_to_delete = [job_id for job_id, time in user_data[user_id]["jobs"].items() if time == target_time]
    for job_id in jobs_to_delete:
        try:
            scheduler.remove_job(job_id)
        except JobLookupError:
            pass
        del user_data[user_id]["jobs"][job_id]

    if target_time in user_data[user_id]["mailing_times"]:
        user_data[user_id]["mailing_times"].remove(target_time)
    save_data()
    bot.send_message(message.chat.id, f"Рассылка на {target_time} удалена.")

@bot.message_handler(func=lambda message: message.text == "Добавить рассылку")
def add_mailing(message):
    bot.send_message(message.chat.id, "Введите время в формате HH:MM")
    bot.register_next_step_handler(message, process_mailing_time)

def process_mailing_time(message):
    user_id = str(message.chat.id)
    time_str = message.text.strip()

    try:
        hour, minute = map(int, time_str.split(':'))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
        time_formatted = f"{hour:02}:{minute:02}"
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат. Используйте HH:MM")
        return

    if user_id not in user_data:
        user_data[user_id] = {"mailing_times": [], "jobs": {}, "last_photo": None}

    if time_formatted in user_data[user_id]["mailing_times"]:
        bot.send_message(message.chat.id, "Это время уже добавлено.")
        return

    user_data[user_id]["mailing_times"].append(time_formatted)
    job_id = f"mailing_{user_id}_{time_formatted}"
    try:
        scheduler.add_job(
            send_mailing,
            'cron',
            hour=hour,
            minute=minute,
            args=[user_id],
            id=job_id,
            timezone=moscow_tz
        )
        user_data[user_id]["jobs"][job_id] = time_formatted
        save_data()
        bot.send_message(message.chat.id, f"Рассылка на {time_formatted} добавлена.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")

def send_mailing(user_id):
    photos = [f for f in os.listdir(PHOTO_DIR) if f.endswith(('jpg', 'jpeg', 'png', 'gif'))]
    if photos:
        with open(os.path.join(PHOTO_DIR, random.choice(photos)), 'rb') as photo:
            bot.send_photo(user_id, photo)

@bot.message_handler(func=lambda message: message.text == "Назад в меню")
def back_to_menu(message):
    show_keyboard(message)

if __name__ == '__main__':
    try:
        bot.polling(none_stop=True)
    except KeyboardInterrupt:
        scheduler.shutdown()
