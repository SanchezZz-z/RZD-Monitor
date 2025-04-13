from dataclasses import asdict
import asyncpg


class DatabaseConnection:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.connection_pool = None

    async def init_connection_pool(self, db_config):
        """
        Инициализация пула соединений с базой данных.
        :param db_config: Объект DbConfig, содержащий параметры подключения.
        """
        if self.connection_pool is None:
            # Преобразуем db_config в словарь перед передачей
            connection_params = asdict(db_config)
            self.connection_pool = await asyncpg.create_pool(**connection_params)

    async def get_connection_pool(self):
        """
        Получение пула соединений с базой данных.
        """
        if self.connection_pool is None:
            raise ValueError("Connection pool is not initialized")
        return self.connection_pool


# Создаем экземпляр класса DatabaseConnection, который будет использоваться в приложении
database_connection = DatabaseConnection()
