#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Echo Bot: just replies to Telegram messages.
"""
import os
import threading
import logging
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import timedelta

import wolframalpha
from sympy.parsing.latex import parse_latex
from sympy.printing.maple import maple_code
from telegram import (
        InlineKeyboardButton, InlineKeyboardMarkup,
        KeyboardButton, ReplyKeyboardMarkup,
        InputMediaDocument, InputMediaPhoto,
        Update)
from telegram.ext import (
    Updater,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext
)

import latex2png
from math_problem import (
    get_integral_subjects, get_integral_problem, get_integral_theory,
)
from joker import get_new_joke

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


class StaticHTTPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super(StaticHTTPRequestHandler, self).__init__(
            *args, directory=os.path.join(os.getcwd(), 'static'), **kwargs)


class StaticHTTPServer(threading.Thread):
    def __init__(self, server_address):
        super(StaticHTTPServer, self).__init__(daemon=True)
        self.server_address = server_address
        self.httpd = HTTPServer(self.server_address, StaticHTTPRequestHandler)

    def run(self):
        logger.info("Starting simple httpd on port %s", self.httpd.server_port)
        self.httpd.serve_forever()


def start_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Hi! Have a patience for new features.")


def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Hang on, man!")


def echo(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("%s)" % update.message.text)


def send_joke(context: CallbackContext):
    joke = get_new_joke()
    if joke is not None:
        context.bot.send_message('@Witty0Bot', joke or 'Шуток нет, но вы держитесь!')


def integral_menu(context: CallbackContext):
    subject_id = context.user_data['integral'].get('subject_id')

    keyboard = [
        [KeyboardButton("Новый пример")],
        ([KeyboardButton("Задать тему")] 
         if subject_id is None else
         [KeyboardButton('Сменить тему'), KeyboardButton("Сбросить тему")]),
        [
            KeyboardButton("Посчитать ответ"),
            KeyboardButton("Теория"),
        ],
    ]
    return keyboard


def integral_command(update: Update, context: CallbackContext) -> None:
    context.user_data.setdefault('integral', {})
    subject_id = context.user_data['integral'].get('subject_id')

    problem_subject_id, problem, integral = get_integral_problem(subject_id)
    context.user_data['integral']['last_integral'] = integral
    context.user_data['integral']['last_subject_id'] = problem_subject_id
    img = latex2png.draw_integral_problem(problem, integral)

    update.message.reply_photo(img, reply_markup=ReplyKeyboardMarkup(integral_menu(context)))


def list_subjects_command(update: Update, context: CallbackContext) -> None:
    subjects = get_integral_subjects()

    keyboard = [
        [InlineKeyboardButton(text, callback_data='set_subject=%s' % id)]
        for id, text in subjects.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text("Выбирите тему из списка:", reply_markup=reply_markup)


def set_subject(update: Update, context: CallbackContext) -> None:
    query = update.callback_query

    subject_id = context.user_data['integral']['subject_id'] = query.data.split('=')[1]

    query.answer()
    query.message.reply_text(f'Выбрана тема: "{get_integral_subjects()[subject_id]}"',
                             reply_markup=ReplyKeyboardMarkup(integral_menu(context)))


def reset_subject_command(update: Update, context: CallbackContext) -> None:
    context.user_data['integral']['subject_id'] = None
    update.message.reply_text('Тема сброшена', reply_markup=ReplyKeyboardMarkup(integral_menu(context)))


def answer_command(update: Update, context: CallbackContext) -> None:
    last_integral = context.user_data['integral']['last_integral']
    integral_latex = last_integral.split('$')[1]
    last_subject_id = context.user_data['integral']['last_subject_id']
    subject = get_integral_subjects()[last_subject_id]
    integral = parse_latex(integral_latex)

    update.message.reply_text(f"*Тема:* _{subject}_", parse_mode='markdown')
    wa_client = wolframalpha.Client('2X5EWE-VU2QXULHQJ')
    logger.info(f'integrate {maple_code(integral.function)} d{integral.free_symbols}')
    res = wa_client.query(f'integrate {maple_code(integral.function)} d{integral.free_symbols}')
    for pod in res.results:
        try:
            update.message.reply_photo(next(next(pod.subpod).img).src,
                                       caption='_WolframAlpha:_ %s' % pod.title, parse_mode='markdown')
        except:
            continue


def theory_command(update: Update, context: CallbackContext) -> None:
    last_subject_id = context.user_data['integral']['last_subject_id']
    doc = get_integral_theory(last_subject_id)

    update.message.reply_document(doc.open('rb'), reply_markup=ReplyKeyboardMarkup(integral_menu(context)))


def main():
    """Starts the bot."""
    updater = Updater("1664508454:AAGwZ1rSk55nNFeYNvwYv-39k2AWGTJKXBg",
                      use_context=True)

    # Run simple http server in background that only gives Bot's
    # home page. Original reason to run this server is to keep my
    # dyno running in Heroku.
    server = StaticHTTPServer(('0.0.0.0', int(os.getenv('PORT', 80))))
    server.start()

    job_queue = updater.job_queue

    job_queue.run_repeating(send_joke, timedelta(hours=1), 0)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler('start', start_command))
    dispatcher.add_handler(CommandHandler('help', help_command))

    # on noncommand i.e message - echo the message on Telegram
    # dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Setup conversation handler for integral command.
    # After it was called following options are awailable: next integral, show answer, theory help.
    dispatcher.add_handler(MessageHandler(Filters.text(['/integral', 'Новый пример']), integral_command))
    dispatcher.add_handler(MessageHandler(Filters.text(['/list_subjects', 'Задать тему', 'Сменить тему']),
                                          list_subjects_command))
    dispatcher.add_handler(MessageHandler(Filters.text(['/reset_subject', 'Сбросить тему']), reset_subject_command))
    dispatcher.add_handler(CallbackQueryHandler(set_subject, pattern='^set_subject=\S*$'))
    dispatcher.add_handler(MessageHandler(Filters.text(['/answer', 'Посчитать ответ']), answer_command))
    dispatcher.add_handler(MessageHandler(Filters.text(['/theory', 'Теория']), theory_command))

    # Start the bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT.
    updater.idle()


if __name__ == '__main__':
    main()
