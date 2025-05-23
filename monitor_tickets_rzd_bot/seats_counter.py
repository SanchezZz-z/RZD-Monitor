import re

NO_PETS_CAR_CLS = ["1Т", "1Х", "1Д", "2Т", "2Х", "2Ц", "2Ш", "3Э", "3Л", "3Т", "3П",]
WHOLE_COUPE_PETS_CAR_CLS = ["1Э", "1Ф", "1У", "1Л", "2Э", "2Ф",]


# Функция, убирающая из строки любые символы, кроме цифр. Нужна для гендерных купе, чтобы убрать индексы (С - смешанное,
# Ц - свободное, Ж - женское, М - мужское)
def remove_non_digits(s):
    return re.sub(r"\D", "", s)


# В вагонах типа СВ (car_type == "Люкс") и Люкс (car_type == "Мягкий") номера мест могут быть указаны через интервалы
# (например, 007-010 вместо 007, 008, 009, 010)
def parse_places(place_str):
    places = []
    for place_num in place_str.split(","):
        if len(place_num) > 4:
            for seat in range(int(place_num[:3]), int(place_num[4:7]) + 1):
                if place_num[-1].isdigit():
                    places.append(str(seat))
                else:
                    places.append(str(seat) + place_num[-1])
        else:
            places.append(place_num)
    return places


# Проверка является ли место верхним на втором этаже двухэтажного поезда
def second_level_place_check(place_num_str):
    if not place_num_str.isdigit():
        return int(place_num_str[:-1]) > 80 and int(place_num_str[:-1]) % 2 == 0
    else:
        return int(place_num_str) > 80 and int(place_num_str) % 2 == 0


