from datetime import datetime, timedelta
import traceback
from venv import logger
import caldav
from caldav.elements import dav, cdav
import psycopg2
import logging


from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from config import TOKEN
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


# Обработчик команды /start
user_states = {}
locationurl = {}
login = {}
password = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["Моё расписание", "Чат с ассистентом"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Выберите опцию:", reply_markup=reply_markup)
def user_exists(tg_id: str) -> bool:
    try:
        conn = psycopg2.connect(
            dbname="test",
            user="postgres",
            password="max11skv",
            host="localhost",  # или IP-адрес вашего сервера
            port="5432"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE tg_id = %s", (tg_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result is not None
    except Exception as e:
        print(f"Ошибка при подключении к базе: {str(e)}\n{traceback.format_exc()}")
        return False


async def get_events(update: Update, context: ContextTypes.DEFAULT_TYPE,  locationurl: str, login: str, password: str):
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) requested events")
    CALDAV_URL=locationurl
    try:
        logger.info(f"Connecting to CalDAV server at {CALDAV_URL}")

        # Create CalDAV client
        client = caldav.DAVClient(
            url=locationurl,
            username=login,
            password=password
        )

        logger.info("Authenticating and getting principal")
        principal = client.principal()

        logger.info("Getting calendar home")
        calendar_home = principal.calendar_home_set

        logger.info("Getting calendars")
        calendars = calendar_home.calendars()

        if not calendars:
            await update.message.reply_text("Календари не найдены")
            return

        logger.info(f"Found {len(calendars)} calendars")

        all_events = []

        # Get events from all calendars
        for calendar in calendars:
            calendar_name = calendar.name or "Без названия"
            logger.info(f"Processing calendar: {calendar_name}")

            try:
                # Get events from today to next 30 days
                start_date = datetime.now()
                end_date = start_date + timedelta(days=30)

                logger.debug(f"Searching events from {start_date} to {end_date}")
                events = calendar.date_search(start=start_date, end=end_date)

                logger.info(f"Found {len(events)} events in calendar {calendar_name}")

                for event in events:
                    try:
                        event_data = event.data
                        logger.debug(f"Processing event data: {event_data[:200]}...")

                        # Parse iCalendar data
                        import icalendar
                        cal = icalendar.Calendar.from_ical(event_data)

                        for component in cal.walk():
                            if component.name == "VEVENT":
                                summary = component.get('summary', 'Без названия')
                                dtstart = component.get('dtstart')
                                dtend = component.get('dtend')
                                description = component.get('description', '')

                                if dtstart:
                                    if hasattr(dtstart.dt, 'strftime'):
                                        start_time = dtstart.dt.strftime('%d.%m.%Y %H:%M')
                                    else:
                                        start_time = str(dtstart.dt)
                                else:
                                    start_time = 'Время не указано'

                                event_text = f"📅 {summary}\n📆 {start_time}"
                                if description:
                                    event_text += f"\n📝 {description[:100]}{'...' if len(str(description)) > 100 else ''}"

                                all_events.append(event_text)

                    except Exception as e:
                        logger.error(f"Error processing individual event: {str(e)}")
                        continue

            except Exception as e:
                logger.error(f"Error processing calendar {calendar_name}: {str(e)}")
                continue

        if all_events:
            # Sort events and limit to 10
            all_events = all_events[:10]
            message = f"📅 Найдено событий: {len(all_events)}\n\n" + "\n\n".join(all_events)
            await update.message.reply_text(message)
        else:
            await update.message.reply_text("События не найдены в указанном периоде")
    except caldav.lib.error.AuthorizationError as e:
        logger.error(f"CalDAV authorization error: {str(e)}")
        await update.message.reply_text("Ошибка авторизации CalDAV")
    except Exception as e:
        logger.error(f"Error connecting to CalDAV: {str(e)}", exc_info=True)

def save_user_credentials(tg_id: str, locationurl: str, login: str, password: str):
    try:
        conn = psycopg2.connect(
            dbname="test",
            user="postgres",
            password="max11skv",
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()


        # Добавление, если не найден

        cursor.execute("UPDATE users SET url = %s, login = %s , password = %s WHERE tg_id = %s", (locationurl,login,password, tg_id))
        conn.commit()
        print(f"Пользователь {tg_id,locationurl,login,password} добавлен в базу.")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Ошибка работы с базой данных: {e}")
async def ask_for_location_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.message.from_user.id
    user_states[tg_id] = "waiting_for_location_url"
    await update.message.reply_text("Пожалуйста, отправьте ссылку в формате https://...")


def add_user_if_not_exists(tg_id, username: str):
    try:
        conn = psycopg2.connect(
            dbname="test",
            user="postgres",
            password="max11skv",
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()

        # Проверка существования
        cursor.execute("SELECT 1 FROM users WHERE tg_id = %s", (tg_id,))
        result = cursor.fetchone()

        # Добавление, если не найден
        if result is None:
            cursor.execute("INSERT INTO users (tg_id, tgname) VALUES (%s,%s)", (tg_id,username))
            conn.commit()
            print(f"Пользователь {tg_id, username} добавлен в базу.")

        else:
            print(f"Пользователь {tg_id, username} уже есть в базе.")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Ошибка работы с базой данных: {e}")


# Обработчик нажатий на кнопки
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.from_user.username
    tg_id = update.message.from_user.id
    text = update.message.text
    if text == "Моё расписание":
        if not username:
            await update.message.reply_text("У вас не задан username в Telegram. Установите его в настройках профиля.")
            return

        if user_exists(tg_id):
            await update.message.reply_text("Вы уже зарегистрированы. Вот ваше расписание 📅")
        else:
            add_user_if_not_exists(tg_id, username)
            await update.message.reply_text("Вы были успешно зарегистрированы! ✅")
        await ask_for_location_url(update, context)
        return

    elif user_states.get(tg_id) == "waiting_for_location_url":

        await update.message.reply_text(f"Спасибо! Вы отправили ссылку:\n{text}")
        locationurl[tg_id]=text
        user_states.pop(tg_id)
        await update.message.reply_text('Введите Login')
        user_states[tg_id]='Login'
    elif user_states.get(tg_id) == "Login":
        await update.message.reply_text('Введите Password')
        login[tg_id]=text
        user_states[tg_id] = 'Password'
    elif user_states.get(tg_id) == "Password":
        password[tg_id]=text
        save_user_credentials(tg_id, locationurl[tg_id], login[tg_id], password[tg_id])
        await get_events(update, context, locationurl[tg_id], login[tg_id], password[tg_id])

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



if user_exists("ivan_telegram"):
    print("Пользователь найден в базе")
else:
    print("Такого пользователя нет")