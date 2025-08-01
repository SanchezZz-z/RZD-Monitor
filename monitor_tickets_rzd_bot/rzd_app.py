import asyncio
import json
import locale
from datetime import datetime
import pytz

import httpx
import string
import random
import urllib3

from monitor_tickets_rzd_bot.seats_counter_new import remove_non_digits
from monitor_tickets_rzd_bot.seats_counter_new import TrainSeatsCounter, Lasto4kaSeatsCounter, SapsanSeatsCounter

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Явно зададим русскую локаль, чтобы дни недели в функции get_train печатались на русском языке
locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")

# Функция для определения бренда поезда вручную по номеру поезда и его маршруту
# Это необходимо так как в случаях, когда билеты на Сапсан и Ласточку полностью распроданы, API возвращает такие поезда
# с пустым полем brand и они попадают в обычные (Скорые и пассажирские) поезда

# 701-746 и 801-846 это Ласточки
# 747 и 748 + МСК - СПб это Невский Экспресс
# 741 - 744 + МСК - СПб это Аврора
# 751 - 785 (мб и больше) + МСК - СПб это Сапсаны

# 2006004 - Москва Октябрьская (Ленинградский Вокзал)
# 2004001 - Санкт-Петербург-Главн. (Московский Вокзал)

def train_brand_manual(train_data):
    train_num = int(remove_non_digits(train_data["number"]))        # Номер поезда
    train_route_start = int(train_data["code0"])                    # Код станции отправления (начальная станция поезда, а не станция отправления пользователя)
    train_route_end = int(train_data["code1"])                      # Код станции прибытия (конечной станции поезда)
    if train_num in range(701, 747) or train_num in range(801, 847):
        if (((train_route_start == 2006004 and train_route_end == 2004001) or
             (train_route_start == 2004001 and train_route_end == 2006004)) and train_num in range(741, 745)):
            return "Аврора"
        else:
            return "Ласточка"
    elif (((train_route_start == 2006004 and train_route_end == 2004001) or
             (train_route_start == 2004001 and train_route_end == 2006004)) and train_num in [747, 748]):
        return "Невский экспресс"
    elif (((train_route_start == 2006004 and train_route_end == 2004001) or
             (train_route_start == 2004001 and train_route_end == 2006004)) and train_num in range(751, 791)):
        return "Сапсан"
    else:
        return "Скорые и пассажирские"


# Функция для "красивого" формата даты
def format_date(date_string):
    start_date = date_string
    date_format = "%d.%m.%Y"
    date_obj = datetime.strptime(start_date, date_format)
    formatted_date = date_obj.strftime("%a %d.%m.%Y").capitalize()
    return formatted_date


def hash_code_gen(size=40, chars=string.ascii_lowercase + string.digits):
    return "".join(random.choice(chars) for _ in range(size))


def device_guid_gen(size=32, chars=string.ascii_uppercase + string.digits):
    return "".join(random.choice(chars) for _ in range(size))


async def get_info_with_rid(rid, device_guid, hashcode, url):
    headers = {
        "Host": "ekmp-i-47-2.rzd.ru",
        "Content-Type": "application/json",
        "Connection": "keep-alive",
        "Accept": "*/*",
        "User-Agent": "RZD/2367 CFNetwork/1568.300.101 Darwin/24.2.0",
        "Accept-Language": "ru",
        "Accept-Encoding": "gzip, deflate, br"
    }

    data_req = {
        "rid": "{}".format(rid),
        "deviceGuid": "{}".format(device_guid),
        "platform": "IOS",
	    "version": "1.47.2(2367)",
        "hashCode": "{}".format(hashcode),
        "protocolVersion": 47
    }

    # Отправляем запрос
    async with httpx.AsyncClient(verify=False) as client:
        res = await client.post(url=url, headers=headers, json=data_req, timeout=10, follow_redirects=True)

        if res.status_code != 200:
            print("Response Code: {}".format(res.status_code))

        return res.json()


