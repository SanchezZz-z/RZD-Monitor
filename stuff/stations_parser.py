import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # Когда открыт Charles.

# Русский алфавит

alphabet = "абвгдежзийклмнопрстуфхцчшщъыьэюя0123456789"

# Создаем файл, куда будем добавлять данные по станциям

station_list = open("stations.txt", "w+")

letter_combo_counter = 0
how_many_letters_used = 2

# Делаем запрос с первыми двумя буквами, чтобы получить названия станций, которые начинаются на эти буквы

for first_letter in alphabet:
    for second_letter in alphabet:

        content_length = len("{}{}".format(first_letter, second_letter).encode('utf-8'))

        # Заголовки. Список необходимых заголовков можно определить, перебирая их в Charles
        # (Если запрос не проходит, значит заголовок обязательный).

        headers = {
            "Host": "ekmp-i-47-1.rzd.ru",
            "Content-Type": "application/json",
            "User-Agent": "RZD/2356 CFNetwork/1410.0.3 Darwin/22.6.0",
            "Content-Length": "{}".format(66 + content_length),
            "Sec-Fetch-Site": "same-origin",
            "Accept-Language": "ru",
            "Accept-Encoding": "gzip, deflate, br"
        }

        # Тело запроса
        data_req = {
            "protocolVersion": 47,
            "type": "STATION",
            "searchValue": "{}{}".format(first_letter, second_letter)
        }

        res = requests.post(
            url="https://ekmp-i-47-1.rzd.ru/v1.0/search/suggest",
            headers=headers,
            json=data_req,
            verify=False,
            timeout=10)

        if res.status_code != 200:  # АШИПКА
            print("Response Code: {}".format(res.status_code))
        else:
            data_res = res.json()  # Ответ

        for station in range(len(data_res["result"]["items"])):
            station_list.write("{}_{}\n".format(data_res["result"]["items"][station]["title"].title(),
                                                data_res["result"]["items"][station]["id"]))
        letter_combo_counter += 1
        print('Combo {} out of {} done.'.format(letter_combo_counter, len(alphabet) ** how_many_letters_used))

station_list.close()
