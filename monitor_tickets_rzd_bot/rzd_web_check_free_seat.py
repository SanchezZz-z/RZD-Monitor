from concurrent.futures import ThreadPoolExecutor

import httpx
import pandas as pd
import matplotlib.pyplot as plt
from pandas.plotting import table
from matplotlib.backends.backend_pdf import PdfPages
import asyncio
import io

from rzd_app import hash_code_gen, get_info_with_rid

MAX_CONCURRENT_REQ = 3


# Функция для определения типа вагона
def car_type_checker(data, car_number):
    for car in data["result"]["lst"][0]["cars"]:
        if car["cnumber"] == car_number:
            if car["type"] == "Купе":
                return "Купе"
            elif car["type"] == "Люкс":
                return "Люкс"
            elif car["type"] == "Мягкий":
                return "Мягкий"
            elif car["type"] == "Плац":
                return "Плац"
    return "sold out"


def make_pdf(df):
    # Начать индексацию с 1
    df.index += 1

    # Создание фигуры и оси
    fig, ax = plt.subplots(figsize=(8, 4))

    # Убираем оси
    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)
    ax.set_frame_on(False)

    # Создание таблицы на основе DataFrame
    tbl = table(ax, df, loc="center", cellLoc="center", colWidths=[0.2] * len(df.columns))

    # Настройка стиля таблицы
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    tbl.scale(1.2, 1.2)

    # Сохранение в PDF
    pdf_buffer = io.BytesIO()
    with PdfPages(pdf_buffer) as pdf:
        pdf.savefig(fig, bbox_inches="tight")
        plt.close()
    pdf_buffer.seek(0)
    return pdf_buffer


# async def make_pdf_async(df):
#     loop = asyncio.get_event_loop()
#     with ThreadPoolExecutor() as pool:
#         pdf_buffer = await loop.run_in_executor(pool, make_pdf, df)
#     return pdf_buffer


async def get_stops(train_num, origin_station, destination_station, departure_date):
    # Тело запроса
    data_req = {
        "TrainNumber": "{}".format(train_num),
        "Origin": "{}".format(origin_station),
        "Destination": "{}".format(destination_station),
        "DepartureDate": "{}".format(departure_date)
    }

    # Заголовки. Список необходимых заголовков можно определить, перебирая их в Charles
    # (Если запрос не проходит, значит заголовок обязательный).
    headers = {
        "Host": "ticket.rzd.ru",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/116.0.0.0 Safari/537.36",
        "Origin": "https://ticket.rzd.ru",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,sr;q=0.6"
    }

    url = "https://ticket.rzd.ru/apib2b/p/Railway/V1/Search/TrainRoute?service_provider=B2B_RZD"
    # Отправляем запрос
    async with httpx.AsyncClient(verify=False) as client:
        res = await client.post(url=url, headers=headers, json=data_req, timeout=10, follow_redirects=True)

        if res.status_code != 200:
            print("Response Code: {}".format(res.status_code))
        else:
            res.json()  # Ответ

    # Ответ содержит список остановок по всему маршруту следования поезда. Нам необходимо сделать из этого словарь
    # только с теми остановками, которые будут по пути следования пользователя.

    stops = {}

    add = False
    for stop in range(len(res.json()["Routes"][0]["RouteStops"])):

        if add:
            if res.json()["Routes"][0]["RouteStops"][stop]["StationCode"] != destination_station:
                stops[res.json()["Routes"][0]["RouteStops"][stop]["StationName"]] = tuple(
                    (res.json()["Routes"][0]["RouteStops"][stop]["StationCode"],
                     res.json()["Routes"][0]["RouteStops"][stop]["LocalDepartureDateTime"][:10]))
            else:
                add = False
                stops[res.json()["Routes"][0]["RouteStops"][stop]["StationName"]] = tuple(
                    (res.json()["Routes"][0]["RouteStops"][stop]["StationCode"],
                     res.json()["Routes"][0]["RouteStops"][stop]["LocalArrivalDateTime"][:10]))
        else:
            if res.json()["Routes"][0]["RouteStops"][stop]["StationCode"] == origin_station:
                stops[res.json()["Routes"][0]["RouteStops"][stop]["StationName"]] = tuple(
                    (res.json()["Routes"][0]["RouteStops"][stop]["StationCode"],
                     res.json()["Routes"][0]["RouteStops"][stop]["LocalDepartureDateTime"][:10]))
                add = True

    # На этом этапе у нас готов словарь с необходимой информацией об остановках по маршруту в формате
    # {название: (код станции, дата отправления с этой станции)}
    return stops


