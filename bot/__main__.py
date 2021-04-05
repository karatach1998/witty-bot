from telegram.ext import Updater

from . import config, disable_webhook_mode, populate_dispatcher


def main():
    updater = Updater(config.TELEGRAM_BOT_TOKEN)
    dispatcher = updater.dispatcher

    populate_dispatcher(dispatcher)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    disable_webhook_mode()
    main()
