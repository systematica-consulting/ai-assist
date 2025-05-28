from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from config import TOKEN
# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["Моё расписание", "Чат с ассистентом"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Выберите опцию:", reply_markup=reply_markup)

# Обработчик нажатий на кнопки
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Моё расписание":
        await update.message.reply_text("Вот твоё расписание (здесь будет расписание)")
    elif text == "Чат с ассистентом":
        keyboard = [
            ["DeepSeek", "Mistral", "Google Gemini"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Выберите нейросеть", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Пожалуйста, выбери одну из доступных опций.")

# Запуск бота
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()
