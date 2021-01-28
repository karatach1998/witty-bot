#!/usr/bin/env python

"""
Echo Bot: just replies to Telegram messages.
"""

from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext


def start_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Hi! Have a patience for new features.")


def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Hang on, man!")


def echo(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("%s)" % update.message.text)


def main():
    """Starts the bot."""
    updater = Updater("1664508454:AAGwZ1rSk55nNFeYNvwYv-39k2AWGTJKXBg", use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # on noncommand i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Start the bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT.
    updater.idle()


if __name__ == '__main__':
    main()
