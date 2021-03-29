import logging
from queue import Queue
from threading import Thread

import requests
from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.view import view_config
from telegram import Bot, Update
from telegram.ext import Dispatcher, Updater

import config
from coordinators import MainCoordinator

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def populate_with_handlers(dispatcher):
    main_coordinator = MainCoordinator()
    dispatcher.add_handler(main_coordinator.conv_handler)


def disable_webhook_mode():
    token = config.TELEGRAM_BOT_TOKEN
    r = requests.get(f'https://api.telegram.org/bot{token}/setWebhook')
    print(r.json())


def enable_webhook_mode():
    base_url = config.APP_BASE_URL
    token = config.TELEGRAM_BOT_TOKEN
    webhook_url = f'{base_url}/{token}'
    r = requests.get(
        f'https://api.telegram.org/bot{token}/setWebhook?url={webhook_url}'
    )
    print(r.json())


def run_webhook_handler_mode():
    enable_webhook_mode()

    bot = Bot(config.TELEGRAM_BOT_TOKEN)
    update_queue = Queue()
    dispatcher = Dispatcher(bot, update_queue)

    populate_with_handlers(dispatcher)

    thread = Thread(target=dispatcher.start, name='dispatcher')
    thread.start()

    @view_config(route_name='bot_webhook')
    def handle_webhook(request):  # pylint: disable=unused-variable
        update = Update.de_json(request.json_body, bot)
        update_queue.put(update)
        return Response()


def run_update_poller_mode():
    disable_webhook_mode()

    updater = Updater(config.TELEGRAM_BOT_TOKEN)
    dispatcher = updater.dispatcher

    populate_with_handlers(dispatcher)

    updater.start_polling()
    updater.idle()


with Configurator() as cfg:
    cfg.add_static_view(name="static", path="static")
    cfg.add_static_view(name="media", path=str(config.MEDIA_PATH))
    cfg.add_route('bot_webhook', f'/{config.TELEGRAM_BOT_TOKEN}')
    app = cfg.make_wsgi_app()

if __name__ == '__main__':

    def run_http_server():
        from wsgiref.simple_server import make_server
        with make_server('localhost', 8080, app) as httpd:
            httpd.serve_forever()

    wsgi_thread = Thread(target=run_http_server)
    wsgi_thread.start()
    run_update_poller_mode()
    wsgi_thread.join()
else:
    run_webhook_handler_mode()
