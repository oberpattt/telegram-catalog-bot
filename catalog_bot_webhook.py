import os
import asyncio
from flask import Flask, request
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# --- Конфигурация
TOKEN = "8272770257:AAHCYt5GKjdaweaTI3frG-tWzItJK8OGSIs"
bot = Bot(token=TOKEN)
app_flask = Flask(__name__)

# --- Публичный URL Render
PUBLIC_URL = "https://oberpat.onrender.com"  # <-- Убедись, что это твой реальный Render URL
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

# --- Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎮 Добро пожаловать! Выберите раздел:", reply_markup=main_menu)

# --- Меню
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id

    if text == "Каталог игр":
        keyboard = [
            [InlineKeyboardButton(f"{item['name']} — {item['price']}₽", callback_data=f"item_{item['name']}")]
            for item in catalog["Игры"]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Выберите игру:", reply_markup=reply_markup)

    elif text == "Просмотр корзины":
        cart_items = carts.get(user_id, [])
        if not cart_items:
            await update.message.reply_text("🛒 Ваша корзина пуста.", reply_markup=main_menu)
            return

        total = sum(next((g["price"] for g in catalog["Игры"] if g["name"] == item), 0) for item in cart_items)
        msg = "🛒 Ваша корзина:\n" + "\n".join(f"- {i}" for i in cart_items) + f"\n\n💰 Итого: {total}₽"
        keyboard = [
            [InlineKeyboardButton("❌ Очистить корзину", callback_data="clear_cart")],
            [InlineKeyboardButton("Оформить заказ", callback_data="checkout")]
        ]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

    elif text == "Оформить заказ":
        await update.message.reply_text("Введите данные для оформления заказа:\n📞 Телефон\n🏠 Адрес")

    else:
        await update.message.reply_text("Выберите пункт меню ниже 👇", reply_markup=main_menu)

# --- Обработка нажатий Inline-кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data.startswith("item_"):
        item_name = data.split("_", 1)[1]
        item = next((i for i in catalog["Игры"] if i["name"] == item_name), None)
        if item:
            keyboard = [
                [InlineKeyboardButton("🛒 Добавить в корзину", callback_data=f"add_{item_name}")],
                [InlineKeyboardButton("⬅ Назад к каталогу", callback_data="back_to_catalog")]
            ]
            with open(item["photo"], "rb") as f:
                await query.message.reply_photo(
                    photo=f,
                    caption=f"🎮 {item['name']}\n\n{item['description']}\n💰 Цена: {item['price']}₽",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )

    elif data.startswith("add_"):
        item_name = data.split("_", 1)[1]
        carts.setdefault(user_id, []).append(item_name)
        await query.message.reply_text(f"✅ {item_name} добавлен в корзину!")

    elif data == "back_to_catalog":
        keyboard = [
            [InlineKeyboardButton(f"{item['name']} — {item['price']}₽", callback_data=f"item_{item['name']}")]
            for item in catalog["Игры"]
        ]
        await query.message.reply_text("Выберите игру:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "clear_cart":
        carts[user_id] = []
        await query.message.reply_text("🧹 Корзина очищена.", reply_markup=main_menu)

    elif data == "checkout":
        await query.message.reply_text("Введите ваши контактные данные для оформления заказа.")

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

# --- Проверка работы сервера
@app_flask.route("/")
def index():
    return "✅ Bot is running on Render!"

# --- Установка webhook
asyncio.run(bot.set_webhook(TELEGRAM_WEBHOOK_URL))

# --- Запуск Flask
if __name__ == "__main__":
    port_str = os.environ.get("PORT")
    port = int(port_str) if port_str and port_str.isdigit() else 5000
    app_flask.run(host="0.0.0.0", port=port)
