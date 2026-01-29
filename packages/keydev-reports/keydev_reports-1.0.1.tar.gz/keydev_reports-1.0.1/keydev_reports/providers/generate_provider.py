import io

from ..report_tools import ExcelCreator, WordEditor
from .base_provider import BaseProvider
from .providers_config import provider_registration


@provider_registration()
class ColorfulTableProvider(BaseProvider):
    """
    Класс для генерации excel отчета с цветными ячейками.
    """

    def export(self):
        if self.use_storage_mode:
            # Storage mode: работаем в памяти
            report = ExcelCreator()  # Без file_name
            # Доступные форматы
            header_format = report.book.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1})
            line_format = report.book.add_format({'bold': True, 'valign': 'vcenter'})
            table_format = {'align': 'center', 'valign': 'vcenter', 'border': 1}

            sheet = report.book.add_worksheet()
            # Наименование отчета
            sheet.merge_range(0, 0, 1, len(self.data['table_data'][0]) - 1, self.data['title'], line_format)
            # Устанавливаем ширину столбцов
            for col_num in range(len(self.data['table_data'][0])):
                sheet.set_column(col_num, col_num, 10)
            # Записываем заголовки
            sheet.set_row(2, 30)  # Высота строки 25
            sheet.write_row(2, 0, self.data['table_data'][0], header_format)
            # Записываем данные
            report.add_data(sheet=sheet, data=self.data['table_data'][1:], start_row=3, table_format=table_format)
            sheet.autofit()
            report.save_excel()

            # Сохраняем через storage и возвращаем относительный путь (не URL!)
            file_content = io.BytesIO(report.get_bytes_io())
            s3_key = self.storage.save(file_content, self.file_name)
            return s3_key
        else:
            # Локальный режим (обратная совместимость)
            report = ExcelCreator(file_name=self.file_name)
            header_format = report.book.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1})
            line_format = report.book.add_format({'bold': True, 'valign': 'vcenter'})
            table_format = {'align': 'center', 'valign': 'vcenter', 'border': 1}

            sheet = report.book.add_worksheet()
            sheet.merge_range(0, 0, 1, len(self.data['table_data'][0]) - 1, self.data['title'], line_format)
            for col_num in range(len(self.data['table_data'][0])):
                sheet.set_column(col_num, col_num, 10)
            sheet.set_row(2, 30)
            sheet.write_row(2, 0, self.data['table_data'][0], header_format)
            report.add_data(sheet=sheet, data=self.data['table_data'][1:], start_row=3, table_format=table_format)
            sheet.autofit()
            report.save_excel()
            return report.get_filepath()


@provider_registration()
class AddTableProvider(BaseProvider):
    """Класс для заполнения данных с помощью метода add_table (xlsxwriter)."""

    def export(self):
        if self.use_storage_mode:
            # Storage mode
            report = ExcelCreator()
            sheet = report.book.add_worksheet()
            line_format = report.book.add_format({'bold': True, 'valign': 'vcenter'})
            sheet.merge_range(0, 0, 1, len(self.data['table_data'][0]) - 1, self.data['title'], line_format)
            report.populate_with_add_table(sheet=sheet, data=self.data['table_data'], start_row=3)
            sheet.autofit()
            report.save_excel()

            file_content = io.BytesIO(report.get_bytes_io())
            s3_key = self.storage.save(file_content, self.file_name)
            return s3_key
        else:
            # Локальный режим
            report = ExcelCreator(file_name=self.file_name)
            sheet = report.book.add_worksheet()
            line_format = report.book.add_format({'bold': True, 'valign': 'vcenter'})
            sheet.merge_range(0, 0, 1, len(self.data['table_data'][0]) - 1, self.data['title'], line_format)
            report.populate_with_add_table(sheet=sheet, data=self.data['table_data'], start_row=3)
            sheet.autofit()
            report.save_excel()
            return report.get_filepath()


@provider_registration()
class WordTableProvider(BaseProvider):
    """
    Генератор Word отчетов с таблицами.
    """

    def export(self):
        if self.use_storage_mode:
            # Storage mode
            word_report = WordEditor()
            word_report.add_table(data=self.data, table_style='Table Grid')
            word_report.save()  # Сохраняем в BytesIO

            file_content = io.BytesIO(word_report.get_bytes_io())
            s3_key = self.storage.save(file_content, self.file_name)
            return s3_key
        else:
            # Локальный режим
            word_report = WordEditor()
            word_report.add_table(data=self.data, table_style='Table Grid')
            word_report.save(new_file_name=self.file_name)
            return word_report.get_filepath()
