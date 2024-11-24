import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # Когда открыт Charles.


def get_train(origin, destination, date):
    # Тело запроса
    data_req = {
        "Origin": "{}".format(origin),
        "Destination": "{}".format(destination),
        "DepartureDate": "{}".format(date),
        "GetByLocalTime": True,
        "SpecialPlacesDemand": "StandardPlacesAndForDisabledPersons",
        "GetTrainsFromSchedule": True
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

    url = "https://ticket.rzd.ru/apib2b/p/Railway/V1/Search/TrainPricing?service_provider=B2B_RZD"
    # Отправляем запрос
    res = requests.post(url=url, headers=headers, json=data_req, verify=False, timeout=10)

    if res.status_code != 200:  # АШИПКА
        print("Response Code: {}".format(res.status_code))
    else:
        res.json()  # Ответ

    # Выбираем нужный поезд из найденных

    train_nums = [0]
    train_count = 1

    for train in range(len(res.json()["Trains"])):
        train_nums.append(res.json()["Trains"][train]["TrainNumber"])

        print("{}.\nПоезд № {}\n{}-{}\nВремя отправления: {} - {}.{}.{}\nВремя прибытия: {} - {}.{}.{}\nВремя в пути {}"
              " часов {} минут\n".format(train_count, res.json()["Trains"][train]["DisplayTrainNumber"],
                                         res.json()["Trains"][train]["InitialStationName"],
                                         res.json()["Trains"][train]["FinalStationName"],
                                         res.json()["Trains"][train]["LocalDepartureDateTime"][11:16],
                                         res.json()["Trains"][train]["LocalDepartureDateTime"][8:10],
                                         res.json()["Trains"][train]["LocalDepartureDateTime"][5:7],
                                         res.json()["Trains"][train]["LocalDepartureDateTime"][:4],
                                         res.json()["Trains"][train]["LocalArrivalDateTime"][11:16],
                                         res.json()["Trains"][train]["LocalArrivalDateTime"][8:10],
                                         res.json()["Trains"][train]["LocalArrivalDateTime"][5:7],
                                         res.json()["Trains"][train]["LocalArrivalDateTime"][:4],
                                         '{0:g}'.format(res.json()["Trains"][train]["TripDuration"] // 60),
                                         '{0:g}'.format(res.json()["Trains"][train]["TripDuration"] % 60)))
        train_count += 1

    while train_count > 1:

        print("\nПожалуйста, выберете поезд из списка.\nЕсли необходимого поезда нет в списке, убедитесь, что правильно"
              "ввели станцию отправления, станцию назначения и дату поездки.\n")
        print("Чтобы закрыть бота, введите 'Стоп'.")

        user_select = input()

        if user_select.title() == "Стоп":
            return 0

        if user_select.isdigit() and int(user_select) in range(1, train_count):
            return train_nums[int(user_select)]
        else:
            if not user_select.isdigit():
                print("Пожалуйста, введите цифру.")
                continue
            elif int(user_select) not in range(1, train_count):
                print("\nВведите цифру от 1 до {}".format(train_count - 1))

    print("По заданным параметрам не найдено поездов. Попробуем еще раз")
    return 0


def get_seats(origin_station, destination_station, date, train):
    # Тело запроса
    data_req = {
        "OriginCode": "{}".format(origin_station),
        "DestinationCode": "{}".format(destination_station),
        "DepartureDate": "{}".format(date),
        "TrainNumber": "{}".format(train),
        "SpecialPlacesDemand": "StandardPlacesAndForDisabledPersons"
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
        "Referer": "https://ticket.rzd.ru/trip/class",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,sr;q=0.6"
    }

    url = "https://ticket.rzd.ru/apib2b/p/Railway/V1/Search/CarPricing?service_provider=B2B_RZD&isBonusPurchase=false"
    # Отправляем запрос
    res = requests.post(url=url, headers=headers, json=data_req, verify=False, timeout=10)

    if res.status_code != 200:  # АШИПКА
        print("Response Code: {}".format(res.status_code))
    else:
        res.json()  # Ответ

    # Фильтруем купе (обычные и инвалидные), плацкарт и СВ.

    available = {
        "coupe": {"total": 0,
                  "upper":
                      {"total": 0,
                       "male": {"total": 0, "pets": 0, "no_pets": 0},
                       "female": {"total": 0, "pets": 0, "no_pets": 0},
                       "free": {"total": 0, "pets": 0, "no_pets": 0},
                       "unisex": {"total": 0, "pets": 0, "no_pets": 0}},
                  "two_storey_upper":
                      {"total": 0,
                       "male": {"total": 0, "pets": 0, "no_pets": 0},
                       "female": {"total": 0, "pets": 0, "no_pets": 0},
                       "free": {"total": 0, "pets": 0, "no_pets": 0},
                       "unisex": {"total": 0, "pets": 0, "no_pets": 0}},
                  "lower":
                      {"total": 0,
                       "male": {"total": 0, "pets": 0, "no_pets": 0},
                       "female": {"total": 0, "pets": 0, "no_pets": 0},
                       "free": {"total": 0, "pets": 0, "no_pets": 0},
                       "unisex": {"total": 0, "pets": 0, "no_pets": 0}},
                  "disabled":
                      {"total": 0, "pets": 0, "no_pets": 0}},
        "plaz": {"total": 0,
                 "upper": {"total": 0, "pets": 0, "no_pets": 0},
                 "side_upper": {"total": 0, "pets": 0, "no_pets": 0},
                 "lower": {"total": 0, "pets": 0, "no_pets": 0},
                 "side_lower": {"total": 0, "pets": 0, "no_pets": 0}},
        "lux": {"total": 0,
                "upper":
                    {"total": 0,
                     "male": {"total": 0, "pets": 0, "no_pets": 0},
                     "female": {"total": 0, "pets": 0, "no_pets": 0},
                     "free": {"total": 0, "pets": 0, "no_pets": 0},
                     "unisex": {"total": 0, "pets": 0, "no_pets": 0}},
                "lower":
                    {"total": 0,
                     "male": {"total": 0, "pets": 0, "no_pets": 0},
                     "female": {"total": 0, "pets": 0, "no_pets": 0},
                     "free": {"total": 0, "pets": 0, "no_pets": 0},
                     "unisex": {"total": 0, "pets": 0, "no_pets": 0}}
                }
    }

    no_pets_class = ["1Т", "1Х", "1Д", "2Т", "2Х", "2Ц", "3Э", "3Л", "3Т", "3П"]

    # Идем по вагонам

    for car in res.json()["Cars"]:
        # Плацкарт
        if car["CarType"] == "ReservedSeat":
            # Идем по вагонам без провоза животных
            if car["ServiceClass"] in no_pets_class:
                # Верхние
                if car["CarPlaceType"] == "Upper" or car["CarPlaceType"] == "UpperWithHigherLevelOfNoise":
                    available["plaz"]["upper"]["no_pets"] += car["PlaceQuantity"]
                # Нижние
                elif car["CarPlaceType"] == "Lower" or car["CarPlaceType"] == "LowerWithHigherLevelOfNoise":
                    available["plaz"]["lower"]["no_pets"] += car["PlaceQuantity"]
                # Верхние боковые
                elif car["CarPlaceType"] == "SideUpper" or car["CarPlaceType"] == "SideUpperWithHigherLevelOfNoise":
                    available["plaz"]["side_upper"]["no_pets"] += car["PlaceQuantity"]
                # Нижние боковые
                elif car["CarPlaceType"] == "SideLower" or car["CarPlaceType"] == "SideLowerWithHigherLevelOfNoise":
                    available["plaz"]["side_lower"]["no_pets"] += car["PlaceQuantity"]
            # Провоз животных разрешен
            else:
                # Верхние
                if car["CarPlaceType"] == "Upper" or car["CarPlaceType"] == "UpperWithHigherLevelOfNoise":
                    available["plaz"]["upper"]["pets"] += car["PlaceQuantity"]
                # Нижние
                elif car["CarPlaceType"] == "Lower" or car["CarPlaceType"] == "LowerWithHigherLevelOfNoise":
                    available["plaz"]["lower"]["pets"] += car["PlaceQuantity"]
                # Верхние боковые
                elif car["CarPlaceType"] == "SideUpper" or car["CarPlaceType"] == "SideUpperWithHigherLevelOfNoise":
                    available["plaz"]["side_upper"]["pets"] += car["PlaceQuantity"]
                # Нижние боковые
                elif car["CarPlaceType"] == "SideLower" or car["CarPlaceType"] == "SideLowerWithHigherLevelOfNoise":
                    available["plaz"]["side_lower"]["pets"] += car["PlaceQuantity"]
        # Купе
        elif car["CarType"] == "Compartment":
            # Идем по вагонам без провоза животных
            if car["ServiceClass"] in no_pets_class:
                # Проверяем, есть ли разделение на мужские и женские купе
                if "МЖ" in car["CarDescription"]:
                    # Верхние
                    if car["CarPlaceType"] == "Upper" or "UpperWithHigherLevelOfNoise" in car["CarPlaceType"]:
                        # Добавляем места в мужских купе
                        available["coupe"]["upper"]["male"]["no_pets"] += car["FreePlaces"].count("М")
                        # Добавляем места в женских купе
                        available["coupe"]["upper"]["female"]["no_pets"] += car["FreePlaces"].count("Ж")
                        # Добавляем места в свободных купе, то есть общие (М/Ж)
                        available["coupe"]["upper"]["free"]["no_pets"] += car["FreePlaces"].count("Ц")
                        # Добавляем места в смешанных купе (М/Ж)
                        available["coupe"]["upper"]["unisex"]["no_pets"] += car["FreePlaces"].count("С")
                        # Верхние на втором этаже двухэтажного поезда
                        if car["IsTwoStorey"]:
                            for place_num in car["FreePlaces"].split(","):
                                if int(place_num[:-1]) > 80 and int(place_num[:-1]) % 2 == 0:
                                    if place_num[-1] == "М":
                                        available["coupe"]["two_storey_upper"]["male"]["no_pets"] += 1
                                    elif place_num[-1] == "Ж":
                                        available["coupe"]["two_storey_upper"]["female"]["no_pets"] += 1
                                    else:
                                        available["coupe"]["two_storey_upper"]["unisex"]["no_pets"] += 1
                    # Нижние
                    elif car["CarPlaceType"] == "Lower" or "LowerWithHigherLevelOfNoise" in car["CarPlaceType"]:
                        # Добавляем места в мужских купе
                        available["coupe"]["lower"]["male"]["no_pets"] += car["FreePlaces"].count("М")
                        # Добавляем места в женских купе
                        available["coupe"]["lower"]["female"]["no_pets"] += car["FreePlaces"].count("Ж")
                        # Добавляем места в свободных купе, то есть общие (М/Ж)
                        available["coupe"]["lower"]["free"]["no_pets"] += car["FreePlaces"].count("Ц")
                        # Добавляем места в смешанных купе (М/Ж)
                        available["coupe"]["lower"]["unisex"]["no_pets"] += car["FreePlaces"].count("С")
                # Идем по вагонам без разделения на мужские и женские купе
                else:
                    # Верхние
                    if car["CarPlaceType"] == "Upper" or "UpperWithHigherLevelOfNoise" in car["CarPlaceType"]:
                        available["coupe"]["upper"]["unisex"]["no_pets"] += car["PlaceQuantity"]
                        # Верхние на втором этаже двухэтажного поезда
                        if car["IsTwoStorey"]:
                            # Избавляемся от букв в номерах мест
                            free_places = ''
                            for char in car["FreePlaces"]:
                                if char != ' ':
                                    if char.isdigit() or char == ',':
                                        free_places += char
                            for place_num in free_places.split(","):
                                if int(place_num) > 80 and int(place_num) % 2 == 0:
                                    available["coupe"]["two_storey_upper"]["unisex"]["no_pets"] += 1
                    # Нижние
                    elif car["CarPlaceType"] == "Lower" or "LowerWithHigherLevelOfNoise" in car["CarPlaceType"]:
                        available["coupe"]["lower"]["unisex"]["no_pets"] += car["PlaceQuantity"]
                    # Для инвалидов
                    elif car["CarPlaceType"] == "InvalidsUpper" or car["CarPlaceType"] == "InvalidsLower":
                        available["coupe"]["disabled"]["no_pets"] += car["PlaceQuantity"]
            # Провоз животных разрешен
            else:
                # Проверяем, есть ли разделение на мужские и женские купе
                if "МЖ" in car["CarDescription"]:
                    # Верхние
                    if car["CarPlaceType"] == "Upper" or "UpperWithHigherLevelOfNoise" in car["CarPlaceType"]:
                        # Добавляем места в мужских купе
                        available["coupe"]["upper"]["male"]["pets"] += car["FreePlaces"].count("М")
                        # Добавляем места в женских купе
                        available["coupe"]["upper"]["female"]["pets"] += car["FreePlaces"].count("Ж")
                        # Добавляем места в свободных купе, то есть общие (М/Ж)
                        available["coupe"]["upper"]["free"]["pets"] += car["FreePlaces"].count("Ц")
                        # Добавляем места в смешанных купе (М/Ж)
                        available["coupe"]["upper"]["unisex"]["pets"] += car["FreePlaces"].count("С")
                        # Верхние на втором этаже двухэтажного поезда
                        if car["IsTwoStorey"]:
                            for place_num in car["FreePlaces"].split(","):
                                if int(place_num[:-1]) > 80 and int(place_num[:-1]) % 2 == 0:
                                    if place_num[-1] == "М":
                                        available["coupe"]["two_storey_upper"]["male"]["pets"] += 1
                                    elif place_num[-1] == "Ж":
                                        available["coupe"]["two_storey_upper"]["female"]["pets"] += 1
                                    else:
                                        available["coupe"]["two_storey_upper"]["unisex"]["pets"] += 1
                    # Нижние
                    elif car["CarPlaceType"] == "Lower" or "LowerWithHigherLevelOfNoise" in car["CarPlaceType"]:
                        # Добавляем места в мужских купе
                        available["coupe"]["lower"]["male"]["pets"] += car["FreePlaces"].count("М")
                        # Добавляем места в женских купе
                        available["coupe"]["lower"]["female"]["pets"] += car["FreePlaces"].count("Ж")
                        # Добавляем места в свободных купе, то есть общие (М/Ж)
                        available["coupe"]["lower"]["free"]["pets"] += car["FreePlaces"].count("Ц")
                        # Добавляем места в смешанных купе (М/Ж)
                        available["coupe"]["lower"]["unisex"]["pets"] += car["FreePlaces"].count("С")
                # Идем по вагонам без разделения на мужские и женские купе
                else:
                    # Верхние
                    if car["CarPlaceType"] == "Upper" or "UpperWithHigherLevelOfNoise" in car["CarPlaceType"]:
                        available["coupe"]["upper"]["unisex"]["pets"] += car["PlaceQuantity"]
                        # Верхние на втором этаже двухэтажного поезда
                        if car["IsTwoStorey"]:
                            # Избавляемся от букв в номерах мест
                            free_places = ''
                            for char in car["FreePlaces"]:
                                if char != ' ':
                                    if char.isdigit() or char == ',':
                                        free_places += char
                            for place_num in free_places.split(","):
                                if int(place_num) > 80 and int(place_num) % 2 == 0:
                                    available["coupe"]["two_storey_upper"]["unisex"]["pets"] += 1
                    # Нижние
                    elif car["CarPlaceType"] == "Lower" or "LowerWithHigherLevelOfNoise" in car["CarPlaceType"]:
                        available["coupe"]["lower"]["unisex"]["pets"] += car["PlaceQuantity"]
        # Считаем места в CB
        elif car["CarType"] == "Luxury":
            # Идем по вагонам без провоза животных
            if car["ServiceClass"] in no_pets_class:
                # Проверяем, есть ли разделение на мужские и женские купе
                if "МЖ" in car["CarDescription"]:
                    # Верхние
                    if car["CarPlaceType"] == "Upper" or "UpperWithHigherLevelOfNoise" in car["CarPlaceType"]:
                        # Добавляем места в мужских купе
                        available["lux"]["upper"]["male"]["no_pets"] += car["FreePlaces"].count("М")
                        # Добавляем места в женских купе
                        available["lux"]["upper"]["female"]["no_pets"] += car["FreePlaces"].count("Ж")
                        # Добавляем места в свободных купе, то есть общие (М/Ж)
                        available["lux"]["upper"]["free"]["no_pets"] += car["FreePlaces"].count("Ц")
                        # Добавляем места в смешанных купе (М/Ж)
                        available["lux"]["upper"]["unisex"]["no_pets"] += car["FreePlaces"].count("С")
                    # Нижние
                    elif car["CarPlaceType"] == "Lower" or "LowerWithHigherLevelOfNoise" in car["CarPlaceType"]:
                        # Добавляем места в мужских купе
                        available["lux"]["lower"]["male"]["no_pets"] += car["FreePlaces"].count("М")
                        # Добавляем места в женских купе
                        available["lux"]["lower"]["female"]["no_pets"] += car["FreePlaces"].count("Ж")
                        # Добавляем места в свободных купе, то есть общие (М/Ж)
                        available["lux"]["lower"]["free"]["no_pets"] += car["FreePlaces"].count("Ц")
                        # Добавляем места в смешанных купе (М/Ж)
                        available["lux"]["lower"]["unisex"]["no_pets"] += car["FreePlaces"].count("С")
                # Идем по вагонам без разделения на мужские и женские купе
                else:
                    # Верхние
                    if car["CarPlaceType"] == "Upper" or "UpperWithHigherLevelOfNoise" in car["CarPlaceType"]:
                        available["lux"]["upper"]["unisex"]["no_pets"] += car["PlaceQuantity"]
                    # Нижние
                    elif car["CarPlaceType"] == "Lower" or "LowerWithHigherLevelOfNoise" in car["CarPlaceType"]:
                        available["lux"]["lower"]["unisex"]["no_pets"] += car["PlaceQuantity"]
            # Провоз животных разрешен
            else:
                # Проверяем, есть ли разделение на мужские и женские купе
                if "МЖ" in car["CarDescription"]:
                    # Верхние
                    if car["CarPlaceType"] == "Upper" or "UpperWithHigherLevelOfNoise" in car["CarPlaceType"]:
                        # Добавляем места в мужских купе
                        available["lux"]["upper"]["male"]["pets"] += car["FreePlaces"].count("М")
                        # Добавляем места в женских купе
                        available["lux"]["upper"]["female"]["pets"] += car["FreePlaces"].count("Ж")
                        # Добавляем места в свободных купе, то есть общие (М/Ж)
                        available["lux"]["upper"]["free"]["pets"] += car["FreePlaces"].count("Ц")
                        # Добавляем места в смешанных купе (М/Ж)
                        available["lux"]["upper"]["unisex"]["pets"] += car["FreePlaces"].count("С")
                    # Нижние
                    elif car["CarPlaceType"] == "Lower" or "LowerWithHigherLevelOfNoise" in car["CarPlaceType"]:
                        # Добавляем места в мужских купе
                        available["lux"]["lower"]["male"]["pets"] += car["FreePlaces"].count("М")
                        # Добавляем места в женских купе
                        available["lux"]["lower"]["female"]["pets"] += car["FreePlaces"].count("Ж")
                        # Добавляем места в свободных купе, то есть общие (М/Ж)
                        available["lux"]["lower"]["free"]["pets"] += car["FreePlaces"].count("Ц")
                        # Добавляем места в смешанных купе (М/Ж)
                        available["lux"]["lower"]["unisex"]["pets"] += car["FreePlaces"].count("С")
                # Идем по вагонам без разделения на мужские и женские купе
                else:
                    # Верхние
                    if car["CarPlaceType"] == "Upper" or "UpperWithHigherLevelOfNoise" in car["CarPlaceType"]:
                        available["lux"]["upper"]["unisex"]["pets"] += car["PlaceQuantity"]
                    # Нижние
                    elif car["CarPlaceType"] == "Lower" or "LowerWithHigherLevelOfNoise" in car["CarPlaceType"]:
                        available["lux"]["lower"]["unisex"]["pets"] += car["PlaceQuantity"]

    return available
