#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

import logging
import re
import sqlite3
from asyncio import sleep

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
    await update.message.reply_text("AddSpam сообщение - добавление шаблона спама(заменяете сообщение на спам шаблон)",
                                    "\nShowSpam - показать существующие шаблоны",
                                    "\nDeleteSpam соообщение - удаляет шаблон спама из базы данных(так же как с AddSpam)")


async def add_spam_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(update.message.text[9:]) <=5:
        await update.message.delete()
        message = await update.message.reply_text("Длина шаблона меньше 5 символов, используйте другой шаблон для добавления.")
        await sleep(5)
        await message.delete()
    else:
        try:
            sqlite_connection = sqlite3.connect('spam.db')
            cursor = sqlite_connection.cursor()
            cursor.execute("INSERT INTO SpamExamples (SpamTemplate) VALUES (?)", (update.message.text[9:],))
            sqlite_connection.commit()
            cursor.close()
            await update.message.delete()
            message = await update.message.reply_text("Шаблон спама добавлен.")
            await sleep(5)
            await message.delete()
        except sqlite3.Error as error:
            print("Ошибка при добавлении шаблона спама в базу данных", error)
        finally:
            if sqlite_connection:
                sqlite_connection.close()


async def delete_spam_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        sqlite_connection = sqlite3.connect('spam.db')
        cursor = sqlite_connection.cursor()
        cursor.execute("DELETE FROM SpamExamples WHERE SpamTemplate=?", (update.message.text[9:],))
        sqlite_connection.commit()
        cursor.close()
        await update.message.delete()
        message = await update.message.reply_text("Шаблон спама удален.")
        await sleep(5)
        await message.delete()
    except sqlite3.Error as error:
        print("Ошибка при удалении шаблона спама из базы данных", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()



async def show_spam_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        sqlite_connection = sqlite3.connect('spam.db')
        cursor = sqlite_connection.cursor()

        sqlite_select_query = """SELECT SpamTemplate FROM SpamExamples"""
        cursor.execute(sqlite_select_query)
        records = cursor.fetchall()
        spam_list = [row[0] for row in records]
        await update.message.reply_text('\n'.join(spam_list))

        cursor.close()

    except sqlite3.Error as error:
        print("Ошибка при работе с SQLite", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()


async def delete_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.text.startswith('/ShowSpam'):
        return  # Если сообщение начинается с команды ShowSpam, выходим из функции
    try:
        sqlite_connection = sqlite3.connect('spam.db')
        cursor = sqlite_connection.cursor()
        cursor.execute("SELECT SpamTemplate FROM SpamExamples")
        records = cursor.fetchall()
        spam_list = [row[0] for row in records]
        for spam in spam_list:
            words = spam.split()
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
    except sqlite3.Error as error:
        print("Ошибка при работе с SQLite", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token("").build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("AddSpam", add_spam_command))
    application.add_handler(CommandHandler("ShowSpam", show_spam_command))
    application.add_handler(CommandHandler("DeleteSpam", delete_spam_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, delete_message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