async def get_train(origin, destination, date):
    # Каждый запрос в приложении включает в себя hashCode. Методом проб и ошибок выяснено, что hashCode может быть любым
    # набором символов. Самое главное, чтобы один hashCode всегда использовался в паре с одним rid.

    # Перед каждым поисковым запросом в приложении осуществляется запрос на получение rid (resultid).
    # rid содержит в себе все необходимые данные по поисковому запросу (станции, дату и тд).

    # Сперва напишем функцию, генерирующую случайный набор букв и цифр. Длина hashCode в любом запросе равна 40.

    hashcode = hash_code_gen()
    device_guid = device_guid_gen()

    # Готовим запрос на получение информации по поездам в нужную дату.

    url = "https://ekmp-i-47-2.rzd.ru/v3.0/timetable/search"

    headers = {
        "Host": "ekmp-i-47-2.rzd.ru",
        "Content-Type": "application/json",
        "User-Agent": "RZD/2367 CFNetwork/1568.300.101 Darwin/24.2.0",
        "Accept-Language": "ru",
        "Accept-Encoding": "gzip, deflate, br"
    }

    data_req = {
        "dir": 0,
        "language": "ru",
        "deviceGuid": "{}".format(device_guid),
        "code0": "{}".format(origin),
        "code1": "{}".format(destination),
        "dt0": "{}".format(date),
        "platform": "IOS",
        "version": "1.47.2(2367)",
        "timezone": "+0300",
        "tfl": 3,
        "responseVersion": 2,
        "protocolVersion": 47,
        "hashCode": "{}".format(hashcode)
    }

    # Отправляем запрос
    async with httpx.AsyncClient(verify=False) as client:
        res = await client.post(url=url, headers=headers, content=json.dumps(data_req, ensure_ascii=False), timeout=10)

        if res.status_code != 200:
            print("Response Code: {}".format(res.status_code))
        else:
            data_res = res.json()

        rid = data_res["result"]["rid"]

        # Для большинства станций достаточно сделать всего один запрос, чтобы по полученному rid получить список
        # поездов, но я заметил, что для поиска по маршруту СПб-МСК и наоборот на сервер несколько раз отправляются
        # запросы с полученным rid и, таким образом, он обновляется несколько раз, следовательно, запрос с самым
        # первым rid будет выдавать ошибку. Для этого был добавлен while loop, чтобы в случае ошибки отправить
        # столько запросов, сколько понадобится. Чтобы loop не завис навсегда, добавлено максимальное количество
        # попыток.

        data_res = await get_info_with_rid(rid, device_guid, hashcode, url)

        attempts = 0

        while "timetables" not in data_res["result"].keys() and attempts < 11:
            await asyncio.sleep(0.5)
            moscow_spb_rid = data_res["result"]["rid"]
            data_res = await get_info_with_rid(rid, device_guid, hashcode, url)
            attempts += 1

    # Список с номерами поездов, которые возвращает API (эти номера отличаются от тех, которые показываются на сайте)
    train_nums_data = {
        "Сапсан": [],
        "Ласточка": [],
        "Скорые и пассажирские": []
    }

    # Список с информацией по каждому поезду
    train_list_data = {
        "Сапсан": [],
        "Ласточка": [],
        "Скорые и пассажирские": []
    }

    # Список с датой и временем отправления каждого поезда (по МСК)
    departure_times_data = {
        "Сапсан": [],
        "Ласточка": [],
        "Скорые и пассажирские": []
    }

    # Список с двухаэтажностью
    is_two_storey_data = {
        "Сапсан": [],
        "Ласточка": [],
        "Скорые и пассажирские": []
    }

    # Инициализация словаря для нумерации (для порядка отображения поездов)
    train_order_counter = {}

    # Установим часовой пояс
    moscow_tz = pytz.timezone("Europe/Moscow")

    # Чтобы не выводить лишние поезда (которые уже отправились) введем проверку на время
    time_check = datetime.now(moscow_tz)

    for train in range(len(data_res["result"]["timetables"][0]["list"])):

        train_info = data_res["result"]["timetables"][0]["list"][train]

        # Строка с датой отправления по московскому времени (так как бот будет на сервере, на котором московское время)
        # date0 и time0 возвращают дату и время по МСК для всех поездов
        date_str = (train_info["date0"] + " " + train_info["time0"])

        # Переводим строку в объект datetime, чтобы сравнить с текущим временем
        departure_date = datetime.strptime(date_str, "%d.%m.%Y %H:%M").replace(tzinfo=moscow_tz)

        # Оставляем только те поезда, которые еще не отправились, и убираем пригородные электрички (у них среди прочих
        # есть параметр subt, равный 1, который отсутствует у поездов дальнего следования)
        if departure_date > time_check and "subt" not in train_info:

            # Определяем бренд поезда вручную (причина выше в начале скрипта)
            brand = train_brand_manual(train_info)
            if brand == "Ласточка":
                category = "Ласточка"
            elif brand == "Сапсан":
                category = "Сапсан"
            else:
                category = "Скорые и пассажирские"

            if category not in train_order_counter:
                train_order_counter[category] = 1  # Отдельный счётчик для каждой категории

            train_order = train_order_counter[category]  # Получить текущий номер для категории

            # Добавляем номер поезда, который возвращает API
            train_nums_data[category].append(train_info["number"])

            # Добавляем дату и время отправления (по Москве)
            departure_times_data[category].append(departure_date)

            # Добавляем запись о двухэтажности
            is_two_storey_data[category].append("двухэтажный" in brand or "аврора" in brand)

            travel_time = "\U000023F3 "

            # Часы и минуты в пути
            hours, minutes = map(int, train_info["timeInWay"].split(":"))

            # Меняем окончания, чтобы читалось нормально
            # Если вдруг меньше часа
            if not hours:

                travel_time += ""

            elif hours == 1 or (hours % 10 == 1 and hours > 20):

                travel_time += "{} час{} ".format(hours, "")

            elif hours in range(2, 5) or (hours % 10 in range(2, 5) and hours > 20):

                travel_time += "{} час{} ".format(hours, "а")

            elif (hours % 100 in range(5, 21)) or (hours % 10 in range(5, 10)) or hours % 10 == 0:

                travel_time += "{} час{} ".format(hours, "ов")

            else:

                travel_time += "{} час{} ".format(hours, "ов")

            # Меняем окончания, чтобы читалось нормально
            if minutes == 1 or (minutes % 10 == 1 and minutes > 20):
                travel_time += "{} минут{}".format(minutes, "а")
            elif minutes in range(2, 5) or (minutes % 10 in range(2, 5) and minutes > 20):
                travel_time += "{} минут{}".format(minutes, "ы")
            elif minutes in range(5, 21) or ((minutes % 10 in range(5, 10) or minutes % 10 == 0) and minutes > 20):
                travel_time += "{} минут".format(minutes)
            # Если вдруг меньше часа
            elif not minutes:
                travel_time += ""

            if "localTime0" in train_info.keys() and "localTime1" in \
                    train_info.keys():

                train_list_data[category].append(
                    "{}.\n\U0001F686 {} — {}\n\U00000023\U0000FE0F\U000020E3 {} {}\n\U00002197\U0000FE0F {}, "
                    "{}\n\U00002198\U0000FE0F {}, {}\n".format(
                        train_order,
                        train_info["route0"],
                        train_info["route1"],
                        train_info["number2"],
                        train_info["brand"],
                        format_date(train_info["localDate0"]),
                        train_info["localTime0"],
                        format_date(train_info["localDate1"]),
                        train_info["localTime1"]) + travel_time.strip())

            elif "localTime0" in train_info.keys():

                train_list_data[category].append(
                    "{}.\n\U0001F686 {} — {}\n\U00000023\U0000FE0F\U000020E3 {} {}\n\U00002197\U0000FE0F {}, "
                    "{}\n\U00002198\U0000FE0F {}, {}\n".format(
                        train_order,
                        train_info["route0"],
                        train_info["route1"],
                        train_info["number2"],
                        train_info["brand"],
                        format_date(train_info["localDate0"]),
                        train_info["localTime0"],
                        format_date(train_info["date1"]),
                        train_info["time1"]) + travel_time.strip())

            elif "localTime1" in train_info.keys():

                train_list_data[category].append(
                    "{}.\n\U0001F686 {} — {}\n\U00000023\U0000FE0F\U000020E3 {} {}\n\U00002197\U0000FE0F {}, "
                    "{}\n\U00002198\U0000FE0F {}, {}\n".format(
                        train_order,
                        train_info["route0"],
                        train_info["route1"],
                        train_info["number2"],
                        train_info["brand"],
                        format_date(train_info["date0"]),
                        train_info["time0"],
                        format_date(train_info["localDate1"]),
                        train_info["localTime1"]) + travel_time.strip())

            else:

                train_list_data[category].append(
                    "{}.\n\U0001F686 {} — {}\n\U00000023\U0000FE0F\U000020E3 {} {}\n\U00002197\U0000FE0F {}, "
                    "{}\n\U00002198\U0000FE0F {}, {}\n".format(
                        train_order,
                        train_info["route0"],
                        train_info["route1"],
                        train_info["number2"],
                        train_info["brand"],
                        format_date(train_info["date0"]),
                        train_info["time0"],
                        format_date(train_info["date1"]),
                        train_info["time1"]) + travel_time.strip())

            train_order_counter[category] += 1

    # train_list_message = "{}\n\n" * len(train_nums)

    # return train_list_message.format(*train_list), train_nums, departure_times, is_two_storey_list

    return train_list_data, train_nums_data, departure_times_data, is_two_storey_data


