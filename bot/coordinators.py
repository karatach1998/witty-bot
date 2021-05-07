from __future__ import annotations

from datetime import timedelta
from itertools import chain
from typing import Iterable, List

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, ConversationHandler, Handler

from .services import (
    BookCollectionService,
    EnglishGrammarService,
    IntegralProblemsService,
    RussianRulesService,
)
from .viewcontrollers import (
    AbstractViewController,
    MainViewController,
    MathProblemsViewController,
)


class AbstractCoordinator:
    viewcontroller: AbstractViewController

    def iter_children(self) -> Iterable[AbstractCoordinator]:
        raise NotImplementedError

    def handlers(self) -> List[Handler[Update]]:
        return self.viewcontroller.handlers()

    def start(
        self, update: Update, context: CallbackContext
    ) -> AbstractCoordinator:
        self.viewcontroller.start_command(update, context)
        return self


class MainCoordinator(AbstractCoordinator):
    def __init__(self) -> None:
        russian_rules_service = RussianRulesService()
        english_grammar_service = EnglishGrammarService()
        book_collection_service = BookCollectionService()
        self.viewcontroller = MainViewController(
            self, russian_rules_service, english_grammar_service,
            book_collection_service
        )

        self._integral_coordinator = IntegralCoordinator(self)

    def iter_children(self) -> Iterable[AbstractCoordinator]:
        return chain((self,), self._integral_coordinator.iter_children())

    @property
    def conv_handler(self) -> ConversationHandler:
        return ConversationHandler(
            entry_points=[CommandHandler("start", self.start)],
            states={coord: coord.handlers()
                    for coord in self.iter_children()},
            fallbacks=[],
            conversation_timeout=timedelta(minutes=15),  # type: ignore
        )

    def integral_handler(
        self, update: Update, context: CallbackContext
    ) -> AbstractCoordinator:
        return self._integral_coordinator.start(update, context)


class ChildCoordinator(AbstractCoordinator):
    def __init__(self, parent: AbstractCoordinator) -> None:
        self.parent = parent

    def iter_children(self) -> Iterable[AbstractCoordinator]:
        return (self,)

    def end_handler(
        self, update: Update, context: CallbackContext
    ) -> AbstractCoordinator:
        return self.parent.start(update, context)


class IntegralCoordinator(ChildCoordinator):
    def __init__(self, parent: AbstractCoordinator) -> None:
        super().__init__(parent)
        integral_problems_service = IntegralProblemsService()
        self.viewcontroller = MathProblemsViewController(
            self, integral_problems_service
        )
