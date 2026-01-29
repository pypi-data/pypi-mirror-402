from pydantic import BaseModel
from typing import Type, NoReturn
from .base_provider import BaseProvider


class ProviderConfig(BaseModel):
    provider_class: Type
    kwargs: dict


class ProviderRegistry:
    """
    Класс для хранения конфигурации провайдеров.
    Класс хранит в себе сам провайдер и его аргументы для метода __init__
    """

    providers = {}

    @classmethod
    def register_provider(cls, provider_class: BaseProvider, kwargs: dict) -> NoReturn:
        """
        Метод для регистрации провайдера.
        :param provider_class: Класс провайдера.
        :param kwargs: Аргументы для __init__. Ключ - аршумент __init__, значение - аттрибуты из класса экспортера
        :return: NoReturn
        """
        provider_name = provider_class.get_class_name()
        cls.providers[provider_name] = ProviderConfig(provider_class=provider_class, kwargs=kwargs)

    @classmethod
    def get_provider_config(cls, name: str):
        return cls.providers.get(name)


def provider_registration(kwargs: dict = None):
    """
    Декоратор для регистрации провайдера в экспортере.
    Можно использовать без аргументов или с аргументами.
    Без аргументов: @provider_registration()
    по дефолту : {'data': 'report_data', 'file_name': 'new_file_path'}
    Пример: @provider_registration(kwargs={'data': 'report_data', 'file_name': 'new_file_path'})
    :param kwargs: Аргументы для __init__ провайдер класса.
    Ключ - аршумент __init__, значение - аттрибуты из класса экспортера
    :return: provider_class - экземпляр провайдера
    """
    if kwargs is None:
        kwargs = {'data': 'report_data', 'file_name': 'new_file_path'}

    def decorator(provider_class):
        ProviderRegistry.register_provider(provider_class, kwargs)
        return provider_class

    return decorator
