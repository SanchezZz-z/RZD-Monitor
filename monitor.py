import json
import asyncio

from db_connection import database_connection
from monitor_setup import generate_user_messages
from rzd_app import get_seats
from testing import delete_successful_monitor_task
from tgbot_template_v3.tgbot.keyboards.inline import restore_monitor_task_inline_keyboard


async def monitor(bot):
    connection_pool = await database_connection.get_connection_pool()
    while True:
        async with connection_pool.acquire() as connection:
            # Извлечение всех записей из trains_to_monitor
            trains_to_monitor = await connection.fetch("SELECT * FROM trains_to_monitor;")
            if trains_to_monitor:
                # Извлечение связанных данных из monitor_tasks
                monitor_tasks_query = (
                    "SELECT "
                    "    id, "
                    "    train_id, "
                    "    user_id, "
                    "    monitor_setup,"
                    "    monitor_setup_info "
                    "FROM monitor_tasks "
                    "WHERE train_id = ANY($1::int[]);"
                )
                train_ids = [record["id"] for record in trains_to_monitor]
                monitor_tasks = await connection.fetch(monitor_tasks_query, train_ids)

                # Создание словаря для сопоставления train_id с monitor_tasks
                monitor_tasks_dict = {}
                for task in monitor_tasks:
                    if task["train_id"] not in monitor_tasks_dict:
                        monitor_tasks_dict[task["train_id"]] = []
                    monitor_tasks_dict[task["train_id"]].append(dict(task))

                # Выполнение запросов к API и обработка данных по мере завершения
                trains_data_dict = {}
                to_do_tasks = {train["id"]: get_seats(train["origin_station"], train["destination_station"],
                                                      train["trip_date"].strftime("%d.%m.%Y"), train["train_num"])
                               for train in trains_to_monitor}

                for train_id, to_do_task in to_do_tasks.items():
                    try:
                        train_data = await to_do_task
                        trains_data_dict[train_id] = train_data

                        if train_id in monitor_tasks_dict:
                            for completed_task in monitor_tasks_dict[train_id]:
                                text = generate_user_messages(json.loads(completed_task["monitor_setup"]), train_data)
                                # Если места нашлись, то отправляем пользователю сообщение и удаляем таск
                                if text:
                                    message_header = ("\U00002757\U00002757\U00002757 <b><u>НАЙДЕНЫ БИЛЕТЫ</u></b> "
                                                      "\U00002757\U00002757\U00002757\n\n")
                                    train_info = "".join(completed_task["monitor_setup_info"].split("\n\n")[0]) + "\n\n"
                                    monitor_deleted_msg_header = ("Сработавший монитор удален\nЕсли Вы не успели "
                                                                  "купить билет, нажмите на кнопку 'Восстановить "
                                                                  "монитор' под этим сообщением\n\n")
                                    monitor_deleted_settings_msg = "\U0001F6E0 Настройки монитора:\n\n"
                                    # Отправляем сообщение, что сработавший монитор удален
                                    await bot.send_message(text=monitor_deleted_msg_header +
                                                           monitor_deleted_settings_msg +
                                                           completed_task["monitor_setup_info"],
                                                           chat_id=completed_task["user_id"],
                                                           reply_markup=restore_monitor_task_inline_keyboard(
                                                               completed_task["id"], completed_task["train_id"]))
                                    # Отправляем сообщение с информацией о найденных билетах
                                    await bot.send_message(text=message_header + train_info + text,
                                                           chat_id=completed_task["user_id"])
                                    # Удаляем монитор
                                    await delete_successful_monitor_task(connection_pool, completed_task["id"])

                    except Exception as e:
                        print("При получении информации о поезде возникла ошибка: {}".format(e))

            await asyncio.sleep(30)
