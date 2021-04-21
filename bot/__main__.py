from telegram.ext import Updater

from . import config, disable_webhook_mode
from .handlers import populate_dispatcher


def main() -> None:
    updater = Updater(config.TELEGRAM_BOT_TOKEN)
    dispatcher = updater.dispatcher  # type: ignore

    populate_dispatcher(dispatcher)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    disable_webhook_mode()
    main()
