"""
Модуль для работы с различными бэкендами хранения файлов.

Поддерживает локальное хранилище (по умолчанию) и Amazon S3.
"""

import io
import os
from abc import ABC, abstractmethod
from typing import Optional
from urllib.parse import urlparse

from django.conf import settings
from django.core.files.storage import FileSystemStorage


class StorageBackend(ABC):
    """Базовый класс для бэкендов хранения файлов."""

    @abstractmethod
    def save(self, file_content: io.BytesIO, relative_path: str) -> str:
        """
        Сохраняет файл и возвращает URL для доступа.

        :param file_content: Содержимое файла в виде BytesIO
        :param relative_path: Относительный путь к файлу (например, 'username/report_2026.xlsx')
        :return: URL для доступа к файлу (локальный путь или presigned URL)
        """
        pass

    @abstractmethod
    def load(self, relative_path: str) -> bytes:
        """
        Загружает файл из хранилища.

        :param relative_path: Относительный путь к файлу
        :return: Содержимое файла в виде байтов
        """
        pass

    @abstractmethod
    def exists(self, relative_path: str) -> bool:
        """
        Проверяет существование файла.

        :param relative_path: Относительный путь к файлу
        :return: True если файл существует
        """
        pass

    @abstractmethod
    def delete(self, relative_path: str) -> None:
        """
        Удаляет файл из хранилища.

        :param relative_path: Относительный путь к файлу
        """
        pass

    @abstractmethod
    def get_full_path(self, relative_path: str) -> str:
        """
        Возвращает полный путь к файлу (для локального хранилища) или ключ (для S3).

        :param relative_path: Относительный путь к файлу
        :return: Полный путь или ключ
        """
        pass

    @abstractmethod
    def get_file_url(self, relative_path: str) -> str:
        """
        Возвращает URL для доступа к файлу.

        :param relative_path: Относительный путь к файлу
        :return: URL (presigned для S3) или локальный путь
        """
        pass


class LocalStorage(StorageBackend):
    """Локальное файловое хранилище."""

    def __init__(self, base_path: Optional[str] = None):
        """
        Инициализация локального хранилища.

        :param base_path: Базовый путь для хранения файлов.
                         По умолчанию: MEDIA_ROOT/keydev_reports/requested_reports/
        """
        if base_path:
            self.base_path = base_path
        else:
            self.base_path = os.path.join(settings.MEDIA_ROOT, 'keydev_reports', 'requested_reports')
        self.storage = FileSystemStorage(location=self.base_path)

    def save(self, file_content: io.BytesIO, relative_path: str) -> str:
        """
        Сохраняет файл локально.

        :param file_content: Содержимое файла
        :param relative_path: Относительный путь (username/report.xlsx)
        :return: Относительный путь к файлу
        """
        full_path = os.path.join(self.base_path, relative_path)
        directory = os.path.dirname(full_path)

        # Создаём директорию если не существует
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        # Записываем файл
        with open(full_path, 'wb') as f:
            file_content.seek(0)
            f.write(file_content.read())

        return relative_path

    def get_file_url(self, relative_path: str) -> str:
        """
        Возвращает полный локальный путь к файлу.

        :param relative_path: Относительный путь к файлу
        :return: Полный локальный путь
        """
        return os.path.join(self.base_path, relative_path)

    def load(self, relative_path: str) -> bytes:
        """
        Загружает файл из локального хранилища.

        :param relative_path: Относительный путь к файлу
        :return: Содержимое файла
        """
        full_path = os.path.join(self.base_path, relative_path)
        with open(full_path, 'rb') as f:
            return f.read()

    def exists(self, relative_path: str) -> bool:
        """Проверяет существование файла."""
        full_path = os.path.join(self.base_path, relative_path)
        return os.path.exists(full_path)

    def delete(self, relative_path: str) -> None:
        """Удаляет локальный файл."""
        full_path = os.path.join(self.base_path, relative_path)
        if os.path.exists(full_path):
            os.remove(full_path)

    def get_full_path(self, relative_path: str) -> str:
        """Возвращает полный путь к файлу."""
        return os.path.join(self.base_path, relative_path)


