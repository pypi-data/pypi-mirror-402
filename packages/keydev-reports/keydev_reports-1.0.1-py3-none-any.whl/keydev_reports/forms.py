from datetime import date
from typing import NoReturn

from django.forms import Form
from django.db.models import QuerySet


class BaseSqlForm(Form):
    """
    Базовая форма для отчетов.
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # Переопределение метода __init__ для каждого подкласса
        def new_init(self, *args, form_fields: tuple | str = None, **new_kwargs) -> NoReturn:
            super(cls, self).__init__(*args, **new_kwargs)

            # Удаление ненужных полей из self.fields
            if form_fields:
                if form_fields == '__all__':
                    pass
                else:
                    all_fields = set(self.fields.keys())
                    for field_name in all_fields - set(form_fields):
                        self.fields.pop(field_name, None)

        # Установка модифицированного метода __init__ в подклассе
        cls.__init__ = new_init  # type: ignore[method-assign]

    def get_sql_func_args(self) -> list:
        """
        Метод для получения аргументов для SQL-функции на основе данных формы.

        Возвращает список аргументов, подготовленных на основе данных, введенных в форму.

        :return: Список аргументов для SQL-функции.
        """
        form_data_str = [
            value.strftime('%Y-%m-%d') if isinstance(value, date) else value for value in self.cleaned_data.values()
        ]

        func_args = [
            v.first().pk if isinstance(v, QuerySet) else (v.pk if hasattr(v, 'pk') else v) for v in form_data_str
        ]
        return func_args
