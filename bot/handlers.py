from telegram.ext import Dispatcher

from .coordinators import MainCoordinator


def populate_dispatcher(dispatcher: Dispatcher) -> None:
    main_coordinator = MainCoordinator()
    dispatcher.add_handler(main_coordinator.conv_handler)
