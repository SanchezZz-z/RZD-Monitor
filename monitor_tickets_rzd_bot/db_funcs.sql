-- Условия:
-- 1) В таблице user_trains есть столбец departure_timestamp (timestamp). Это время отправления поезда. Необходимо,
-- чтобы каждую минуту проводилась проверка - если время departure_timestamp позднее или равно текущему времени, то
-- запись с таким поездом удаляется из таблицы (потому что поезд уже отправился). Кроме того, если в таблицах
-- trains_to_monitor или dropped_trains_to_monitor есть запись с такими же origin_station, destination_station,
-- trip_date и train_num, как и удаленного поезда в таблице user_trains, то она тоже должна быть удалена. Если из
-- таблицы trains_to_monitor удаляется поезд, который уже отправился, то записи с такими же train_id должны быть удалены
-- из таблицы monitor_tasks.
-- 2) В таблице trains_to_monitor не может быть записей с train_id, которых нет в таблице monitor_tasks. Если возникает
-- такая ситуация, что в таблице trains_to_monitor есть запись с train_id, которого нет в таблице monitor_tasks, тогда
-- такая запись переносится в dropped_trains_to_monitor и удаляется из таблицы trains_to_monitor.
-- 3) При удалении записи (поезда) из таблицы user_trains необходимо проверить, есть ли в таблице trains_to_monitor
-- записи (поезда) с такими же origin_station, destination_station,trip_date и train_num. Если есть, то необходимо
-- получить id записи и удалить из таблицы monitor_tasks все записи, у которых train_id совпадает с полученным id, а
-- user_id совпадает с user_id поезда, удаленного из таблицы user_trains.
-- 4) Из таблицы dropped_trains_to_monitor удалять поезда, у которых trip_date больше (позже), чем текущая дата.

-- Установим часовой пояс
SET TIME ZONE 'Europe/Moscow';

-- Убедитесь, что у вас установлено расширение pg_cron
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Функция для удаления отправившихся поездов (по моему, она немного дублирует действия
-- delete_related_monitor_tasks_trigger)
CREATE OR REPLACE FUNCTION remove_departed_trains()
RETURNS VOID AS $$
BEGIN
    DELETE FROM monitor_tasks
    WHERE train_id IN (
        SELECT id
        FROM trains_to_monitor
        WHERE (origin_station, destination_station, trip_date, train_num) IN (
            SELECT origin_station, destination_station, trip_date, train_num
            FROM user_trains
            WHERE departure_timestamp <= timezone('Europe/Moscow', NOW())
        )
    );

    DELETE FROM trains_to_monitor
    WHERE (origin_station, destination_station, trip_date, train_num) IN (
        SELECT origin_station, destination_station, trip_date, train_num
        FROM user_trains
        WHERE departure_timestamp <= timezone('Europe/Moscow', NOW())
    );

    DELETE FROM dropped_trains_to_monitor
    WHERE (origin_station, destination_station, trip_date, train_num) IN (
        SELECT origin_station, destination_station, trip_date, train_num
        FROM user_trains
        WHERE departure_timestamp <= timezone('Europe/Moscow', NOW())
    );

    DELETE FROM user_trains
    WHERE departure_timestamp <= timezone('Europe/Moscow', NOW());
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION transfer_orphaned_trains()
RETURNS VOID AS $$
BEGIN
    INSERT INTO dropped_trains_to_monitor (id, origin_station, destination_station, trip_date, train_num)
    SELECT id, origin_station, destination_station, trip_date, train_num
    FROM trains_to_monitor
    WHERE id NOT IN (SELECT train_id FROM monitor_tasks);

    DELETE FROM trains_to_monitor
    WHERE id NOT IN (SELECT train_id FROM monitor_tasks);
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION delete_related_monitor_tasks_trigger()
RETURNS TRIGGER AS $$
DECLARE
    train_rec RECORD;
BEGIN
    -- Проверяем, было ли удалено значение из таблицы user_trains
    IF TG_OP = 'DELETE' THEN
        -- Поиск записей в trains_to_monitor, совпадающих с удаленной записью из user_trains
        FOR train_rec IN
            SELECT id FROM trains_to_monitor
            WHERE origin_station = OLD.origin_station
              AND destination_station = OLD.destination_station
              AND trip_date = OLD.trip_date
              AND train_num = OLD.train_num
        LOOP
            -- Удаление записей из monitor_tasks, связанных с найденными train_id
            DELETE FROM monitor_tasks
            WHERE train_id = train_rec.id
              AND user_id = OLD.user_id;
        END LOOP;
    END IF;

    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- Создание триггера на таблицу user_trains
CREATE OR REPLACE TRIGGER delete_related_monitor_tasks_trigger
AFTER DELETE ON user_trains
FOR EACH ROW
EXECUTE FUNCTION delete_related_monitor_tasks_trigger();


CREATE OR REPLACE FUNCTION delete_dropped_trains()
RETURNS void AS $$
BEGIN
    -- Удаление из dropped_trains_to_monitor, если trip_date больше текущей даты
    DELETE FROM dropped_trains_to_monitor
    WHERE trip_date < CURRENT_DATE;
END;
$$ LANGUAGE plpgsql;


-- Запланируйте выполнение функции remove_departed_trains каждую минуту
SELECT cron.schedule('remove_departed_trains', '*/1 * * * *', 'SELECT remove_departed_trains();');

-- Запланируйте выполнение функции transfer_orphaned_trains каждую минуту
SELECT cron.schedule('transfer_orphaned_trains', '*/1 * * * *', 'SELECT transfer_orphaned_trains();');

-- Запланируйте выполнение функции delete_dropped_trains каждую минуту
SELECT cron.schedule('delete_dropped_trains', '*/1 * * * *', 'SELECT delete_dropped_trains();');
