import re
from collections import defaultdict

SEAT_TYPES = {
    "lower": "Нижнее",
    "upper": "Верхнее",
    "two_storey_upper": "Верхнее на втором этаже",
    "disabled": "Для инвалидов и их сопровождающих",
    "side_lower": "Нижнее боковое",
    "side_upper": "Верхнее боковое",
    "whole_coupe": "Все купе",
}

CAR_TYPES = {
    "coupe": "Купе",
    "plaz": "Плацкарт",
    "lux": "СВ",
    "premium": "Люкс",
}

CAR_PETS = {
    "no_pets": "Запрещен",
    "pets": "Разрешен",
    "pets_whole_coupe": "Только при выкупе всего купе",
}

COUPE_GENDERS = {
    "female": "Женский",
    "male": "Мужской",
    "unisex": "Смешанный",
    "free": "Купе свободно",
}


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
        if current_data["total"]:
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
def generate_user_messages(user_choice, lel):
    paths = generate_paths(user_choice)
    data_results = get_data_from_paths(paths, lel)

    messages = []

    if too_many_free_seats(data_results, 15):

        too_many_free_seats_msg = "В соответствии с Вашими настройками найдено более 15 свободных мест"

        messages.append(too_many_free_seats_msg)

    else:

        for path, result in data_results:
            messages.extend(format_seat_info(path, result))

    return "".join(messages).lstrip("\n\n")
