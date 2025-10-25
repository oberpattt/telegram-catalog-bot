import os
import asyncio
from flask import Flask, request
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# --- Конфигурация
TOKEN = "8272770257:AAHCYt5GKjdaweaTI3frG-tWzItJK8OGSIs"
PUBLIC_URL = "https://oberpat.onrender.com"
TELEGRAM_WEBHOOK_URL = f"{PUBLIC_URL}/{TOKEN}"

bot = Bot(token=TOKEN)
app_flask = Flask(__name__)

# --- Каталог
catalog = {
    "Игры": [
        {"name": "Игра Уличный гонщик", "description": "Захватывающее приключение с отличной графикой и сюжетом.", "photo": "game1.jpeg", "price": 100},
        {"name": "Игра Mortal Kombat (PS5)", "description": "Лучшая игра жанре драк", "photo": "game3.jpeg", "price": 250},
        {"name": "Игра Ведьмак 3. Дикая охота (PS5)", "description": "Полное издание для PS5, русская озвучка", "photo": "game4.jpeg", "price": 250},
        {"name": "Игра Dishonored 2", "description": "Сложная стратегия, где решает каждый ход.", "photo": "game2.jpeg", "price": 200},
    ]
}

carts = {}
main_menu = ReplyKeyboardMarkup(
    [
        [KeyboardButton("Каталог игр")],
        [KeyboardButton("Просмотр корзины"), KeyboardButton("Оформить заказ")],
        [KeyboardButton("Мои заказы")],
        [KeyboardButton("❓ Часто задаваемые вопросы")]
    ],
    resize_keyboard=True
)

# --- Обработчики
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выберите раздел:", reply_markup=main_menu)

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id

    if text == "Каталог игр":
        category = "Игры"
        keyboard = [[InlineKeyboardButton(f"{item['name']} — {item['price']}р", callback_data=f"item_{item['name']}")] for item in catalog[category]]
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
    else:
        await update.message.reply_text("Выберите пункт из меню 👇", reply_markup=main_menu)

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
                [InlineKeyboardButton("Назад к каталогу", callback_data="back_to_catalog")],
                [InlineKeyboardButton("Добавить в корзину", callback_data=f"add_{item_name}")],
                [InlineKeyboardButton("Просмотр корзины", callback_data="view_cart")],
                [InlineKeyboardButton("Оформить заказ", callback_data="checkout")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            with open(item["photo"], "rb") as f:
                await query.message.reply_photo(
                    photo=f,
                    caption=f"🎮 {item['name']} — {item['price']}р\n{item['description']}",
                    reply_markup=reply_markup
                )
    elif data.startswith("add_"):
        item_name = data.split("_", 1)[1]
        carts.setdefault(user_id, []).append(item_name)
        await query.message.reply_text(f"✅ {item_name} добавлен в корзину!")

# --- Telegram Application
app_telegram = Application.builder().token(TOKEN).build()
app_telegram.add_handler(CommandHandler("start", start))
app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))
app_telegram.add_handler(CallbackQueryHandler(button_handler))

# --- Flask маршруты
@app_flask.route("/")
def index():
    return "Bot is running!"

@app_flask.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update_data = request.get_json(force=True)
    update = Update.de_json(update_data, bot)
    asyncio.create_task(app_telegram.process_update(update))  # ✅ <-- вот ключевая замена!
    return "OK", 200

# --- Устанавливаем вебхук при запуске
async def set_webhook():
    await bot.set_webhook(TELEGRAM_WEBHOOK_URL)
asyncio.run(set_webhook())

# --- Запускаем Flask
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app_flask.run(host="0.0.0.0", port=port)