async def get_seats(origin_station, destination_station, date, train):

    device_guid = device_guid_gen()
    hashcode = hash_code_gen()

    # Готовим запрос на получение информации по свободным местам в нужном поезде.
    # Первый запрос на получение rid.

    url = "https://ekmp-i-47-2.rzd.ru/v1.0/ticket/selection"

    headers = {
        "Host": "ekmp-i-47-2.rzd.ru",
        "Content-Type": "application/json",
        "User-Agent": "RZD/2367 CFNetwork/1496.0.7 Darwin/23.5.0",
        "Accept-Language": "ru",
        "Accept-Encoding": "gzip, deflate, br"
    }

    data_req = {"code0": "{}".format(origin_station),
                "code1": "{}".format(destination_station),
                "dt0": "{}".format(date),
                "tnum0": "{}".format(train),
                "deviceGuid": "{}".format(device_guid),
                "platform": "IOS",
                "version": "1.47.2(2367)",
                "hashCode": "{}".format(hashcode),
                "protocolVersion": 47
                }

    # Отправляем запрос
    async with httpx.AsyncClient(verify=False) as client:

        res = await client.post(url=url, headers=headers, json=data_req, timeout=10)

        if res.status_code != 200:  # АШИПКА
            print("Response Code: {}".format(res.status_code))
        else:
            data_res = res.json()  # Ответ

        rid = data_res["result"]["rid"]

        # Второй запрос уже непосредственно на получение свободных мест в нужном поезде

        data_res = await get_info_with_rid(rid, device_guid, hashcode, url)

        # Если на некоторые поезда (Ласточки и Сапсаны) вообще нет мест, то API возвращает ошибку 1093 с сообщением
        if data_res.get("errorCode") == 1093 and data_res.get("errorMessage", "").startswith("Мест нет"):
            return 0

        try:
            while data_res.get("result") is None or "lst" not in data_res["result"].keys():
                moscow_spb_rid = data_res["result"]["rid"]
                data_res = await get_info_with_rid(rid, device_guid, hashcode, url)

                # Проверяем ошибку внутри цикла
                if data_res.get("errorCode") == 1093 and data_res.get("errorMessage", "").startswith("Мест нет"):
                    return 0

        except AttributeError as e:

            print("AttributeError occurred: {}, data_res: {}".format(e, data_res))
            # Можно вернуть 0 или другое значение по умолчанию
            return 0

    # Считаем места

    brand = data_res["result"]["lst"][0].get("brand", "").capitalize()
    if brand == "Сапсан":
        counter = SapsanSeatsCounter(data_res)
    elif brand == "Ласточка":
        counter = Lasto4kaSeatsCounter(data_res)
    else:
        counter = TrainSeatsCounter(data_res)

    counter.count_seats()
    available_seats = counter.get_available_seats()
    return available_seats


# s = asyncio.run(get_train("2000000", "2010050", "18.06.2025"))
# # s = asyncio.run(get_train("2004000", "2064570", "29.05.2024"))
# print([key for key in s[0].keys() if len(s[0][key]) > 0])
# for key in s[0].keys():
#     if len(s[0][key]) > 0:
#         print(key)
# print(s[0])
# print(s[1])
# print(s[0])
# print(s[-1])
# print(json.dumps(s, indent=4, ensure_ascii=False))

# import json
# train_number = "740\u042f"
# origin_station = "2000000"
# destination_station = "2010050"
# departure_date = "18.06.2025"
# print(json.dumps(get_seats(origin_station, destination_station, departure_date, train_number)["coupe"], indent=4,
#                  ensure_ascii=False))

# lel = asyncio.run(get_seats(origin_station, destination_station, departure_date, train_number))
# print(json.dumps(lel, indent=4, ensure_ascii=False))

# user_choice = {
#     "car_type": ["coupe", "lux"],
#     "gender": "female",
#     "same_gender_only": False,
#     "pets_allowed": "whatever",
#     "seat_type": ["lower", "upper", "two_storey_upper"],
# }

# print(generate_user_messages(user_choice, lel))
# print(generate_paths(user_choice))
