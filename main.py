#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Echo Bot: just replies to Telegram messages.
"""
import os
import threading
import logging
from itertools import chain
from datetime import timedelta
from urllib.parse import urljoin
from wsgiref.simple_server import make_server

import yaml
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    # KeyboardButton,
    ReplyKeyboardMarkup,
    # Update,
)
from telegram.ext import (
    Updater,
    # CallbackContext,
    MessageHandler,
    Filters,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
)
from pyramid.config import Configurator

import config
from services import (
    IntegralProblemsService,
    RussianRulesService,
    BookCollectionService,
)


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


class HTTPServer(threading.Thread):
    def __init__(self, server_address):
        global config  # pylint: disable=global-statement

        super().__init__(daemon=True)
        self.server_address = (server_host, server_port) = server_address

        media_path = config.MEDIA_PATH
        with Configurator() as config:
            config.add_static_view(name="static", path="static")
            config.add_static_view(name="media", path=str(media_path))
            app = config.make_wsgi_app()
        self.httpd = make_server(server_host, server_port, app)

    def run(self):
        logger.info("Starting simple httpd on port %s", self.httpd.server_port)
        self.httpd.serve_forever()


HOME_STR = "\U0001F3E0"
MAIN, MATH_PROBLEMS, RUSSIAN_RULES, BOOK_COLLECTION = range(4)


class AbstractView:
    state = None

    def handlers(self):
        raise NotImplementedError

    def keyboard(self, context):
        raise NotImplementedError

    def start_command(self, update, context):
        raise NotImplementedError


class MainView(AbstractView):
    state = MAIN

    def __init__(
        self,
        integral_problems_view,
        diffeq_problems_view,
        russian_rules_view,
        book_collection_view,
    ):
        self._integral_problems_view = integral_problems_view
        self._diffeq_problems_view = diffeq_problems_view
        self._russian_rules_view = russian_rules_view
        self._book_collection_view = book_collection_view

    menu_titles = ("Integral", "Diffeq", "Russian rules", "Book collection")
    INTEGRAL, DIFFEQ, RUSSIAN_RULES, BOOK_COLLECTION = range(4)

    def handlers(self):
        mts = self.menu_titles
        return [
            MessageHandler(Filters.text(msg), handler)
            for msg, handler in [
                (mts[self.INTEGRAL], self._integral_problems_view.start_command),
                (mts[self.DIFFEQ], self._diffeq_problems_view.start_command),
                (mts[self.RUSSIAN_RULES], self._russian_rules_view.start_command),
                (mts[self.BOOK_COLLECTION], self._book_collection_view.start_command),
            ]
        ]

    def keyboard(self, context):
        mts = self.menu_titles
        return [
            [mts[self.INTEGRAL], mts[self.DIFFEQ]],
            [mts[self.RUSSIAN_RULES]],
            [mts[self.BOOK_COLLECTION]],
        ]

    def start_command(self, update, context):
        update.message.reply_text(
            "Main menu", reply_markup=ReplyKeyboardMarkup(self.keyboard(context))
        )
        return self.state


class MathProblemsView(AbstractView):
    state = MATH_PROBLEMS

    def __init__(self, math_problems_service):
        self._math_problems = math_problems_service
        self._subject_name = math_problems_service.subject_name
        self._chapter_titles_mapping = dict(
            enumerate(math_problems_service.chapter_titles)
        )

    menu_titles = ("New problem", "Set chapter", "Reset chapter", "Solve", "Theory")
    GET_PROBLEM, SET_CHAPTER, RESET_CHAPTER, SOLVE, THEORY = range(5)

    def handlers(self):
        mts = self.menu_titles
        return list(
            chain(
                [
                    MessageHandler(Filters.text(msg), handler)
                    for msg, handler in [
                        (mts[self.GET_PROBLEM], self.random_problem_command),
                        (mts[self.SET_CHAPTER], self.list_chapters_command),
                        (mts[self.RESET_CHAPTER], self.reset_chapter_command),
                        (mts[self.SOLVE], self.solve_last_problem_command),
                        (mts[self.THEORY], self.theory_for_last_problem_command),
                    ]
                ],
                [
                    CallbackQueryHandler(
                        self.set_chapter_callback,
                        pattern=r"^chapter_id: \d+$",
                        pass_user_data=True,
                    )
                ],
            )
        )

    def _view_context(self, context):
        return context.user_data.setdefault(f"math_problems.{self._subject_name}", {})

    def keyboard(self, context):
        view_context = self._view_context(context)
        chapter_is_set = view_context.get("chapter_title")
        mts = self.menu_titles
        return [
            [mts[self.GET_PROBLEM]],
            [mts[self.SET_CHAPTER] if not chapter_is_set else mts[self.RESET_CHAPTER]],
            [mts[self.SOLVE], mts[self.THEORY], HOME_STR],
        ]

    def start_command(self, update, context):
        update.message.reply_text(
            f"{self._subject_name.capitalize()} problems",
            reply_markup=ReplyKeyboardMarkup(self.keyboard(context)),
        )
        return self.state

    def list_chapters_command(self, update, context):  # pylint: disable=unused-argument
        inline_keyboard = [
            [InlineKeyboardButton(title, callback_data=f"chapter_id: {id}")]
            for id, title in self._chapter_titles_mapping.items()
        ]
        update.message.reply_text(
            "Choose chapter", reply_markup=InlineKeyboardMarkup(inline_keyboard)
        )
        return self.state

    def set_chapter_callback(self, update, context):
        query = update.callback_query
        print(query.data)
        view_context = self._view_context(context)

        query.answer()
        chapter_id = yaml.safe_load(query.data).get("chapter_id")
        chapter_title = self._chapter_titles_mapping[chapter_id]
        view_context["chapter_title"] = chapter_title

        query.message.reply_text(
            f'Selected chapter "{chapter_title}"',
            reply_markup=ReplyKeyboardMarkup(self.keyboard(context)),
        )
        return self.state

    def reset_chapter_command(self, update, context):
        view_context = self._view_context(context)
        view_context.pop("chapter_title")
        update.message.reply_text(
            "Chapter reseted", reply_markup=ReplyKeyboardMarkup(self.keyboard(context))
        )
        return self.state

    def random_problem_command(self, update, context):
        view_context = self._view_context(context)
        chapter_title = view_context.get("chapter_title")
        problem = self._math_problems.get_random_problem(chapter_title)
        view_context["last_problem"] = problem
        img = self._math_problems.get_problem_img(problem)
        update.message.reply_photo(
            img, reply_markup=ReplyKeyboardMarkup(self.keyboard(context))
        )
        return self.state

    def solve_last_problem_command(self, update, context):
        view_context = self._view_context(context)
        last_problem = view_context.get("last_problem")
        if last_problem is not None:
            solutions = self._math_problems.get_solution_sequence(last_problem)
            for caption, img in solutions:
                update.message.reply_photo(
                    img,
                    caption=caption,
                    reply_markup=ReplyKeyboardMarkup(self.keyboard(context)),
                )
        return self.state

    def theory_for_last_problem_command(self, update, context):
        view_context = self._view_context(context)
        last_problem = view_context.get("last_problem")
        pdf, title = self._math_problems.get_theory_pdf(last_problem, return_title=True)
        update.message.reply_document(
            pdf,
            f"{title}.pdf",
            reply_markup=ReplyKeyboardMarkup(self.keyboard(context)),
        )
        return self.state


class RussianRulesView(AbstractView):
    state = RUSSIAN_RULES

    def __init__(self, russian_rules_service):
        self._russian_rules = russian_rules_service

    def handlers(self):
        return [
            MessageHandler(Filters.text(part_title), self.random_paragraph_command)
            for part_title in self._russian_rules.part_titles
        ]

    def keyboard(self, context):
        part_titles = self._russian_rules.part_titles
        return list(chain([[part_title] for part_title in part_titles], [[HOME_STR]]))

    def start_command(self, update, context):
        update.message.reply_text(
            "Choose grammar part",
            reply_markup=ReplyKeyboardMarkup(self.keyboard(context)),
        )
        return self.state

    def random_paragraph_command(self, update, context):
        part_title = update.message.text
        html = self._russian_rules.get_random_paragraph_html(part_title)

        html_file_name = f"russian_rules-{update.message.chat_id}.html"
        html_file_path = config.MEDIA_PATH / html_file_name
        html_file_path.write_text(html)

        update.message.reply_text(
            urljoin(config.APP_URL, f"/media/{html_file_name}"),
            reply_markup=ReplyKeyboardMarkup(self.keyboard(context)),
        )
        return self.state


class BookCollectionView(AbstractView):
    state = BOOK_COLLECTION

    def __init__(self, book_collection_service):
        self._book_collection = book_collection_service
        self._book_titles_mapping = dict(enumerate(book_collection_service.book_titles))

    def handlers(self):
        return [CallbackQueryHandler(self.get_book_callback, pattern=r"^book_id: \d+$")]

    def keyboard(self, context):
        pass

    def start_command(self, update, context):
        inline_keyboard = [
            [InlineKeyboardButton(title, callback_data=f"book_id: {id}")]
            for id, title in self._book_titles_mapping.items()
        ]
        update.message.reply_text(
            "Select book", reply_markup=InlineKeyboardMarkup(inline_keyboard)
        )
        return self.state

    def get_book_callback(self, update, context):  # pylint: disable=unused-argument
        query = update.callback_query
        query.answer("Loading...")

        book_id = yaml.safe_load(query.data).get("book_id")
        book_title = self._book_titles_mapping[book_id]
        chapter_pdf, title_tuple = self._book_collection.get_random_book_chapter_pdf(
            book_title, return_title_tuple=True
        )
        _, _, chapter_title = title_tuple

        query.message.reply_document(
            chapter_pdf,
            filename=f"{chapter_title}.pdf",
            caption=" / ".join(filter(bool, title_tuple)),
            timeout=(5 * 60),
        )
        return  # MAIN


def create_app_handler():
    integral_problems_view = MathProblemsView(IntegralProblemsService())
    diffeq_problem_view = MathProblemsView(IntegralProblemsService())
    russian_rules_view = RussianRulesView(RussianRulesService())
    book_collection_view = BookCollectionView(BookCollectionService())
    main_view = MainView(
        integral_problems_view,
        diffeq_problem_view,
        russian_rules_view,
        book_collection_view,
    )

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", main_view.start_command)],
        states={
            view.state: view.handlers()
            for view in [
                main_view,
                integral_problems_view,
                russian_rules_view,
                book_collection_view,
            ]
        },
        fallbacks=[MessageHandler(Filters.text(HOME_STR), main_view.start_command)],
        conversation_timeout=timedelta(minutes=15),
    )
    return conv_handler


def main():
    """Starts the bot."""
    updater = Updater(config.TELEGRAM_BOT_TOKEN, use_context=True)

    # Run simple http server in background that only gives Bot's
    # home page. Original reason to run this server is to keep my
    # dyno running in Heroku.
    if "DYNO" in os.environ or True:
        server = HTTPServer(("0.0.0.0", int(os.getenv("PORT", "8080"))))
        server.start()

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add app ConversationHandler
    dispatcher.add_handler(create_app_handler())

    # Start the bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT.
    updater.idle()


if __name__ == "__main__":
    main()
