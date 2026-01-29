from django.db import connection


def execute_sql_query(cursor: connection.cursor, func_name: str, func_args: list, fields: str = '*') -> list:
    """
    Выполнение SQL-запроса с использованием заданных параметров.

    :param cursor: Курсор базы данных
    :param func_name: Имя SQL-функции
    :param func_args: Аргументы SQL-запроса
    :param fields: Выбранные поля для запроса

    :return: Результаты SQL-запроса
    """
    selected_fields = ','.join(fields) if fields != '*' else fields
    order = ','.join(['%s' for _ in func_args])

    cursor.execute(f'SELECT {selected_fields} FROM {func_name}({order})', func_args)
    result = cursor.fetchall()

    return result


def get_sql_column_data(func_args: list, sql_functions: tuple, fields: str = '*'):
    """
    Метод для запуска SQL-запроса и получения данных из таблицы по колонкам.
    :param func_args: аргументы sql функции.
    :return: dict
    """
    data = {}
    with connection.cursor() as cursor:
        for func_name in sql_functions:
            results = execute_sql_query(cursor, func_name, func_args, fields)
            column_names = [column[0] for column in cursor.description]

            for i, column in enumerate(column_names):
                if column not in data:
                    data[column] = ''
                    # Concatenate data for the column into a string
                data[column] += ', '.join(str(row[i]) for row in results)
    return data
