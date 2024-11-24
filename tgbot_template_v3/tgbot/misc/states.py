from aiogram.fsm.state import StatesGroup, State


class Train(StatesGroup):
    main_menu = State()
    train_menu = State()
    delete_train = State()
    confirm_delete_train = State()
    train_menu_start = State()
    confirm_start = State()
    select_destination = State()
    confirm_destination = State()
    select_date = State()
    confirm_route = State()
    select_train = State()
    confirm_train = State()


class Monitor(StatesGroup):
    monitor_menu = State()
    delete_monitor = State()
    confirm_delete_monitor = State()
    add_train_to_monitor = State()
    confirm_train_to_monitor = State()
    select_car_type = State()
    confirm_car_type = State()
    select_gender = State()
    confirm_gender = State()
    ask_same_gender = State()
    confirm_same_gender = State()
    pets_allowed = State()
    confirm_pets_allowed = State()
    select_seat_type = State()
    confirm_seat_type = State()
    confirm_monitor_setup = State()