# async def get_info_with_rid(rid, hashcode, url):
#     attempts = 0
#
#     while True:
#
#         headers = {
#             "Host": "ekmp-i-47-2.rzd.ru",
#             "Content-Type": "application/json",
#             "Connection": "keep-alive",
#             "Accept": "*/*",
#             "User-Agent": "RZD/2356 CFNetwork/1410.0.3 Darwin/22.6.0",
#             "Accept-Language": "ru",
#             "Accept-Encoding": "gzip, deflate, br"
#         }
#
#         data_req = {
#             "rid": "{}".format(rid),
#             "hashCode": "{}".format(hashcode),
#             "protocolVersion": 47
#         }
#
#         # Отправляем запрос
#         async with httpx.AsyncClient(verify=False) as client:
#             res = await client.post(url=url, headers=headers, json=data_req, timeout=10, follow_redirects=True)
#
#             attempts += 1
#
#             if res.status_code != 200:  # АШИПКА
#                 print("Response Code: {}".format(res.status_code))
#
#             if ("timetables" in res.json()["result"].keys() or "lst" in res.json()["result"].keys()) or attempts > 5:
#                 return res.json()
#             else:
#                 continue


async def get_free_seats_in_a_coupe(train_num, origin_station, destination_station, date, car_number, seat):
    hashcode = hash_code_gen()

    # Готовим запрос на получение информации по свободным местам в нужном поезде.
    # Первый запрос на получение rid.

    url = "https://ekmp-i-47-2.rzd.ru/v1.0/ticket/selection"

    headers = {
        "Host": "ekmp-i-47-2.rzd.ru",
        "Content-Type": "application/json",
        "User-Agent": "RZD/2356 CFNetwork/1410.0.3 Darwin/22.6.0",
        "Accept-Language": "ru",
        "Accept-Encoding": "gzip, deflate, br"
    }

    data_req = {"code0": "{}".format(origin_station),
                "code1": "{}".format(destination_station),
                "dt0": "{}".format(date),
                "tnum0": "{}".format(train_num),
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

    free = []
    coupe = []
    car_type = car_type_checker(data_res, car_number)
    # Функция работает только для купе и СВ вагонов
    if car_type != "Плац":
        for car in data_res["result"]["lst"][0]["cars"]:
            if car["cnumber"] == car_number:
                if car_type == "Купе":

                    if seat % 4 == 0:
                        coupe.extend([seat - 3, seat - 2, seat - 1, seat])
                    elif seat % 4 == 1:
                        coupe.extend([seat, seat + 1, seat + 2, seat + 3])
                    elif seat % 4 == 2:
                        coupe.extend([seat - 1, seat, seat + 1, seat + 2])
                    else:
                        coupe.extend([seat - 2, seat - 1, seat, seat + 1])

                    for i in range(len(car["seats"])):
                        for place_num in car["seats"][i]["places"].split(","):
                            if place_num.isnumeric():
                                if place_num.startswith("0"):
                                    free.append(int(place_num.lstrip("0")))
                                else:
                                    free.append(int(place_num))
                            else:
                                if place_num.startswith("0"):
                                    if place_num[-1].isalpha():
                                        free.append(int(place_num.lstrip("0")[:-1]))
                                    else:
                                        free.append(int(place_num.lstrip("0")))
                                else:
                                    free.append(int(place_num))

                # Бывают такие вагоны, в которых есть одновременно и люкс места, и СВ (технически функция и с люкс
                # вагонами работает, но ее нет смысла применять, так как там только выкуп всего купе возможен)
                elif car_type in ["Люкс", "Мягкий"]:

                    if seat % 2 == 0:
                        coupe.extend([seat - 1, seat])
                    else:
                        coupe.extend([seat, seat + 1])

                    for i in range(len(car["seats"])):
                        for place_num in car["seats"][i]["places"].split(","):
                            if len(place_num) > 4:
                                for seat in range(int(place_num[:3]), int(place_num[4:7]) + 1):
                                    if place_num[-1].isdigit():
                                        free.append(int(str(seat)))
                                    else:
                                        free.append(int(str(seat) + place_num[-1]))
                            else:
                                if place_num.startswith("0"):
                                    if place_num[-1].isalpha():
                                        free.append(int(place_num.lstrip("0")[:-1]))
                                    else:
                                        free.append(int(place_num.lstrip("0")))
                                else:
                                    free.append(int(place_num))

        coupe_set = set(coupe)
        free_set = set(free)

        if len(coupe_set.intersection(free_set)) > 0:
            return origin_station, coupe_set.intersection(free_set)
        else:
            return origin_station, "Купе полностью выкуплено"

    else:
        return 0


async def free_seats_check(train_num, origin_station, destination_station, departure_date, car_number, seat):
    car_is_valid = await get_free_seats_in_a_coupe(train_num, origin_station, destination_station,
                                                   "{2}.{1}.{0}".format(*departure_date.split("-")), car_number, seat)
    if car_is_valid:
        stops = await get_stops(train_num, origin_station, destination_station, departure_date)
        to_do = []
        for s in range(len(list(stops.keys())[:-1])):
            date = "{2}.{1}.{0}".format(*stops[list(stops.keys())[s]][1].split("-"))
            origin_station = stops[list(stops.keys())[s]][0]
            destination_station = stops[list(stops.keys())[s + 1]][0]
            to_do.append(get_free_seats_in_a_coupe(train_num, origin_station, destination_station, date,
                                                   car_number, seat))
        result = await asyncio.gather(*to_do)
        stops_list = [stop for stop in stops.keys()][:-1]
        free_seats = []
        for i in range(len(stops.keys()) - 1):
            if result[i] is None:
                free_seats.append("Купе полностью выкуплено")
            else:
                if isinstance(result[i][1], set):
                    free_seats.append(str(result[i][1])[1:-1])
                else:
                    free_seats.append(result[i][1])
        return pd.DataFrame({"Остановка": stops_list, "Свободные места": free_seats})
    else:
        return "Данная функция работает только в вагонах типа купе и СВ"


def main(train_num, origin_station, destination_station, departure_date, car_number, seat):
    report = asyncio.run(
        free_seats_check(train_num, origin_station, destination_station, departure_date, car_number, seat))
    # return report
    # if type(report).__name__ == "DataFrame":
    #     make_pdf(report)
    print(report)


if __name__ == "__main__":
    # В этой функции в случае, если у города отправления и города назначения есть несколько вокзалов, ОБЯЗАТЕЛЬНО
    # надо указывать точный вокзал отправления / прибытия
    # main("020С", "2000003", "2064570", "2024-06-28", "05", 12)
    # main("043А", "2004001", "2010215", "2024-08-10", "08", 110)
    # main("155А", "2004001", "2000007", "2024-07-03", "02", 14)
    # main("119А", "2004001", "2001025", "2024-06-06", "07", 10)
    main("049А", "2004001", "2064570", "2024-07-19", "12", 1)
    # main("036С", "2004001", "2064570", "2024-09-12", "12", 9)
    # asyncio.run((free_seats_check("020С", "2000003", "2064570", "2024-06-28", "05", 12)))

# print(datetime.datetime.now() + datetime.timedelta(days=0))
