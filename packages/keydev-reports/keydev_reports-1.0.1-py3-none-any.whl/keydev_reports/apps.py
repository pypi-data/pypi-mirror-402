from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class ReportsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'keydev_reports'

    def ready(self):
        """
        Валидация конфигурации при запуске приложения.
        """
        self._validate_storage_config()

    def _validate_storage_config(self):
        """
        Проверяет корректность настроек хранилища.
        """
        storage_config = getattr(settings, 'KEYDEV_REPORTS_STORAGE', {})
        backend = storage_config.get('STORAGE_BACKEND', 'local')

        if backend == 's3':
            # Проверяем наличие обязательных настроек для S3
            required_settings = ['S3_BUCKET']
            missing_settings = []

            for setting in required_settings:
                if not storage_config.get(setting):
                    missing_settings.append(setting)

            if missing_settings:
                raise ImproperlyConfigured(
                    f'S3 storage backend requires the following settings in KEYDEV_REPORTS_STORAGE: '
                    f'{", ".join(missing_settings)}. '
                    f'Example configuration:\n'
                    f'KEYDEV_REPORTS_STORAGE = {{\n'
                    f"    'STORAGE_BACKEND': 's3',\n"
                    f"    'S3_BUCKET': 'your-bucket-name',\n"
                    f"    'S3_REGION': 'us-east-1',  # Optional, default: us-east-1\n"
                    f"    'S3_PREFIX': 'keydev_reports/requested_reports/',  # Optional\n"
                    f"    'S3_TEMPLATE_PREFIX': 'keydev_reports/report_templates',  # Optional\n"
                    f"    'S3_PRESIGNED_URL_EXPIRATION': 3600,  # Optional, default: 3600 seconds (1 hour)\n"
                    f"    'AWS_ACCESS_KEY_ID': 'your-access-key',  # Optional if using IAM roles\n"
                    f"    'AWS_SECRET_ACCESS_KEY': 'your-secret-key',  # Optional if using IAM roles\n"
                    f'}}\n'
                    f'Note: Install S3 dependencies with: pip install keydev-reports[s3]'
                )

            # Проверяем установлен ли boto3
            try:
                import boto3  # noqa: F401
            except ImportError:
                raise ImproperlyConfigured(
                    'S3 storage backend requires boto3. Install it with: pip install keydev-reports[s3]'
                ) from None

            # Проверяем установлен ли django-storages (для FileField storage)
            try:
                import storages  # noqa: F401
            except ImportError:
                raise ImproperlyConfigured(
                    'S3 template storage requires django-storages. Install it with: pip install keydev-reports[s3]'
                ) from None

        elif backend not in ['local', 's3']:
            raise ImproperlyConfigured(f"Unknown storage backend: '{backend}'. Supported backends: 'local', 's3'")
