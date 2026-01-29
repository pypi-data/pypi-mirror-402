import os
from enum import Enum
from pprint import pprint
from typing import List, Union, Iterable, Type

from datetime import date, datetime
from decimal import Decimal

import pdfkit
from celery.result import AsyncResult
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import get_template
from django.utils.encoding import escape_uri_path
from django.views import View

from pydantic import ValidationError

from .models import ReportTemplate
from .tasks import get_no_template_report, get_template_report, run_sql_functions, run_sql_functions_optional
from .providers import (
    ColorfulTableProvider,
    ProxyModelProvider,
    TableProvider,
    TemplateProvider,
    SingleMergedTableProvider,
    ProxyPDFModelProvider,
    AddTableProvider,
)
from .mixins import FileNameMixin


class ReportFormat(Enum):
    """
    Формат отчетов.
    """

    EXCEL = {
        'extension': ['xlsx', 'xls'],
        'content_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    }
    PDF = {
        'extension': ['pdf'],
        'content_type': 'application/pdf',
    }
    WORD = {
        'extension': ['docx', 'doc'],
        'content_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    }

    def __getitem__(self, key):
        return self.value[key]

    @classmethod
    def get_content_type(cls, extension: str) -> str:
        """
        Метод для получения типа содержимого файла (content_type)
        для переданного расширения.

        :param extension: Расширение файла.
        :return: Тип содержимого файла, соответствующий заданному расширению.
        :raises: ValueError, если расширение не поддерживается.
        """
        for format_enum in cls:
            if extension in format_enum.value['extension']:
                return format_enum.value['content_type']
        else:
            raise ValueError(f'Неподдерживаемое расширение файла: {extension}')


class BaseReportView(View):
    """
    Базовый класс для отчетов.

    Атрибуты:
    title (str): Название отчета.
    task_name (callable): Celery задача для генерации отчета.
    report_format (ReportFormat): Доступные форматы для отчетов.
    provider (BaseProvider): Провайдер отчета.
    report_template (str): Название шаблона (name).
    model (Type): Модель.
    form_class : (BaseSqlForm).
    form_fields : Поля из формы (по дефолту все поля).
    obj_pk (str): Поле в форме для получения объекта из модели.
    url_name (str): Имя url.
    """

    # Название отчета
    title: str
    # Celery задача для генерации отчета
    task_name: callable
    # Доступные форматы для отчетов
    report_format = ReportFormat
    # Класс провайдера для генерации отчета
    provider: Type
    # Название шаблона (name)
    report_template: str
    # Модель
    model: Type = None
    # Форма
    form_class = None
    form_fields: Union[tuple, str] = '__all__'
    obj_pk: str  # Поле в форме для получения объекта из модели
    # URL путь для отчета
    url_name: str
    # Флаг для определения источника даты в названии отчета: True c текущей датой | False из формы
    is_current_date: bool = False

    def get_report_template(self) -> int:
        """
        Метод для получения шаблона.

        :return: Возвращает pk шаблона
        """
        return get_object_or_404(ReportTemplate, name=self.report_template).pk

    def get_data_from_task(self, *args, **kwargs):
        """
        Функция для запуска задачи.

        :param args:
        :param kwargs:
        :return:
        """
        return self.task_name.delay(*args, **kwargs)

    def report_response(self, file_path: str) -> HttpResponse:
        """
        Метод для скачивания файла.
        Поддерживает как локальные пути, так и S3 presigned URLs.

        :param file_path: Путь к файлу или URL

        :return: HttpResponse или HttpResponseRedirect
        """
        from .storage import is_s3_url

        # Проверяем является ли это S3 URL
        if is_s3_url(file_path):
            # Для S3 делаем редирект на presigned URL
            from django.http import HttpResponseRedirect

            return HttpResponseRedirect(file_path)
        else:
            # Локальный файл - отдаём как раньше
            file_extension = os.path.splitext(file_path)[-1][1:]
            content_type = self.report_format.get_content_type(file_extension)
            response = HttpResponse(open(file_path, 'rb'), content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename={escape_uri_path(os.path.basename(file_path))}'
            return response

    def get_provider_name(self) -> str:
        """
        Метод для получения названия провайдера.

        :return: Название провайдера
        """
        return self.provider.get_class_name()

    def add_data(self, *args, **kwargs) -> Iterable:
        """
        Метод для добавления данных. Метод должен вызывать update_data и передать в нее данные
        """
        pass

    def update_data(self, data: Iterable) -> Iterable:
        """
        Метод для обновления данных.
        Вызывается после add_data чтобы добавить данные НЕ ИЗМЕНЯЯ ИСХОДНЫЙ КОД.
        """
        return data

    def get_context_data(self):
        form = self.form_class(form_fields=self.form_fields)
        context = {'form': form, 'url_name': self.url_name}
        return context

    def set_report_title(self):
        """Метод для обновления названия отчета."""
        return self.title


class SqlReportView(FileNameMixin, BaseReportView):
    """
    Класс для отчетов с sql функциями.

    Attributes:
    sql_function (str, dict): Название функции или словарь с функциями,
    где ключ - символ подстановки, значение - название функции.
    serializer_class (BaseSerializer): Сериализатор данных из sql функции.
    fields (tuple, dict, str): Доступные поля для отчета.
    """

    sql_function: Union[str, dict]
    serializer_class = None
    fields: Union[tuple, dict, str] = '__all__'
    template_name: str = 'keydev_reports/report_modal_form.html'
    task_name = get_no_template_report
    provider = ColorfulTableProvider

    @classmethod
    def get_fields(cls) -> dict:
        """
        Метод для получения всех доступных полей.
        :return: Словарь, где ключ - название полей, а значение - читаемое название полей.
        """
        if isinstance(cls.fields, dict):
            return cls.fields
        elif isinstance(cls.fields, tuple):
            return cls.serializer_class.get_field_names(include=cls.fields)
        else:
            return cls.serializer_class.get_field_names()

    def get_serialized_data(self, fetched_data: List[dict], fields: tuple = None) -> list:
        """
        Метод для валидации данных из sql функции.
        :param fetched_data: данные из sql функции.
        :param fields: Поля для выборки из сериализатора.
        :return: list Лист с данными.
        """
        final_data = list()
        for item in fetched_data:
            try:
                validated_data = self.serializer_class(**item).values_list(include=fields)
                final_data.append(validated_data)
            except ValidationError as e:
                errors = e.errors()
                pprint(f'Validation error: {errors}')
        return final_data

    def download_report(self, task):
        task.wait()
        task_status = AsyncResult(task.id).status

        if task_status == 'SUCCESS':
            filepath = task.get('files')['files'][0]
            return self.report_response(filepath)
        else:
            return HttpResponse('Произошла ошибка при формировании отчета.')

    def get(self, request):
        form_html = render(request, self.template_name, self.get_context_data()).content
        return JsonResponse({'form_html': form_html.decode('utf-8'), 'title': self.title})

    def add_data(self, func_args: list, *args, **kwargs):
        super().add_data(*args, **kwargs)
        final_data = {}
        fetched_data = run_sql_functions(self.sql_function, func_args)
        table_data = list()
        headers = list(v for k, v in fetched_data[0].items())
        table_data.append(headers)
        table_data.extend(self.get_serialized_data(fetched_data[1:]))

        final_data['table_data'] = table_data
        final_data['title'] = self.set_report_title()
        return self.update_data(final_data)

    def post(self, request):
        form = self.form_class(request.POST, form_fields=self.form_fields)
        if form.is_valid():
            self.form_instance = form
            func_args = form.get_sql_func_args()
            result = self.get_data_from_task(
                report_data=self.add_data(func_args),
                user_name=request.user.username,
                report_name=self.title,
                extension='xlsx',
                provider_name=self.get_provider_name(),
                file_name=self.get_file_name(),
            )
            return JsonResponse({'task_id': result.id, 'status': result.status})
        else:
            messages.error(request, 'Форма не валидна.')
        form_html = render(request, self.template_name, self.get_context_data()).content
        return JsonResponse({'form_html': form_html.decode('utf-8'), 'title': self.title})


class ProxyReportView(BaseReportView):
    """
    Класс для отчетов с proxy моделями.
    """

    provider = ProxyModelProvider
    task_name = get_template_report

    def add_data(self, pk):
        obj = self.model.proxy_objects.get_all_data().get(pk=pk)
        report_data = obj.get_report_data()
        return self.update_data(report_data)

    def get(self, request, pk, report_id):
        result = self.get_data_from_task(
            report_data=self.add_data(pk),
            user_name=request.user.username,
            report_id=report_id,
            provider_name=self.get_provider_name(),
        )
        return JsonResponse({'task_id': result.id, 'status': result.status})


class CheckBoxReportView(SqlReportView):
    """
    Класс для отчетов с выбором полей (checkbox).
    """

    template_name = 'keydev_reports/standard_report_form.html'
    task_name = get_no_template_report

    def get_context_data(self):
        context = super().get_context_data()
        context['fields'] = self.get_fields()
        context['title'] = self.title
        return context

    def add_data(self, func_args: list, fields: tuple):
        fetched_data = run_sql_functions(self.sql_function, func_args)
        final_data = {}
        table_data = list()
        headers = list(v for k, v in fetched_data[0].items() if k in fields)
        table_data.append(headers)
        table_data.extend(self.get_serialized_data(fetched_data[1:], fields))
        final_data['table_data'] = table_data
        final_data['title'] = self.set_report_title()
        return self.update_data(final_data)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())

    def post(self, request):
        fields = tuple(
            field
            for field in request.POST.keys()
            if field != 'csrfmiddlewaretoken'
            and field != 'date_min'
            and field != 'date_max'
            and field != 'report_format'
        )
        form = self.form_class(request.POST, form_fields=self.form_fields)

        if form.is_valid():
            self.form_instance = form
            func_args = form.get_sql_func_args()
            result = self.get_data_from_task(
                report_data=self.add_data(func_args, fields),
                user_name=request.user.username,
                report_name=self.title,
                extension='xlsx',
                provider_name=self.get_provider_name(),
                file_name=self.get_file_name(),
            )
            return JsonResponse({'task_id': result.id, 'status': result.status})
        else:
            messages.error(request, 'Форма не валидна.')
        return render(request, self.template_name, self.get_context_data())


class TemplateReportView(SqlReportView):
    """
    Класс для отчетов с подстановкой таблиц в шаблон.
    """

    task_name = get_template_report
    provider = TableProvider

    def add_data(self, func_args: list, *args, **kwargs):
        data = run_sql_functions(self.sql_function, func_args)
        return self.update_data(data)

    def post(self, request):
        form = self.form_class(request.POST, form_fields=self.form_fields)
        if form.is_valid():
            self.form_instance = form
            func_args = form.get_sql_func_args()
            result = self.get_data_from_task(
                report_data=self.add_data(func_args),
                user_name=request.user.username,
                report_id=self.get_report_template(),
                provider_name=self.get_provider_name(),
                file_name=self.get_file_name(),
            )
            return JsonResponse({'task_id': result.id, 'status': result.status})
        else:
            messages.error(request, 'Форма не валидна.')
        form_html = render(request, self.template_name, self.get_context_data()).content
        return JsonResponse({'form_html': form_html.decode('utf-8'), 'title': self.title})


class ReplacerView(TemplateReportView):
    """
    Класс для отчетов с подставлением значений и с подстановкой таблиц.
    Данные берутся из прокси моделей и из скл функций.
    """

    model = None
    provider = TemplateProvider

    def add_data(self, pk: int, func_args: list) -> Iterable:
        obj = self.model.proxy_objects.get_all_data().get(pk=pk)
        data = {'replace_data': obj.get_report_data(), 'table_data': run_sql_functions(self.sql_function, func_args)}
        return self.update_data(data)

    def post(self, request):
        form = self.form_class(request.POST, form_fields=self.form_fields)
        if form.is_valid():
            self.form_instance = form
            func_args = form.get_sql_func_args()
            result = self.get_data_from_task(
                report_data=self.add_data(form.cleaned_data[self.obj_pk].pk, func_args),
                user_name=request.user.username,
                report_id=self.get_report_template(),
                provider_name=self.get_provider_name(),
                file_name=self.get_file_name(),
            )
            return JsonResponse({'task_id': result.id, 'status': result.status})
        else:
            messages.error(request, 'Форма не валидна.')
        form_html = render(request, self.template_name, self.get_context_data()).content
        return JsonResponse({'form_html': form_html.decode('utf-8'), 'title': self.title})


class SingleMergedTableView(TemplateReportView):
    """
    Класс для отчетов с подставлением значений и с подстановкой таблиц.
    Данные берутся из скл функций, а данные для единичных подстановок по умолчанию пустые
    (могут предоставляться вспомогательным методам - update_data).
    """

    provider = SingleMergedTableProvider

    def add_data(self, func_args: list):
        data = {'replace_data': {}, 'table_data': run_sql_functions(self.sql_function, func_args)}
        return self.update_data(data)

    def post(self, request):
        form = self.form_class(request.POST, form_fields=self.form_fields)
        if form.is_valid():
            self.form_instance = form
            func_args = form.get_sql_func_args()
            result = self.get_data_from_task(
                report_data=self.add_data(func_args),
                user_name=request.user.username,
                report_id=self.get_report_template(),
                provider_name=self.get_provider_name(),
                file_name=self.get_file_name(),
            )
            return JsonResponse({'task_id': result.id, 'status': result.status})
        else:
            messages.error(request, 'Форма не валидна.')
        form_html = render(request, self.template_name, self.get_context_data()).content
        return JsonResponse({'form_html': form_html.decode('utf-8'), 'title': self.title})


def get_pdf_file(request, template, result_content=None):
    """
    Создает и возвращает PDF-файл на основе указанного шаблона и данных.

    :param request: HttpRequest объект Django, представляющий текущий HTTP запрос.
    :type request: HttpRequest

    :param template: Имя шаблона, который будет использован для создания PDF-файла.
    :type template: str

    :param result_content: Словарь с данными, которые будут использованы при рендеринге шаблона.
    :type result_content: dict, optional

    :return: Объект HttpResponse сгенерированным PDF-файлом.
    :rtype: HttpResponse

    """
    if result_content is None:
        result_content = {}
    template = get_template(template)
    html = template.render(result_content)
    path_wkhtmltopdf = '/bin/wkhtmltopdf'
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
    options = {
        'zoom': 1.00,
        'page-size': 'A4',
        'encoding': 'utf-8',
        'margin-top': '0cm',
        'margin-bottom': '0cm',
        'margin-left': '0cm',
        'margin-right': '0cm',
    }
    folder = settings.MEDIA_ROOT + f'/pdf_reports/{str(request.user.username)}/'
    if not os.path.exists(folder):
        os.makedirs(folder)
    file_name = folder + f'{str(request.user.username)}_{datetime.now().strftime("%d-%m-%Y_%H-%M-%S")}.pdf'
    pdfkit.from_string(str(html), file_name, configuration=config, options=options)
    with open(file_name, 'rb') as file:
        response = HttpResponse(file, content_type='application/pdf')
        return response


class PdfView(View):
    """
    Генерирует и возвращает PDF-файл на основе указанного шаблона и данных.

    Атрибуты:
        queryset: Запрос, используемый для извлечения данных для шаблона.
        html_file: Имя шаблона, используемого для создания PDF-файла.
        context: Переменная контекста, используемая для рендеринга шаблона.
    """

    queryset = None
    html_file = None
    context = None

    def get(self, request, pk):
        queryset = self.queryset.objects.all()
        return get_pdf_file(request, self.html_file, {self.context: queryset})


class ProxyPDFReportView(ProxyReportView):
    provider = ProxyPDFModelProvider


class SqlReportViewOptional(FileNameMixin, BaseReportView):
    """
    Представление для построения SQL-отчёта с возможностью передачи массива ENUM-значений
    в качестве последнего аргумента SQL-функции.

    Поддерживает асинхронную генерацию отчёта, автоподстановку заголовков, обработку алиасов,
    а также вывод формы в модальном окне.

    Атрибуты:
        sql_function (Union[str, dict]):
            Название SQL-функции или словарь {ключ: функция}
            для множественных запросов.
        fields (Union[tuple, dict, str]):
            Список или отображение полей формы. По умолчанию '__all__'.
        template_name (str):
            Шаблон формы, отображаемый в модальном окне.
        task_name (callable):
            Функция для запуска асинхронной задачи генерации отчёта.
        provider (BaseProvider):
            Класс для вставки таблиц в отчёт (например, Word/Excel).

    Методы:
        clean_value(value): Преобразует значение в сериализуемый формат (строку, число, дату и т.д.).
        download_report(task): Загружает сгенерированный файл отчёта после завершения задачи.
        get(request): Возвращает HTML формы в JSON для отображения в модальном окне.
        add_data(func_args, *args, **kwargs): Получает данные из SQL-функции и форматирует результат с заголовками.
        post(request): Обрабатывает отправку формы, запускает задачу генерации отчета и возвращает task_id.
    """

    sql_function: Union[str, dict]
    fields: Union[tuple, dict, str] = '__all__'
    template_name: str = 'keydev_reports/report_modal_form.html'
    task_name = get_no_template_report
    provider = AddTableProvider

    @staticmethod
    def clean_value(value):
        """
        Приводит значение к сериализуемому виду:
        - None → пустая строка
        - Decimal → float
        - date/datetime → ISO строка
        - всё остальное → str(value)

        Args:
            value (Any): Значение ячейки таблицы.

        Returns:
            Union[str, int, float]: Преобразованное значение.
        """
        if value is None:
            return ''
        if isinstance(value, (int, float, str)):
            return value
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        return str(value)

    def download_report(self, task):
        """
        Получает файл отчета после выполнения асинхронной задачи.

        Args:
            task (AsyncResult): Задача Celery или другая асинхронная задача.

        Returns:
            HttpResponse: Содержимое файла или сообщение об ошибке.
        """
        task.wait()
        task_status = AsyncResult(task.id).status

        if task_status == 'SUCCESS':
            filepath = task.get('files')['files'][0]
            return self.report_response(filepath)
        else:
            return HttpResponse('Произошла ошибка при формировании отчета.')

    def get(self, request):
        """
        Обрабатывает GET-запрос и возвращает HTML формы отчета.

        Args:
            request (HttpRequest): Запрос от клиента.

        Returns:
            JsonResponse: HTML формы и заголовок для модального окна.
        """
        form_html = render(request, self.template_name, self.get_context_data()).content
        return JsonResponse({'form_html': form_html.decode('utf-8'), 'title': self.title})

    def add_data(self, func_args: list, *args, **kwargs):
        """
        Получает данные из SQL-функции и подготавливает их для отчета,
        применяя алиасы к заголовкам, если они заданы в форме.

        Args:
            func_args (list): Аргументы для SQL-функции.
            form (BaseForm, optional): Форма, содержащая метод get_column_aliases().

        Returns:
            dict: Обновленные данные с заголовками, таблицей и заголовком отчета.
        """
        form = kwargs.get('form')
        fetched_data = run_sql_functions_optional(
            sql_functions=self.sql_function,
            func_args=func_args,
            title=self.title,
            form_fields=self.form_fields,
            clean_func=self.clean_value,
        )

        # Получаем алиасы из формы
        column_aliases = {}
        if form and hasattr(form, 'get_column_aliases'):
            column_aliases = form.get_column_aliases()

        # Распаковка
        headers = fetched_data.get('headers', [])
        raw_table_data = fetched_data.get('table_data', [])
        data_rows = raw_table_data[1:] if raw_table_data else []

        # Применяем алиасы
        display_headers = [column_aliases.get(h, h) for h in headers]

        final_data = {
            'table_data': [display_headers] + data_rows,
            'headers': display_headers,
            'title': self.set_report_title(),
        }

        return self.update_data(final_data)

    def post(self, request):
        """
        Обрабатывает POST-запрос, валидирует форму, запускает задачу отчета
        и возвращает идентификатор асинхронной задачи.

        Args:
            request (HttpRequest): Запрос от клиента.

        Returns:
            JsonResponse: Статус задачи или HTML с ошибкой валидации формы.
        """
        form = self.form_class(request.POST, form_fields=self.form_fields)
        if form.is_valid():
            self.form_instance = form
            func_args = form.get_sql_func_args()
            result = self.get_data_from_task(
                report_data=self.add_data(func_args, form=form),
                user_name=request.user.username,
                report_name=self.title,
                extension='xlsx',
                provider_name=self.get_provider_name(),
                file_name=self.get_file_name(),
            )
            return JsonResponse({'task_id': result.id, 'status': result.status})
        else:
            messages.error(request, 'Форма не валидна.')
        form_html = render(request, self.template_name, self.get_context_data()).content
        return JsonResponse({'form_html': form_html.decode('utf-8'), 'title': self.title})
