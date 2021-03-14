#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Echo Bot: just replies to Telegram messages.
"""
import logging
import os
import threading
from wsgiref.simple_server import make_server

from pyramid.config import Configurator
from telegram.ext import Updater  # CallbackContext,

import config
from coordinators import MainCoordinator

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


class HTTPServer(threading.Thread):
    def __init__(self, server_address):
        super().__init__(daemon=True)
        self.server_address = (server_host, server_port) = server_address

        with Configurator() as cfg:
            cfg.add_static_view(name="static", path="static")
            cfg.add_static_view(name="media", path=str(config.MEDIA_PATH))
            main_coordinator = cfg.make_wsgi_app()
        self.httpd = make_server(server_host, server_port, main_coordinator)

    def run(self):
        logger.info("Starting simple httpd on port %s", self.httpd.server_port)
        self.httpd.serve_forever()


def main():
    """Starts the bot."""
    updater = Updater(config.TELEGRAM_BOT_TOKEN, use_context=True)

    # Run simple http server in background that only gives Bot's
    # home page. Original reason to run this server is to keep my
    # dyno running in Heroku.
    if "DYNO" in os.environ:
        server = HTTPServer(("0.0.0.0", int(os.getenv("PORT", "8080"))))
        server.start()

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    main_coordinator = MainCoordinator()

    # Add main_coordinator's ConversationHandler
    dispatcher.add_handler(main_coordinator.conv_handler)

    # Start the bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT.
    updater.idle()


if __name__ == "__main__":
    main()
