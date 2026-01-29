from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class BaseSerializer(BaseModel):
    """
    Базовый класс для сериализации и валидации данных.
    """

    model_config = ConfigDict(populate_by_name=True)

    def values_list(self, include: Optional[List[str]] = None, exclude: Optional[List[str]] = None) -> list:
        """
        Метод для получения значений полей как список.
        Метод преобразовывает значения с типом dict в list.

        :param include: Поля для включения в список.
        :param exclude: Поля для исключения из списка.
        :return: Список из значений полей.
        """
        data = list()
        if include:
            data = list(self.model_dump(include=include).values())
        if exclude:
            data = list(self.model_dump(exclude=exclude).values())
        if include is None and exclude is None:
            data = list(self.model_dump().values())
        return data

    @classmethod
    def get_field_names(cls, include: tuple = None) -> dict:
        """
        Возвращает словарь с именами полей и их псевдонимами.

        :param include: Список имен полей, которые требуется включить (по умолчанию - None, что означает все поля).
        :type include: tuple or None

        :return: Словарь, где ключи - имена полей, значения - читаемое название полей.
        :rtype: dict
        """
        if include is None:
            return {k: v.alias for k, v in cls.model_fields.items()}
        return {k: v.alias for k, v in cls.model_fields.items() if k in include}
