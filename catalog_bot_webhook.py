import os
from flask import Flask, request
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import asyncio

# --- Конфигурация
TOKEN = "8272770257:AAHCYt5GKjdaweaTI3frG-tWzItJK8OGSIs"
bot = Bot(token=TOKEN)
app_flask = Flask(__name__)

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

# --- Хэндлеры
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выберите раздел:", reply_markup=main_menu)

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id

    if text == "Каталог игр":
        category = "Игры"
        # Используем индекс в callback_data вместо полного имени
        keyboard = [
            [InlineKeyboardButton(f"{item['name']} — {item['price']}р", callback_data=f"item_{idx}")]
            for idx, item in enumerate(catalog[category])
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f"Каталог {category}:", reply_markup=reply_markup)

    elif text == "Просмотр корзины":
        cart_items = carts.get(user_id, [])
        if not cart_items:
            await update.message.reply_text("🛒 Ваша корзина пуста.", reply_markup=main_menu)
            return
        text_cart = "🛒 Ваша корзина:\n"
        total = 0
        keyboard = []
        for i in cart_items:
            item = next((it for it in catalog["Игры"] if it["name"] == i), None)
            if item:
                text_cart += f"- {i} — {item['price']}р\n"
                total += item['price']
                keyboard.append([InlineKeyboardButton(f"❌ Удалить {i}", callback_data=f"remove_{i}")])
        keyboard.append([InlineKeyboardButton("Оформить заказ", callback_data="checkout")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        text_cart += f"\n💰 Итого: {total}р"
        await update.message.reply_text(text_cart, reply_markup=reply_markup)

    elif text == "Оформить заказ":
        cart_items = carts.get(user_id, [])
        if not cart_items:
            await update.message.reply_text("Ваша корзина пуста.", reply_markup=main_menu)
            return
        await update.message.reply_text(
            "Введите данные для оформления заказа в одном сообщении:\nтелефон: <телефон>\nимя: <имя>\nадрес: <адрес>",
            reply_markup=main_menu
        )
    else:
        await update.message.reply_text("Пожалуйста, выберите раздел из меню ниже 👇", reply_markup=main_menu)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data.startswith("item_"):
        idx = int(data.split("_")[1])
        item = catalog["Игры"][idx]
        keyboard = [
            [InlineKeyboardButton("Назад к каталогу", callback_data="back_to_catalog")],
            [InlineKeyboardButton("Добавить в корзину", callback_data=f"add_{idx}")],
            [InlineKeyboardButton("Просмотр корзины", callback_data="view_cart")],
            [InlineKeyboardButton("Оформить заказ", callback_data="checkout")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            with open(item["photo"], "rb") as f:
                await query.message.reply_photo(photo=f, caption=f"🎮 {item['name']} — {item['price']}р\n{item['description']}", reply_markup=reply_markup)
        except FileNotFoundError:
            await query.message.reply_text(f"🎮 {item['name']} — {item['price']}р\n{item['description']}", reply_markup=reply_markup)

    elif data.startswith("add_"):
        idx = int(data.split("_")[1])
        item_name = catalog["Игры"][idx]["name"]
        carts.setdefault(user_id, []).append(item_name)
        await query.message.reply_text(f"✅ {item_name} добавлен в корзину!")

    elif data == "back_to_catalog":
        await handle_menu(update, context)

# --- Создание приложения Telegram
app_telegram = ApplicationBuilder().token(TOKEN).build()
app_telegram.add_handler(CommandHandler("start", start))
app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))
app_telegram.add_handler(CallbackQueryHandler(button_handler))

# --- Flask route для Telegram Webhook
@app_flask.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    app_telegram.update_queue.put_nowait(update)
    return "OK"

@app_flask.route("/")
def index():
    return "Bot is running!"

# --- Установка webhook
asyncio.run(bot.set_webhook(TELEGRAM_WEBHOOK_URL))

# --- Запуск Flask
if __name__ == "__main__":
    port_str = os.environ.get("PORT")
    port = int(port_str) if port_str and port_str.isdigit() else 5000
    app_flask.run(host="0.0.0.0", port=port)
