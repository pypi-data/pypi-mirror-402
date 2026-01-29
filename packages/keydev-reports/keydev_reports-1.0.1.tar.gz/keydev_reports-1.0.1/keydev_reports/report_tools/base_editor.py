import io
from abc import abstractmethod
from typing import Optional


class BaseEditor:
    """
    Базовый класс для создания отчетов.
    """

    def __init__(self, file_name: str = None):
        self.output = io.BytesIO()
        self.file_name = file_name
        #: Workbook
        self.book = None

    @staticmethod
    def get_search_text(search_text):
        """
        Статический метод для формирования текста поиска (ключа) на основе переданного текста.
        :param search_text: Текст, на основе которого формируется ключ для поиска.
        :return: Строка, представляющая ключ для поиска.
        """
        return '${' + search_text + '}'

    def get_filepath(self):
        """
        Метод для получения рабочей книги (workbook) класса.
        :return: Рабочая книга (workbook).
        """
        return self.file_name

    def save(self, new_file_name: Optional[str] = None) -> None:
        """
        Метод для сохранения Excel-файла с новым именем (если указано) или перезаписи текущего.
        :param new_file_name: Новое имя файла (по умолчанию перезапись текущего файла).
        """
        self.file_name = new_file_name if new_file_name else self.file_name
        self.book.save(self.file_name)

    @abstractmethod
    def load_from_bytes(self, content: bytes) -> None:
        """
        Загружает документ из байтов.
        Должен быть реализован в подклассах.

        :param content: Содержимое файла в виде байтов
        """
        pass

    @abstractmethod
    def get_bytes_io(self) -> bytes:
        """
        Возвращает содержимое документа в виде байтов.
        Должен быть реализован в подклассах.

        :return: Содержимое файла в виде байтов
        """
        pass
