import requests
import time
import origin_destination_date
import rzd_web
from monitor_tickets_rzd_bot import seats_counter, rzd_app


def seats():
    # Получение от пользователя даты и времени, а также станции отправления и пункта назначения происходит локально.
    while True:
        try:
            origin, destination = origin_destination_date.origin_destination()
        except TypeError:
            return 0
        else:
            pass

        try:
            dd, mm, yyyy = origin_destination_date.date()
        except TypeError:
            return 0
        else:
            pass
        break

    app_date = "{}.{}.{}".format(dd, mm, yyyy)
    web_date = "{}-{}-{}".format(yyyy, mm, dd)

    errors = 0

    while errors < 5:

        # Работа через приложение более предпочтительна, так как приложение практически не банит за спам запросами в
        # отличие от сайта. Однако, бывает, что приложение по какой-то причине тормозит или не работает вовсе и в
        # таком случае запросы будут идти через сайт. Если ошибок нет, то работаем в app mode, как только появляются
        # ошибки, то включаем web mode. Если и там запрос не проходит, то переключаемся обратно на приложение. Если
        # после 10 таких переключений не удалось достичь результата, то, вероятнее всего, РЖД нас забанил и робот
        # останавливается. Лечится проксями, но я их пока не прикрутил.

        # App mode

        if not errors % 2:

            try:
                train_num = rzd_app.get_train(origin, destination, app_date)
            except KeyError:
                print("По заданным параметрам не найдено поездов. Перехожу в web mode.")
                errors += 1
                continue
            except requests.exceptions.ReadTimeout:
                print("Кажется у РЖД проблемы. Сейчас попробуем еще раз. Перехожу в web mode.")
                errors += 1
                continue
            else:
                if not train_num:
                    break

            if not train_num:
                return 0
            else:
                try:
                    seats = rzd_app.get_seats(origin, destination, app_date, train_num)
                except requests.exceptions.ReadTimeout:
                    print("Кажется у РЖД проблемы. Сейчас попробуем еще раз. Перехожу в web mode.")
                    continue
                else:
                    seats_counter.show_available(seats)
                    break

        # Web mode

        else:

            try:
                train_num = rzd_web.get_train(origin, destination, web_date)
            except KeyError:
                print("По заданным параметрам не найдено поездов. Попробуем еще раз")
                errors += 1
                continue
            except requests.exceptions.ReadTimeout:
                print("Кажется у РЖД проблемы. Сейчас попробуем еще раз. Перехожу в app mode.")
                errors += 1
                continue
            else:
                if not train_num:
                    return 0

            if not train_num:
                continue
            else:
                try:
                    seats = rzd_web.get_seats(origin, destination, web_date, train_num)
                except requests.exceptions.ReadTimeout:
                    print("Кажется у РЖД проблемы. Сейчас попробуем еще раз. Перехожу в app mode.")
                    continue
                else:
                    seats_counter.show_available(seats)
                    break
    if errors == 5:
        print("Судя по всему РЖД Вас забанил. Ждите, пока разраб добавит возможность использовать прокси.")
        return 0
    else:
        # Вот тут надо будет написать: Если нужное Вам место есть в продаже, тогда бегом покупать на сайт РЖД. Если
        # нужного Вам места нет, то укажите тип места, которое Вам необходимо и Вы получите уведомление,
        # если оно появится в продаже. Итак, Вам потребуется монитор? (Д/Н).
        #
        # Эта функция будет возвращать либо 0, если монитор не нужен, либо тип(ы) мест, которые выберет юзер. И,
        # наконец, самая финальная функция с самим монитором в зависимости от ответа либо запустится, либо нет.

        errors = 0
        attempts = 0
        pass_select = monitor_setup.passenger()
        what_to_monitor = monitor_setup.places_to_monitor(pass_select, seats)
        print("\nЗапускаем монитор\n")
        print(sum(what_to_monitor))

        while sum(what_to_monitor) == 0 and errors < 5:

            # App mode

            if not errors % 2:

                try:
                    seats = rzd_app.get_seats(origin, destination, app_date, train_num)
                    seats_counter.show_available(seats)
                except requests.exceptions.ReadTimeout:
                    print("Кажется у РЖД проблемы. Сейчас попробуем еще раз. Перехожу в web mode.")
                    errors += 1
                    continue
                else:
                    what_to_monitor = monitor_setup.places_to_monitor(pass_select, seats)
                    attempts += 1
                    print("Попытка № {}".format(attempts))
                    time.sleep(10)

            # Web mode

            else:

                try:
                    seats = rzd_web.get_seats(origin, destination, web_date, train_num)
                    seats_counter.show_available(seats)
                except requests.exceptions.ReadTimeout:
                    print("Кажется у РЖД проблемы. Сейчас попробуем еще раз. Перехожу в app mode.")
                    errors += 1
                    continue
                else:
                    what_to_monitor = monitor_setup.places_to_monitor(pass_select, seats)
                    attempts += 1
                    print("Попытка № {}".format(attempts))
                    time.sleep(10)

        if errors == 5:
            print("Судя по всему РЖД Вас забанил. Ждите, пока разраб добавит возможность использовать прокси.")
            return "FAILED!"
        else:
            print(sum(what_to_monitor))
            print("SUCCESS!\nМЕСТО НАЙДЕНО!")
