from typing import Iterable, Dict, List, Union, Callable

from django.db import connection

from celery import shared_task

from .sql_utils import execute_sql_query
from .exporter import TemplateReportExporter, ReportExporter


@shared_task
def get_template_report(
    report_data: Iterable, user_name: str, report_id: int, provider_name: str, file_name: str | None = None
):
    """
    Функция для отчетов с шаблонами.
    :param report_data: Данные для отчета.
    :param user_name: Имя пользователя.
    :param report_id: Первичный ключ шаблона (ReportTemplate)
    :param provider_name: Название провайдера.
    :param file_name: Название отчета.
    :return: data
    """
    report = TemplateReportExporter(
        report_data=report_data,
        user_name=user_name,
        report_id=report_id,
        provider_name=provider_name,
        file_name=file_name,
    )
    data = dict()
    try:
        files = [
            report.get_report(),
        ]
    except Exception as e:
        data['error'] = str(e)
    else:
        data['files'] = files
    return data


@shared_task
def get_no_template_report(
    report_data: Iterable,
    user_name: str,
    report_name: str,
    extension: str,
    provider_name: str,
    file_name: str | None = None,
):
    """
    Функция для генерации отчетов.
    :param report_data: Данные для отчета.
    :param user_name: Имя пользователя.
    :param report_name: Название отчета.
    :param extension: Расширение отчета.
    :param provider_name: Название провайдера.
    :param file_name: Название отчета.
    :return: data
    """
    report = ReportExporter(
        report_data=report_data,
        user_name=user_name,
        report_name=report_name,
        extension=extension,
        provider_name=provider_name,
        file_name=file_name,
    )
    data = dict()
    try:
        files = [
            report.get_report(),
        ]
    except Exception as e:
        data['error'] = str(e)
    else:
        data['files'] = files
    return data


def run_sql_functions(
    sql_functions: Union[str, Dict[str, str]], func_args: List, fields: str = '*'
) -> Union[List[Dict], Dict[str, List[Dict]]]:
    """
    Функция для получения данных из одиночных или множественных SQL-функций.

    :param sql_functions: Sql-функция.
    :param func_args: Аргументы SQL-запроса.
    :param fields: Выбранные поля для запроса.
    :return: Результат выполнения SQL-функций в виде списка словарей или словаря,
    где ключи - имена функций, значения - списки словарей с результатами.
    """
    data = {} if isinstance(sql_functions, dict) else []

    if isinstance(sql_functions, str):
        sql_function = {f'{sql_functions}': sql_functions}
    else:
        sql_function = sql_functions

    with connection.cursor() as cursor:
        for key, func_name in sql_function.items():
            results = execute_sql_query(cursor, func_name, func_args, fields)
            column_names = [column[0] for column in cursor.description]
            if isinstance(data, dict):
                data[key] = results
            else:
                data.extend([dict(zip(column_names, row, strict=True)) for row in results])

    return data


def run_sql_functions_optional(
    sql_functions: Union[str, Dict[str, str]],
    func_args: List,
    title: str,
    form_fields: List[str],
    clean_func: Callable = lambda v: v,  # по умолчанию просто возвращает значение
) -> dict:
    """
    Выполняет одну или несколько SQL-функций PostgreSQL с передачей аргументов, включая массив ENUM-типов в конце,
    и форматирует результат в таблицу с заголовками и данными для отчёта.

    Поддерживает как одиночную SQL-функцию (строка), так и несколько (словарь {ключ: функция}).

    Args:
        sql_functions (Union[str, Dict[str, str]]): Название SQL-функции (строкой) или словарь {ключ: функция}
            для вызова нескольких функций.
        func_args (List): Аргументы для SQL-функции, где последний элемент — массив (ENUM PostgreSQL),
            передаваемый как список или строка "{val1,val2}".
        title (str): Заголовок отчета (будет включен в выходной словарь).
        form_fields (List[str]): Список названий полей формы, где последний элемент — это тип ENUM массива PostgreSQL.
        clean_func (Callable): Функция для очистки/преобразования значений перед вставкой в таблицу.
            По умолчанию возвращает значение как есть.

    Raises:
        ValueError: Если количество аргументов не совпадает с количеством полей формы.
        TypeError: Если результат SQL-функции — не список словарей.

    Returns:
        dict: Один из двух вариантов:
            - Если `sql_functions` — строка: словарь с ключами `"headers"`, `"table_data"` и `"title"`.
            - Если `sql_functions` — словарь: словарь с ключами из `sql_functions`,
            где каждому соответствует вложенный словарь-отчёт.

    Example:
        >>> run_sql_functions_optional(
        >>>     sql_functions='get_customer_data',
        >>>     func_args=['2024-01-01', '{active,inactive}'],
        >>>     title='Отчет по клиентам',
        >>>     form_fields=['start_date', 'customer_status_enum'],
        >>>     clean_func=lambda v: str(v) if v is not None else ''
        >>> )
    """
    if len(func_args) != len(form_fields):
        raise ValueError(f'Количество аргументов ({len(func_args)}) не соответствует полям формы ({len(form_fields)})')

    enum_type = form_fields[-1]

    # Преобразуем последний аргумент в список, если это строка
    last_arg = func_args[-1]
    if last_arg:
        if isinstance(last_arg, str):
            func_args[-1] = last_arg.strip('{}').split(',')
    else:
        func_args[-1] = []

    placeholders = ['%s'] * len(func_args)
    placeholders[-1] += f'::{enum_type}[]'

    is_multiple = isinstance(sql_functions, dict)
    data = {} if is_multiple else []

    sql_function_map = {sql_functions: sql_functions} if not is_multiple else sql_functions

    with connection.cursor() as cursor:
        for key, func_name in sql_function_map.items():
            full_query = f'SELECT {func_name}({", ".join(placeholders)})'

            # Debug аргументы (не используется, но может пригодиться)
            # debug_args = [...]
            cursor.execute(full_query, func_args)
            row = cursor.fetchone()
            result = row[0] if row and row[0] else []

            if not isinstance(result, list) or not result:
                output = {'table_data': [], 'headers': [], 'title': title}
            elif not isinstance(result[0], dict):
                raise TypeError(f'Ожидался список словарей, но data[0] = {result[0]} (тип {type(result[0])})')
            else:
                headers = list(result[0].keys())
                table_data = [[clean_func(item.get(field)) for field in headers] for item in result]
                output = {'table_data': [headers] + table_data, 'headers': headers, 'title': title}

            if is_multiple:
                data[key] = output
            else:
                data = output

    return data
