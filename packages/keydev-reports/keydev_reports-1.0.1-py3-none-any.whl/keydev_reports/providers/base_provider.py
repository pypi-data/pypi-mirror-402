import io
from abc import ABC, abstractmethod
from typing import Iterable, Union


class BaseProvider(ABC):
    """
    Базовый класс для создания отчетов.
    """

    def __init__(self, data: Union[Iterable, dict], file_name: str):
        """
        Инициализатор класса.
        :param data: Данные для отчета.
        :param file_name: Путь к файлу (относительный или абсолютный в зависимости от режима).
        """
        self.data = data
        self.file_name = file_name

        # Импортируем здесь чтобы избежать циклических импортов
        from ..storage import get_storage_backend

        self.storage = get_storage_backend()

        # Определяем режим работы: если file_name это относительный путь (без /)
        # то работаем в режиме storage, иначе - в режиме совместимости (локальные файлы)
        self.use_storage_mode = file_name and not file_name.startswith('/')

    @abstractmethod
    def export(self):
        """
        Метод для получения отчета.
        :return: Относительный путь к файлу (S3 key) - НЕ URL!
        """
        pass

    @classmethod
    def get_class_name(cls):
        """
        Метод для получения имени класса.
        :return:
        """
        return cls.__name__

    def save_report_to_storage(self, file_content: io.BytesIO, relative_path: str) -> str:
        """
        Сохраняет отчёт через storage backend.

        :param file_content: Содержимое файла в виде BytesIO
        :param relative_path: Относительный путь для сохранения
        :return: URL или путь к сохранённому файлу
        """
        return self.storage.save(file_content, relative_path)

    def get_final_url(self, relative_path: str) -> str:
        """
        Получает финальный URL/путь для доступа к файлу.

        :param relative_path: Относительный путь к файлу
        :return: URL (для S3) или полный локальный путь
        """
        return self.storage.get_file_url(relative_path)