class TrainSeatsCounter:
    def __init__(self, data):
        self.data = data
        self.available = {
            "coupe": self.init_coupe_data(),
            "plaz": self.init_plaz_data(),
            "lux": self.init_lux_data(),
            "premium": self.init_premium_data(),
        }

    def init_coupe_data(self):
        return {
            "total": 0,
            "upper": self.init_seat_data(),
            "two_storey_upper": self.init_seat_data(),
            "lower": self.init_seat_data(),
            "disabled": {"total": 0, "pets": {}, "pets_whole_coupe": {}, "no_pets": {}},
        }

    def init_plaz_data(self):
        return {
            "total": 0,
            "upper": {"total": 0, "pets": {}, "no_pets": {}},
            "side_upper": {"total": 0, "pets": {}, "no_pets": {}},
            "lower": {"total": 0, "pets": {}, "no_pets": {}},
            "side_lower": {"total": 0, "pets": {}, "no_pets": {}},
        }

    def init_lux_data(self):
        return {
            "total": 0,
            "upper": self.init_seat_data(),
            "lower": self.init_seat_data(),
        }

    def init_premium_data(self):
        return {"total": 0, "whole_coupe": {"total": 0, "pets_whole_coupe": {}}}

    def init_seat_data(self):
        return {
            "total": 0,
            "male": {"total": 0, "pets": {}, "pets_whole_coupe": {}, "no_pets": {}},
            "female": {"total": 0, "pets": {}, "pets_whole_coupe": {}, "no_pets": {}},
            "free": {"total": 0, "pets": {}, "pets_whole_coupe": {}, "no_pets": {}},
            "unisex": {"total": 0, "pets": {}, "pets_whole_coupe": {}, "no_pets": {}},
        }

    def count_seats(self):

        for car in self.data["result"]["lst"][0]["cars"]:

            car_number = int(car["cnumber"])
            car_type = car["type"]
            car_cls = car["clsType"]
            add_signs = car.get("addSigns", "")

            if car_type == "Плац":

                for seat in car["seats"]:
                    self.update_plaz_seats(car_number, seat, car_cls in NO_PETS_CAR_CLS)

            elif car_type == "Купе":

                for seat in car["seats"]:
                    self.update_coupe_seats(car_number, seat, car_cls, "МЖ" in add_signs,
                                            car.get("bDeck2", False), "tariffNonRef" in seat.keys())

            elif car_type == "Люкс":

                places = parse_places(car["places"])

                for seat in car["seats"]:
                    self.update_lux_seats(car_number, seat, car_cls, "МЖ" in add_signs, places)

            elif car_type == "Мягкий":

                places = parse_places(car["places"])

                price = int(car["tariff"])
                self.update_premium_seats(car_number, "pets_whole_coupe", places, price)

    def update_plaz_seats(self, car_number, seat, no_pets):

        pet_status = "no_pets" if no_pets else "pets"
        seat_type = seat["type"]
        seat_label = seat["label"]
        free_seats = seat["places"].split(",")
        price = int(seat["tariff"])

        seat_map = {
            "up": "upper",
            "dn": "lower",
            "lup": "side_upper",
            "ldn": "side_lower",
        }

        if seat_label == "Последнее купе, верхнее":
            seat_type = "up"
        elif seat_label == "Последнее купе, нижнее":
            seat_type = "dn"
        elif seat_label == "Боковое верхнее у туалета":
            seat_type = "lup"
        elif seat_label == "Боковое нижнее у туалета":
            seat_type = "ldn"

        seat_key = seat_map.get(seat_type)
        if seat_key:
            self.available["plaz"][seat_key][pet_status][car_number] = \
                (self.available["plaz"][seat_key][pet_status].get(car_number, []) +
                 [(place_num.lstrip("0"), price) for place_num in free_seats])

    def update_coupe_seats(self, car_number, seat, car_cls, has_gender_split, two_storey, no_refund_tariff_available):

        if car_cls in NO_PETS_CAR_CLS:
            pet_status = "no_pets"
        elif car_cls in WHOLE_COUPE_PETS_CAR_CLS:
            pet_status = "pets_whole_coupe"
        else:
            pet_status = "pets"

        seat_type = seat["type"]
        places = seat["places"].split(",")
        price = int(seat["tariff"])
        price_non_refundable = seat["tariff2"]

        if price_non_refundable is not None:
            price_non_refundable = int(price_non_refundable)
            price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

        if has_gender_split:

            if no_refund_tariff_available:

                self.update_gender_split_coupe(car_number, pet_status, seat_type, places, two_storey, price,
                                               price_non_refundable)

            else:

                self.update_gender_split_coupe(car_number, pet_status, seat_type, places, two_storey, price)

        else:

            if no_refund_tariff_available:

                self.update_unisex_coupe(car_number, places, pet_status, seat_type, two_storey, price,
                                         price_non_refundable)

            else:

                self.update_unisex_coupe(car_number, places, pet_status, seat_type, two_storey, price)

    def update_gender_split_coupe(self, car_number, pet_status, seat_type, places, two_storey, price,
                                  price_non_refundable=None):

        male_places, female_places, free_places, unisex_places = [], [], [], []

        for place_num in places:
            cleaned_place_num = remove_non_digits(place_num.lstrip("0"))
            if "М" in place_num:
                male_places.append(cleaned_place_num)
            elif "Ж" in place_num:
                female_places.append(cleaned_place_num)
            elif "Ц" in place_num:
                free_places.append(cleaned_place_num)
            # Перечень свободных мест может быть записан в виде "002,004,024С"
            # Места в смешанных купе вообще могут идти без буквы в конце
            else:
                unisex_places.append(cleaned_place_num)

        if seat_type in ["up", "lastup"]:

            self.update_coupe_upper(car_number, "male", pet_status, male_places, two_storey, price,
                                    price_non_refundable)
            self.update_coupe_upper(car_number, "female", pet_status, female_places, two_storey, price,
                                    price_non_refundable)
            self.update_coupe_upper(car_number, "free", pet_status, free_places, two_storey, price,
                                    price_non_refundable)
            self.update_coupe_upper(car_number, "unisex", pet_status, unisex_places, two_storey, price,
                                    price_non_refundable)

        elif seat_type in ["dn", "lastdn"]:

            if price_non_refundable is not None:

                self.available["coupe"]["lower"]["male"][pet_status][car_number] = \
                    (self.available["coupe"]["lower"]["male"][pet_status].get(car_number, []) +
                     [(remove_non_digits(place_num.lstrip("0")), price, price_non_refundable) for place_num in
                      male_places])

                self.available["coupe"]["lower"]["female"][pet_status][car_number] = \
                    (self.available["coupe"]["lower"]["female"][pet_status].get(car_number, []) +
                     [(remove_non_digits(place_num.lstrip("0")), price, price_non_refundable) for place_num in
                      female_places])

                self.available["coupe"]["lower"]["free"][pet_status][car_number] = \
                    (self.available["coupe"]["lower"]["free"][pet_status].get(car_number, []) +
                     [(remove_non_digits(place_num.lstrip("0")), price, price_non_refundable) for place_num in
                      free_places])

                self.available["coupe"]["lower"]["unisex"][pet_status][car_number] = \
                    (self.available["coupe"]["lower"]["unisex"][pet_status].get(car_number, []) +
                     [(remove_non_digits(place_num.lstrip("0")), price, price_non_refundable) for place_num in
                      unisex_places])

            else:

                self.available["coupe"]["lower"]["male"][pet_status][car_number] = \
                    (self.available["coupe"]["lower"]["male"][pet_status].get(car_number, []) +
                     [(remove_non_digits(place_num.lstrip("0")), price) for place_num in male_places])

                self.available["coupe"]["lower"]["female"][pet_status][car_number] = \
                    (self.available["coupe"]["lower"]["female"][pet_status].get(car_number, []) +
                     [(remove_non_digits(place_num.lstrip("0")), price) for place_num in female_places])

                self.available["coupe"]["lower"]["free"][pet_status][car_number] = \
                    (self.available["coupe"]["lower"]["free"][pet_status].get(car_number, []) +
                     [(remove_non_digits(place_num.lstrip("0")), price) for place_num in free_places])

                self.available["coupe"]["lower"]["unisex"][pet_status][car_number] = \
                    (self.available["coupe"]["lower"]["unisex"][pet_status].get(car_number, []) +
                     [(remove_non_digits(place_num.lstrip("0")), price) for place_num in unisex_places])

    def update_unisex_coupe(self, car_number, places, pet_status, seat_type, two_storey, price,
                            price_non_refundable=None):

        if price_non_refundable is not None:

            if seat_type in ["up", "lastup"]:

                self.update_coupe_upper(car_number, "unisex", pet_status, places, two_storey, price,
                                        price_non_refundable)

            elif seat_type in ["dn", "lastdn"]:

                self.available["coupe"]["lower"]["unisex"][pet_status][car_number] = \
                    (self.available["coupe"]["lower"]["unisex"][pet_status].get(car_number, []) +
                     [(remove_non_digits(place_num.lstrip("0")), price, price_non_refundable) for place_num in places])

            elif seat_type in ["invalid_lower", "invalid_upper"]:

                self.available["coupe"]["disabled"][pet_status][car_number] = \
                    (self.available["coupe"]["disabled"][pet_status].get(car_number, []) +
                     [(remove_non_digits(place_num.lstrip("0")), price, price_non_refundable) for place_num in places])

        else:

            if seat_type in ["up", "lastup"]:

                self.update_coupe_upper(car_number, "unisex", pet_status, places, two_storey, price)

            elif seat_type in ["dn", "lastdn"]:

                self.available["coupe"]["lower"]["unisex"][pet_status][car_number] = \
                    (self.available["coupe"]["lower"]["unisex"][pet_status].get(car_number, []) +
                     [(remove_non_digits(place_num.lstrip("0")), price) for place_num in places])

            elif seat_type in ["invalid_lower", "invalid_upper"]:

                self.available["coupe"]["disabled"][pet_status][car_number] = \
                    (self.available["coupe"]["disabled"][pet_status].get(car_number, []) +
                     [(remove_non_digits(place_num.lstrip("0")), price) for place_num in places])

    def update_coupe_upper(self, car_number, gender, pet_status, places, two_storey, price, price_non_refundable=None):

        if price_non_refundable is not None:
            for place_num in places:
                if two_storey:
                    if second_level_place_check(place_num):

                        self.available["coupe"]["two_storey_upper"][gender][pet_status][car_number] = \
                            self.available["coupe"]["two_storey_upper"][gender][pet_status].get(car_number, [])
                        (self.available["coupe"]["two_storey_upper"][gender][pet_status][car_number]
                         .append((remove_non_digits(place_num.lstrip("0")), price, price_non_refundable)))

                    else:

                        self.available["coupe"]["upper"][gender][pet_status][car_number] = \
                            self.available["coupe"]["upper"][gender][pet_status].get(car_number, [])
                        (self.available["coupe"]["upper"][gender][pet_status][car_number]
                         .append((remove_non_digits(place_num.lstrip("0")), price, price_non_refundable)))
                else:

                    self.available["coupe"]["upper"][gender][pet_status][car_number] = \
                        self.available["coupe"]["upper"][gender][pet_status].get(car_number, [])
                    (self.available["coupe"]["upper"][gender][pet_status][car_number]
                     .append((remove_non_digits(place_num.lstrip("0")), price, price_non_refundable)))

        else:
            for place_num in places:
                if two_storey:
                    if second_level_place_check(place_num):

                        self.available["coupe"]["two_storey_upper"][gender][pet_status][car_number] = \
                            self.available["coupe"]["two_storey_upper"][gender][pet_status].get(car_number, [])
                        (self.available["coupe"]["two_storey_upper"][gender][pet_status][car_number]
                         .append((remove_non_digits(place_num.lstrip("0")), price)))

                    else:

                        self.available["coupe"]["upper"][gender][pet_status][car_number] = \
                            self.available["coupe"]["upper"][gender][pet_status].get(car_number, [])
                        (self.available["coupe"]["upper"][gender][pet_status][car_number]
                         .append((remove_non_digits(place_num.lstrip("0")), price)))
                else:

                    self.available["coupe"]["upper"][gender][pet_status][car_number] = \
                        self.available["coupe"]["upper"][gender][pet_status].get(car_number, [])
                    (self.available["coupe"]["upper"][gender][pet_status][car_number]
                     .append((remove_non_digits(place_num.lstrip("0")), price)))

    def update_lux_seats(self, car_number, seat, car_cls, has_gender_split, places):

        if car_cls in NO_PETS_CAR_CLS:
            pet_status = "no_pets"
        elif car_cls in WHOLE_COUPE_PETS_CAR_CLS:
            pet_status = "pets_whole_coupe"
        else:
            pet_status = "pets"

        seat_type = seat["type"]
        price = int(seat["tariff"])

        if has_gender_split:
            for place_num in places:
                if seat_type in ["up", "lastup"]:

                    self.update_lux_gender_split(car_number, "upper", pet_status, place_num, price)

                elif seat_type in ["dn", "lastdn"]:

                    self.update_lux_gender_split(car_number, "lower", pet_status, place_num, price)
        else:

            if seat_type in ["up", "lastup"]:

                self.available["lux"]["upper"]["unisex"][pet_status][car_number] = \
                    (self.available["lux"]["upper"]["unisex"][pet_status].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in places])

            elif seat_type in ["dn", "lastdn"]:

                self.available["lux"]["lower"]["unisex"][pet_status][car_number] = \
                    (self.available["lux"]["lower"]["unisex"][pet_status].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in places])

    def update_lux_gender_split(self, car_number, level, pet_status, place_num, price):

        if "М" in place_num:

            self.available["lux"][level]["male"][pet_status][car_number] = \
                self.available["lux"][level]["male"][pet_status].get(car_number, [])
            (self.available["lux"][level]["male"][pet_status][car_number]
             .append((remove_non_digits(place_num.lstrip("0")), price)))

        elif "Ж" in place_num:

            self.available["lux"][level]["female"][pet_status][car_number] = \
                self.available["lux"][level]["female"][pet_status].get(car_number, [])
            (self.available["lux"][level]["female"][pet_status][car_number]
             .append((remove_non_digits(place_num.lstrip("0")), price)))

        elif "Ц" in place_num:

            self.available["lux"][level]["free"][pet_status][car_number] = \
                self.available["lux"][level]["free"][pet_status].get(car_number, [])
            (self.available["lux"][level]["free"][pet_status][car_number]
             .append((remove_non_digits(place_num.lstrip("0")), price)))

        else:

            self.available["lux"][level]["unisex"][pet_status][car_number] = \
                self.available["lux"][level]["unisex"][pet_status].get(car_number, [])
            (self.available["lux"][level]["unisex"][pet_status][car_number]
             .append((remove_non_digits(place_num.lstrip("0")), price)))

    def update_premium_seats(self, car_number, pet_status, places, price):

        for place_num in places:
            self.available["premium"]["whole_coupe"][pet_status][car_number] = \
                self.available["premium"]["whole_coupe"][pet_status].get(car_number, [])
            (self.available["premium"]["whole_coupe"][pet_status][car_number]
             .append((place_num.lstrip("0"), price)))

    # Этот метод чисто для быстрой проверки, что количество мест посчитано верно
    # По факту он не используется (он реализован немного коряво, но считает правильно)

    def get_available_seats(self, data=None):

        if data is None:
            data = self.available

        if isinstance(data, dict):
            total = 0
            for key, value in data.items():
                if key == "total":
                    continue
                if isinstance(value, dict):
                    # Рекурсивный вызов метода update_totals
                    self.get_available_seats(value)
                    total += value.get("total", 0)
                elif isinstance(value, list):
                    total += len(value)
            data["total"] = total

        return self.available


