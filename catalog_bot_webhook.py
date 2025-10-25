from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# --- Конфигурация
TOKEN = "8272770257:AAHCYt5GKjdaweaTI3frG-tWzItJK8OGSIs"
ADMIN_ID = 181269564

# --- Каталог
catalog = {
    "Игры": [
        {"name": "Игра Уличный гонщик", "description": "Захватывающее приключение с отличной графикой и сюжетом.", "photo": "game1.jpeg", "price": 100},
        {"name": "Игра Mortal Kombat (PS5)", "description": "Лучшая игра жанре драк", "photo": "game3.jpeg", "price": 250},
        {"name": "Игра Ведьмак 3. Дикая охота (PS5)", "description": "Лcomplete edition для PlayStation 5, русская озвучка", "photo": "game4.jpeg", "price": 250},
        {"name": "Игра Dishonored 2", "description": "Сложная стратегия, где решает каждый ход.", "photo": "game2.jpeg", "price": 200},
    ]
}

# --- Хранилище данных
carts = {}
orders = {}
order_info = {}

# --- Глобальный счетчик заказов
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

# --- Старт / главное меню
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выберите раздел:", reply_markup=main_menu)

# --- Обработка текстовых кнопок
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global global_order_number
    text = update.message.text
    user_id = update.message.from_user.id

    # --- Каталог игр
    if text == "Каталог игр":
        category = "Игры"
        keyboard = [[InlineKeyboardButton(f"{item['name']} — {item['price']}р", callback_data=f"item_{item['name']}")] for item in catalog[category]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f"Каталог {category}:", reply_markup=reply_markup)

    # --- Просмотр корзины
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

    # --- Оформление заказа
    elif text == "Оформить заказ":
        cart_items = carts.get(user_id, [])
        if not cart_items:
            await update.message.reply_text("Ваша корзина пуста.", reply_markup=main_menu)
            return
        await update.message.reply_text(
            "Введите данные для оформления заказа в одном сообщении:\n\n"
            "телефон: <ваш телефон>\n"
            "имя: <ваше имя>\n"
            "адрес: <адрес доставки>\n\n"
            "Пример:\n+7 123 456 78 90\nИван Иванов\nул. Ленина 10",
            reply_markup=main_menu
        )

    # --- Мои заказы
    elif text == "Мои заказы":
        user_orders = orders.get(user_id, [])
        user_infos = order_info.get(user_id, [])
        if not user_orders:
            await update.message.reply_text("📦 У вас пока нет заказов.", reply_markup=main_menu)
            return

        text_orders = "📦 Мои заказы:\n"
        for idx, order_dict in enumerate(user_orders):
            order_number = order_dict["order_number"]
            items = order_dict["items"]
            text_orders += f"\nЗаказ {order_number}:\n"
            order_total = sum(next(it['price'] for it in catalog["Игры"] if it['name']==name) for name in items)
            for name in items:
                price = next(it['price'] for it in catalog["Игры"] if it['name']==name)
                text_orders += f"- {name} — {price}р\n"
            text_orders += f"💰 Итого: {order_total}р\n"

            if idx < len(user_infos):
                info = user_infos[idx]
                text_orders += f"📞 Телефон: {info['phone']}\n👤 Имя: {info['name']}\n🏠 Адрес: {info['address']}\n"

        await update.message.reply_text(text_orders, reply_markup=main_menu)

    # --- FAQ
    elif text == "❓ Часто задаваемые вопросы":
        keyboard = [
            [InlineKeyboardButton("💳 Способы оплаты", callback_data="faq_payment")],
            [InlineKeyboardButton("🚚 Доставка", callback_data="faq_delivery")],
            [InlineKeyboardButton("ℹ️ О нас", callback_data="faq_about")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Выберите вопрос:", reply_markup=reply_markup)

    # --- Обработка ввода заказа (три строки)
    elif "\n" in text:
        lines = text.strip().split("\n")
        if len(lines) != 3:
            await update.message.reply_text(
                "Неверный формат. Введите три строки: телефон, имя, адрес",
                reply_markup=main_menu
            )
            return

        phone, name, address = [line.strip() for line in lines]
        cart_items = carts.get(user_id, [])
        if not cart_items:
            await update.message.reply_text("Ваша корзина пуста.", reply_markup=main_menu)
            return

        # Увеличиваем глобальный номер заказа
        global_order_number += 1
        order_number = global_order_number

        # Сохраняем заказ как словарь с глобальным номером
        orders.setdefault(user_id, []).append({
            "order_number": order_number,
            "items": cart_items.copy()
        })
        order_info.setdefault(user_id, []).append({
            "phone": phone,
            "name": name,
            "address": address
        })
        carts[user_id] = []

        total = sum(next(it['price'] for it in catalog["Игры"] if it['name']==name) for name in cart_items)
        text_order = f"✅ Ваш заказ оформлен! Номер заказа: {order_number}\n"
        for i in cart_items:
            price = next(it['price'] for it in catalog["Игры"] if it['name']==i)
            text_order += f"- {i} — {price}р\n"
        text_order += f"💰 Итого: {total}р\n📞 {phone}\n👤 {name}\n🏠 {address}"
        await update.message.reply_text(text_order, reply_markup=main_menu)

    else:
        await update.message.reply_text("Пожалуйста, выберите раздел из меню ниже 👇", reply_markup=main_menu)

# --- Inline-кнопки
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    # FAQ
    if data == "faq_payment":
        await query.message.reply_text("💳 *Способы оплаты:*\n\nМы принимаем оплату банковской картой или наличными при получении.", parse_mode="Markdown")
    elif data == "faq_delivery":
        await query.message.reply_text("🚚 *Доставка:*\n\nДоставка в черте города производится на следующий день после оформления заказа.", parse_mode="Markdown")
    elif data == "faq_about":
        await query.message.reply_text("ℹ️ *О нас:*\n\nУ нас лучшие условия для покупки игр онлайн!", parse_mode="Markdown")
    elif data == "back_main":
        await query.message.reply_text("Выберите раздел:", reply_markup=main_menu)
        return

    # Каталог
    elif data.startswith("item_"):
        item_name = data.split("_", 1)[1]
        item = next((i for i in catalog["Игры"] if i["name"] == item_name), None)
        if not item:
            await query.message.reply_text("Игра не найдена.")
            return

        keyboard = [
            [InlineKeyboardButton("Назад к каталогу", callback_data="back_to_catalog")],
            [InlineKeyboardButton("Добавить в корзину", callback_data=f"add_{item_name}")],
            [InlineKeyboardButton("Просмотр корзины", callback_data="view_cart")],
            [InlineKeyboardButton("Оформить заказ", callback_data="checkout")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        with open(item["photo"], "rb") as f:
            await query.message.reply_photo(photo=f, caption=f"🎮 {item['name']} — {item['price']}р\n\n{item['description']}", reply_markup=reply_markup)

    # Добавление в корзину
    elif data.startswith("add_"):
        item_name = data.split("_", 1)[1]
        carts.setdefault(user_id, []).append(item_name)
        await query.message.reply_text(f"✅ {item_name} добавлен в корзину!")

    # Просмотр корзины
    elif data == "view_cart":
        cart_items = carts.get(user_id, [])
        if not cart_items:
            await query.message.reply_text("🛒 Ваша корзина пуста.", reply_markup=main_menu)
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
        await query.message.reply_text(text_cart, reply_markup=reply_markup)

    # Удаление из корзины
    elif data.startswith("remove_"):
        item_name = data.split("_", 1)[1]
        if user_id in carts and item_name in carts[user_id]:
            carts[user_id].remove(item_name)
            await query.message.reply_text(f"❌ {item_name} удален из корзины.")
        else:
            await query.message.reply_text(f"{item_name} не найден в вашей корзине.")

    # Оформить заказ через кнопку
    elif data == "checkout":
        await query.message.reply_text(
            "Введите данные для оформления заказа в одном сообщении:\n\n"
            "телефон: <ваш телефон>\n"
            "имя: <ваше имя>\n"
            "адрес: <адрес доставки>\n\n"
            "Пример:\n+7 123 456 78 90\nИван Иванов\nул. Ленина 10",
            reply_markup=main_menu
        )

    # Назад к каталогу
    elif data == "back_to_catalog":
        category = "Игры"
        keyboard = [[InlineKeyboardButton(f"{item['name']} — {item['price']}р", callback_data=f"item_{item['name']}")] for item in catalog[category]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(f"Каталог {category}:", reply_markup=reply_markup)

# --- Запуск
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # Настройка webhook для Telegram
    url = f"https://<твое_имя_проекта>.onrender.com/{TOKEN}"
    bot.set_webhook(url)
    print(f"Webhook установлен на {url}")
    app.run(host="0.0.0.0", port=port)
