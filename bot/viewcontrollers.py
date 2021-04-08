import io
from itertools import chain
from urllib.parse import urljoin

import requests
import yaml
from telegram import (  # Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)
from telegram.ext import (  # CallbackContext,
    CallbackQueryHandler,
    Filters,
    MessageHandler,
)

from . import config

HOME_STR = "\U0001F3E0"


class AbstractInlineDialogue:
    def handlers(self):
        raise NotImplementedError

    def start_dialogue_command(self, update, context):
        raise NotImplementedError


class RussianRulesInlineDialogue(AbstractInlineDialogue):
    def __init__(self, russian_rules_service):
        self._russian_rules = russian_rules_service
        self._russian_rules_part_titles = dict(
            enumerate(self._russian_rules.part_titles)
        )

    def handlers(self):
        return [
            CallbackQueryHandler(
                self.paragraph_callback,
                pattern=r"^russian_rules.part_id: \d+$"
            )
        ]

    def start_dialogue_command(self, update, context):
        inline_keyboard = [[
            InlineKeyboardButton(
                title, callback_data=f"russian_rules.part_id: {id}"
            )
        ] for id, title in self._russian_rules_part_titles.items()]
        update.message.reply_text(
            "Выберите раздел правил",
            reply_markup=InlineKeyboardMarkup(inline_keyboard),
        )

    def paragraph_callback(self, update, context):  # pylint: disable=unused-argument
        query = update.callback_query
        query.answer("Загрузка...")

        part_id = yaml.safe_load(query.data).get("russian_rules.part_id")
        part_title = self._russian_rules_part_titles[part_id]
        chapter_title, html = (
            self._russian_rules.get_random_paragraph_html(
                part_title, return_chapter_title=True
            )
        )

        chat_id = update.effective_message.chat_id
        html_file_name = f"russian_rules-{chat_id}.html"
        html_file_url = urljoin(
            config.APP_BASE_URL, f"{config.MEDIA_URL}/{html_file_name}"
        )
        requests.post(html_file_url, files={'file': io.StringIO(html)})
        print(f'URL for {chapter_title}:', html_file_url)

        query.message.reply_text(
            f'<a href="{html_file_url}">{chapter_title}</a>',
            parse_mode="HTML",
        )


class BookCollectionInlineDialogue(AbstractInlineDialogue):
    def __init__(self, book_collection_service):
        self._book_collection = book_collection_service
        self._book_titles_mapping = dict(
            enumerate(book_collection_service.book_titles)
        )

    def handlers(self):
        return [
            CallbackQueryHandler(
                self.get_book_callback, pattern=r"^book_id: \d+$"
            )
        ]

    def start_dialogue_command(self, update, context):
        inline_keyboard = [[
            InlineKeyboardButton(title, callback_data=f"book_id: {id}")
        ] for id, title in self._book_titles_mapping.items()]
        update.message.reply_text(
            "Выберите книгу",
            reply_markup=InlineKeyboardMarkup(inline_keyboard)
        )

    def get_book_callback(self, update, context):  # pylint: disable=unused-argument
        query = update.callback_query
        query.answer("Загрузка...")

        book_id = yaml.safe_load(query.data).get("book_id")
        book_title = self._book_titles_mapping[book_id]
        chapter_pdf, title_tuple = (
            self._book_collection.get_random_book_chapter_pdf(
                book_title, return_title_tuple=True
            )
        )
        _, _, chapter_title = title_tuple

        query.message.reply_document(
            chapter_pdf,
            filename=f"{chapter_title}.pdf",
            caption=" / ".join(filter(bool, title_tuple)),
            timeout=(5 * 60),
        )


class AbstractViewController:
    def handlers(self):
        raise NotImplementedError

    def keyboard(self, context):
        raise NotImplementedError

    def start_command(self, update, context):
        raise NotImplementedError


class MainViewController(AbstractViewController):
    def __init__(
        self, delegate, russian_rules_service, book_collection_service
    ):
        self.delegate = delegate
        self._russian_rules_dialogue = RussianRulesInlineDialogue(
            russian_rules_service
        )
        self._book_collection_dialogue = BookCollectionInlineDialogue(
            book_collection_service
        )

    menu_titles = ("Integral", "Russian rules", "Book collection")
    INTEGRAL, RUSSIAN_RULES, BOOK_COLLECTION = range(3)

    def handlers(self):
        mts = self.menu_titles
        handlers = [
            MessageHandler(Filters.text(msg), conv_handler)
            for msg, conv_handler in [
                (mts[self.INTEGRAL], self.integral_command),
                (
                    mts[self.RUSSIAN_RULES],
                    self._russian_rules_dialogue.start_dialogue_command
                ),
                (
                    mts[self.BOOK_COLLECTION],
                    self._book_collection_dialogue.start_dialogue_command
                ),
            ]
        ]
        handlers.extend(self._russian_rules_dialogue.handlers())
        handlers.extend(self._book_collection_dialogue.handlers())
        return handlers

    def keyboard(self, context):
        mts = self.menu_titles
        return [
            [mts[self.INTEGRAL]],
            [mts[self.RUSSIAN_RULES]],
            [mts[self.BOOK_COLLECTION]],
        ]

    def start_command(self, update, context):
        update.message.reply_text(
            "Main menu",
            reply_markup=ReplyKeyboardMarkup(self.keyboard(context))
        )

    def integral_command(self, update, context):
        return self.delegate.integral_handler(update, context)


class MathProblemsViewController(AbstractViewController):
    def __init__(self, delegate, math_problems_service):
        self.delegate = delegate
        self._math_problems = math_problems_service
        self._subject_name = math_problems_service.subject_name
        self._chapter_titles_mapping = dict(
            enumerate(math_problems_service.chapter_titles)
        )

    menu_titles = (
        "New problem", "Set chapter", "Reset chapter", "Solve", "Theory"
    )
    GET_PROBLEM, SET_CHAPTER, RESET_CHAPTER, SOLVE, THEORY = range(5)

    def handlers(self):
        mts = self.menu_titles
        return list(
            chain([
                MessageHandler(Filters.text(msg), conv_handler)
                for msg, conv_handler in [
                    (mts[self.GET_PROBLEM], self.random_problem_command),
                    (mts[self.SET_CHAPTER], self.list_chapters_command),
                    (mts[self.RESET_CHAPTER], self.reset_chapter_command),
                    (mts[self.SOLVE], self.solve_last_problem_command),
                    (mts[self.THEORY], self.theory_for_last_problem_command),
                    (HOME_STR, self.end_command),
                ]
            ], [
                CallbackQueryHandler(
                    self.set_chapter_callback,
                    pattern=r"^chapter_id: \d+$",
                    pass_user_data=True
                )
            ])
        )

    def _viewcontroller_context(self, context):
        return context.user_data.setdefault(
            f"math_problems.{hash(self._subject_name)}", {}
        )

    def keyboard(self, context):
        viewcontroller_context = self._viewcontroller_context(context)
        chapter_is_set = viewcontroller_context.get("chapter_title")
        mts = self.menu_titles
        return [
            [mts[self.GET_PROBLEM]],
            [
                mts[self.SET_CHAPTER]
                if not chapter_is_set else mts[self.RESET_CHAPTER]
            ],
            [mts[self.SOLVE], mts[self.THEORY], HOME_STR],
        ]

    def start_command(self, update, context):
        update.message.reply_text(
            f"{self._subject_name.capitalize()} problems",
            reply_markup=ReplyKeyboardMarkup(self.keyboard(context)),
        )

    def end_command(self, update, context):
        return self.delegate.end_handler(update, context)

    def list_chapters_command(self, update, context):  # pylint: disable=unused-argument
        inline_keyboard = [[
            InlineKeyboardButton(title, callback_data=f"chapter_id: {id}")
        ] for id, title in self._chapter_titles_mapping.items()]
        update.message.reply_text(
            "Choose chapter",
            reply_markup=InlineKeyboardMarkup(inline_keyboard)
        )

    def set_chapter_callback(self, update, context):
        query = update.callback_query
        print(query.data)
        viewcontroller_context = self._viewcontroller_context(context)

        query.answer()
        chapter_id = yaml.safe_load(query.data).get("chapter_id")
        chapter_title = self._chapter_titles_mapping[chapter_id]
        viewcontroller_context["chapter_title"] = chapter_title

        query.message.reply_text(
            f'Selected chapter "{chapter_title}"',
            reply_markup=ReplyKeyboardMarkup(self.keyboard(context)),
        )

    def reset_chapter_command(self, update, context):
        viewcontroller_context = self._viewcontroller_context(context)
        viewcontroller_context.pop("chapter_title")
        update.message.reply_text(
            "Chapter reseted",
            reply_markup=ReplyKeyboardMarkup(self.keyboard(context))
        )

    def random_problem_command(self, update, context):
        viewcontroller_context = self._viewcontroller_context(context)
        chapter_title = viewcontroller_context.get("chapter_title")
        problem = self._math_problems.get_random_problem(chapter_title)
        viewcontroller_context["last_problem"] = problem
        img = self._math_problems.get_problem_img(problem)
        update.message.reply_photo(
            img, reply_markup=ReplyKeyboardMarkup(self.keyboard(context))
        )

    def solve_last_problem_command(self, update, context):
        viewcontroller_context = self._viewcontroller_context(context)
        last_problem = viewcontroller_context.get("last_problem")
        if last_problem is not None:
            solutions = (
                self._math_problems.get_solution_sequence(last_problem)
            )

            for title, img in solutions:
                update.message.reply_photo(
                    img,
                    caption=f"_WolframAlpha:_ {title}",
                    parse_mode="MarkdownV2",
                    reply_markup=ReplyKeyboardMarkup(self.keyboard(context)),
                )

    def theory_for_last_problem_command(self, update, context):
        viewcontroller_context = self._viewcontroller_context(context)
        last_problem = viewcontroller_context.get("last_problem")
        pdf, title = self._math_problems.get_theory_pdf(
            last_problem, return_title=True
        )
        update.message.reply_document(
            pdf,
            f"{title}.pdf",
            reply_markup=ReplyKeyboardMarkup(self.keyboard(context)),
        )
