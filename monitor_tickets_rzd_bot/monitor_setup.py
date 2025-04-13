import re
from collections import defaultdict
from const import *


def generate_paths(monitor_setup):
    paths = []

    base_path = "available"

    # Если у пользователя даже тип вагона не выбран, значит он ищет инвалидные места (а они есть только в купе)
    if monitor_setup["car_type"] is None:

        car_type_option = "['coupe']"
        seat_type_option = "['disabled']"

        return [base_path + car_type_option + seat_type_option + "['pets_whole_coupe']",
                base_path + car_type_option + seat_type_option + "['pets']"]

    else:

        # Для каждого типа вагона
        for car_type in monitor_setup["car_type"]:
            car_type_option = "['{}']".format(car_type)

            if car_type == "premium":
                seat_type_option = "['whole_coupe']"
                pets_option = "['pets_whole_coupe']"
                paths.append(base_path + car_type_option + seat_type_option + pets_option)
                continue

            for seat_type in monitor_setup["seat_type"]:
                if "side" in seat_type and car_type != "plaz":
                    continue
                if "two_storey" in seat_type and car_type == "lux":
                    continue
                else:
                    seat_type_option = "['{}']".format(seat_type)

                # Если это купе или СВ, добавляем дополнительные пути
                if car_type in ["coupe", "lux"]:
                    possible_genders = ["female", "male", "unisex", "free"]
                    for gender in possible_genders:
                        # Фильтруем по полу и условию same_gender_only
                        if monitor_setup["same_gender_only"]:
                            if monitor_setup["gender"] == "male" and gender not in ["male", "free"]:
                                continue
                            if monitor_setup["gender"] == "female" and gender not in ["female", "free"]:
                                continue
                        else:
                            if monitor_setup["gender"] == "male" and gender not in ["male", "unisex", "free"]:
                                continue
                            if monitor_setup["gender"] == "female" and gender not in ["female", "unisex", "free"]:
                                continue

                        gender_option = "['{}']".format(gender)

                        if monitor_setup["pets_allowed"] == "whatever":
                            paths.append(
                                base_path + car_type_option + seat_type_option + gender_option + "['no_pets']")
                            paths.append(
                                base_path + car_type_option + seat_type_option + gender_option + "['pets']")
                            paths.append(
                                base_path + car_type_option + seat_type_option + gender_option
                                + "['pets_whole_coupe']")
                        else:
                            pets_option = "['{}']".format(monitor_setup["pets_allowed"])
                            paths.append(
                                base_path + car_type_option + seat_type_option + gender_option + pets_option)
                            if monitor_setup["pets_allowed"] == "no_pets":
                                paths.append(
                                    base_path + car_type_option + seat_type_option + gender_option
                                    + "['pets_whole_coupe']")

                elif car_type == "plaz":
                    if monitor_setup["pets_allowed"] == "whatever":
                        paths.append(base_path + car_type_option + seat_type_option + "['no_pets']")
                        paths.append(base_path + car_type_option + seat_type_option + "['pets']")
                    else:
                        pets_option = "['{}']".format(monitor_setup["pets_allowed"])
                        paths.append(base_path + car_type_option + seat_type_option + pets_option)

        return paths


def extract_values_from_path(path):
    # Используем регулярное выражение для поиска всех значений в квадратных скобках
    values = re.findall(r"\['([^']+)']", path)
    return values


# Функция получения данных по путям
def get_data_from_paths(paths, data):
    results = []
    for path in paths:
        path_parts = extract_values_from_path(path)
        current_data = data
        for key in path_parts:
            if key.isdigit():
                key = int(key)
            current_data = current_data.get(key, {})
        if current_data.get("total", 0):
            results.append((path, current_data))
    return results


