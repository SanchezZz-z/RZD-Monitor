from abc import ABC, abstractmethod
import re

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

class SeatsCounterBase(ABC):
    def __init__(self, data):
        self.data = data
        self.available = self.init_available()

    @abstractmethod
    def init_available(self):
        """Инициализация структуры available для конкретного типа поезда."""
        pass

    @abstractmethod
    def count_seats(self):

        """Подсчет мест для конкретного типа поезда."""

        pass

    def process_prices(self, price, price_non_refundable):

        """Обработка цен: возврат кортежа (основная цена, невозвратная цена или None)."""

        if price_non_refundable is not None:
            price_non_refundable = int(price_non_refundable)
            return max(price, price_non_refundable), min(price, price_non_refundable)
        return int(price), None

    def update_seats(self, target_dict, car_number, free_seats, price, price_non_refundable=None):

        """Обновление словаря мест с учетом цен."""

        price, price_non_ref = self.process_prices(price, price_non_refundable)
        seat_data = (
            [(place_num.lstrip("0"), price, price_non_ref) for place_num in free_seats]
            if price_non_ref is not None
            else [(place_num.lstrip("0"), price) for place_num in free_seats]
        )
        target_dict[car_number] = target_dict.get(car_number, []) + seat_data

    def get_available_seats(self, data=None):

        """Рекурсивный подсчет общего количества мест."""

        if data is None:
            data = self.available

        if isinstance(data, dict):
            total = 0
            for key, value in data.items():
                if key == "total":
                    continue
                if isinstance(value, dict):
                    self.get_available_seats(value)
                    total += value.get("total", 0)
                elif isinstance(value, list):
                    total += len(value)
            data["total"] = total
        return self.available

class TrainSeatsCounter(SeatsCounterBase):
    def init_available(self):
        return {
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
                self.update_seats(self.available["premium"]["whole_coupe"]["pets_whole_coupe"],
                                 car_number, places, price)

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
            "Последнее купе, верхнее": "upper",
            "Последнее купе, нижнее": "lower",
            "Боковое верхнее у туалета": "side_upper",
            "Боковое нижнее у туалета": "side_lower",
        }
        seat_key = seat_map.get(seat_type) or seat_map.get(seat_label)
        if seat_key:
            self.update_seats(self.available["plaz"][seat_key][pet_status], car_number, free_seats, price)

    def update_coupe_seats(self, car_number, seat, car_cls, has_gender_split, two_storey, no_refund_tariff_available):
        pet_status = (
            "no_pets" if car_cls in NO_PETS_CAR_CLS else
            "pets_whole_coupe" if car_cls in WHOLE_COUPE_PETS_CAR_CLS else
            "pets"
        )
        seat_type = seat["type"]
        places = seat["places"].split(",")
        price = int(seat["tariff"])
        price_non_refundable = seat.get("tariff2")

        if has_gender_split:
            self.update_gender_split_coupe(car_number, pet_status, seat_type, places, two_storey,
                                          price, price_non_refundable if no_refund_tariff_available else None)
        else:
            self.update_unisex_coupe(car_number, pet_status, seat_type, places, two_storey,
                                    price, price_non_refundable if no_refund_tariff_available else None)

    def update_gender_split_coupe(self, car_number, pet_status, seat_type, places, two_storey, price, price_non_refundable=None):
        gender_map = {"М": "male", "Ж": "female", "Ц": "free"}
        classified_places = {"male": [], "female": [], "free": [], "unisex": []}
        for place in places:
            place_clean = remove_non_digits(place.lstrip("0"))
            gender = next((g for k, g in gender_map.items() if k in place), "unisex")
            classified_places[gender].append(place_clean)

        if seat_type in ["up", "lastup"]:
            for gender, place_list in classified_places.items():
                self.update_coupe_upper(car_number, gender, pet_status, place_list, two_storey, price, price_non_refundable)
        elif seat_type in ["dn", "lastdn"]:
            for gender, place_list in classified_places.items():
                self.update_seats(self.available["coupe"]["lower"][gender][pet_status], car_number, place_list, price, price_non_refundable)

    def update_unisex_coupe(self, car_number, pet_status, seat_type, places, two_storey, price, price_non_refundable=None):
        if seat_type in ["up", "lastup"]:
            self.update_coupe_upper(car_number, "unisex", pet_status, places, two_storey, price, price_non_refundable)
        elif seat_type in ["dn", "lastdn"]:
            self.update_seats(self.available["coupe"]["lower"]["unisex"][pet_status], car_number, places, price, price_non_refundable)
        elif seat_type in ["invalid_lower", "invalid_upper"]:
            self.update_seats(self.available["coupe"]["disabled"][pet_status], car_number, places, price, price_non_refundable)

    def update_coupe_upper(self, car_number, gender, pet_status, places, two_storey, price, price_non_refundable=None):
        for place in places:
            target = (
                self.available["coupe"]["two_storey_upper"][gender][pet_status] if two_storey and second_level_place_check(place)
                else self.available["coupe"]["upper"][gender][pet_status]
            )
            self.update_seats(target, car_number, [place], price, price_non_refundable)

    def update_lux_seats(self, car_number, seat, car_cls, has_gender_split, places):
        pet_status = (
            "no_pets" if car_cls in NO_PETS_CAR_CLS else
            "pets_whole_coupe" if car_cls in WHOLE_COUPE_PETS_CAR_CLS else
            "pets"
        )
        seat_type = seat["type"]
        price = int(seat["tariff"])

        if has_gender_split:
            for place in places:
                self.update_lux_gender_split(car_number, seat_type, pet_status, place, price)
        else:
            level = "upper" if seat_type in ["up", "lastup"] else "lower" if seat_type in ["dn", "lastdn"] else None
            if level:
                self.update_seats(self.available["lux"][level]["unisex"][pet_status], car_number, places, price)

    def update_lux_gender_split(self, car_number, seat_type, pet_status, place, price):
        gender_map = {"М": "male", "Ж": "female", "Ц": "free"}
        level = "upper" if seat_type in ["up", "lastup"] else "lower" if seat_type in ["dn", "lastdn"] else None
        if level:
            gender = next((g for k, g in gender_map.items() if k in place), "unisex")
            self.update_seats(self.available["lux"][level][gender][pet_status], car_number, [remove_non_digits(place.lstrip("0"))], price)


