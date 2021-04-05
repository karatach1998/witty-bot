from .coordinators import MainCoordinator


def populate_dispatcher(dispatcher):
    main_coordinator = MainCoordinator()
    dispatcher.add_handler(main_coordinator.conv_handler)