# Функция форматирования информации о местах
def format_seat_info(path, result):
    path_parts = extract_values_from_path(path)
    car_type = path_parts[0]
    seat_type = path_parts[1]

    car_type_label = CAR_TYPES[car_type]
    seat_type_label = SEAT_TYPES[seat_type]

    # Определение наличия политики провоза животных
    if path_parts[-1] in CAR_PETS:
        pets_allowed = path_parts[-1]
        pets_label = CAR_PETS[pets_allowed]
    else:
        pets_label = ""

    # Определение состава купе
    if car_type in ["coupe", "lux"] and path_parts[-2] in COUPE_GENDERS:
        coupe_gender = path_parts[-2]
        coupe_gender_label = COUPE_GENDERS[coupe_gender]
    else:
        coupe_gender_label = ""

    grouped_data = defaultdict(lambda: defaultdict(list))

    for car, seats in result.items():
        if car == 'total':
            continue
        for seat in seats:
            seat_info = ("{} ({}₽)".format(seat[0], seat[1]) if len(seat) == 2 else
                         "{} (Возвр. {} ₽ / Невозвр. {} ₽)".format(seat[0], seat[1], seat[2]))
            grouped_data[(car_type_label, seat_type_label, pets_label, coupe_gender_label)][car].append(seat_info)

    messages = []
    for (car_type_label, seat_type_label, pets_label, coupe_gender_label), cars in grouped_data.items():
        message_header = "\n\n\U0001F683 Тип вагона: {}\n\U0001F6CF Тип места: {}\n".format(car_type_label,
                                                                                            seat_type_label)
        if coupe_gender_label:
            message_header += "\U0001F6BB Состав купе: {}\n".format(coupe_gender_label)
        message_header += "\U0001F43E Провоз животных: {}\n\n".format(pets_label)

        car_messages = []
        for car, seats in sorted(cars.items(), key=lambda item: int(item[0])):
            car_message = "Вагон {}\n\u25B6  Места: {}".format(car, ", ".join(seats))
            car_messages.append(car_message)
        messages.append(message_header + "\n".join(car_messages).strip())

    return messages


def too_many_free_seats(data, max_len):
    total_sum = 0
    for _, value_dict in data:
        if "total" in value_dict:
            total_sum += value_dict["total"]
    return total_sum > max_len


# Основная функция генерации сообщений для пользователя
def generate_user_messages(user_choice, seats_data):
    paths = generate_paths(user_choice)
    data_results = get_data_from_paths(paths, seats_data)

    messages = []

    if too_many_free_seats(data_results, 15):

        too_many_free_seats_msg = "В соответствии с Вашими настройками найдено более 15 свободных мест"

        messages.append(too_many_free_seats_msg)

    else:

        for path, result in data_results:
            messages.extend(format_seat_info(path, result))

    return "".join(messages).lstrip("\n\n")


