import asyncio
import locale
from datetime import datetime
import pytz

import httpx
import string
import random
import urllib3

from monitor_setup import generate_user_messages
from seats_counter_new import TrainSeatsCounter, Lasto4kaSeatsCounter, SapsanSeatsCounter

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Явно зададим русскую локаль, чтобы дни недели в функции get_train печатались на русском языке
locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")


# Функция для "красивого" формата даты
def format_date(date_string):
    start_date = date_string
    date_format = "%d.%m.%Y"
    date_obj = datetime.strptime(start_date, date_format)
    formatted_date = date_obj.strftime("%a %d.%m.%Y").capitalize()
    return formatted_date


def hash_code_gen(size=40, chars=string.ascii_lowercase + string.digits):
    return "".join(random.choice(chars) for _ in range(size))


async def get_info_with_rid(rid, hashcode, url):
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

    # Готовим запрос на получение информации по поездам в нужную дату.

    url = "https://ekmp-i-47-2.rzd.ru/v3.0/timetable/search"

    headers = {
        "Host": "ekmp-i-47-2.rzd.ru",
        "Content-Type": "application/json",
        "User-Agent": "RZD/2367 CFNetwork/1568.300.101 Darwin/24.2.0",
        "Sec-Fetch-Site": "same-origin",
        "Accept-Language": "ru",
        "Accept-Encoding": "gzip, deflate, br"
    }

    data_req = {"code0": "{}".format(origin),
                "code1": "{}".format(destination),
                "dt0": "{}".format(date),
                "timezone": "+0300",
                "withoutSeats": "y",
                "dir": 0,
                "tfl": 3,
                "responseVersion": 2,
                "protocolVersion": 47,
                "hashCode": "{}".format(hashcode)}

    # Отправляем запрос
    async with httpx.AsyncClient(verify=False) as client:
        res = await client.post(url=url, headers=headers, json=data_req, timeout=10)

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

        data_res = await get_info_with_rid(rid, hashcode, url)

        attempts = 0

        while "timetables" not in data_res["result"].keys() and attempts < 11:
            await asyncio.sleep(0.5)
            moscow_spb_rid = data_res["result"]["rid"]
            data_res = await get_info_with_rid(moscow_spb_rid, hashcode, url)
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

            # Определяем бренд поезда
            brand = train_info["brand"].lower()
            if "ласточка" in brand:
                category = "Ласточка"
            elif "сапсан" in brand:
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

        data_res = await get_info_with_rid(rid, hashcode, url)

        while "lst" not in data_res["result"].keys():
            moscow_spb_rid = data_res["result"]["rid"]
            data_res = await get_info_with_rid(moscow_spb_rid, hashcode, url)

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


# s = asyncio.run(get_train("2000000", "2004000", "26.04.2025"))
# s = asyncio.run(get_train("2004000", "2064570", "26.05.2024"))
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
# train_number = "020С"
# origin_station = "2000003"
# destination_station = "2064570"
# departure_date = "02.07.2025"
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
