def passenger():
    while True:

        answers = ""

        print("Чтобы закрыть бота, введите 'Стоп'.")
        print("Укажите Ваш пол.\n1 - Мужской.\n2 - Женский.\n")
        user_gender_query = input("\n")

        if user_gender_query.title() == "Стоп":
            return 0

        if user_gender_query.isdigit() and int(user_gender_query) in range(1, 3):
            answers += user_gender_query
            break
        else:
            if not user_gender_query.isdigit():
                print("Пожалуйста, введите цифру.")
            elif int(user_gender_query) not in range(1, 3):
                print("Пожалуйста, введите цифру от {} до {}.".format(1, 2))

    while True:

        print("Чтобы закрыть бота, введите 'Стоп'.")
        print("Вам бы хотелось ехать в чисто мужском/женском купе или все равно? Разделение купе на мужские и женские "
              "доступно только для вагонов Купе и СВ.\n1 - Хочу чисто мужское/женское купе.\n2 - Все равно.\n")
        user_gender_coupe_query = input("\n")

        if user_gender_coupe_query.title() == "Стоп":
            return 0

        if user_gender_coupe_query.isdigit() and int(user_gender_coupe_query) in range(1, 3):
            answers += user_gender_coupe_query
            break
        else:
            if not user_gender_coupe_query.isdigit():
                print("Пожалуйста, введите цифру.")
            elif int(user_gender_coupe_query) not in range(1, 3):
                print("Пожалуйста, введите цифру от {} до {}.".format(1, 2))

    while True:

        print("Чтобы закрыть бота, введите 'Стоп'.")
        print("Вам бы хотелось ехать в вагоне, где провоз животных разрешен, запрещен или все равно?\n1 - Нужен вагон, "
              "где можно ехать с животными.\n2 - Нужен вагон, где нельзя ехать с животными.\n3 - Все равно.\n")

        user_pet_coupe_query = input("\n")

        if user_pet_coupe_query.title() == "Стоп":
            return 0

        if user_pet_coupe_query.isdigit() and int(user_pet_coupe_query) in range(1, 4):
            answers += user_pet_coupe_query
            break
        else:
            if not user_pet_coupe_query.isdigit():
                print("Пожалуйста, введите цифру.")
            elif int(user_pet_coupe_query) not in range(1, 3):
                print("Пожалуйста, введите цифру от {} до {}.".format(1, 3))

    """# Вот тут мы уточняем данные (надо будет понменять текст)
    print("Дата поездки: {}.{}.{}\nДата поездки указана верно? Введите Д/Н (да или нет)."

    choice = '?'
    yes_no = ["Д", "Н"]
    while choice not in yes_no:
        print("Чтобы закрыть бота, введите 'Стоп'.")
        choice = input().upper()

        if choice.title() == "Стоп":
            break
            #return 0

        if choice not in yes_no:
            print("Введите 'Д' или 'Н'.")
            continue
        else:
            if choice == 'Д':
                return dd, mm, yyyy
            else:
                continue"""

    while True:

        print("Чтобы закрыть бота, введите 'Стоп'.")
        print("Выберете тип вагона.\n1 - Плацкарт.\n2 - Купе.\n3 - СВ.\n")
        user_car_type_query = input("\n")

        if user_car_type_query.title() == "Стоп":
            return 0

        if user_car_type_query.isdigit() and int(user_car_type_query) in range(1, 4):
            answers += user_car_type_query
            break
        else:
            if not user_car_type_query.isdigit():
                print("Пожалуйста, введите цифру.")
            elif int(user_car_type_query) not in range(1, 4):
                print("Пожалуйста, введите цифру от {} до {}.".format(1, 3))

    while True:

        # Идем по плацкарту.

        if int(answers[3]) == 1:

            print("Чтобы закрыть бота, введите 'Стоп'.")
            print("Выберете место.\n1 - Нижнее.\n2 - Верхнее.\n3 - Нижнее боковое.\n4 - Верхнее боковое.\n5 - Любое.\n")
            user_seat_type_query = input("\n")

            if user_seat_type_query.title() == "Стоп":
                return 0

            if user_seat_type_query.isdigit() and int(user_seat_type_query) in range(1, 6):
                answers += user_seat_type_query
                break
            else:
                if not user_seat_type_query.isdigit():
                    print("Пожалуйста, введите цифру.")
                elif int(user_seat_type_query) not in range(1, 6):
                    print("Пожалуйста, введите цифру от {} до {}.".format(1, 5))

        # Идем по купе.
        elif int(answers[3]) == 2:

            print("Чтобы закрыть бота, введите 'Стоп'.")
            print("Выберете место.\n1 - Нижнее.\n2 - Верхнее (НО без верхних мест на втором этаже двухэтажного "
                  "поезда).\n3 - Верхнее (ВСЕ верхние места).\n4 - Места для инвалидов.\n5 - Любое (кроме мест для "
                  "инвалидов).\n")
            user_seat_type_query = input("\n")

            if user_seat_type_query.title() == "Стоп":
                return 0

            if user_seat_type_query.isdigit() and int(user_seat_type_query) in range(1, 6):
                answers += user_seat_type_query
                break
            else:
                if not user_seat_type_query.isdigit():
                    print("Пожалуйста, введите цифру.")
                elif int(user_seat_type_query) not in range(1, 6):
                    print("Пожалуйста, введите цифру от {} до {}.".format(1, 5))

        # Идем по СВ.
        elif int(answers[3]) == 3:

            print("Чтобы закрыть бота, введите 'Стоп'.")
            print(
                "Выберете место.\n1 - Нижнее.\n2 - Верхнее (ВСЕ верхние места).\n3 - Любое.\n")
            user_seat_type_query = input("\n")

            if user_seat_type_query.title() == "Стоп":
                return 0

            if user_seat_type_query.isdigit() and int(user_seat_type_query) in range(1, 4):
                answers += user_seat_type_query
                break
            else:
                if not user_seat_type_query.isdigit():
                    print("Пожалуйста, введите цифру.")
                elif int(user_seat_type_query) not in range(1, 4):
                    print("Пожалуйста, введите цифру от {} до {}.".format(1, 3))
    return answers