class SapsanSeatsCounter(SeatsCounterBase):
    def init_available(self):
        return {
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

        car_type_map = {
            "Первый класс": self.update_first_class_seats,
            "Купе-переговорная": self.update_negotiation_coupe_seats,
            "Бизнес-купе": self.update_business_coupe_seats,
            "Бизнес класс": self.update_business_class_seats,
            "Купе-Сьют": self.update_coupe_suite_seats,
            "Вагон-бистро": self.update_bistro_seats,
            "Семейный": self.update_family_seats,
            "Эконом+": self.update_eco_plus_seats,
            "Эконом": self.update_eco_seats,
            "Базовый": self.update_base_seats,
        }

        for car in self.data["result"]["lst"][0]["cars"]:

            car_number = int(car["cnumber"])
            car_type = car["catLabelLoc"]
            if car_type in car_type_map:
                for seat in car["seats"]:
                    car_type_map[car_type](car_number, seat)

    def update_first_class_seats(self, car_number, seat):
        seat_type = seat["label"].replace(",", "")
        free_seats = parse_places(seat["places"]) if "-" in seat["places"] else seat["places"].split(",")
        price = int(seat["tariff"])
        price_non_refundable = seat.get("tariff2")

        seat_map = {
            "Не у стола против хода": self.available["first_class"]["backwards"]["no_table"],
            "Не у стола по ходу": self.available["first_class"]["forward"]["no_table"],
            "Свободные места": self.available["first_class"]["forward"]["separate"],
        }
        if seat_type in seat_map:
            self.update_seats(seat_map[seat_type], car_number, free_seats, price, price_non_refundable)

    def update_negotiation_coupe_seats(self, car_number, seat):
        free_seats = parse_places(seat["places"]) if "-" in seat["places"] else seat["places"].split(",")
        price = int(seat["tariff"])
        price_non_refundable = seat.get("tariff2")
        self.update_seats(self.available["negotiation_coupe"]["coupe"]["seats"], car_number, free_seats, price, price_non_refundable)

    def update_business_coupe_seats(self, car_number, seat):
        free_seats = parse_places(seat["places"]) if "-" in seat["places"] else seat["places"].split(",")
        price = int(seat["tariff"])
        price_non_refundable = seat.get("tariff2")
        self.update_seats(self.available["business_coupe"]["coupe"]["seats"], car_number, free_seats, price, price_non_refundable)

    def update_business_class_seats(self, car_number, seat):
        seat_type = seat["label"].replace(",", "")
        free_seats = parse_places(seat["places"]) if "-" in seat["places"] else seat["places"].split(",")
        price = int(seat["tariff"])
        price_non_refundable = seat.get("tariff2")

        seat_map = {
            "Не у стола против хода": self.available["business_class"]["backwards"]["no_table"],
            "Не у стола по ходу": self.available["business_class"]["forward"]["no_table"],
            "У стола против хода": self.available["business_class"]["backwards"]["table"],
            "У стола по ходу": self.available["business_class"]["forward"]["table"],
        }
        if seat_type in seat_map:
            self.update_seats(seat_map[seat_type], car_number, free_seats, price, price_non_refundable)

    def update_coupe_suite_seats(self, car_number, seat):
        free_seats = parse_places(seat["places"]) if "-" in seat["places"] else seat["places"].split(",")
        price = int(seat["tariff"])
        price_non_refundable = seat.get("tariff2")
        self.update_seats(self.available["coupe_suite"]["coupe"]["seats"], car_number, free_seats, price, price_non_refundable)

    def update_bistro_seats(self, car_number, seat):
        seat_type = seat["label"].replace(",", "")
        free_seats = parse_places(seat["places"]) if "-" in seat["places"] else seat["places"].split(",")
        price = int(seat["tariff"])
        price_non_refundable = seat.get("tariff2")

        seat_map = {
            "У стола против хода": self.available["bistro_car"]["backwards"]["table"],
            "У стола по ходу": self.available["bistro_car"]["forward"]["table"],
        }
        if seat_type in seat_map:
            self.update_seats(seat_map[seat_type], car_number, free_seats, price, price_non_refundable)

    def update_family_seats(self, car_number, seat):
        seat_type = seat["label"].replace(",", "")
        free_seats = parse_places(seat["places"]) if "-" in seat["places"] else seat["places"].split(",")
        price = int(seat["tariff"])
        price_non_refundable = seat.get("tariff2")

        seat_map = {
            "Не у стола по ходу": self.available["family"]["forward"]["no_table"],
            "Место пассажира с детьми": self.available["family"]["kids"]["seats"],
        }
        if seat_type in seat_map:
            self.update_seats(seat_map[seat_type], car_number, free_seats, price, price_non_refundable)

    def update_eco_plus_seats(self, car_number, seat):
        seat_type = seat["label"].replace(",", "")
        free_seats = parse_places(seat["places"]) if "-" in seat["places"] else seat["places"].split(",")
        price = int(seat["tariff"])
        price_non_refundable = seat.get("tariff2")

        seat_map = {
            "Не у стола против хода": self.available["eco_plus"]["backwards"]["no_table"],
            "Не у стола по ходу": self.available["eco_plus"]["forward"]["no_table"],
            "У стола против хода": self.available["eco_plus"]["backwards"]["table"],
            "У стола по ходу": self.available["eco_plus"]["forward"]["table"],
            "Место пассажира с детьми": self.available["eco_plus"]["kids"]["seats"],
            "Место для матери и ребенка": self.available["eco_plus"]["babies"]["seats"],
        }
        if seat_type in seat_map:
            self.update_seats(seat_map[seat_type], car_number, free_seats, price, price_non_refundable)

    def update_eco_seats(self, car_number, seat):
        seat_type = seat["label"].replace(",", "")
        free_seats = parse_places(seat["places"]) if "-" in seat["places"] else seat["places"].split(",")
        price = int(seat["tariff"])
        price_non_refundable = seat.get("tariff2")

        seat_map = {
            "Не у стола против хода": self.available["eco"]["backwards"]["no_table"],
            "Не у стола по ходу": self.available["eco"]["forward"]["no_table"],
            "У стола против хода": self.available["eco"]["backwards"]["table"],
            "У стола по ходу": self.available["eco"]["forward"]["table"],
            "Без окна против хода": self.available["eco"]["backwards"]["no_window"],
            "Без окна по ходу": self.available["eco"]["forward"]["no_window"],
            "Место для проезда с мелким домашним животным": self.available["eco"]["pets"]["seats"],
            "Место для инвалида": self.available["eco"]["disabled"]["seats"],
        }
        if seat_type in seat_map:
            self.update_seats(seat_map[seat_type], car_number, free_seats, price, price_non_refundable)

    def update_base_seats(self, car_number, seat):
        seat_type = seat["label"].replace(",", "")
        free_seats = parse_places(seat["places"]) if "-" in seat["places"] else seat["places"].split(",")
        price = int(seat["tariff"])
        price_non_refundable = seat.get("tariff2")

        seat_map = {
            "Не у стола против хода": self.available["base"]["backwards"]["no_table"],
            "Не у стола по ходу": self.available["base"]["forward"]["no_table"],
            "У стола против хода": self.available["base"]["backwards"]["table"],
            "У стола по ходу": self.available["base"]["forward"]["table"],
            "Без окна против хода": self.available["base"]["backwards"]["no_window"],
            "Без окна по ходу": self.available["base"]["forward"]["no_window"],
        }
        if seat_type in seat_map:
            self.update_seats(seat_map[seat_type], car_number, free_seats, price, price_non_refundable)

class Lasto4kaSeatsCounter(SeatsCounterBase):
    def init_available(self):
        return {
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
            "forward": {"total": 0, "no_table": {},  "no_window": {}, "window": {}},
            "backwards": {"total": 0, "no_table": {}, "no_window": {}, "window": {}},
            "regular": {"total": 0, "seats": {}},
            "pets": {"total": 0, "seats": {}},
            "window": {"total": 0, "seats": {}},
            "no_window": {"total": 0, "seats": {}},
        }

    def init_base_data(self):
        return {
            "total": 0,
            "forward": {"total": 0, "no_table": {}, "no_window": {}, "window": {}},
            "backwards": {"total": 0, "no_table": {}, "no_window": {}, "window": {}},
            "regular": {"total": 0, "seats": {}},
            "window": {"total": 0, "seats": {}},
            "no_window": {"total": 0, "seats": {}},
            "disabled": {"total": 0, "seats": {}},
        }

    def count_seats(self):
        car_type_map = {
            "Бизнес класс": self.update_business_class_seats,
            "Эконом": self.update_eco_seats,
            "Базовый": self.update_base_seats,
        }
        for car in self.data["result"]["lst"][0]["cars"]:
            car_number = int(car["cnumber"])
            car_type = car["catLabelLoc"]
            if car_type in car_type_map:
                for seat in car["seats"]:
                    car_type_map[car_type](car_number, seat)

    def update_business_class_seats(self, car_number, seat):
        seat_type = seat["label"].replace(",", "")
        free_seats = parse_places(seat["places"]) if "-" in seat["places"] else seat["places"].split(",")
        price = int(seat["tariff"])
        price_non_refundable = seat.get("tariff2")

        seat_map = {
            "Не у стола против хода": self.available["business_class"]["backwards"]["no_table"],
            "Не у стола по ходу": self.available["business_class"]["forward"]["no_table"],
            "У стола против хода": self.available["business_class"]["backwards"]["table"],
            "У стола по ходу": self.available["business_class"]["forward"]["table"],
            "Без окна против хода": self.available["business_class"]["backwards"]["no_window"],
            "Без окна по ходу": self.available["business_class"]["forward"]["no_window"],
            "У окна против хода": self.available["business_class"]["backwards"]["window"],
            "У окна по ходу": self.available["business_class"]["forward"]["window"],
            "У стола": self.available["business_class"]["table"]["seats"],
            "У окна": self.available["business_class"]["window"]["seats"],
            "Обычное": self.available["business_class"]["regular"]["seats"],
        }
        if seat_type in seat_map:
            self.update_seats(seat_map[seat_type], car_number, free_seats, price, price_non_refundable)

    def update_eco_seats(self, car_number, seat):
        seat_type = seat["label"].replace(",", "")
        free_seats = parse_places(seat["places"]) if "-" in seat["places"] else seat["places"].split(",")
        price = int(seat["tariff"])
        price_non_refundable = seat.get("tariff2")

        seat_map = {
            "Не у стола против хода": self.available["eco"]["backwards"]["no_table"],
            "Не у стола по ходу": self.available["eco"]["forward"]["no_table"],
            "Без окна против хода": self.available["eco"]["backwards"]["no_window"],
            "Без окна по ходу": self.available["eco"]["forward"]["no_window"],
            "У окна против хода": self.available["eco"]["backwards"]["window"],
            "У окна по ходу": self.available["eco"]["forward"]["window"],
            "Место для проезда с мелким домашним животным": self.available["eco"]["pets"]["seats"],
            "Без окна": self.available["eco"]["no_window"]["seats"],
            "У окна": self.available["eco"]["window"]["seats"],
            "Обычное": self.available["eco"]["regular"]["seats"],
        }
        if seat_type in seat_map:
            self.update_seats(seat_map[seat_type], car_number, free_seats, price, price_non_refundable)

    def update_base_seats(self, car_number, seat):
        seat_type = seat["label"].replace(",", "")
        free_seats = parse_places(seat["places"]) if "-" in seat["places"] else seat["places"].split(",")
        price = int(seat["tariff"])
        price_non_refundable = seat.get("tariff2")

        seat_map = {
            "Не у стола против хода": self.available["base"]["backwards"]["no_table"],
            "Не у стола по ходу": self.available["base"]["forward"]["no_table"],
            "Без окна против хода": self.available["base"]["backwards"]["no_window"],
            "Без окна по ходу": self.available["base"]["forward"]["no_window"],
            "У окна против хода": self.available["base"]["backwards"]["window"],
            "У окна по ходу": self.available["base"]["forward"]["window"],
            "Место для инвалида": self.available["base"]["disabled"]["seats"],
            "Без окна": self.available["base"]["no_window"]["seats"],
            "У окна": self.available["base"]["window"]["seats"],
            "Обычное": self.available["base"]["regular"]["seats"],
        }
        if seat_type in seat_map:
            self.update_seats(seat_map[seat_type], car_number, free_seats, price, price_non_refundable)
