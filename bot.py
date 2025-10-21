import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL")  # "@username_канала" или numeric id вида -100xxxxxxxxxx
ADMINS = os.getenv("@CHANNEL")    # опционально: список id через запятую; если пусто — публиковать может любой

if not BOT_TOKEN or not CHANNEL:
    raise RuntimeError("Не заданы BOT_TOKEN или CHANNEL в переменных окружения")

ADMIN_SET = set()
if ADMINS:
    try:
        ADMIN_SET = {int(x.strip()) for x in ADMINS.split(",") if x.strip()}
    except Exception:
        pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Привет! Пришли текст/фото/видео/аудио.\n"
        "Потом нажми «Опубликовать», и я отправлю это в канал."
    )
    if ADMIN_SET:
        text += "\n(Публиковать по кнопке могут только админы.)"
    await update.message.reply_text(text)

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return
    cb_data = f"PUB|{msg.chat_id}|{msg.message_id}"
    keyboard = [[
        InlineKeyboardButton("✅ Опубликовать", callback_data=cb_data),
        InlineKeyboardButton("❌ Отменить", callback_data="CANCEL")
    ]]
    await msg.reply_text(
        "Отправить это в канал?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data.startswith("PUB|"):
        if ADMIN_SET and query.from_user and query.from_user.id not in ADMIN_SET:
            await query.edit_message_text("Недостаточно прав для публикации.")
            return
        try:
            _, from_chat_id, message_id = data.split("|")
            from_chat_id = int(from_chat_id)
            message_id = int(message_id)
            await context.bot.copy_message(
                chat_id=CHANNEL,
                from_chat_id=from_chat_id,
                message_id=message_id
            )
            await query.edit_message_text("Опубликовано в канал ✅")
        except Exception as e:
            await query.edit_message_text(f"Не удалось опубликовать: {e}")

    elif data == "CANCEL":
        await query.edit_message_text("Отменено ❌")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, on_message))
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
