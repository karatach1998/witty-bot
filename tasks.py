import os

from celery import Celery
from telegram import Bot, Update
from telegram.ext import Dispatcher

import config
from handlers import populate_dispatcher

bot = Bot(config.TELEGRAM_BOT_TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

populate_dispatcher(dispatcher)

celery = Celery('bot', broker=os.getenv('CLOUDAMQP_URL'))


@celery.task
def handle_webhook(data):
    update = Update.de_json(data, bot)
    dispatcher.process_update(update)