def generate_sapsan_paths(monitor_setup):
    paths = []
    base_path = "available"

    # Извлекаем данные пользователя
    car_types = monitor_setup["selected_car_types"]
    direction = monitor_setup["direction"]
    table = monitor_setup["table"]
    seat_types = monitor_setup["selected_seat_types"]

    # Возможные направления для "whatever"
    directions = ["forward", "backwards"] if direction == "whatever" else [direction]
    # Возможные варианты стола для "whatever"
    table_options = ["table", "no_table"] if table == "whatever" else [table] if table else [None]

    # Типы мест, которые не зависят от направления
    special_seat_types = ["pets", "disabled", "kids", "babies", "coupe"]

    # Описание структуры available для каждого вагона
    car_type_structures = {
        "first_class": {
            "directions": ["forward", "backwards"],
            "seat_types": {
                "forward": ["no_table", "separate"],
                "backwards": ["no_table"]
            }
        },
        "negotiation_coupe": {
            "seat_types": ["coupe"]
        },
        "business_coupe": {
            "seat_types": ["coupe"]
        },
        "business_class": {
            "directions": ["forward", "backwards"],
            "seat_types": {
                "forward": ["no_table", "table"],
                "backwards": ["no_table", "table"]
            }
        },
        "coupe_suite": {
            "seat_types": ["coupe"]
        },
        "bistro_car": {
            "directions": ["forward", "backwards"],
            "seat_types": {
                "forward": ["table"],
                "backwards": ["table"]
            }
        },
        "family": {
            "directions": ["forward"],
            "seat_types": {
                "forward": ["no_table", "table"],
                None: ["kids"]
            }
        },
        "eco_plus": {
            "directions": ["forward", "backwards"],
            "seat_types": {
                "forward": ["no_table", "table"],
                "backwards": ["no_table", "table"],
                None: ["kids", "babies"]
            }
        },
        "eco": {
            "directions": ["forward", "backwards"],
            "seat_types": {
                "forward": ["no_table", "table", "no_window"],
                "backwards": ["no_table", "table", "no_window"],
                None: ["pets", "disabled"]
            }
        },
        "base": {
            "directions": ["forward", "backwards"],
            "seat_types": {
                "forward": ["no_table", "table", "no_window"],
                "backwards": ["no_table", "table", "no_window"]
            }
        }
    }

    # Проходим по каждому выбранному типу вагона
    for car_type in car_types:
        car_type_option = "['{}']".format(car_type)
        car_structure = car_type_structures.get(car_type, {})

        # Определяем направления для вагона
        car_directions = car_structure.get("directions", [None])

        # Если у вагона нет направлений, используем только None
        applicable_directions = [None] if None in car_directions else directions

        # Обрабатываем типы мест
        seat_types_by_dir = car_structure.get("seat_types", [])
        if isinstance(seat_types_by_dir, dict):
            available_seat_types = seat_types_by_dir.get(None, [])  # Специальные места
            for dir in applicable_directions:
                if dir:
                    available_seat_types.extend(seat_types_by_dir.get(dir, []))  # Направленные места
        else:
            available_seat_types = seat_types_by_dir  # Для вагонов без направлений

        # Фильтруем выбранные типы мест
        for seat_type in seat_types:
            if seat_type not in available_seat_types:
                continue  # Пропускаем неподходящие типы мест

            # Проверяем совместимость с table
            if table == "table" and seat_type not in ["table"] and seat_type not in special_seat_types:
                continue
            if table == "no_table" and seat_type == "table":
                continue

            # Формируем путь для seat_type
            seat_type_option = "['{}']".format(seat_type)
            seats_option = "['seats']" if seat_type in special_seat_types else ""

            # Специальные места не зависят от направления
            if seat_type in special_seat_types:
                paths.append(base_path + car_type_option + seat_type_option + seats_option)
            else:
                # Направленные места
                for dir in applicable_directions:
                    if dir and dir not in car_directions:
                        continue
                    direction_option = "['{}']".format(dir) if dir else ""
                    # Учитываем "whatever" для table
                    if table == "whatever" and seat_type in ["no_table", "table"]:
                        for table_opt in table_options:
                            if (table_opt == "table" and seat_type == "no_table") or \
                               (table_opt == "no_table" and seat_type == "table"):
                                continue
                            filtered_seat_type_option = "['{}']".format(seat_type)
                            paths.append(base_path + car_type_option + direction_option + filtered_seat_type_option + seats_option)
                    else:
                        paths.append(base_path + car_type_option + direction_option + seat_type_option + seats_option)

    return list(set(paths))

def format_sapsan_seat_info(path, result):
    path_parts = extract_values_from_path(path)
    car_type = path_parts[0]
    car_type_label = SAP_CAR_TYPES[car_type]

    # Определяем направление и тип места
    direction_label = ""
    seat_type = ""
    if len(path_parts) > 1 and path_parts[1] in SAP_DIRECTIONS:
        direction_label = SAP_DIRECTIONS[path_parts[1]]
        seat_type = path_parts[2] if len(path_parts) > 2 else ""
    else:
        seat_type = path_parts[1] if len(path_parts) > 1 else ""

    seat_type_label = SAP_SEAT_TYPES.get(seat_type, "")

    grouped_data = defaultdict(lambda: defaultdict(list))

    for car, seats in result.items():
        if car == 'total':
            continue
        for seat in seats:
            seat_info = ("{} ({}₽)".format(seat[0], seat[1]) if len(seat) == 2 else
                         "{} (Возвр. {} ₽ / Невозвр. {} ₽)".format(seat[0], seat[1], seat[2]))
            grouped_data[(car_type_label, direction_label, seat_type_label)][car].append(seat_info)

    messages = []
    for (car_type_label, direction_label, seat_type_label), cars in grouped_data.items():
        message_header = "\n\n\U0001F683 Тип вагона: {}\n".format(car_type_label)
        if direction_label:
            message_header += "\U0001F66F Направление: {}\n".format(direction_label)
        message_header += "\U0001F6CF Тип места: {}\n\n".format(seat_type_label)

        car_messages = []
        for car, seats in sorted(cars.items(), key=lambda item: int(item[0])):
            car_message = "Вагон {}\n\u25B6  Места: {}".format(car, ", ".join(seats))
            car_messages.append(car_message)
        messages.append(message_header + "\n".join(car_messages).strip())

    return messages


