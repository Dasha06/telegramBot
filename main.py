#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

import logging
import re
from asyncio import sleep  # Добавьте этот импорт

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
    await update.message.reply_text("AddSpam <сообщение> - добавление шаблона спама\n ShowSpam - показать существующие шаблоны")

async def add_spam_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    with open('spam.txt', 'a') as file:
        file.write("\n"+update.message.text[9:])
    await update.message.delete()
    message = await update.message.reply_text("Шаблон спама добавлен.")
    await sleep(5)
    await message.delete()

async def show_spam_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    with open('spam.txt', 'r') as file:
        spam_list = file.read().splitlines()
        await update.message.reply_text('\n'.join(spam_list))

async def delete_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.text.startswith('/ShowSpam'):
        return  # Если сообщение начинается с команды ShowSpam, выходим из функции
    with open('spam.txt', 'r') as file:
        spam_list = file.read().splitlines()
        for spam in spam_list:
            words = spam.split()
            pattern = '|'.join([re.escape(word) for word in words])  # Создаем шаблон из отдельных слов, игнорируя регистр
            if all(re.search(word, update.message.text, re.IGNORECASE) for word in words):
                await update.message.delete()
                chat_id = update.message.chat.id
                user_id = update.message.from_user.id if update.message.from_user else None
                try:
                    await context.bot.ban_chat_member(chat_id, user_id)
                except Exception as e:
                    print(f"Ошибка: {e}")
                print('забан')
                break


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token("").build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("AddSpam", add_spam_command))
    application.add_handler(CommandHandler("ShowSpam", show_spam_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, delete_message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