class S3Storage(StorageBackend):
    """Amazon S3 хранилище для файлов отчётов."""

    def __init__(self):
        """Инициализация S3 клиента."""
        try:
            import boto3
            from botocore.config import Config
            from botocore.exceptions import ClientError
        except ImportError as e:
            raise ImportError(
                'boto3 is required for S3 storage. Install it with: pip install keydev-reports[s3]'
            ) from e

        self.ClientError = ClientError
        self.Config = Config

        # Получаем настройки из Django settings
        storage_config = getattr(settings, 'KEYDEV_REPORTS_STORAGE', {})

        self.bucket_name = storage_config.get('S3_BUCKET')
        self.region_name = storage_config.get('S3_REGION', 'us-east-1')
        self.prefix = storage_config.get('S3_PREFIX', 'keydev_reports/requested_reports/')
        self.presigned_url_expiration = storage_config.get('S3_PRESIGNED_URL_EXPIRATION', 3600)

        # Endpoint URLs (для MinIO или других S3-совместимых хранилищ)
        self.endpoint_url = storage_config.get('S3_ENDPOINT_URL')  # Внутренний URL (docker)
        self.external_endpoint_url = storage_config.get('S3_EXTERNAL_ENDPOINT_URL')  # Внешний URL (браузер)

        # Стиль адресации: 'virtual' или 'path'
        self.addressing_style = self._get_addressing_style(storage_config)

        # AWS credentials
        aws_access_key = storage_config.get('AWS_ACCESS_KEY_ID')
        aws_secret_key = storage_config.get('AWS_SECRET_ACCESS_KEY')

        # Инициализация S3 клиента
        client_kwargs = {'region_name': self.region_name}
        if aws_access_key and aws_secret_key:
            client_kwargs['aws_access_key_id'] = aws_access_key
            client_kwargs['aws_secret_access_key'] = aws_secret_key

        # Добавляем endpoint_url для MinIO или других S3-совместимых хранилищ
        if self.endpoint_url:
            client_kwargs['endpoint_url'] = self.endpoint_url
            # MinIO/DigitalOcean Spaces требуют Signature V4
            client_kwargs['config'] = Config(
                signature_version='s3v4',
                s3={'addressing_style': self.addressing_style},
            )
        else:
            # Для AWS S3 тоже устанавливаем addressing_style
            client_kwargs['config'] = Config(s3={'addressing_style': self.addressing_style})

        self.s3_client = boto3.client('s3', **client_kwargs)

        # Отдельный клиент для presigned URLs с внешним endpoint
        # Нужен потому что подпись включает хост, и замена URL после генерации ломает подпись
        if self.external_endpoint_url and self.external_endpoint_url != self.endpoint_url:
            presigned_kwargs = client_kwargs.copy()
            presigned_kwargs['endpoint_url'] = self.external_endpoint_url
            presigned_kwargs['config'] = Config(
                signature_version='s3v4',
                s3={'addressing_style': self.addressing_style},
            )
            self.presigned_client = boto3.client('s3', **presigned_kwargs)
        else:
            self.presigned_client = self.s3_client

    def _get_addressing_style(self, storage_config: dict) -> str:
        """
        Определяет стиль адресации S3 URLs

        :param storage_config: конфигурация хранилища
        :return: 'virtual' или 'path'
        :raises ValueError: если для custom endpoint не указан addressing_style
        """
        addressing_style = storage_config.get('S3_ADDRESSING_STYLE')

        # Если явно задан - используем его
        if addressing_style:
            if addressing_style not in ('virtual', 'path'):
                raise ValueError(f"S3_ADDRESSING_STYLE must be 'virtual' or 'path', got: {addressing_style}")
            return addressing_style

        # Для AWS S3 (без custom endpoint) по умолчанию virtual
        if not self.endpoint_url:
            return 'virtual'

        # Для custom endpoints требуем явной настройки
        raise ValueError(
            f'S3_ADDRESSING_STYLE must be explicitly set in KEYDEV_REPORTS_STORAGE for custom S3 endpoints.\n'
            f'Current endpoint: {self.endpoint_url}\n'
            f"Set S3_ADDRESSING_STYLE='path' for MinIO or 'virtual' for DigitalOcean Spaces"
        )

    def save(self, file_content: io.BytesIO, relative_path: str) -> str:
        """
        Загружает файл в S3.

        :param file_content: Содержимое файла
        :param relative_path: Относительный путь (username/report.xlsx)
        :return: Полный S3 ключ (с префиксом, например: keydev_reports/requested_reports/username/report.xlsx)
        :raises: Exception при ошибке загрузки
        """
        s3_key = f'{self.prefix}{relative_path}'
        content_type = self._get_content_type(relative_path)

        try:
            file_content.seek(0)
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content.read(),
                ContentType=content_type,
                ContentDisposition=f'attachment; filename="{os.path.basename(relative_path)}"',
            )

            # Возвращаем полный S3 ключ (с префиксом) чтобы файл можно было найти
            return s3_key

        except self.ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))

            if error_code == 'NoSuchBucket':
                raise Exception(
                    f"S3 bucket '{self.bucket_name}' not found. "
                    f'Please create the bucket or check KEYDEV_REPORTS_STORAGE settings.'
                ) from e
            elif error_code == 'AccessDenied':
                raise Exception(
                    f"Access denied to S3 bucket '{self.bucket_name}'. "
                    f'Please check your AWS credentials and IAM permissions.'
                ) from e
            else:
                raise Exception(f'Failed to upload file to S3: [{error_code}] {error_message}') from e

        except Exception as e:
            raise Exception(f'Unexpected error uploading to S3: {str(e)}') from e

    def load(self, relative_path: str) -> bytes:
        """
        Загружает файл из S3.

        :param relative_path: Относительный путь к файлу
        :return: Содержимое файла
        :raises: Exception при ошибке загрузки
        """
        s3_key = f'{self.prefix}{relative_path}'

        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            return response['Body'].read()

        except self.ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == 'NoSuchKey':
                raise FileNotFoundError(f'File not found in S3: {relative_path}') from e
            raise Exception(f'Failed to load file from S3: {str(e)}') from e

    def exists(self, relative_path: str) -> bool:
        """
        Проверяет существование файла в S3.

        :param relative_path: Относительный путь к файлу
        :return: True если файл существует
        """
        s3_key = f'{self.prefix}{relative_path}'

        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except self.ClientError:
            return False

    def delete(self, relative_path: str) -> None:
        """
        Удаляет файл из S3.

        :param relative_path: Относительный путь к файлу
        :raises: Exception при ошибке удаления
        """
        s3_key = f'{self.prefix}{relative_path}'

        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
        except self.ClientError as e:
            raise Exception(f'Failed to delete file from S3: {str(e)}') from e

    def get_presigned_url(self, relative_path: str, expiration: Optional[int] = None) -> str:
        """
        Генерирует presigned URL для скачивания файла.

        :param relative_path: Относительный путь к файлу
        :param expiration: Время жизни URL в секундах (по умолчанию из настроек)
        :return: Presigned URL
        :raises: Exception при ошибке генерации URL
        """
        s3_key = f'{self.prefix}{relative_path}'
        expiration = expiration or self.presigned_url_expiration

        try:
            # Используем presigned_client с внешним endpoint для корректной подписи
            url = self.presigned_client.generate_presigned_url(
                'get_object', Params={'Bucket': self.bucket_name, 'Key': s3_key}, ExpiresIn=expiration
            )

            # Workaround для баги boto3 с некоторыми S3-совместимыми провайдерами:
            # При virtual-hosted style boto3 иногда добавляет bucket и в subdomain (✓) и в path (✗)
            # Результат: https://bucket.region.provider.com/bucket/path - неправильно
            # Ожидаем: https://bucket.region.provider.com/path - правильно
            # Удаляем дублирующийся bucket из path если он там появился
            # Применяем workaround только для virtual-hosted style
            if self.addressing_style == 'virtual':
                duplicate_pattern = f'/{self.bucket_name}/'
                if duplicate_pattern in url:
                    url = url.replace(duplicate_pattern, '/', 1)

            return url
        except self.ClientError as e:
            raise Exception(f'Failed to generate presigned URL: {str(e)}') from e

    def get_file_url(self, relative_path: str) -> str:
        """
        Возвращает presigned URL для доступа к файлу.
        Обёртка над get_presigned_url для единообразия интерфейса.

        :param relative_path: Относительный путь к файлу
        :return: Presigned URL
        """
        return self.get_presigned_url(relative_path)

    def get_full_path(self, relative_path: str) -> str:
        """
        Возвращает S3 ключ (путь в бакете).

        :param relative_path: Относительный путь к файлу
        :return: Полный S3 ключ
        """
        return f'{self.prefix}{relative_path}'

    @staticmethod
    def _get_content_type(file_path: str) -> str:
        """
        Определяет MIME тип файла по расширению.

        :param file_path: Путь к файлу
        :return: MIME тип
        """
        extension = os.path.splitext(file_path)[-1].lower()
        content_types = {
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.pdf': 'application/pdf',
            '.csv': 'text/csv',
        }
        return content_types.get(extension, 'application/octet-stream')


def get_storage_backend() -> StorageBackend:
    """
    Фабричная функция для получения бэкенда хранения.

    Выбирает бэкенд на основе настроек Django:
    - 'local' (по умолчанию): LocalStorage
    - 's3': S3Storage

    :return: Экземпляр StorageBackend
    :raises: ValueError если указан неизвестный бэкенд
    """
    storage_config = getattr(settings, 'KEYDEV_REPORTS_STORAGE', {})
    backend = storage_config.get('STORAGE_BACKEND', 'local')

    if backend == 's3':
        return S3Storage()
    elif backend == 'local':
        return LocalStorage()
    else:
        raise ValueError(f"Unknown storage backend: '{backend}'. Available options: 'local', 's3'")


def is_s3_url(url: str) -> bool:
    """
    Проверяет, является ли URL ссылкой на S3 (presigned URL).

    :param url: URL для проверки
    :return: True если это S3 URL
    """
    if not url:
        return False
    parsed = urlparse(url)
    return parsed.scheme in ('http', 'https') and (
        's3.amazonaws.com' in parsed.netloc or '.s3.' in parsed.netloc or 'amazonaws.com' in parsed.netloc
    )