def generate_sapsan_user_messages(user_choice, seats_data):
    paths = generate_sapsan_paths(user_choice)
    data_results = get_data_from_paths(paths, seats_data)

    messages = []

    if too_many_free_seats(data_results, 15):
        too_many_free_seats_msg = "В соответствии с Вашими настройками найдено более 15 свободных мест"
        messages.append(too_many_free_seats_msg)
    else:
        for path, result in data_results:
            messages.extend(format_sapsan_seat_info(path, result))

    return "".join(messages).lstrip("\n\n")


def generate_lastochka_paths(monitor_setup):
    paths = []
    base_path = "available"

    # Извлекаем данные пользователя
    car_types = monitor_setup["selected_car_types"]
    direction = monitor_setup["direction"]
    table = monitor_setup["table"]
    seat_types = monitor_setup["selected_seat_types"]

    # Возможные направления для "whatever"
    directions = ["forward", "backwards"] if direction == "whatever" else [direction]
    # Возможные варианты стола для "whatever"
    table_options = ["table", "no_table"] if table == "whatever" else [table] if table else [None]

    # Типы мест, которые не зависят от направления (исключаем window, no_window)
    special_seat_types = ["pets", "regular", "table", "disabled"]

    # Описание структуры available для каждого вагона
    car_type_structures = {
        "business_class": {
            "directions": ["forward", "backwards"],
            "seat_types": {
                "forward": ["no_table", "table", "window", "no_window"],
                "backwards": ["no_table", "table", "window", "no_window"],
                None: ["regular", "window", "table"]
            }
        },
        "eco": {
            "directions": ["forward", "backwards"],
            "seat_types": {
                "forward": ["no_table", "window", "no_window"],
                "backwards": ["no_table", "window", "no_window"],
                None: ["regular", "pets", "window", "no_window"]
            }
        },
        "base": {
            "directions": ["forward", "backwards"],
            "seat_types": {
                "forward": ["no_table", "window", "no_window"],
                "backwards": ["no_table", "window", "no_window"],
                None: ["regular", "window", "no_window", "disabled"]
            }
        }
    }

    # Специальная обработка для disabled
    if seat_types == ["disabled"]:
        if "base" in car_types:
            paths.append("available['base']['disabled']['seats']")
        return paths

    # Проходим по каждому выбранному типу вагона
    for car_type in car_types:
        car_type_option = "['{}']".format(car_type)
        car_structure = car_type_structures.get(car_type, {})

        # Определяем направления для вагона
        car_directions = car_structure.get("directions", [None])

        # Если у вагона нет направлений, используем только None
        applicable_directions = [None] if None in car_directions else directions

        # Обрабатываем типы мест
        seat_types_by_dir = car_structure.get("seat_types", [])
        if isinstance(seat_types_by_dir, dict):
            # Исключаем disabled, если оно не выбрано
            available_special_seats = [s for s in seat_types_by_dir.get(None, []) if
                                       s != "disabled" or "disabled" in seat_types]
            available_seat_types = available_special_seats
            for dir in applicable_directions:
                if dir:
                    available_seat_types.extend(seat_types_by_dir.get(dir, []))  # Направленные места
        else:
            available_seat_types = seat_types_by_dir  # Для вагонов без направлений

        # Фильтруем выбранные типы мест
        for seat_type in seat_types:
            if seat_type not in available_seat_types:
                continue  # Пропускаем неподходящие типы мест

            # Проверяем совместимость с table
            if table == "table" and seat_type not in ["table"] and seat_type not in special_seat_types:
                continue
            if table == "no_table" and seat_type == "table":
                continue

            # Формируем путь для seat_type
            seat_type_option = "['{}']".format(seat_type)
            seats_option = "['seats']" if seat_type in special_seat_types or seat_type in ["window",
                                                                                           "no_window"] else ""

            # Специальные места не зависят от направления
            if seat_type in special_seat_types:
                paths.append(base_path + car_type_option + seat_type_option + seats_option)
            else:
                # Направленные места, включая window и no_window
                for dir in applicable_directions:
                    if dir and dir not in car_directions:
                        continue
                    direction_option = "['{}']".format(dir) if dir else ""
                    # Учитываем "whatever" для table
                    if table == "whatever" and seat_type in ["no_table", "table"]:
                        for table_opt in table_options:
                            if (table_opt == "table" and seat_type == "no_table") or \
                                    (table_opt == "no_table" and seat_type == "table"):
                                continue
                            filtered_seat_type_option = "['{}']".format(seat_type)
                            paths.append(base_path + car_type_option + direction_option + filtered_seat_type_option)
                    else:
                        paths.append(base_path + car_type_option + direction_option + seat_type_option)

            # Добавляем специальные пути для window и no_window, если они есть в None
            if seat_type in ["window", "no_window"] and seat_type in seat_types_by_dir.get(None, []):
                paths.append(base_path + car_type_option + seat_type_option + "['seats']")

    return list(set(paths))

