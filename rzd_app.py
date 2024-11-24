import asyncio
import locale
from datetime import datetime
import pytz

import httpx
import string
import random
import urllib3

from monitor_setup import generate_user_messages
from seats_counter import TrainSeatsCounter

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
        "User-Agent": "RZD/2367 CFNetwork/1496.0.7 Darwin/23.5.0",
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
        "User-Agent": "RZD/2367 CFNetwork/1496.0.7 Darwin/23.5.0",
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
    train_nums = []

    # Список с информацией по каждому поезду
    train_list = []

    # Список с датой и временем отправления каждого поезда (по МСК)
    departure_times = []

    # Список с двухаэтажностью
    is_two_storey_list = []

    # Для порядка отображения поездов
    train_order = 0

    # Установим часовой пояс
    moscow_tz = pytz.timezone("Europe/Moscow")

    # Чтобы не выводить лишние поезда (которые уже отправились) введем проверку на время
    time_check = datetime.now(moscow_tz)

    for train in range(len(data_res["result"]["timetables"][0]["list"])):

        # Строка с датой отправления по московскому времени (так как бот будет на сервере, на котором московское время)
        date_str = (data_res["result"]["timetables"][0]["list"][train]["date0"] + " " +
                    data_res["result"]["timetables"][0]["list"][train]["time0"])

        # Переводим строку в объект datetime, чтобы сравнить с текущим временем
        departure_date = datetime.strptime(date_str, "%d.%m.%Y %H:%M").replace(tzinfo=moscow_tz)

        # Оставляем только те поезда, которые еще не отправились, и убираем "Ласточки" и "Сапсаны" + пригородные
        # электрички (у них среди прочих есть параметр subt, равный 1, который отсутствует у поездов дальнего
        # следования)
        if (departure_date > time_check and
                data_res["result"]["timetables"][0]["list"][train]["brand"].lower() not in ["сапсан", "ласточка"] and
                "subt" not in data_res["result"]["timetables"][0]["list"][train]):

            # Меняем порядок отображения поездов
            train_order += 1

            # Добавляем номер поезда, который возвращает API
            train_nums.append(data_res["result"]["timetables"][0]["list"][train]["number"])

            # Добавляем дату и время отправления (по Москве)
            departure_times.append(departure_date)

            # Добавляем запись о двухэтажности
            is_two_storey_list.append("двухэтажный" in data_res["result"]["timetables"][0]["list"][train]["brand"]
                                      .lower())

            travel_time = "\U000023F3 "

            # Часы в пути
            hours = int(data_res["result"]["timetables"][0]["list"][train]["timeInWay"][
                        :data_res["result"]["timetables"][0]["list"][train]["timeInWay"].index(":")])

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

            # Минуты в пути
            minutes = int(data_res["result"]["timetables"][0]["list"][train]["timeInWay"][
                          data_res["result"]["timetables"][0]["list"][train]["timeInWay"].index(":") + 1:])

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

            if "localTime0" in data_res["result"]["timetables"][0]["list"][train].keys() and "localTime1" in \
                    data_res["result"]["timetables"][0]["list"][train].keys():

                train_list.append(
                    "{}.\n\U0001F686 {} — {}\n\U00000023\U0000FE0F\U000020E3 {} {}\n\U00002197\U0000FE0F {}, "
                    "{}\n\U00002198\U0000FE0F {}, {}\n".format(
                        train_order,
                        data_res["result"]["timetables"][0]["list"][train]["route0"],
                        data_res["result"]["timetables"][0]["list"][train]["route1"],
                        data_res["result"]["timetables"][0]["list"][train]["number2"],
                        data_res["result"]["timetables"][0]["list"][train]["brand"],
                        format_date(data_res["result"]["timetables"][0]["list"][train]["localDate0"]),
                        data_res["result"]["timetables"][0]["list"][train]["localTime0"],
                        format_date(data_res["result"]["timetables"][0]["list"][train]["localDate1"]),
                        data_res["result"]["timetables"][0]["list"][train]["localTime1"]) + travel_time)

            elif "localTime0" in data_res["result"]["timetables"][0]["list"][train].keys():

                train_list.append(
                    "{}.\n\U0001F686 {} — {}\n\U00000023\U0000FE0F\U000020E3 {} {}\n\U00002197\U0000FE0F {}, "
                    "{}\n\U00002198\U0000FE0F {}, {}\n".format(
                        train_order,
                        data_res["result"]["timetables"][0]["list"][train]["route0"],
                        data_res["result"]["timetables"][0]["list"][train]["route1"],
                        data_res["result"]["timetables"][0]["list"][train]["number2"],
                        data_res["result"]["timetables"][0]["list"][train]["brand"],
                        format_date(data_res["result"]["timetables"][0]["list"][train]["localDate0"]),
                        data_res["result"]["timetables"][0]["list"][train]["localTime0"],
                        format_date(data_res["result"]["timetables"][0]["list"][train]["date1"]),
                        data_res["result"]["timetables"][0]["list"][train]["time1"]) + travel_time)

            elif "localTime1" in data_res["result"]["timetables"][0]["list"][train].keys():

                train_list.append(
                    "{}.\n\U0001F686 {} — {}\n\U00000023\U0000FE0F\U000020E3 {} {}\n\U00002197\U0000FE0F {}, "
                    "{}\n\U00002198\U0000FE0F {}, {}\n".format(
                        train_order,
                        data_res["result"]["timetables"][0]["list"][train]["route0"],
                        data_res["result"]["timetables"][0]["list"][train]["route1"],
                        data_res["result"]["timetables"][0]["list"][train]["number2"],
                        data_res["result"]["timetables"][0]["list"][train]["brand"],
                        format_date(data_res["result"]["timetables"][0]["list"][train]["date0"]),
                        data_res["result"]["timetables"][0]["list"][train]["time0"],
                        format_date(data_res["result"]["timetables"][0]["list"][train]["localDate1"]),
                        data_res["result"]["timetables"][0]["list"][train]["localTime1"]) + travel_time)

            else:

                train_list.append(
                    "{}.\n\U0001F686 {} — {}\n\U00000023\U0000FE0F\U000020E3 {} {}\n\U00002197\U0000FE0F {}, "
                    "{}\n\U00002198\U0000FE0F {}, {}\n".format(
                        train_order,
                        data_res["result"]["timetables"][0]["list"][train]["route0"],
                        data_res["result"]["timetables"][0]["list"][train]["route1"],
                        data_res["result"]["timetables"][0]["list"][train]["number2"],
                        data_res["result"]["timetables"][0]["list"][train]["brand"],
                        format_date(data_res["result"]["timetables"][0]["list"][train]["date0"]),
                        data_res["result"]["timetables"][0]["list"][train]["time0"],
                        format_date(data_res["result"]["timetables"][0]["list"][train]["date1"]),
                        data_res["result"]["timetables"][0]["list"][train]["time1"]) + travel_time)

    train_list_message = "{}\n\n" * len(train_nums)

    return train_list_message.format(*train_list), train_nums, departure_times, is_two_storey_list


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

    # Фильтруем купе (обычные и инвалидные), плацкарт и СВ.

    counter = TrainSeatsCounter(data_res)
    counter.count_seats()
    available_seats = counter.get_available_seats()
    return available_seats


# s = asyncio.run(get_train("2064570", "2004000", "26.06.2024"))
# s = asyncio.run(get_train("2004000", "2064570", "26.05.2024"))
# print(s[-2])
# print(s[1])
# print(s[0])
# print(s[-1])
# print(json.dumps(s, indent=4, ensure_ascii=False))


# train_number = "035А"
# origin_station = "2004000"
# destination_station = "2064570"
# departure_date = "14.08.2024"
# print(json.dumps(get_seats(origin_station, destination_station, departure_date, train_number)["coupe"], indent=4,
#                  ensure_ascii=False))

# lel = asyncio.run(get_seats(origin_station, destination_station, departure_date, train_number))
# print(json.dumps(lel["coupe"], indent=4, ensure_ascii=False))

# user_choice = {
#     "car_type": ["coupe", "lux"],
#     "gender": "female",
#     "same_gender_only": False,
#     "pets_allowed": "whatever",
#     "seat_type": ["lower", "upper", "two_storey_upper"],
# }

# print(generate_user_messages(user_choice, lel))
# print(generate_paths(user_choice))
