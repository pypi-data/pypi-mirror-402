class FileNameMixin:
    def get_file_name(self):
        """
        Переопределяем название отчета в зависимости от формы
        :return: Новое название отчета
        """
        if self.is_current_date:
            return None

        form_fields = self.form_fields
        title = self.title
        form_instance = self.form_instance
        if 'date' in form_fields:
            date = form_instance.cleaned_data['date'].strftime('%d_%m_%Y')
            return f'{title}_{date}'
        elif 'date_min' in form_fields and 'date_max' in form_fields:
            date_min = form_instance.cleaned_data['date_min'].strftime('%d_%m_%Y')
            date_max = form_instance.cleaned_data['date_max'].strftime('%d_%m_%Y')
            return f'{title}_{date_min}_{date_max}'
        elif 'year' in form_fields and 'choice' in form_fields:
            year = form_instance.cleaned_data['year']
            quarter = form_instance.cleaned_data['choice']
            quarters = {
                '1': f'01_01_{year}_31_03_{year}',
                '2': f'01_04_{year}_30_06_{year}',
                '3': f'01_07_{year}_30_09_{year}',
                '4': f'01_10_{year}_31_12_{year}',
            }
            return f'{title}_{quarters[quarter]}'
        return title
