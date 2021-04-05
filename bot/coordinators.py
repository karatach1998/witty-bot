from datetime import timedelta
from itertools import chain

from telegram.ext import CommandHandler, ConversationHandler  # CallbackContext,

from .services import (
    BookCollectionService,
    IntegralProblemsService,
    RussianRulesService,
)
from .viewcontrollers import MainViewController, MathProblemsViewController


class AbstractCoordinator:
    viewcontroller = None

    def iter_children(self):
        raise NotImplementedError

    def handlers(self):
        return self.viewcontroller.handlers()

    def start(self, update, context):
        self.viewcontroller.start_command(update, context)
        return self


class MainCoordinator(AbstractCoordinator):
    def __init__(self):
        russian_rules_service = RussianRulesService()
        book_collection_service = BookCollectionService()
        self.viewcontroller = MainViewController(
            self, russian_rules_service, book_collection_service
        )

        self._integral_coordinator = IntegralCoordinator(self)

    def iter_children(self):
        return chain((self,), self._integral_coordinator.iter_children())

    @property
    def conv_handler(self):
        return ConversationHandler(
            entry_points=[CommandHandler("start", self.start)],
            states={coord: coord.handlers()
                    for coord in self.iter_children()},
            fallbacks=[],
            conversation_timeout=timedelta(minutes=15),
        )

    def integral_handler(self, update, context):
        return self._integral_coordinator.start(update, context)


class IntegralCoordinator(AbstractCoordinator):
    def __init__(self, parent):
        self.parent = parent
        integral_problems_service = IntegralProblemsService()
        self.viewcontroller = MathProblemsViewController(
            self, integral_problems_service
        )

    def iter_children(self):
        return (self,)

    def end_handler(self, update, context):
        return self.parent.start(update, context)