class SapsanSeatsCounter:
    def __init__(self, data):
        self.data = data
        self.available = {
            "first_class": self.init_first_class_data(),
            "negotiation_coupe": self.init_negotiation_coupe_data(),
            "business_coupe": self.init_business_coupe_data(),
            "business_class": self.init_business_class_data(),
            "coupe_suite": self.init_coupe_suite_data(),
            "bistro_car": self.init_bistro_data(),
            "family": self.init_family_data(),
            "eco_plus": self.init_eco_plus_data(),
            "eco": self.init_eco_data(),
            "base": self.init_base_data(),
        }

    def init_first_class_data(self):
        return {
            "total": 0,
            "forward": {"total": 0, "no_table": {}, "separate": {}},
            "backwards": {"total": 0, "no_table": {}},
        }

    def init_negotiation_coupe_data(self):
        return {
            "total": 0,
            "coupe": {"total": 0, "seats": {}},
        }

    def init_business_coupe_data(self):
        return {
            "total": 0,
            "coupe": {"total": 0, "seats": {}},
        }

    def init_business_class_data(self):
        return {
            "total": 0,
            "forward": {"total": 0, "no_table": {}, "table": {}},
            "backwards": {"total": 0, "no_table": {}, "table": {}},
        }

    def init_coupe_suite_data(self):
        return {
            "total": 0,
            "coupe": {"total": 0, "seats": {}},
        }

    def init_bistro_data(self):
        return {
            "total": 0,
            "forward": {"total": 0, "table": {}},
            "backwards": {"total": 0, "table": {}},
        }

    def init_family_data(self):
        return {
            "total": 0,
            "forward": {"total": 0, "no_table": {}, "table": {}},
            "kids": {"total": 0, "seats": {}},
        }

    def init_eco_plus_data(self):
        return {
            "total": 0,
            "forward": {"total": 0, "no_table": {}, "table": {}},
            "backwards": {"total": 0, "no_table": {}, "table": {}},
            "kids": {"total": 0, "seats": {}},
            "babies": {"total": 0, "seats": {}},
        }

    def init_eco_data(self):
        return {
            "total": 0,
            "forward": {"total": 0, "no_table": {}, "table": {}, "no_window": {}},
            "backwards": {"total": 0, "no_table": {}, "table": {}, "no_window": {}},
            "pets": {"total": 0, "seats": {}},
            "disabled": {"total": 0, "seats": {}},
        }

    def init_base_data(self):
        return {
            "total": 0,
            "forward": {"total": 0, "no_table": {}, "table": {}, "no_window": {}},
            "backwards": {"total": 0, "no_table": {}, "table": {}, "no_window": {}},
        }

    def count_seats(self):

        for car in self.data["result"]["lst"][0]["cars"]:

            car_number = int(car["cnumber"])
            car_type = car["catLabelLoc"]

            if car_type == "Первый класс":

                for seat in car["seats"]:
                    self.update_first_class_seats(car_number, seat)

            elif car_type == "Купе-переговорная":

                for seat in car["seats"]:
                    self.update_negotiation_coupe_seats(car_number, seat)

            elif car_type == "Бизнес-купе":

                for seat in car["seats"]:
                    self.update_business_coupe_seats(car_number, seat)

            elif car_type == "Бизнес класс":

                for seat in car["seats"]:
                    self.update_business_class_seats(car_number, seat)

            elif car_type == "Купе-Сьют":

                for seat in car["seats"]:
                    self.update_coupe_suite_seats(car_number, seat)

            elif car_type == "Вагон-бистро":

                for seat in car["seats"]:
                    self.update_bistro_seats(car_number, seat)

            elif car_type == "Семейный":

                for seat in car["seats"]:
                    self.update_family_seats(car_number, seat)

            elif car_type == "Эконом+":

                for seat in car["seats"]:
                    self.update_eco_plus_seats(car_number, seat)

            elif car_type == "Эконом":

                for seat in car["seats"]:
                    self.update_eco_seats(car_number, seat)

            elif car_type == "Базовый":

                for seat in car["seats"]:
                    self.update_base_seats(car_number, seat)

    def update_first_class_seats(self, car_number, seat):

        seat_type = seat["label"].replace(",", "")
        free_seats = parse_places(seat["places"]) if "-" in seat["places"] else seat["places"].split(",")
        price = int(seat["tariff"])
        price_non_refundable = seat["tariff2"]

        if seat_type == "Не у стола против хода":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["first_class"]["backwards"]["no_table"][car_number] = \
                    (self.available["first_class"]["backwards"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["first_class"]["backwards"]["no_table"][car_number] = \
                    (self.available["first_class"]["backwards"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "Не у стола по ходу":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["first_class"]["forward"]["no_table"][car_number] = \
                    (self.available["first_class"]["forward"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["first_class"]["forward"]["no_table"][car_number] = \
                    (self.available["first_class"]["forward"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "Свободные места":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["first_class"]["forward"]["separate"][car_number] = \
                    (self.available["first_class"]["forward"]["separate"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["first_class"]["forward"]["separate"][car_number] = \
                    (self.available["first_class"]["forward"]["separate"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

    def update_negotiation_coupe_seats(self, car_number, seat):

        free_seats = parse_places(seat["places"]) if "-" in seat["places"] else seat["places"].split(",")
        price = int(seat["tariff"])
        price_non_refundable = seat["tariff2"]

        if price_non_refundable is not None:

            price_non_refundable = int(price_non_refundable)
            price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

            self.available["negotiation_coupe"]["coupe"]["seats"][car_number] = \
                (self.available["negotiation_coupe"]["coupe"]["seats"].get(car_number, []) +
                 [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

        else:

            self.available["negotiation_coupe"]["coupe"]["seats"][car_number] = \
                (self.available["negotiation_coupe"]["coupe"]["seats"].get(car_number, []) +
                 [(place_num.lstrip("0"), price) for place_num in free_seats])

    def update_business_coupe_seats(self, car_number, seat):

        free_seats = parse_places(seat["places"]) if "-" in seat["places"] else seat["places"].split(",")
        price = int(seat["tariff"])
        price_non_refundable = seat["tariff2"]

        if price_non_refundable is not None:

            price_non_refundable = int(price_non_refundable)
            price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

            self.available["business_coupe"]["coupe"]["seats"][car_number] = \
                (self.available["business_coupe"]["coupe"]["seats"].get(car_number, []) +
                 [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

        else:

            self.available["business_coupe"]["coupe"]["seats"][car_number] = \
                (self.available["business_coupe"]["coupe"]["seats"].get(car_number, []) +
                 [(place_num.lstrip("0"), price) for place_num in free_seats])

    def update_business_class_seats(self, car_number, seat):

        seat_type = seat["label"].replace(",", "")
        free_seats = parse_places(seat["places"]) if "-" in seat["places"] else seat["places"].split(",")
        price = int(seat["tariff"])
        price_non_refundable = seat["tariff2"]

        if seat_type == "Не у стола против хода":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["business_class"]["backwards"]["no_table"][car_number] = \
                    (self.available["business_class"]["backwards"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["business_class"]["backwards"]["no_table"][car_number] = \
                    (self.available["business_class"]["backwards"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "Не у стола по ходу":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["business_class"]["forward"]["no_table"][car_number] = \
                    (self.available["business_class"]["forward"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["business_class"]["forward"]["no_table"][car_number] = \
                    (self.available["business_class"]["forward"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "У стола против хода":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["business_class"]["backwards"]["table"][car_number] = \
                    (self.available["business_class"]["backwards"]["table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["business_class"]["backwards"]["table"][car_number] = \
                    (self.available["business_class"]["backwards"]["table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "У стола по ходу":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["business_class"]["forward"]["table"][car_number] = \
                    (self.available["business_class"]["forward"]["table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["business_class"]["forward"]["table"][car_number] = \
                    (self.available["business_class"]["forward"]["table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

    def update_coupe_suite_seats(self, car_number, seat):

        free_seats = parse_places(seat["places"]) if "-" in seat["places"] else seat["places"].split(",")
        price = int(seat["tariff"])
        price_non_refundable = seat["tariff2"]

        if price_non_refundable is not None:

            price_non_refundable = int(price_non_refundable)
            price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

            self.available["coupe_suite"]["coupe"]["seats"][car_number] = \
                (self.available["coupe_suite"]["coupe"]["seats"].get(car_number, []) +
                 [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

        else:

            self.available["coupe_suite"]["coupe"]["seats"][car_number] = \
                (self.available["coupe_suite"]["coupe"]["seats"].get(car_number, []) +
                 [(place_num.lstrip("0"), price) for place_num in free_seats])

    def update_bistro_seats(self, car_number, seat):

        seat_type = seat["label"].replace(",", "")
        free_seats = parse_places(seat["places"]) if "-" in seat["places"] else seat["places"].split(",")
        price = int(seat["tariff"])
        price_non_refundable = seat["tariff2"]

        if seat_type == "У стола против хода":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["bistro_car"]["backwards"]["table"][car_number] = \
                    (self.available["bistro_car"]["backwards"]["table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["bistro_car"]["backwards"]["table"][car_number] = \
                    (self.available["bistro_car"]["backwards"]["table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "У стола по ходу":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["bistro_car"]["forward"]["table"][car_number] = \
                    (self.available["bistro_car"]["forward"]["table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["bistro_car"]["forward"]["table"][car_number] = \
                    (self.available["bistro_car"]["forward"]["table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

    def update_family_seats(self, car_number, seat):

        seat_type = seat["label"].replace(",", "")
        free_seats = parse_places(seat["places"]) if "-" in seat["places"] else seat["places"].split(",")
        price = int(seat["tariff"])
        price_non_refundable = seat["tariff2"]

        if seat_type == "Не у стола по ходу":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["family"]["forward"]["no_table"][car_number] = \
                    (self.available["family"]["forward"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["family"]["forward"]["no_table"][car_number] = \
                    (self.available["family"]["forward"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "Место пассажира с детьми":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["family"]["kids"]["seats"][car_number] = \
                    (self.available["family"]["kids"]["seats"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["family"]["kids"]["seats"][car_number] = \
                    (self.available["family"]["kids"]["seats"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

    def update_eco_plus_seats(self, car_number, seat):

        seat_type = seat["label"].replace(",", "")
        free_seats = parse_places(seat["places"]) if "-" in seat["places"] else seat["places"].split(",")
        price = int(seat["tariff"])
        price_non_refundable = seat["tariff2"]

        if seat_type == "Не у стола против хода":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["eco_plus"]["backwards"]["no_table"][car_number] = \
                    (self.available["eco_plus"]["backwards"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["eco_plus"]["backwards"]["no_table"][car_number] = \
                    (self.available["eco_plus"]["backwards"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "Не у стола по ходу":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["eco_plus"]["forward"]["no_table"][car_number] = \
                    (self.available["eco_plus"]["forward"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["eco_plus"]["forward"]["no_table"][car_number] = \
                    (self.available["eco_plus"]["forward"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "У стола против хода":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["eco_plus"]["backwards"]["table"][car_number] = \
                    (self.available["eco_plus"]["backwards"]["table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["eco_plus"]["backwards"]["table"][car_number] = \
                    (self.available["eco_plus"]["backwards"]["table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "У стола по ходу":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["eco_plus"]["forward"]["table"][car_number] = \
                    (self.available["eco_plus"]["forward"]["table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["eco_plus"]["forward"]["table"][car_number] = \
                    (self.available["eco_plus"]["forward"]["table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "Место пассажира с детьми":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["eco_plus"]["kids"]["seats"][car_number] = \
                    (self.available["eco_plus"]["kids"]["seats"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["eco_plus"]["kids"]["seats"][car_number] = \
                    (self.available["eco_plus"]["kids"]["seats"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "Место для матери и ребенка":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["eco_plus"]["babies"]["seats"][car_number] = \
                    (self.available["eco_plus"]["babies"]["seats"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["eco_plus"]["babies"]["seats"][car_number] = \
                    (self.available["eco_plus"]["babies"]["seats"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

    def update_eco_seats(self, car_number, seat):

        seat_type = seat["label"].replace(",", "")
        free_seats = parse_places(seat["places"]) if "-" in seat["places"] else seat["places"].split(",")
        price = int(seat["tariff"])
        price_non_refundable = seat["tariff2"]

        if seat_type == "Не у стола против хода":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["eco"]["backwards"]["no_table"][car_number] = \
                    (self.available["eco"]["backwards"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["eco"]["backwards"]["no_table"][car_number] = \
                    (self.available["eco"]["backwards"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "Не у стола по ходу":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["eco"]["forward"]["no_table"][car_number] = \
                    (self.available["eco"]["forward"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["eco"]["forward"]["no_table"][car_number] = \
                    (self.available["eco"]["forward"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "У стола против хода":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["eco"]["backwards"]["table"][car_number] = \
                    (self.available["eco"]["backwards"]["table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["eco"]["backwards"]["table"][car_number] = \
                    (self.available["eco"]["backwards"]["table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "У стола по ходу":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["eco"]["forward"]["table"][car_number] = \
                    (self.available["eco"]["forward"]["table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["eco"]["forward"]["table"][car_number] = \
                    (self.available["eco"]["forward"]["table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "Без окна против хода":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["eco"]["backwards"]["no_window"][car_number] = \
                    (self.available["eco"]["backwards"]["no_window"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["eco"]["backwards"]["no_window"][car_number] = \
                    (self.available["eco"]["backwards"]["no_window"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "Без окна по ходу":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["eco"]["forward"]["no_window"][car_number] = \
                    (self.available["eco"]["forward"]["no_window"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["eco"]["forward"]["no_window"][car_number] = \
                    (self.available["eco"]["forward"]["no_window"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "Место для проезда с мелким домашним животным":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["eco"]["pets"]["seats"][car_number] = \
                    (self.available["eco"]["pets"]["seats"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["eco"]["pets"]["seats"][car_number] = \
                    (self.available["eco"]["pets"]["seats"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "Место для инвалида":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["eco"]["disabled"]["seats"][car_number] = \
                    (self.available["eco"]["disabled"]["seats"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["eco"]["disabled"]["seats"][car_number] = \
                    (self.available["eco"]["disabled"]["seats"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

    def update_base_seats(self, car_number, seat):

        seat_type = seat["label"].replace(",", "")
        free_seats = parse_places(seat["places"]) if "-" in seat["places"] else seat["places"].split(",")
        price = int(seat["tariff"])
        price_non_refundable = seat["tariff2"]

        if seat_type == "Не у стола против хода":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["base"]["backwards"]["no_table"][car_number] = \
                    (self.available["base"]["backwards"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["base"]["backwards"]["no_table"][car_number] = \
                    (self.available["base"]["backwards"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "Не у стола по ходу":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["base"]["forward"]["no_table"][car_number] = \
                    (self.available["base"]["forward"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["base"]["forward"]["no_table"][car_number] = \
                    (self.available["base"]["forward"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "У стола против хода":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["base"]["backwards"]["table"][car_number] = \
                    (self.available["base"]["backwards"]["table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["base"]["backwards"]["table"][car_number] = \
                    (self.available["base"]["backwards"]["table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "У стола по ходу":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["base"]["forward"]["table"][car_number] = \
                    (self.available["base"]["forward"]["table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["base"]["forward"]["table"][car_number] = \
                    (self.available["base"]["forward"]["table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "Без окна против хода":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["base"]["backwards"]["no_window"][car_number] = \
                    (self.available["base"]["backwards"]["no_window"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["base"]["backwards"]["no_window"][car_number] = \
                    (self.available["base"]["backwards"]["no_window"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "Без окна по ходу":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["base"]["forward"]["no_window"][car_number] = \
                    (self.available["base"]["forward"]["no_window"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["base"]["forward"]["no_window"][car_number] = \
                    (self.available["base"]["forward"]["no_window"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

    def get_available_seats(self, data=None):

        if data is None:
            data = self.available

        if isinstance(data, dict):
            total = 0
            for key, value in data.items():
                if key == "total":
                    continue
                if isinstance(value, dict):
                    # Рекурсивный вызов метода update_totals
                    self.get_available_seats(value)
                    total += value.get("total", 0)
                elif isinstance(value, list):
                    total += len(value)
            data["total"] = total

        return self.available

class Lasto4kaSeatsCounter:
    def __init__(self, data):
        self.data = data
        self.available = {
            "business_class": self.init_business_class_data(),
            "eco": self.init_eco_data(),
            "base": self.init_base_data(),
        }

    def init_business_class_data(self):
        return {
            "total": 0,
            "forward": {"total": 0, "no_table": {}, "table": {}, "no_window": {}, "window": {}},
            "backwards": {"total": 0, "no_table": {}, "table": {}, "no_window": {}, "window": {}},
            "regular": {"total": 0, "seats": {}},
            "window": {"total": 0, "seats": {}},
            "table": {"total": 0, "seats": {}},
        }

    def init_eco_data(self):
        return {
            "total": 0,
            "forward": {"total": 0, "no_table": {}, "no_window": {}, "window": {}},
            "backwards": {"total": 0, "no_table": {}, "no_window": {}, "window": {}},
            "regular": {"total": 0, "seats": {}},
            "window": {"total": 0, "seats": {}},
            "no_window": {"total": 0, "seats": {}},
            "pets": {"total": 0, "seats": {}},
        }

    def init_base_data(self):
        return {
            "total": 0,
            "forward": {"total": 0, "no_table": {}, "table": {}, "no_window": {}, "window": {}},
            "backwards": {"total": 0, "no_table": {}, "table": {}, "no_window": {}, "window": {}},
            "regular": {"total": 0, "seats": {}},
            "window": {"total": 0, "seats": {}},
            "no_window": {"total": 0, "seats": {}},
            "disabled": {"total": 0, "seats": {}},
        }

    def count_seats(self):

        for car in self.data["result"]["lst"][0]["cars"]:

            car_number = int(car["cnumber"])
            car_type = car["catLabelLoc"]

            if car_type == "Бизнес класс":

                for seat in car["seats"]:
                    self.update_business_class_seats(car_number, seat)

            elif car_type == "Эконом":

                for seat in car["seats"]:
                    self.update_eco_seats(car_number, seat)

            elif car_type == "Базовый":

                for seat in car["seats"]:
                    self.update_base_seats(car_number, seat)

    def update_business_class_seats(self, car_number, seat):

        seat_type = seat["label"].replace(",", "").replace(",", "")
        free_seats = parse_places(seat["places"]) if "-" in seat["places"] else seat["places"].split(",")
        price = int(seat["tariff"])
        price_non_refundable = seat["tariff2"]

        if seat_type == "Не у стола против хода":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["business_class"]["backwards"]["no_table"][car_number] = \
                    (self.available["business_class"]["backwards"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["business_class"]["backwards"]["no_table"][car_number] = \
                    (self.available["business_class"]["backwards"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "Не у стола по ходу":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["business_class"]["forward"]["no_table"][car_number] = \
                    (self.available["business_class"]["forward"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["business_class"]["forward"]["no_table"][car_number] = \
                    (self.available["business_class"]["forward"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "У стола против хода":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["business_class"]["backwards"]["table"][car_number] = \
                    (self.available["business_class"]["backwards"]["table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["business_class"]["backwards"]["table"][car_number] = \
                    (self.available["business_class"]["backwards"]["table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "У стола по ходу":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["business_class"]["forward"]["table"][car_number] = \
                    (self.available["business_class"]["forward"]["table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["business_class"]["forward"]["table"][car_number] = \
                    (self.available["business_class"]["forward"]["table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "Без окна против хода":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["business_class"]["backwards"]["no_window"][car_number] = \
                    (self.available["business_class"]["backwards"]["no_window"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["business_class"]["backwards"]["no_window"][car_number] = \
                    (self.available["business_class"]["backwards"]["no_window"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "Без окна по ходу":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["business_class"]["forward"]["no_window"][car_number] = \
                    (self.available["business_class"]["forward"]["no_window"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["business_class"]["forward"]["no_window"][car_number] = \
                    (self.available["business_class"]["forward"]["no_window"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "У окна против хода":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["business_class"]["backwards"]["window"][car_number] = \
                    (self.available["business_class"]["backwards"]["window"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["business_class"]["backwards"]["window"][car_number] = \
                    (self.available["business_class"]["backwards"]["window"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "У окна по ходу":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["business_class"]["forward"]["window"][car_number] = \
                    (self.available["business_class"]["forward"]["window"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["business_class"]["forward"]["window"][car_number] = \
                    (self.available["business_class"]["forward"]["window"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "У стола":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["business_class"]["table"]["seats"][car_number] = \
                    (self.available["business_class"]["table"]["seats"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["business_class"]["table"]["seats"][car_number] = \
                    (self.available["business_class"]["table"]["seats"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "У окна":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["business_class"]["window"]["seats"][car_number] = \
                    (self.available["business_class"]["window"]["seats"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["business_class"]["window"]["seats"][car_number] = \
                    (self.available["business_class"]["window"]["seats"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "Обычное":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["business_class"]["regular"]["seats"][car_number] = \
                    (self.available["business_class"]["regular"]["seats"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["business_class"]["regular"]["seats"][car_number] = \
                    (self.available["business_class"]["regular"]["seats"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

    def update_eco_seats(self, car_number, seat):

        seat_type = seat["label"].replace(",", "")
        free_seats = parse_places(seat["places"]) if "-" in seat["places"] else seat["places"].split(",")
        price = int(seat["tariff"])
        price_non_refundable = seat["tariff2"]

        if seat_type == "Не у стола против хода":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["eco"]["backwards"]["no_table"][car_number] = \
                    (self.available["eco"]["backwards"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["eco"]["backwards"]["no_table"][car_number] = \
                    (self.available["eco"]["backwards"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "Не у стола по ходу":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["eco"]["forward"]["no_table"][car_number] = \
                    (self.available["eco"]["forward"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["eco"]["forward"]["no_table"][car_number] = \
                    (self.available["eco"]["forward"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "Без окна против хода":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["eco"]["backwards"]["no_window"][car_number] = \
                    (self.available["eco"]["backwards"]["no_window"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["eco"]["backwards"]["no_window"][car_number] = \
                    (self.available["eco"]["backwards"]["no_window"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "Без окна по ходу":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["eco"]["forward"]["no_window"][car_number] = \
                    (self.available["eco"]["forward"]["no_window"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["eco"]["forward"]["no_window"][car_number] = \
                    (self.available["eco"]["forward"]["no_window"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])
                
        elif seat_type == "У окна против хода":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["eco"]["backwards"]["window"][car_number] = \
                    (self.available["eco"]["backwards"]["window"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["eco"]["backwards"]["window"][car_number] = \
                    (self.available["eco"]["backwards"]["window"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "У окна по ходу":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["eco"]["forward"]["window"][car_number] = \
                    (self.available["eco"]["forward"]["window"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["eco"]["forward"]["window"][car_number] = \
                    (self.available["eco"]["forward"]["window"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "Место для проезда с мелким домашним животным":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["eco"]["pets"]["seats"][car_number] = \
                    (self.available["eco"]["pets"]["seats"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["eco"]["pets"]["seats"][car_number] = \
                    (self.available["eco"]["pets"]["seats"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "Без окна":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["eco"]["no_window"]["seats"][car_number] = \
                    (self.available["eco"]["no_window"]["seats"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["eco"]["no_window"]["seats"][car_number] = \
                    (self.available["eco"]["no_window"]["seats"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "У окна":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["eco"]["window"]["seats"][car_number] = \
                    (self.available["eco"]["window"]["seats"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["eco"]["window"]["seats"][car_number] = \
                    (self.available["eco"]["window"]["seats"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "Обычное":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["eco"]["regular"]["seats"][car_number] = \
                    (self.available["eco"]["regular"]["seats"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["eco"]["regular"]["seats"][car_number] = \
                    (self.available["eco"]["regular"]["seats"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

    def update_base_seats(self, car_number, seat):

        seat_type = seat["label"].replace(",", "")
        free_seats = parse_places(seat["places"]) if "-" in seat["places"] else seat["places"].split(",")
        price = int(seat["tariff"])
        price_non_refundable = seat["tariff2"]

        if seat_type == "Не у стола против хода":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["base"]["backwards"]["no_table"][car_number] = \
                    (self.available["base"]["backwards"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["base"]["backwards"]["no_table"][car_number] = \
                    (self.available["base"]["backwards"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "Не у стола по ходу":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["base"]["forward"]["no_table"][car_number] = \
                    (self.available["base"]["forward"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["base"]["forward"]["no_table"][car_number] = \
                    (self.available["base"]["forward"]["no_table"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "Без окна против хода":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["base"]["backwards"]["no_window"][car_number] = \
                    (self.available["base"]["backwards"]["no_window"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["base"]["backwards"]["no_window"][car_number] = \
                    (self.available["base"]["backwards"]["no_window"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "Без окна по ходу":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["base"]["forward"]["no_window"][car_number] = \
                    (self.available["base"]["forward"]["no_window"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["base"]["forward"]["no_window"][car_number] = \
                    (self.available["base"]["forward"]["no_window"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "У окна против хода":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["base"]["backwards"]["window"][car_number] = \
                    (self.available["base"]["backwards"]["window"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["base"]["backwards"]["window"][car_number] = \
                    (self.available["base"]["backwards"]["window"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "У окна по ходу":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["base"]["forward"]["window"][car_number] = \
                    (self.available["base"]["forward"]["window"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["base"]["forward"]["window"][car_number] = \
                    (self.available["base"]["forward"]["window"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "Место для инвалида":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["base"]["disabled"]["seats"][car_number] = \
                    (self.available["base"]["disabled"]["seats"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["base"]["disabled"]["seats"][car_number] = \
                    (self.available["base"]["disabled"]["seats"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "Без окна":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["base"]["no_window"]["seats"][car_number] = \
                    (self.available["base"]["no_window"]["seats"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["base"]["no_window"]["seats"][car_number] = \
                    (self.available["base"]["no_window"]["seats"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "У окна":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["base"]["window"]["seats"][car_number] = \
                    (self.available["base"]["window"]["seats"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["base"]["window"]["seats"][car_number] = \
                    (self.available["base"]["window"]["seats"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

        elif seat_type == "Обычное":

            if price_non_refundable is not None:

                price_non_refundable = int(price_non_refundable)
                price, price_non_refundable = max([price, price_non_refundable]), min([price, price_non_refundable])

                self.available["base"]["regular"]["seats"][car_number] = \
                    (self.available["base"]["regular"]["seats"].get(car_number, []) +
                     [(place_num.lstrip("0"), price, price_non_refundable) for place_num in free_seats])

            else:

                self.available["base"]["regular"]["seats"][car_number] = \
                    (self.available["base"]["regular"]["seats"].get(car_number, []) +
                     [(place_num.lstrip("0"), price) for place_num in free_seats])

    def get_available_seats(self, data=None):

        if data is None:
            data = self.available

        if isinstance(data, dict):
            total = 0
            for key, value in data.items():
                if key == "total":
                    continue
                if isinstance(value, dict):
                    # Рекурсивный вызов метода update_totals
                    self.get_available_seats(value)
                    total += value.get("total", 0)
                elif isinstance(value, list):
                    total += len(value)
            data["total"] = total

        return self.available