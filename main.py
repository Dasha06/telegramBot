#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

import logging
import re

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")

async def add_spam_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    with open('spam.txt', 'a') as file:
        file.write("\n"+update.message.text[9:])
    await update.message.reply_text("Шаблон спама добавлен.")


async def delete_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    with open('spam.txt', 'r') as file:
        spam_list = file.read().splitlines()  # Читаем файл и разбиваем на строки
        for spam in spam_list:
            # Создаем регулярное выражение для проверки с учетом лишних слов
            pattern = re.sub(r'\\s+', r'\\s*', re.escape(spam))  # Заменяем пробелы на пробелы с возможными лишними словами
            if re.search(pattern, update.message.text, re.IGNORECASE):  # Проверяем, есть ли спам в сообщении
                await update.message.delete()
                chat_id = update.message.chat.id  # Исправлено: chat_id
                user_id = update.message.from_user.id if update.message.from_user else None
                await context.bot.ban_chat_member(chat_id, user_id)
                break  # Выходим из цикла после нахождения спама


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token("<YOUR-TOKEN>").build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("AddSpam", add_spam_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT, delete_message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

