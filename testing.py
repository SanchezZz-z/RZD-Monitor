import json
import re
from collections import OrderedDict
from datetime import datetime

from aiogram import types
from fuzzywuzzy import process
import asyncpg


# Функция для считывания станций и их кодов
def load_stations(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        stations = json.load(f)
    return stations


# Функция для поиска ближайших совпадений станций с запросом пользователя
def find_matches(user_input, station_data, threshold=70, limit=10):
    station_names = [station["name"] for station in station_data]
    # Проверка точного совпадения по началу строки
    exact_matches = [station for station in station_names if station.lower().startswith(user_input.lower())]
    if exact_matches:
        return [(match, station_data[station_names.index(match)]["expressCode"]) for match in exact_matches][:limit]
    # Использование алгоритма сравнения строк для поиска ближайших совпадений
    matches = process.extract(user_input, station_names, limit=limit)
    closest_matches = [(match[0], station_data[station_names.index(match[0])]["expressCode"]) for match in matches if
                       match[1] >= threshold]
    return closest_matches


# Функция для получения из общего списка поездов / мониторов, которые выбрал пользователь
def get_user_choice(user_list: str, user_choice: list):
    blocks = re.split(r"(?=\d+\.\n)", user_list.strip())
    selected_blocks = [blocks[i] for i in user_choice]
    return "".join(selected_blocks)


async def create_connection_pool(connection_params):
    """
    Создает пул соединений с базой данных на основе параметров подключения.
    """
    pool = await asyncpg.create_pool(**connection_params)
    return pool


async def add_user_train(pool, values):
    """
    Добавляет запись в таблицу базы данных.
    Если запись успешно добавлена, возвращает "Успешно".
    Если запись уже существует из-за нарушения constraint, возвращает "Такая запись уже есть".
    """
    async with pool.acquire() as connection:
        try:
            async with connection.transaction():
                (user_id, origin_station, destination_station, trip_date, train_num,
                 train_info, departure_timestamp, is_two_storey, train_type) = values
                if isinstance(trip_date, datetime):
                    trip_date = trip_date.date()
                if isinstance(departure_timestamp, datetime) and departure_timestamp.tzinfo is not None:
                    departure_timestamp = departure_timestamp.replace(tzinfo=None)
                # Используем параметры для передачи значений, чтобы избежать проблем с кодировкой
                query = (
                    "INSERT INTO user_trains (user_id, origin_station, destination_station, trip_date, train_num,"
                    "                         train_info, departure_timestamp, is_two_storey, train_type) "
                    "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9);"
                )
                await connection.execute(query, user_id, origin_station, destination_station, trip_date, train_num,
                                         train_info, departure_timestamp, is_two_storey, train_type)
            return "\U00002705 Поезд успешно добавлен в список Ваших поездов"
        except asyncpg.exceptions.UniqueViolationError:
            return "\U00002757 Этот поезд уже был добавлен ранее"


# Функция для получения информации о поездах пользователя
async def get_user_trains(pool, user_id):
    async with pool.acquire() as connection:
        async with connection.transaction():
            query = (
                "SELECT"
                "   id,"
                "   train_info,"
                "   ROW_NUMBER() OVER (ORDER BY departure_timestamp) "
                "FROM user_trains "
                "WHERE user_id = $1 "
                "ORDER BY departure_timestamp;"
            )
            res = await connection.fetch(query, user_id)
            # Вернем результат в виде строки (как в случае с выбором поезда) и список айдишников (понадобится для
            # удаления поездов, а также для получения информации о конкретном поезде)
            return ("\n\n".join(["{}.\n".format(train["row_number"]) + train["train_info"] for train in res]),
                    [train["id"] for train in res])


# Функция для получения информации о ВЫБРАННОМ поезде
async def get_train_info(pool, train_id, monitor=True):
    async with pool.acquire() as connection:
        async with connection.transaction():
            if monitor:
                query = (
                    "SELECT"
                    "   train_num,"
                    "   trip_date,"
                    "   origin_station,"
                    "   destination_station,"
                    "   is_two_storey,"
                    "   train_info,"
                    "   train_type "
                    "FROM user_trains "
                    "WHERE id = $1;"
                )
            else:
                query = (
                    "SELECT"
                    "   train_num,"
                    "   trip_date,"
                    "   origin_station,"
                    "   destination_station "
                    "FROM user_trains "
                    "WHERE id = $1;"
                )
            res = await connection.fetch(query, train_id)
            return res[0]


# Функция для удаления выбранного поезда
async def delete_selected_trains(pool, train_ids):
    if not train_ids:
        return

    async with pool.acquire() as connection:
        async with connection.transaction():
            # Создание строки запроса с правильным количеством параметров
            query = (
                "DELETE FROM user_trains "
                "WHERE id = ANY($1);"
            )
            await connection.execute(query, train_ids)


# Функция для добавления поезда в отслеживаемые поезда
async def add_train_to_monitor(pool, train_info):
    async with pool.acquire() as connection:
        async with connection.transaction():
            # Сперва проверяем, нет ли нужного поезда среди удаленных (dropped_trains_to_monitor)
            # Используем параметры для передачи значений, чтобы избежать проблем с кодировкой
            check_query = (
                "SELECT id "
                "FROM dropped_trains_to_monitor "
                "WHERE origin_station = $1 AND destination_station = $2 AND trip_date = $3 AND train_num = $4;"
            )
            check_result = await connection.fetchval(check_query, *train_info)
            # Если нет, тогда пробуем вставить поезд в таблицу
            if check_result is None:
                # При условии, если нарушается constraint по уникальности поездов, тогда ничего не делаем
                insert_query = (
                    "INSERT INTO trains_to_monitor (origin_station, destination_station, trip_date, train_num) "
                    "VALUES ($1, $2, $3, $4)"
                    "ON CONFLICT (origin_station, destination_station, trip_date, train_num) DO NOTHING "
                    "RETURNING id;"
                )
                # Если условие выполняется, тогда возвращаем id добавленного поезда
                result = await connection.fetchval(insert_query, *train_info)

                # Если в таблице уже есть запись с нужным поездом, то возвращаем ее id
                if result is None:
                    conflict_query = (
                        "SELECT id "
                        "FROM trains_to_monitor "
                        "WHERE origin_station = $1 AND destination_station = $2 AND trip_date = $3 AND train_num = $4;"
                    )
                    result = await connection.fetchval(conflict_query, *train_info)
            # Если нужный поезд был среди удаленных, тогда возвращаем его в trains_to_monitor и возвращаем id записи
            else:
                insert_query = (
                    "INSERT INTO trains_to_monitor (id, origin_station, destination_station, trip_date, train_num) "
                    "SELECT id, origin_station, destination_station, trip_date, train_num "
                    "FROM dropped_trains_to_monitor "
                    "WHERE id = $1 "
                    "RETURNING id;"
                )
                result = await connection.fetchval(insert_query, check_result)
                # И удаляем запись из таблицы с удаленными поездами (dropped_trains_to_monitor)
                delete_query = (
                    "DELETE FROM dropped_trains_to_monitor "
                    "WHERE id = $1;"
                )
                await connection.execute(delete_query, check_result)

            return result


# Функция для вывода активных мониторов
async def get_active_monitors(pool, user_id):
    async with pool.acquire() as connection:
        async with connection.transaction():
            query = (
                "SELECT"
                "   mt.id,"
                "   mt.monitor_setup_info,"
                "   ROW_NUMBER() OVER (ORDER BY ut.departure_timestamp) "
                "FROM monitor_tasks AS mt "
                "LEFT JOIN public.trains_to_monitor AS ttm "
                "ON mt.train_id = ttm.id "
                "LEFT JOIN user_trains AS ut "
                "ON mt.user_id = ut.user_id AND ttm.trip_date = ut.trip_date AND ttm.train_num = ut.train_num "
                "WHERE mt.user_id = $1 "
                "ORDER BY ut.departure_timestamp;"
            )
            res = await connection.fetch(query, user_id)
            # Вернем результат в виде строки (как в случае с выбором поезда) и список айдишников (понадобится для
            # удаления поездов, а также для получения информации о конкретном поезде)
            return ("\n\n".join(["{}.\n".format(monitor["row_number"]) + monitor["monitor_setup_info"]
                                 for monitor in res]), [monitor["id"] for monitor in res])


# Функция для добавления таска (монитора) пользователя в таблицу с тасками
async def add_monitor_task(pool, train_to_monitor_id, user_id, monitor_config_dict, monitor_config_msg):
    async with pool.acquire() as connection:
        try:
            async with connection.transaction():
                # Чтобы гарантировать, что порядок ключей не изменится при конвертации словаря в JSON, воспользуемся
                # OrderedDict
                monitor_config_dict = OrderedDict(monitor_config_dict.items())
                # Превращаем словарь в JSON
                monitor_config_json = json.dumps(monitor_config_dict)
                # Используем параметры для передачи значений, чтобы избежать проблем с кодировкой
                query = (
                    "INSERT INTO monitor_tasks (train_id, user_id, monitor_setup, monitor_setup_info) "
                    "VALUES ($1, $2, $3, $4);"
                )
                await connection.execute(query, train_to_monitor_id, user_id, monitor_config_json, monitor_config_msg)
            return "\U00002705 Монитор успешно добавлен в список Ваших мониторов"
        except asyncpg.exceptions.UniqueViolationError:
            return "\U00002757 Такой монитор уже был добавлен ранее"


# Функция для проверки, возможно ли быстро восстановить монитор и получения информации о поезде
async def quick_restore_task_check(pool, train_id):
    async with pool.acquire() as connection:
        async with connection.transaction():
            # Если train_id есть либо в trains_to_monitor, либо в dropped_trains_to_monitor, то восстановить монитор
            # можно. Если train_id в таблицах нет, значит поезд уже отправился и восстановить монитор нельзя
            trains_to_monitor_query = (
                "SELECT "
                "   origin_station, "
                "   destination_station, "
                "   trip_date, "
                "   train_num "
                "FROM trains_to_monitor "
                "WHERE id = $1;"
            )
            train_data = await connection.fetch(trains_to_monitor_query, train_id)
            if not train_data:
                dropped_trains_to_monitor_query = (
                    "SELECT "
                    "   origin_station, "
                    "   destination_station, "
                    "   trip_date, "
                    "   train_num "
                    "FROM dropped_trains_to_monitor "
                    "WHERE id = $1;"
                )
                train_data = await connection.fetch(dropped_trains_to_monitor_query, train_id)

            return train_data


# Если монитор можно восстановить, то необходимо получить настройку монитора
async def quick_restore_task_setup(pool, task_id):
    async with pool.acquire() as connection:
        async with connection.transaction():
            get_setup_query = (
                "SELECT "
                "   monitor_setup "
                "FROM successful_monitor_tasks "
                "WHERE id = $1;"
            )
            task_setup = await connection.fetchval(get_setup_query, task_id)
            return json.loads(task_setup)


# Функция восстановления монитора
async def quick_restore_task(pool, task_id, train_id):
    async with pool.acquire() as connection:
        async with connection.transaction():
            # Восстанавливаем сам таск
            task_restore_query = (
                "INSERT INTO monitor_tasks (id, train_id, user_id, monitor_setup, monitor_setup_info) "
                "SELECT "
                "   id,"
                "   train_id,"
                "   user_id, "
                "   monitor_setup, "
                "   monitor_setup_info "
                "FROM successful_monitor_tasks "
                "WHERE id = $1;"
            )
            await connection.execute(task_restore_query, task_id)
            # И поезд, если он был перенесен в dropped_trains_to_monitor
            train_check_query = (
                "SELECT EXISTS(SELECT 1 FROM trains_to_monitor WHERE id = $1)"
            )
            train_exists = await connection.fetchval(train_check_query, train_id)
            # Если поезд в dropped_trains_to_monitor, то восстанавливаем его, если нет, то ничего не делаем
            if not train_exists:
                train_restore_query = (
                    "INSERT INTO trains_to_monitor (id, origin_station, destination_station, trip_date, train_num) "
                    "SELECT "
                    "   id,"
                    "   origin_station,"
                    "   destination_station, "
                    "   trip_date, "
                    "   train_num "
                    "FROM dropped_trains_to_monitor "
                    "WHERE id = $1;"
                )
                await connection.execute(train_restore_query, train_id)
                # И удаляем его из dropped_trains_to_monitor
                train_delete_query = (
                    "DELETE FROM dropped_trains_to_monitor "
                    "WHERE id = $1;"
                )
                await connection.execute(train_delete_query, train_id)
            return "\U00002705 Монитор успешно восстановлен"


# Функция удаления из активных и сохранения успешного таска
async def delete_successful_monitor_task(pool, task_id):
    async with pool.acquire() as connection:
        async with connection.transaction():
            # Сначала перенесем отработавший таск в successful_monitor_tasks
            save_successful_task_query = (
                "INSERT INTO successful_monitor_tasks (id, train_id, user_id, monitor_setup, monitor_setup_info, "
                "success_timestamp) "
                "SELECT "
                "   id,"
                "   train_id,"
                "   user_id, "
                "   monitor_setup, "
                "   monitor_setup_info,"
                "   NOW() "
                "FROM monitor_tasks "
                "WHERE id = $1;"
            )
            await connection.execute(save_successful_task_query, task_id)
            # Затем удаляем его
            delete_successful_task_query = (
                "DELETE FROM monitor_tasks "
                "WHERE id = $1;"
            )
            await connection.execute(delete_successful_task_query, task_id)


# Функция для удаления выбранного монитора
async def delete_selected_monitors(pool, monitor_ids):
    if not monitor_ids:
        return

    async with pool.acquire() as connection:
        async with connection.transaction():
            # Создание строки запроса с правильным количеством параметров
            query = (
                "DELETE FROM monitor_tasks "
                "WHERE id = ANY($1);"
            )
            await connection.execute(query, monitor_ids)


# Чисто тестовая функция
async def get_monitor_task_config(pool, monitor_task_id):
    async with pool.acquire() as connection:
        query = "SELECT monitor_setup FROM monitor_tasks WHERE id = $1"
        monitor_setup_json = await connection.fetchval(query, monitor_task_id)

        if monitor_setup_json:
            # Превращаем JSON в словарь
            monitor_setup_dict = json.loads(monitor_setup_json)
            return monitor_setup_dict
        else:
            return None


# Сохраняем всех пользователей, взаимодействовавших с ботом
# Просто API телеграма не позволяет получить user_id пользователя через его username, значит для получения user_id
# необходимо, чтобы пользователь сначала сам написал боту, а затем я (админ) добавлю его айди в список разрешенных
async def save_user(pool, user_id, username):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (user_id, username)
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE
            SET username = EXCLUDED.username
            """,
            user_id, username
        )

# Функция для получения user_id
async def get_user_id_by_username(pool, username):
    async with pool.acquire() as conn:
        result = await conn.fetchrow(
            "SELECT user_id FROM users WHERE username = $1",
            username
        )
        return result["user_id"] if result else None

# Функция для выдачи доступа к боту
async def add_allowed_user(pool, user_id):
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO allowed_users (user_id) VALUES ($1) ON CONFLICT DO NOTHING",
            user_id
        )

# Функция для удаления доступа к боту
async def remove_allowed_user(pool, user_id):
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM allowed_users WHERE user_id = $1",
            user_id
        )

# Проверка доступа
async def is_user_allowed(pool, user_id):
    async with pool.acquire() as conn:
        result = await conn.fetchrow(
            "SELECT 1 FROM allowed_users WHERE user_id = $1",
            user_id
        )
        return bool(result)

# Фильтр для проверки доступа
async def check_access(pool, message: types.Message):
    user_id = message.from_user.id
    return await is_user_allowed(pool, user_id)


# async def main():
#     pool = await create_connection_pool(dbconfig())
#
#     s = await quick_restore_task_check(pool, 23)
#
#     print(s[0])
#
# asyncio.run(main())
