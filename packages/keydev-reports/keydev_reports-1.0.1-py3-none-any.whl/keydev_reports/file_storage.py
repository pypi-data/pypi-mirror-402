"""
Кастомные storage классы для Django FileField.

Обеспечивает поддержку загрузки шаблонов отчётов из S3 или локального хранилища.
"""

from django.conf import settings
from django.core.files.storage import FileSystemStorage


def get_report_template_storage():
    """
    Возвращает storage класс для FileField модели ReportTemplate.

    Выбирает storage на основе настроек KEYDEV_REPORTS_STORAGE:
    - 'local' (по умолчанию): FileSystemStorage
    - 's3': S3Boto3Storage (требует django-storages)

    :return: Экземпляр storage класса
    """
    storage_config = getattr(settings, 'KEYDEV_REPORTS_STORAGE', {})
    backend = storage_config.get('STORAGE_BACKEND', 'local')

    if backend == 's3':
        try:
            from storages.backends.s3boto3 import S3Boto3Storage
        except ImportError:
            raise ImportError(
                'django-storages[s3] is required for S3 template storage. '
                'Install it with: pip install keydev-reports[s3] django-storages[s3]'
            ) from None

        # Настройки для S3 хранилища шаблонов
        class ReportTemplateS3Storage(S3Boto3Storage):
            """S3 storage для шаблонов отчётов."""

            def __init__(self, **kwargs):
                # Используем настройки из KEYDEV_REPORTS_STORAGE
                storage_config = getattr(settings, 'KEYDEV_REPORTS_STORAGE', {})

                kwargs['bucket_name'] = storage_config.get('S3_BUCKET')
                kwargs['region_name'] = storage_config.get('S3_REGION', 'us-east-1')
                # ВАЖНО: location должен быть пустым, так как file.name в БД уже содержит полный путь
                # Префикс 'keydev_reports/report_templates/' уже включён в file.name из БД
                kwargs['location'] = ''

                # AWS credentials (опционально, если используются IAM роли)
                aws_access_key = storage_config.get('AWS_ACCESS_KEY_ID')
                aws_secret_key = storage_config.get('AWS_SECRET_ACCESS_KEY')

                if aws_access_key:
                    kwargs['access_key'] = aws_access_key
                if aws_secret_key:
                    kwargs['secret_key'] = aws_secret_key

                # Настройки безопасности
                kwargs['default_acl'] = 'private'
                kwargs['file_overwrite'] = False
                kwargs['querystring_auth'] = True  # Использовать presigned URLs

                super().__init__(**kwargs)

        return ReportTemplateS3Storage()

    else:
        # Локальное хранилище (по умолчанию)
        return FileSystemStorage()


# Singleton instance для использования в models.py
report_template_storage = get_report_template_storage()
