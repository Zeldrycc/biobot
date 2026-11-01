import json
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from dotenv import load_dotenv
load_dotenv()

# Укажите ваш токен от @BotFather
TOKEN = os.environ.get("TOKEN")

DATA_FILE = "users_data.json"

# Константы для 5 шагов анкеты
COLOR, SCHOOL, AGE, CITY, BIO = range(5)


# --- Работа с JSON ---
async def load_data() -> dict:
  """Асинхронная загрузка данных пользователей из JSON-файла."""
  if not os.path.exists(DATA_FILE):
    return {}
  try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
      return json.load(f)
  except Exception:
    return {}


async def save_data(data: dict) -> None:
  """Асинхронное сохранение данных пользователей в JSON-файл."""
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)


# --- Клавиатура ---
def get_main_keyboard() -> InlineKeyboardMarkup:
  """Создание инлайн-кнопок."""
  return InlineKeyboardMarkup([
      [
          InlineKeyboardButton("🆘 Помощь", callback_data="help"),
          InlineKeyboardButton("👤 Профиль", callback_data="profile"),
      ],
      [InlineKeyboardButton("💾 Сохранить данные", callback_data="save_data")],
  ])


# --- Обработчики команд ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = update.effective_user
  user_id = str(user.id)
  data = await load_data()

  if user_id not in data:
    data[user_id] = {
        "username": user.username,
        "first_name": user.first_name,
        "bio": {},
    }
    await save_data(data)

  await update.message.reply_text(
      f"Привет, {user.first_name}! Я бот-биография. Заполни свою анкету с"
      " помощью кнопки ниже:",
      reply_markup=get_main_keyboard(),
  )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text(
      "📖 **Справка по боту:**\n\n"
      "/start — Запустить бота\n"
      "/help — Показать эту справку\n"
      "/cancel — Отменить заполнение анкеты\n\n"
      "Используйте инлайн-кнопки ниже для управления:",
      reply_markup=get_main_keyboard(),
      parse_mode="Markdown",
  )


# --- Обработчики инлайн-кнопок (Помощь и Профиль) ---
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()

  if query.data == "help":
    await query.edit_message_text(
        "🆘 Вы зашли в раздел помощи. Используйте кнопки для навигации.",
        reply_markup=get_main_keyboard(),
    )

  elif query.data == "profile":
    user_id = str(query.from_user.id)
    data = await load_data()
    user_info = data.get(user_id, {})
    bio = user_info.get("bio", {})

    profile_text = (
        "👤 **Ваша анкета (биография):**\n\n"
        f"🆔 **User ID:** `{query.from_user.id}`\n"
        f"📛 **Имя:** {query.from_user.first_name}\n"
        f"🎨 **Любимый цвет:** {bio.get('color', 'Не указано')}\n"
        f"🏫 **Школа/Училище:** {bio.get('school', 'Не указано')}\n"
        f"🎂 **Возраст:** {bio.get('age', 'Не указано')}\n"
        f"🏙️ **Город:** {bio.get('city', 'Не указано')}\n"
        f"✍️ **О себе:** {bio.get('about', 'Не указано')}"
    )

    await query.edit_message_text(
        profile_text, reply_markup=get_main_keyboard(), parse_mode="Markdown"
    )


# --- 5-шаговая цепочка опроса (ConversationHandler) ---


async def save_data_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  """Шаг 0: Нажатие кнопки 'Сохранить данные'"""
  query = update.callback_query
  await query.answer()
  await query.message.reply_text(
      "🎨 **Шаг 1 из 5**\nНапишите свой **любимый цвет**:", parse_mode="Markdown"
  )
  return COLOR


async def receive_color(update: Update, context: ContextTypes.DEFAULT_TYPE):
  """Шаг 1: Сохраняем цвет $\rightarrow$ Переход к школе"""
  context.user_data["color"] = update.message.text
  await update.message.reply_text(
      "🏫 **Шаг 2 из 5**\nУкажите вашу **школу / училище / университет**:",
      parse_mode="Markdown",
  )
  return SCHOOL


async def receive_school(update: Update, context: ContextTypes.DEFAULT_TYPE):
  """Шаг 2: Сохраняем школу $\rightarrow$ Переход к возрасту"""
  context.user_data["school"] = update.message.text
  await update.message.reply_text(
      "🎂 **Шаг 3 из 5**\nУкажите ваш **возраст**:", parse_mode="Markdown"
  )
  return AGE


async def receive_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
  """Шаг 3: Сохраняем возраст $\rightarrow$ Переход к городу"""
  context.user_data["age"] = update.message.text
  await update.message.reply_text(
      "🏙️ **Шаг 4 из 5**\nВ каком **городе** вы живете?", parse_mode="Markdown"
  )
  return CITY


async def receive_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
  """Шаг 4: Сохраняем город $\rightarrow$ Переход к блоке 'о себе'"""
  context.user_data["city"] = update.message.text
  await update.message.reply_text(
      "✍️ **Шаг 5 из 5**\nНапишите пару слов **о себе**:", parse_mode="Markdown"
  )
  return BIO


async def receive_bio_and_save(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  """Шаг 5: Сохраняем 'о себе' и записываем всю структуру в JSON"""
  user = update.effective_user
  user_id = str(user.id)

  user_bio = {
      "color": context.user_data.get("color"),
      "school": context.user_data.get("school"),
      "age": context.user_data.get("age"),
      "city": context.user_data.get("city"),
      "about": update.message.text,
  }

  data = await load_data()
  if user_id not in data:
    data[user_id] = {}

  data[user_id]["username"] = user.username
  data[user_id]["first_name"] = user.first_name
  data[user_id]["bio"] = user_bio

  await save_data(data)

  await update.message.reply_text(
      "✅ Ваша анкета-биография успешно сохранена! Посмотреть ее можно через"
      " кнопку «Профиль».",
      reply_markup=get_main_keyboard(),
  )
  return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
  """Отмена заполнения анкеты"""
  await update.message.reply_text(
      "❌ Заполнение анкеты отменено.", reply_markup=get_main_keyboard()
  )
  return ConversationHandler.END


# --- Запуск приложения ---
def main():
  application = Application.builder().token(TOKEN).build()

  # Настройка ConversationHandler для строго последовательных шагов
  conv_handler = ConversationHandler(
      entry_points=[CallbackQueryHandler(save_data_start, pattern="^save_data$")],
      states={
          COLOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_color)],
          SCHOOL: [
              MessageHandler(filters.TEXT & ~filters.COMMAND, receive_school)
          ],
          AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_age)],
          CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_city)],
          BIO: [
              MessageHandler(
                  filters.TEXT & ~filters.COMMAND, receive_bio_and_save
              )
          ],
      },
      fallbacks=[CommandHandler("cancel", cancel)],
  )

  # Регистрация обработчиков
  application.add_handler(CommandHandler("start", start))
  application.add_handler(CommandHandler("help", help_command))
  application.add_handler(conv_handler)
  application.add_handler(
      CallbackQueryHandler(button_callback, pattern="^(help|profile)$")
  )

  print("Бот-биография запущен и готов к работе...")
  application.run_polling()


if __name__ == "__main__":
  main()