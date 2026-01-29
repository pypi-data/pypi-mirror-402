import datetime
from typing import Iterable, Optional

import xlsxwriter
from xlsxwriter.worksheet import Worksheet
from xlsxwriter.utility import xl_rowcol_to_cell

from .base_editor import BaseEditor


class ExcelCreator(BaseEditor):
    """
    Класс для создания Excel отчетов.
    Инструмент позволяет создавать и заполнять файл данными.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        """
        Конструктор класса. Создает объект для создания Excel-отчета.

        :param filename: Имя файла для сохранения отчета (по умолчанию - в памяти).
        """
        self.row_width = 20  # Ширина строк по умолчанию
        self.book = xlsxwriter.Workbook(self.file_name if self.file_name else self.output)
        self.date_format = self.book.add_format({'num_format': 'yyyy-mm-dd'})
        self.formats = {
            'date': {'num_format': 'yyyy-mm-dd'},
            'table': {
                'header': {'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1},
                'body': {'align': 'center', 'valign': 'vcenter', 'border': 1},
            },
            'colors': {'odd': '#FFFFFF', 'even': '#EEEEEE'},
        }

    def add_data(
        self,
        sheet: Worksheet,
        data: Iterable[Iterable],
        start_row: int = 0,
        start_col: int = 0,
        table_format: Optional[dict] = None,
    ) -> None:
        """
        Метод для добавления данных на лист отчета.

        :param sheet: Экземпляр листа.
        :type sheet: Worksheet
        :param data: Данные для добавления в виде двумерного итерируемого объекта.
        :type data: Iterable[Iterable]
        :param start_row: Начальная строка для добавления данных (по умолчанию - 0).
        :type start_row: int, optional
        :param start_col: Начальная колонка для добавления данных (по умолчанию - 0).
        :type start_col: int, optional
        :param table_format: Опциональный параметр, словарь с форматированием таблицы (по умолчанию - None).
        :type table_format: Optional[dict], optional
        """

        # Создаем форматы для четных и нечетных строк
        row_color_1 = self.book.add_format({'bg_color': self.formats['colors']['odd']})
        row_color_2 = self.book.add_format({'bg_color': self.formats['colors']['even']})

        # Инициализируем переменные с форматами по умолчанию
        cell_format_1 = row_color_1
        cell_format_2 = row_color_2

        # Если передан пользовательский формат, создаем форматы ячеек на его основе
        date_odd_format = None
        date_even_format = None
        if table_format:
            new_format_1 = {**table_format, **{'bg_color': self.formats['colors']['odd']}}
            new_format_2 = {**table_format, **{'bg_color': self.formats['colors']['even']}}
            date_format_1 = {**table_format, **self.formats['date'], **{'bg_color': self.formats['colors']['odd']}}
            date_format_2 = {**table_format, **self.formats['date'], **{'bg_color': self.formats['colors']['even']}}
            cell_format_1 = self.book.add_format(new_format_1)
            cell_format_2 = self.book.add_format(new_format_2)
            date_odd_format = self.book.add_format(date_format_1)
            date_even_format = self.book.add_format(date_format_2)

        # Итерируемся по данным и добавляем их на лист с соответствующими форматами
        for row_index, row_data in enumerate(data):
            # Определяем, четная ли текущая строка
            is_even = row_index % 2 == 0

            # Выбираем соответствующий цвет строки и формат ячейки
            row_color = row_color_1 if is_even else row_color_2
            cell_format = cell_format_1 if is_even else cell_format_2
            date_format = date_odd_format if is_even else date_even_format if table_format else None
            # Устанавливаем цвет строки
            sheet.set_row(start_row + row_index, 25, cell_format=row_color)

            # Заполняем ячейки данными с применением выбранного формата
            for col_num, cell_data in enumerate(row_data):
                if isinstance(cell_data, datetime.date):
                    sheet.write_datetime(start_row + row_index, start_col + col_num, cell_data, date_format)
                else:
                    sheet.write(start_row + row_index, start_col + col_num, cell_data, cell_format)

    def populate_with_add_table(
        self,
        sheet: Worksheet,
        data: Iterable[Iterable],
        options: Optional[dict] = None,
        start_row: int = 0,
        start_col: int = 0,
    ):
        """
        Метод для добавления таблицы на лист отчета.
        :param sheet: Экземпляр листа.
        :param data: Данные для добавления в виде двумерного итерируемого объекта.
        :param options: Опциональный параметр, словарь с настройками таблицы.
        :param start_row: Начальная строка для добавления данных (по умолчанию - 0).
        :param start_col: Начальная колонка для добавления данных (по умолчанию - 0).
        :return: NoReturn
        """
        header_row = data[0]
        data_row = data[1]  # Берем строку после заголовка - чтобы определить формат для столбцов
        num_rows = len(data)
        num_cols = len(header_row)

        # Define cell formats for date columns
        date_format = self.book.add_format({'num_format': 'yyyy-mm-dd'})

        # Create a table range
        table_start_cell = xl_rowcol_to_cell(start_row, start_col)
        table_end_cell = xl_rowcol_to_cell(start_row + num_rows - 1, start_col + num_cols - 1)
        table_range = '{}:{}'.format(table_start_cell, table_end_cell)
        columns = [{'header': header} for header in header_row]
        default_options = {'data': data[1:], 'columns': columns, 'style': 'Table Style Light 1', 'autofilter': False}
        options = options if options else default_options
        # Create the table
        sheet.add_table(table_range, options)

        # Apply date format to date columns
        for col_index, header in enumerate(data_row):
            if isinstance(header, datetime.date):
                col_letter = chr(ord('A') + start_col + col_index)
                date_col_range = '{}{}:{}{}'.format(col_letter, start_row + 1, col_letter, start_row + num_rows)
                sheet.set_column(date_col_range, None, date_format)

    @staticmethod
    def merge_columns(
        sheet: Worksheet, data: Iterable[Iterable], format, start_row: int = 0, start_col: int = 0
    ) -> None:
        """
        Объединяет ячейки для повторяющихся колонок.
        Эта функция объединяет ячейки в каждой строке таблицы для повторяющихся колонок,
        сохраняя структуру заголовков в списке data.

        :param sheet: Экземпляр листа.
        :param data: Данные для добавления в виде двумерного итерируемого объекта.
        :param format: Формат ячеек.
        :param start_col: Начальная колонка для начала объединения (по умолчанию 0).
        :return: NoReturn
        """
        # Объединение ячеек для повторяющихся заголовков
        for row, row_data in enumerate(data):
            row += start_row
            merge_start_col = start_col
            prev_header = row_data[start_col]
            # Перебор ячеек в строке, начиная со следующей после start_col
            for col, header in enumerate(row_data[start_col + 1 :], start=start_col + 1):
                # Проверка наличия повторяющегося заголовка
                if header != prev_header:
                    # Если предыдущий заголовок отличается от текущего,
                    # то объединяем ячейки с предыдущего до текущего заголовка
                    if merge_start_col != col - 1:
                        sheet.merge_range(row, merge_start_col, row, col - 1, prev_header, format)
                    else:
                        sheet.write(row, col - 1, prev_header, format)
                    # Обновляем начальную колонку для следующего блока объединения
                    merge_start_col = col
                    # Обновляем предыдущий заголовок
                    prev_header = header
            # Объединяем ячейки, если последний блок не был объединен
            last_col = len(row_data) - 1
            if merge_start_col != last_col:
                sheet.merge_range(row, merge_start_col, row, last_col, prev_header, format)
            else:
                sheet.write(row, last_col, prev_header, format)

    def save_excel(self) -> None:
        """
        Метод для сохранения книги.
        :return: NoReturn
        """
        if self.file_name:
            self.book.close()
        else:
            # Сохраняем отчет в памяти и сбрасываем позицию объекта BytesIO
            self.book.close()
            self.output.seek(0)

    def get_bytes_io(self) -> bytes:
        """
        Метод для получения содержимого Excel-файла в виде объекта BytesIO.

        :return: bytes с содержимым Excel-файла.
        """
        return self.output.read()