def format_lastochka_seat_info(path, result):
    path_parts = extract_values_from_path(path)
    car_type = path_parts[0]
    car_type_label = LASTOCHKA_CAR_TYPES.get(car_type, car_type)

    # Определяем направление и тип места
    direction_label = ""
    seat_type = ""
    if len(path_parts) > 1 and path_parts[1] in LASTOCHKA_DIRECTIONS:
        direction_label = LASTOCHKA_DIRECTIONS[path_parts[1]]
        seat_type = path_parts[2] if len(path_parts) > 2 else ""
    else:
        seat_type = path_parts[1] if len(path_parts) > 1 else ""

    seat_type_label = LASTOCHKA_SEAT_TYPES.get(seat_type, seat_type)

    grouped_data = defaultdict(lambda: defaultdict(list))

    for car, seats in result.items():
        if car == 'total':
            continue
        for seat in seats:
            seat_info = ("{} ({}₽)".format(seat[0], seat[1]) if len(seat) == 2 else
                         "{} (Возвр. {} ₽ / Невозвр. {} ₽)".format(seat[0], seat[1], seat[2]))
            grouped_data[(car_type_label, direction_label, seat_type_label)][car].append(seat_info)

    messages = []
    for (car_type_label, direction_label, seat_type_label), cars in grouped_data.items():
        message_header = "\n\n\U0001F683 Тип вагона: {}\n".format(car_type_label)
        if direction_label:
            message_header += "\U0001F66F Направление: {}\n".format(direction_label)
        message_header += "\U0001F6CF Тип места: {}\n\n".format(seat_type_label)

        car_messages = []
        for car, seats in sorted(cars.items(), key=lambda item: int(item[0])):
            car_message = "Вагон {}\n\u25B6  Места: {}".format(car, ", ".join(seats))
            car_messages.append(car_message)
        messages.append(message_header + "\n".join(car_messages).strip())

    return messages

def generate_lastochka_user_messages(user_choice, seats_data):
    paths = generate_lastochka_paths(user_choice)
    data_results = get_data_from_paths(paths, seats_data)

    messages = []

    if too_many_free_seats(data_results, 15):
        too_many_free_seats_msg = "В соответствии с Вашими настройками найдено более 15 свободных мест"
        messages.append(too_many_free_seats_msg)
    else:
        for path, result in data_results:
            messages.extend(format_lastochka_seat_info(path, result))

    return "".join(messages).lstrip("\n\n")
