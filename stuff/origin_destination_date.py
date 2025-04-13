import json

# Открываем базу станций

stations = open("../monitor_tickets_rzd_bot/stations v2.0.json")

# Конвертируем json в словарь

statoins_dict = json.load(stations)

stations.close()


# Функция, которая будет искать необходимую пользователю станцию в базе и выдавать до 8 станций, найденных по его
# запросу

def station_select(search_query):
    match_expresscode = [0]

    match_count = 1

    for station in range(len(statoins_dict)):
        if search_query.title() in statoins_dict[station]["name"][:len(search_query)]:
            print("{} - {}\n".format(match_count, statoins_dict[station]["name"]))
            match_expresscode.append(statoins_dict[station]["expressCode"])
            match_count += 1
        if match_count == 11:
            break

    while match_count > 1:

        print("\nПожалуйста, выберете станцию из списка.\nЕсли необходимой станции нет в списке, убедитесь, "
              "что правильно ввели название.\n")
        print("Чтобы закрыть бота, введите 'Стоп'.")

        user_select = input()

        if user_select.title() == "Стоп":
            return 0

        if user_select.isdigit() and int(user_select) in range(1, match_count):
            return match_expresscode[int(user_select)]
        else:
            if not user_select.isdigit():
                print("Пожалуйста, введите цифру.")
                continue
            elif int(user_select) not in range(1, match_count):
                print("\nВведите цифру от 1 до {}".format(match_count - 1))

    print("Станций с таким названием не найдено. Попробуем еще раз.")
    return 0


def origin_destination():
    while True:

        while True:

            print("Чтобы закрыть бота, введите 'Стоп'.")
            user_origin_query = input("Откуда едем?\n")

            if user_origin_query.title() == "Стоп":
                return 0

            origin_station = station_select(user_origin_query)

            if not origin_station:
                continue
            else:
                break

        while True:

            print("Чтобы закрыть бота, введите 'Стоп'.")
            user_destination_query = input("Куда едем?\n")

            if user_destination_query.title() == "Стоп":
                return 0

            destination_station = station_select(user_destination_query)

            if not destination_station:
                continue
            else:
                break

        if origin_station == destination_station:
            print("Пункт отправления не может совпадать с пунктом назначения. Попробуем еще раз.")
            continue
        else:
            return origin_station, destination_station


def date():
    while True:

        while True:

            print("Чтобы закрыть бота, введите 'Стоп'.")
            print("Введите дату поездки.")
            user_day_query = input("Введите день.\n")

            if user_day_query.title() == "Стоп":
                return 0

            if user_day_query.isdigit() and int(user_day_query) in range(1, 32):
                if len(user_day_query) < 2:
                    dd = "{}{}".format(0, user_day_query)
                    break
                else:
                    dd = user_day_query
                    break
            else:
                if not user_day_query.isdigit():
                    print("Пожалуйста, введите цифру.")
                    continue
                elif int(user_day_query) not in range(1, 32):
                    print("Пожалуйста, введите день от {} до {}".format(1, 31))
                    continue

        while True:

            print("Чтобы закрыть бота, введите 'Стоп'.")
            user_month_query = input("Введите месяц.\n")

            if user_month_query.title() == "Стоп":
                return 0

            if user_month_query.isdigit() and int(user_month_query) in range(1, 13):
                if len(user_month_query) < 2:
                    mm = "{}{}".format(0, user_month_query)
                    break
                else:
                    mm = user_month_query
                    break
            else:
                if not user_month_query.isdigit():
                    print("Пожалуйста, введите цифру.")
                    continue
                elif int(user_month_query) not in range(1, 13):
                    print("Пожалуйста, введите месяц от {} до {}".format(1, 12))
                    continue

        while True:

            print("Чтобы закрыть бота, введите 'Стоп'.")
            user_year_query = input("Введите год.\n")

            if user_year_query.title() == "Стоп":
                return 0

            if user_year_query.isdigit() and int(user_year_query) in range(2023, 2025):
                yyyy = user_year_query
                break
            else:
                if not user_year_query.isdigit():
                    print("Пожалуйста, введите цифру.")
                    continue
                elif int(user_year_query) not in range(2023, 2025):
                    print("Пожалуйста, введите год {} или {}".format(2023, 2024))

        print("Дата поездки: {}.{}.{}\nДата поездки указана верно? Введите Д/Н (да или нет).".format(dd, mm, yyyy))

        choice = '?'
        yes_no = ["Д", "Н"]
        while choice not in yes_no:
            print("Чтобы закрыть бота, введите 'Стоп'.")
            choice = input().upper()

            if choice.title() == "Стоп":
                return 0

            if choice not in yes_no:
                print("Введите 'Д' или 'Н'.")
                continue
            else:
                if choice == 'Д':
                    return dd, mm, yyyy
                else:
                    continue
