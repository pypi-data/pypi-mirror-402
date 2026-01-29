from django.db import models

from .file_storage import report_template_storage


class ReportTemplate(models.Model):
    """
    Модель шаблона отчета.
    """

    name: models.CharField = models.CharField(max_length=100, verbose_name='Название отчета')
    related_model: models.CharField = models.CharField(max_length=100, verbose_name='Модель', null=True, blank=True)
    file: models.FileField = models.FileField(
        upload_to='',  # Префикс уже установлен в storage (S3_TEMPLATE_PREFIX или location)
        max_length=255,
        verbose_name='Файл',
        storage=report_template_storage,
    )
    is_active: models.BooleanField = models.BooleanField(default=True, verbose_name='Активен')
    product: models.CharField = models.CharField(max_length=100, verbose_name='Продукт', null=True, blank=True)

    class Meta:
        verbose_name = 'Шаблон отчета'
        verbose_name_plural = 'Шаблоны отчетов'

    def __str__(self):
        return self.name
