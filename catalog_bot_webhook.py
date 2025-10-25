import os
from flask import Flask, request
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# --- Конфигурация
TOKEN = "8272770257:AAHCYt5GKjdaweaTI3frG-tWzItJK8OGSIs"
bot = Bot(token=TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot, None, workers=0)

# --- Публичный URL Render
PUBLIC_URL = "https://telegram-catalog-bot.onrender.com"
TELEGRAM_WEBHOOK_URL = f"{PUBLIC_URL}/{TOKEN}"

# --- Каталог
catalog = {
    "Игры": [
        {"name": "Игра Уличный гонщик", "description": "Захватывающее приключение с отличной графикой и сюжетом.", "photo": "game1.jpeg", "price": 100},
        {"name": "Игра Mortal Kombat (PS5)", "description": "Лучшая игра жанре драк", "photo": "game3.jpeg", "price": 250},
        {"name": "Игра Ведьмак 3. Дикая охота (PS5)", "description": "Полное издание для PS5, русская озвучка", "photo": "game4.jpeg", "price": 250},
        {"name": "Игра Dishonored 2", "description": "Сложная стратегия, где решает каждый ход.", "photo": "game2.jpeg", "price": 200},
    ]
}

# --- Хранилище данных
carts = {}
orders = {}
order_info = {}
global_order_number = 0

# --- Главное меню
main_menu = ReplyKeyboardMarkup(
    [
        [KeyboardButton("Каталог игр")],
        [KeyboardButton("Просмотр корзины"), KeyboardButton("Оформить заказ")],
        [KeyboardButton("Мои заказы")],
        [KeyboardButton("❓ Часто задаваемые вопросы")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

# --- Хэндлеры бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выберите раздел:", reply_markup=main_menu)

# (Здесь вставь всю функцию handle_menu и button_handler без изменений)
# Например: handle_menu и button_handler из твоего предыдущего кода

# --- Регистрация хэндлеров
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))
dispatcher.add_handler(CallbackQueryHandler(button_handler))

# --- Flask route для Telegram Webhook
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK"

# --- Проверка работы сервера
@app.route("/")
def index():
    return "Bot is running!"

# --- Установка webhook
bot.set_webhook(TELEGRAM_WEBHOOK_URL)

# --- Запуск Flask
if __name__ == "__main__":
    print("OS module loaded:", "os" in globals())
    port = int(os.environ.get("PORT", 5000))
    print("Port:", port)
    app.run(host="0.0.0.0", port=port)