def places_to_monitor(answers, available):
    if int(answers[3]) == 1:
        if int(answers[4]) == 1:
            if int(answers[2]) == 1:
                return available["plaz"]["lower"]["pets"]
            elif int(answers[2]) == 2:
                return available["plaz"]["lower"]["pets"]
            elif int(answers[2]) == 3:
                return available["plaz"]["lower"]["total"]
        elif int(answers[4]) == 2:
            if int(answers[2]) == 1:
                return available["plaz"]["upper"]["pets"]
            elif int(answers[2]) == 2:
                return available["plaz"]["upper"]["pets"]
            elif int(answers[2]) == 3:
                return available["plaz"]["upper"]["total"]
        elif int(answers[4]) == 3:
            if int(answers[2]) == 1:
                return available["plaz"]["side_lower"]["pets"]
            elif int(answers[2]) == 2:
                return available["plaz"]["side_lower"]["pets"]
            elif int(answers[2]) == 3:
                return available["plaz"]["side_lower"]["total"]
        elif int(answers[4]) == 4:
            if int(answers[2]) == 1:
                return available["plaz"]["side_upper"]["pets"]
            elif int(answers[2]) == 2:
                return available["plaz"]["side_upper"]["pets"]
            elif int(answers[2]) == 3:
                return available["plaz"]["side_upper"]["total"]
        elif int(answers[4]) == 5:
            if int(answers[2]) == 1:
                return available["plaz"]["lower"]["pets"], available["plaz"]["upper"]["pets"], \
                    available["plaz"]["side_lower"]["pets"], available["plaz"]["side_upper"]["pets"]
            elif int(answers[2]) == 2:
                return available["plaz"]["lower"]["no_pets"], available["plaz"]["upper"]["no_pets"], \
                    available["plaz"]["side_lower"]["no_pets"], available["plaz"]["side_upper"]["no_pets"]
            elif int(answers[2]) == 3:
                return available["plaz"]["total"]

    elif int(answers[3]) == 2:
        if int(answers[4]) == 1:
            if int(answers[0]) == 1:
                if int(answers[1]) == 1:
                    if int(answers[2]) == 1:
                        return available["coupe"]["lower"]["male"]["pets"], available["coupe"]["lower"]["free"]["pets"]
                    elif int(answers[2]) == 2:
                        return available["coupe"]["lower"]["male"]["no_pets"], available["coupe"]["lower"]["free"][
                            "no_pets"]
                    elif int(answers[2]) == 3:
                        return available["coupe"]["lower"]["male"]["total"], available["coupe"]["lower"]["free"][
                            "total"]
                if int(answers[1]) == 2:
                    if int(answers[2]) == 1:
                        return available["coupe"]["lower"]["male"]["pets"], available["coupe"]["lower"]["free"]["pets"], \
                            available["coupe"]["lower"]["unisex"]["pets"]
                    elif int(answers[2]) == 2:
                        return available["coupe"]["lower"]["male"]["no_pets"], available["coupe"]["lower"]["free"][
                            "no_pets"], available["coupe"]["lower"]["unisex"]["no_pets"]
                    elif int(answers[2]) == 3:
                        return available["coupe"]["lower"]["male"]["total"], available["coupe"]["lower"]["free"][
                            "total"], available["coupe"]["lower"]["unisex"]["total"]
            elif int(answers[0]) == 2:
                if int(answers[1]) == 1:
                    if int(answers[2]) == 1:
                        return available["coupe"]["lower"]["female"]["pets"], available["coupe"]["lower"]["free"][
                            "pets"]
                    elif int(answers[2]) == 2:
                        return available["coupe"]["lower"]["female"]["no_pets"], available["coupe"]["lower"]["free"][
                            "no_pets"]
                    elif int(answers[2]) == 3:
                        return available["coupe"]["lower"]["female"]["total"], available["coupe"]["lower"]["free"][
                            "total"]
                if int(answers[1]) == 2:
                    if int(answers[2]) == 1:
                        return available["coupe"]["lower"]["female"]["pets"], available["coupe"]["lower"]["free"][
                            "pets"], available["coupe"]["lower"]["unisex"]["pets"]
                    elif int(answers[2]) == 2:
                        return available["coupe"]["lower"]["female"]["no_pets"], available["coupe"]["lower"]["free"][
                            "no_pets"], available["coupe"]["lower"]["unisex"]["no_pets"]
                    elif int(answers[2]) == 3:
                        return available["coupe"]["lower"]["female"]["total"], available["coupe"]["lower"]["free"][
                            "total"], available["coupe"]["lower"]["unisex"]["total"]
        elif int(answers[4]) == 2:
            if int(answers[0]) == 1:
                if int(answers[1]) == 1:
                    if int(answers[2]) == 1:
                        return available["coupe"]["upper"]["male"]["pets"], available["coupe"]["upper"]["free"]["pets"]
                    elif int(answers[2]) == 2:
                        return available["coupe"]["upper"]["male"]["no_pets"], available["coupe"]["upper"]["free"][
                            "no_pets"]
                    elif int(answers[2]) == 3:
                        return available["coupe"]["upper"]["male"]["total"], available["coupe"]["upper"]["free"][
                            "total"]
                if int(answers[1]) == 2:
                    if int(answers[2]) == 1:
                        return available["coupe"]["upper"]["male"]["pets"], available["coupe"]["upper"]["free"]["pets"], \
                            available["coupe"]["upper"]["unisex"]["pets"]
                    elif int(answers[2]) == 2:
                        return available["coupe"]["upper"]["male"]["no_pets"], available["coupe"]["upper"]["free"][
                            "no_pets"], available["coupe"]["upper"]["unisex"]["no_pets"]
                    elif int(answers[2]) == 3:
                        return available["coupe"]["upper"]["male"]["total"], available["coupe"]["upper"]["free"][
                            "total"], available["coupe"]["upper"]["unisex"]["total"]
            elif int(answers[0]) == 2:
                if int(answers[1]) == 1:
                    if int(answers[2]) == 1:
                        return available["coupe"]["upper"]["female"]["pets"], available["coupe"]["upper"]["free"][
                            "pets"]
                    elif int(answers[2]) == 2:
                        return available["coupe"]["upper"]["female"]["no_pets"], available["coupe"]["upper"]["free"][
                            "no_pets"]
                    elif int(answers[2]) == 3:
                        return available["coupe"]["upper"]["female"]["total"], available["coupe"]["upper"]["free"][
                            "total"]
                if int(answers[1]) == 2:
                    if int(answers[2]) == 1:
                        return available["coupe"]["upper"]["female"]["pets"], available["coupe"]["upper"]["free"][
                            "pets"], available["coupe"]["upper"]["unisex"]["pets"]
                    elif int(answers[2]) == 2:
                        return available["coupe"]["upper"]["female"]["no_pets"], available["coupe"]["upper"]["free"][
                            "no_pets"], available["coupe"]["upper"]["unisex"]["no_pets"]
                    elif int(answers[2]) == 3:
                        return available["coupe"]["upper"]["female"]["total"], available["coupe"]["upper"]["free"][
                            "total"], available["coupe"]["upper"]["unisex"]["total"]
        elif int(answers[4]) == 3:
            if int(answers[0]) == 1:
                if int(answers[1]) == 1:
                    if int(answers[2]) == 1:
                        return available["coupe"]["upper"]["male"]["pets"], \
                            available["coupe"]["two_storey_upper"]["male"]["pets"], available["coupe"]["upper"]["free"][
                            "pets"], \
                            available["coupe"]["two_storey_upper"]["free"]["pets"]
                    elif int(answers[2]) == 2:
                        return available["coupe"]["upper"]["male"]["no_pets"], \
                            available["coupe"]["two_storey_upper"]["male"]["no_pets"], \
                            available["coupe"]["upper"]["free"]["no_pets"], \
                            available["coupe"]["two_storey_upper"]["free"]["no_pets"]
                    elif int(answers[2]) == 3:
                        return available["coupe"]["upper"]["male"]["total"], \
                            available["coupe"]["two_storey_upper"]["male"]["total"], \
                            available["coupe"]["upper"]["free"]["total"], \
                            available["coupe"]["two_storey_upper"]["free"]["total"]
                if int(answers[1]) == 2:
                    if int(answers[2]) == 1:
                        return available["coupe"]["upper"]["male"]["pets"], available["coupe"]["upper"]["free"]["pets"], \
                            available["coupe"]["upper"]["unisex"]["pets"], \
                            available["coupe"]["two_storey_upper"]["male"]["pets"], \
                            available["coupe"]["two_storey_upper"]["free"]["pets"], \
                            available["coupe"]["two_storey_upper"]["unisex"]["pets"]
                    elif int(answers[2]) == 2:
                        return available["coupe"]["upper"]["male"]["no_pets"], available["coupe"]["upper"]["free"][
                            "no_pets"], available["coupe"]["upper"]["unisex"]["no_pets"], \
                            available["coupe"]["two_storey_upper"]["male"]["no_pets"], \
                            available["coupe"]["two_storey_upper"]["free"]["no_pets"], \
                            available["coupe"]["two_storey_upper"]["unisex"]["no_pets"]
                    elif int(answers[2]) == 3:
                        return available["coupe"]["upper"]["male"]["total"], available["coupe"]["upper"]["free"][
                            "total"], available["coupe"]["upper"]["unisex"]["total"], \
                            available["coupe"]["two_storey_upper"]["male"]["total"], \
                            available["coupe"]["two_storey_upper"]["free"]["total"], \
                            available["coupe"]["two_storey_upper"]["unisex"]["total"]
            elif int(answers[0]) == 2:
                if int(answers[1]) == 1:
                    if int(answers[2]) == 1:
                        return available["coupe"]["upper"]["female"]["pets"], \
                            available["coupe"]["two_storey_upper"]["female"]["pets"], \
                            available["coupe"]["upper"]["female"]["pets"], \
                            available["coupe"]["two_storey_upper"]["free"]["pets"]
                    elif int(answers[2]) == 2:
                        return available["coupe"]["upper"]["female"]["no_pets"], \
                            available["coupe"]["two_storey_upper"]["female"]["no_pets"], \
                            available["coupe"]["upper"]["free"]["no_pets"], \
                            available["coupe"]["two_storey_upper"]["free"]["no_pets"]
                    elif int(answers[2]) == 3:
                        return available["coupe"]["upper"]["female"]["total"], \
                            available["coupe"]["two_storey_upper"]["female"]["total"], \
                            available["coupe"]["upper"]["free"]["total"], \
                            available["coupe"]["two_storey_upper"]["free"]["total"]
                if int(answers[1]) == 2:
                    if int(answers[2]) == 1:
                        return available["coupe"]["upper"]["female"]["pets"], available["coupe"]["upper"]["free"][
                            "pets"], available["coupe"]["upper"]["unisex"]["pets"], \
                            available["coupe"]["two_storey_upper"]["female"]["pets"], \
                            available["coupe"]["two_storey_upper"]["free"]["pets"], \
                            available["coupe"]["two_storey_upper"]["unisex"]["pets"]
                    elif int(answers[2]) == 2:
                        return available["coupe"]["upper"]["female"]["no_pets"], available["coupe"]["upper"]["free"][
                            "no_pets"], available["coupe"]["upper"]["unisex"]["no_pets"], \
                            available["coupe"]["two_storey_upper"]["upper"]["no_pets"], \
                            available["coupe"]["two_storey_upper"]["free"]["no_pets"], \
                            available["coupe"]["two_storey_upper"]["unisex"]["no_pets"]
                    elif int(answers[2]) == 3:
                        return available["coupe"]["upper"]["female"]["total"], available["coupe"]["upper"]["free"][
                            "total"], available["coupe"]["upper"]["unisex"]["total"], \
                            available["coupe"]["two_storey_upper"]["female"]["total"], \
                            available["coupe"]["two_storey_upper"]["free"]["total"], \
                            available["coupe"]["two_storey_upper"]["unisex"]["total"]
        elif int(answers[4]) == 4:
            return available["coupe"]["disabled"]["total"]
        elif int(answers[4]) == 5:
            if int(answers[0]) == 1:
                if int(answers[1]) == 1:
                    if int(answers[2]) == 1:
                        return available["coupe"]["lower"]["male"]["pets"], available["coupe"]["upper"]["male"]["pets"], \
                            available["coupe"]["two_storey_upper"]["male"]["pets"], available["coupe"]["lower"]["free"][
                            "pets"], available["coupe"]["upper"]["free"]["pets"], \
                            available["coupe"]["two_storey_upper"]["free"]["pets"]
                    elif int(answers[2]) == 2:
                        return available["coupe"]["lower"]["male"]["no_pets"], available["coupe"]["upper"]["male"][
                            "no_pets"], available["coupe"]["two_storey_upper"]["male"]["no_pets"], \
                            available["coupe"]["lower"]["free"]["no_pets"], available["coupe"]["upper"]["free"][
                            "no_pets"], available["coupe"]["two_storey_upper"]["free"]["no_pets"]
                    elif int(answers[2]) == 3:
                        return available["coupe"]["lower"]["male"]["total"], available["coupe"]["upper"]["male"][
                            "total"], available["coupe"]["two_storey_upper"]["male"]["total"], \
                            available["coupe"]["lower"]["free"]["total"], available["coupe"]["free"]["male"][
                            "total"], available["coupe"]["two_storey_upper"]["free"]["total"]
                elif int(answers[1]) == 2:
                    if int(answers[2]) == 1:
                        return available["coupe"]["lower"]["male"]["pets"], available["coupe"]["upper"]["male"]["pets"], \
                            available["coupe"]["two_storey_upper"]["male"]["pets"], available["coupe"]["lower"]["free"][
                            "pets"], available["coupe"]["upper"]["free"]["pets"], \
                            available["coupe"]["two_storey_upper"]["free"]["pets"], \
                            available["coupe"]["lower"]["unisex"][
                                "pets"], available["coupe"]["upper"]["unisex"]["pets"], \
                            available["coupe"]["two_storey_upper"]["unisex"]["pets"]
                    elif int(answers[2]) == 2:
                        return available["coupe"]["lower"]["male"]["no_pets"], available["coupe"]["upper"]["male"][
                            "no_pets"], available["coupe"]["two_storey_upper"]["male"]["no_pets"], \
                            available["coupe"]["lower"]["free"]["no_pets"], available["coupe"]["upper"]["free"][
                            "no_pets"], \
                            available["coupe"]["two_storey_upper"]["free"]["no_pets"], \
                            available["coupe"]["lower"]["unisex"]["no_pets"], available["coupe"]["upper"]["unisex"][
                            "no_pets"], available["coupe"]["two_storey_upper"]["unisex"]["no_pets"]
                    elif int(answers[2]) == 3:
                        return available["coupe"]["lower"]["male"]["total"], available["coupe"]["upper"]["male"][
                            "total"], available["coupe"]["two_storey_upper"]["male"]["total"], \
                            available["coupe"]["lower"]["free"]["total"], available["coupe"]["upper"]["free"]["total"], \
                            available["coupe"]["two_storey_upper"]["free"]["total"], \
                            available["coupe"]["lower"]["unisex"][
                                "total"], available["coupe"]["upper"]["unisex"]["total"], \
                            available["coupe"]["two_storey_upper"]["unisex"]["total"]
            if int(answers[0]) == 2:
                if int(answers[1]) == 1:
                    if int(answers[2]) == 1:
                        return available["coupe"]["lower"]["female"]["pets"], available["coupe"]["upper"]["female"][
                            "pets"], available["coupe"]["two_storey_upper"]["female"]["pets"], \
                            available["coupe"]["lower"]["free"]["pets"], available["coupe"]["upper"]["free"][
                            "pets"], available["coupe"]["two_storey_upper"]["free"]["pets"]
                    elif int(answers[2]) == 2:
                        return available["coupe"]["lower"]["female"]["no_pets"], available["coupe"]["upper"]["female"][
                            "no_pets"], available["coupe"]["two_storey_upper"]["female"]["no_pets"], \
                            available["coupe"]["lower"]["free"]["no_pets"], available["coupe"]["upper"]["free"][
                            "no_pets"], available["coupe"]["two_storey_upper"]["free"]["no_pets"]
                    elif int(answers[2]) == 3:
                        return available["coupe"]["lower"]["female"]["total"], available["coupe"]["upper"]["female"][
                            "total"], available["coupe"]["two_storey_upper"]["female"]["total"], \
                            available["coupe"]["lower"]["free"]["total"], available["coupe"]["free"]["female"][
                            "total"], available["coupe"]["two_storey_upper"]["free"]["total"]
                elif int(answers[1]) == 2:
                    if int(answers[2]) == 1:
                        return available["coupe"]["lower"]["female"]["pets"], available["coupe"]["upper"]["female"][
                            "pets"], available["coupe"]["two_storey_upper"]["female"]["pets"], \
                            available["coupe"]["lower"]["free"]["pets"], available["coupe"]["upper"]["free"]["pets"], \
                            available["coupe"]["two_storey_upper"]["free"]["pets"], \
                            available["coupe"]["lower"]["unisex"][
                                "pets"], available["coupe"]["upper"]["unisex"]["pets"], \
                            available["coupe"]["two_storey_upper"]["unisex"]["pets"]
                    elif int(answers[2]) == 2:
                        return available["coupe"]["lower"]["female"]["no_pets"], available["coupe"]["upper"]["female"][
                            "no_pets"], available["coupe"]["two_storey_upper"]["female"]["no_pets"], \
                            available["coupe"]["lower"]["free"]["no_pets"], available["coupe"]["upper"]["free"][
                            "no_pets"], \
                            available["coupe"]["two_storey_upper"]["free"]["no_pets"], \
                            available["coupe"]["lower"]["unisex"]["no_pets"], available["coupe"]["upper"]["unisex"][
                            "no_pets"], available["coupe"]["two_storey_upper"]["unisex"]["no_pets"]
                    elif int(answers[2]) == 3:
                        return available["coupe"]["lower"]["female"]["total"], available["coupe"]["upper"]["female"][
                            "total"], available["coupe"]["two_storey_upper"]["female"]["total"], \
                            available["coupe"]["lower"]["free"]["total"], available["coupe"]["upper"]["free"]["total"], \
                            available["coupe"]["two_storey_upper"]["free"]["total"], \
                            available["coupe"]["lower"]["unisex"][
                                "total"], available["coupe"]["upper"]["unisex"]["total"], \
                            available["coupe"]["two_storey_upper"]["unisex"]["total"]

    elif int(answers[3]) == 3:
        if int(answers[4]) == 1:
            if int(answers[0]) == 1:
                if int(answers[1]) == 1:
                    if int(answers[2]) == 1:
                        return available["lux"]["lower"]["male"]["pets"], available["lux"]["lower"]["free"]["pets"]
                    elif int(answers[2]) == 2:
                        return available["lux"]["lower"]["male"]["no_pets"], available["lux"]["lower"]["free"][
                            "no_pets"]
                    elif int(answers[2]) == 3:
                        return available["lux"]["lower"]["male"]["total"], available["lux"]["lower"]["free"]["total"]
                if int(answers[1]) == 2:
                    if int(answers[2]) == 1:
                        return available["lux"]["lower"]["male"]["pets"], available["lux"]["lower"]["free"]["pets"], \
                            available["lux"]["lower"]["unisex"]["pets"]
                    elif int(answers[2]) == 2:
                        return available["lux"]["lower"]["male"]["no_pets"], available["lux"]["lower"]["free"][
                            "no_pets"], available["lux"]["lower"]["unisex"]["no_pets"]
                    elif int(answers[2]) == 3:
                        return available["lux"]["lower"]["male"]["total"], available["lux"]["lower"]["free"]["total"], \
                            available["lux"]["lower"]["unisex"]["total"]
            elif int(answers[0]) == 2:
                if int(answers[1]) == 1:
                    if int(answers[2]) == 1:
                        return available["lux"]["lower"]["female"]["pets"], available["lux"]["lower"]["free"]["pets"]
                    elif int(answers[2]) == 2:
                        return available["lux"]["lower"]["female"]["no_pets"], available["lux"]["lower"]["free"][
                            "no_pets"]
                    elif int(answers[2]) == 3:
                        return available["lux"]["lower"]["female"]["total"], available["lux"]["lower"]["free"]["total"]
                if int(answers[1]) == 2:
                    if int(answers[2]) == 1:
                        return available["lux"]["lower"]["female"]["pets"], available["lux"]["lower"]["free"]["pets"], \
                            available["lux"]["lower"]["unisex"]["pets"]
                    elif int(answers[2]) == 2:
                        return available["lux"]["lower"]["female"]["no_pets"], available["lux"]["lower"]["free"][
                            "no_pets"], available["lux"]["lower"]["unisex"]["no_pets"]
                    elif int(answers[2]) == 3:
                        return available["lux"]["lower"]["female"]["total"], available["lux"]["lower"]["free"]["total"], \
                            available["lux"]["lower"]["unisex"]["total"]
        elif int(answers[4]) == 2:
            if int(answers[0]) == 1:
                if int(answers[1]) == 1:
                    if int(answers[2]) == 1:
                        return available["lux"]["upper"]["male"]["pets"], available["lux"]["upper"]["free"]["pets"]
                    elif int(answers[2]) == 2:
                        return available["lux"]["upper"]["male"]["no_pets"], available["lux"]["upper"]["free"][
                            "no_pets"]
                    elif int(answers[2]) == 3:
                        return available["lux"]["upper"]["male"]["total"], available["lux"]["upper"]["free"]["total"]
                if int(answers[1]) == 2:
                    if int(answers[2]) == 1:
                        return available["lux"]["upper"]["male"]["pets"], available["lux"]["upper"]["free"]["pets"], \
                            available["lux"]["upper"]["unisex"]["pets"]
                    elif int(answers[2]) == 2:
                        return available["lux"]["upper"]["male"]["no_pets"], available["lux"]["upper"]["free"][
                            "no_pets"], available["lux"]["upper"]["unisex"]["no_pets"]
                    elif int(answers[2]) == 3:
                        return available["lux"]["upper"]["male"]["total"], available["lux"]["upper"]["free"]["total"], \
                            available["lux"]["upper"]["unisex"]["total"]
            elif int(answers[0]) == 2:
                if int(answers[1]) == 1:
                    if int(answers[2]) == 1:
                        return available["lux"]["upper"]["female"]["pets"], available["lux"]["upper"]["free"]["pets"]
                    elif int(answers[2]) == 2:
                        return available["lux"]["upper"]["female"]["no_pets"], available["lux"]["upper"]["free"][
                            "no_pets"]
                    elif int(answers[2]) == 3:
                        return available["lux"]["upper"]["female"]["total"], available["lux"]["upper"]["free"]["total"]
                if int(answers[1]) == 2:
                    if int(answers[2]) == 1:
                        return available["lux"]["upper"]["female"]["pets"], available["lux"]["upper"]["free"]["pets"], \
                            available["lux"]["upper"]["unisex"]["pets"]
                    elif int(answers[2]) == 2:
                        return available["lux"]["upper"]["female"]["no_pets"], available["lux"]["upper"]["free"][
                            "no_pets"], available["lux"]["upper"]["unisex"]["no_pets"]
                    elif int(answers[2]) == 3:
                        return available["lux"]["upper"]["female"]["total"], available["lux"]["upper"]["free"]["total"], \
                            available["lux"]["upper"]["unisex"]["total"]
        elif int(answers[4]) == 3:
            if int(answers[0]) == 1:
                if int(answers[1]) == 1:
                    if int(answers[2]) == 1:
                        return available["lux"]["lower"]["male"]["pets"], available["lux"]["upper"]["male"]["pets"], \
                            available["lux"]["lower"]["free"]["pets"], available["lux"]["upper"]["free"]["pets"]
                    elif int(answers[2]) == 2:
                        return available["lux"]["lower"]["male"]["no_pets"], available["lux"]["upper"]["male"][
                            "no_pets"], available["lux"]["lower"]["free"]["no_pets"], available["lux"]["upper"]["free"][
                            "no_pets"]
                    elif int(answers[2]) == 3:
                        return available["lux"]["lower"]["male"]["total"], available["lux"]["upper"]["male"]["total"], \
                            available["lux"]["lower"]["free"]["total"], available["lux"]["upper"]["free"]["total"]
                elif int(answers[1]) == 2:
                    if int(answers[2]) == 1:
                        return available["lux"]["lower"]["male"]["pets"], available["lux"]["upper"]["male"]["pets"], \
                            available["lux"]["lower"]["free"][
                                "pets"], available["lux"]["upper"]["free"]["pets"], available["lux"]["lower"]["unisex"][
                            "pets"], available["lux"]["upper"]["unisex"]["pets"]
                    elif int(answers[2]) == 2:
                        return available["lux"]["lower"]["male"]["no_pets"], available["lux"]["upper"]["male"][
                            "no_pets"], available["lux"]["lower"]["free"]["no_pets"], available["lux"]["upper"]["free"][
                            "no_pets"], \
                            available["lux"]["lower"]["unisex"][
                                "no_pets"], available["lux"]["upper"]["unisex"]["no_pets"],
                    elif int(answers[2]) == 3:
                        return available["lux"]["lower"]["male"]["total"], available["lux"]["upper"]["male"]["total"], \
                            available["lux"]["lower"]["free"][
                                "total"], available["lux"]["upper"]["free"]["total"], \
                            available["lux"]["lower"]["unisex"]["total"], available["lux"]["upper"]["unisex"]["total"]
            if int(answers[0]) == 2:
                if int(answers[1]) == 1:
                    if int(answers[2]) == 1:
                        return available["lux"]["lower"]["female"]["pets"], available["lux"]["upper"]["female"]["pets"], \
                            available["lux"]["lower"]["free"]["pets"], available["lux"]["upper"]["free"]["pets"]
                    elif int(answers[2]) == 2:
                        return available["lux"]["lower"]["female"]["no_pets"], available["lux"]["upper"]["female"][
                            "no_pets"], available["lux"]["lower"]["free"]["no_pets"], available["lux"]["upper"]["free"][
                            "no_pets"]
                    elif int(answers[2]) == 3:
                        return available["lux"]["lower"]["female"]["total"], available["lux"]["upper"]["female"][
                            "total"], available["lux"]["lower"]["free"]["total"], available["lux"]["upper"]["free"][
                            "total"]
                elif int(answers[1]) == 2:
                    if int(answers[2]) == 1:
                        return available["lux"]["lower"]["female"]["pets"], available["lux"]["upper"]["female"]["pets"], \
                            available["lux"]["lower"]["free"][
                                "pets"], available["lux"]["upper"]["free"]["pets"], available["lux"]["lower"]["unisex"][
                            "pets"], available["lux"]["upper"]["unisex"]["pets"]
                    elif int(answers[2]) == 2:
                        return available["lux"]["lower"]["female"]["no_pets"], available["lux"]["upper"]["female"][
                            "no_pets"], available["lux"]["lower"]["free"]["no_pets"], available["lux"]["upper"]["free"][
                            "no_pets"], available["lux"]["lower"]["unisex"]["no_pets"], \
                            available["lux"]["upper"]["unisex"]["no_pets"]
                    elif int(answers[2]) == 3:
                        return available["lux"]["lower"]["female"]["total"], available["lux"]["upper"]["female"][
                            "total"], available["lux"]["lower"]["free"]["total"], available["lux"]["upper"]["free"][
                            "total"], available["lux"]["lower"]["unisex"][
                            "total"], available["lux"]["upper"]["unisex"]["total"]
