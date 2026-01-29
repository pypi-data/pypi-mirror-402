import datetime
import io
import os
from typing import Iterable

from django.conf import settings

from .models import ReportTemplate
from .providers import ProviderRegistry
from .storage import get_storage_backend


class BaseExporter:
    """
    Базовый класс экспортер.
    """

    def __init__(self, report_data: Iterable, user_name: str, provider_name: str, file_name: None | str):
        #: dict: Данные для отчета.
        self.report_data = report_data
        #: str: Имя пользователя, запрашивающего отчет.
        self.user_name = user_name
        self.provider_name = provider_name
        #: list: Расширения отчетов (Excel, Word).
        self.excel_report_extensions = ['xlsx', 'xls']
        self.word_report_extensions = ['docx', 'doc']
        self.default_path = os.path.join(settings.MEDIA_ROOT, 'keydev_reports', 'requested_reports', self.user_name)
        # : str: Название отчета.
        self.file_name = file_name

        # Инициализируем storage backend
        self.storage = get_storage_backend()

    def create_provider_instance(self, provider_name: str):
        """
        Метод для создания экземпляра провайдера.
        :param provider_name: Название провайдера.
        :return: Экземпляр провайдера.
        """
        provider_config = ProviderRegistry.get_provider_config(provider_name)
        if provider_config:
            kwargs_dict = provider_config.kwargs
            mapped_kwargs = {key: getattr(self, value) for key, value in kwargs_dict.items()}
            return provider_config.provider_class(**mapped_kwargs).export()
        else:
            raise ValueError(
                f'Unknown provider: {provider_name}, available providers: {ProviderRegistry.providers.keys()}'
            )

    def get_report(self) -> str:
        """
        Метод для возврата отчета по типу отчета (proxy, sql).
        :return: Путь к файлу.
        """
        return self.create_provider_instance(self.provider_name)


class TemplateReportExporter(BaseExporter):
    """
    Класс для создания отчетов с шаблонами (экспортер).
    """

    def __init__(self, report_id: int, table_data: dict = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        """
        Инициализирует объект TemplateReportExporter и устанавливает атрибуты класса.
        :param report_data: Данные для отчета.
        :param user_name: Имя пользователя, запрашивающего отчет.
        :param report_id: Шаблон отчета, полученный по идентификатору.
        :param report_type: Тип отчета (sql, proxy, replacer).
        """
        #: int: Шаблон отчета, полученный по идентификатору.
        self.report_template = ReportTemplate.objects.get(id=report_id)
        #: str: Новый отчет (путь к файлу).
        self.new_file_path = self._get_report_new_path()
        #: dict: Данные для таблицы. В случае если нужно принимать 2 данных.
        self.table_data = table_data

    def _get_report_new_path(self) -> str:
        """
        Метод для создания нового шаблона на основе полученного шаблона.
        Метод создает новый файл с уникальным именем для отчета.
        :return: Возвращает путь к файлу или URL в зависимости от storage backend.
        """
        extension = self.report_template.file.name.split('.')[-1]
        if self.file_name:
            filename = f'{self.file_name}.{extension}'
        else:
            timestamp = datetime.datetime.now().strftime('%d_%m_%Y_%H_%M_%S')
            filename = f'{self.report_template.name}_{timestamp}.{extension}'.replace(' ', '_')

        # Относительный путь для storage
        relative_path = os.path.join(self.user_name, filename)

        # Читаем шаблон из file field (работает и с S3, и с локальным хранилищем)
        with self.report_template.file.open('rb') as template_file:
            template_content = template_file.read()

        # Сохраняем копию шаблона через storage backend
        self.storage.save(io.BytesIO(template_content), relative_path)

        # Возвращаем относительный путь для провайдеров
        # Провайдер сам решит как его обработать (через storage.load() для S3 или напрямую для local)
        return relative_path


class ReportExporter(BaseExporter):
    """
    Класс для генерации отчетов экспортер.
    """

    def __init__(self, report_name: str, extension: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.report_name = report_name
        self.extension = extension
        self.new_file_path = self.build_file_path()

    def build_file_path(self) -> str:
        """
        Метод для построения относительного пути к файлу отчета.
        Используется storage backend для сохранения.
        :return: Относительный путь к файлу отчета (для передачи в провайдер).
        """
        if self.file_name:
            filename = f'{self.file_name}.{self.extension}'
        else:
            filename = f'{self.report_name}_{datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S")}.{self.extension}'

        # Возвращаем относительный путь (провайдер работает с относительными путями)
        relative_path = os.path.join(self.user_name, filename)
        return relative_path
