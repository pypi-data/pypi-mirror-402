=================
keydev-reports
=================

.. image:: https://img.shields.io/pypi/v/keydev-reports.svg
   :target: https://pypi.org/project/keydev-reports/
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/keydev-reports.svg
   :target: https://pypi.org/project/keydev-reports/
   :alt: Python versions

.. image:: https://img.shields.io/badge/django-4.1%2B-green.svg
   :target: https://www.djangoproject.com/
   :alt: Django versions

Django-библиотека для создания и экспорта отчётов в Excel, Word и PDF форматах с поддержкой шаблонов и гибкой настройкой хранилища (локальное или S3).

Основные возможности
---------------------

* 📊 **Генерация отчётов** - создание Excel, Word и PDF документов
* 📝 **Работа с шаблонами** - подстановка данных в готовые шаблоны
* 🎨 **Гибкое форматирование** - цвета, стили, объединение ячеек
* 💾 **Два режима хранения** - локальное хранилище или Amazon S3
* ⚡ **Асинхронная генерация** - интеграция с Celery
* 🔄 **Обратная совместимость** - полная поддержка существующего кода

Установка
---------

Базовая установка
~~~~~~~~~~~~~~~~~

.. code-block:: bash

    pip install keydev-reports

Установка с поддержкой S3
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    pip install keydev-reports[s3]

Быстрый старт
-------------

1. Добавьте ``keydev_reports`` в ``INSTALLED_APPS``:

.. code-block:: python

    INSTALLED_APPS = [
        ...
        'keydev_reports',
    ]

2. Примените миграции:

.. code-block:: bash

    python manage.py migrate

3. Создайте шаблон отчёта в админке Django (``/admin/keydev_reports/reporttemplate/``)

Настройка хранилища
--------------------

Локальное хранилище (по умолчанию)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Без дополнительных настроек файлы сохраняются в ``MEDIA_ROOT/keydev_reports/requested_reports/``:

.. code-block:: python

    # settings.py
    MEDIA_ROOT = BASE_DIR / 'media'
    MEDIA_URL = '/media/'

Хранилище Amazon S3
~~~~~~~~~~~~~~~~~~~~

**Шаг 1: Установка зависимостей**

.. code-block:: bash

    pip install keydev-reports[s3]

**Шаг 2: Настройка Django**

.. code-block:: python

    # settings.py

    KEYDEV_REPORTS_STORAGE = {
        # Обязательные параметры
        'STORAGE_BACKEND': 's3',
        'S3_BUCKET': 'my-reports-bucket',

        # Опциональные параметры (значения по умолчанию)
        'S3_REGION': 'us-east-1',
        'S3_PREFIX': 'keydev_reports/requested_reports/',
        'S3_TEMPLATE_PREFIX': 'keydev_reports/report_templates',
        'S3_PRESIGNED_URL_EXPIRATION': 3600,  # 1 час

        # AWS credentials (не нужны при использовании IAM ролей)
        'AWS_ACCESS_KEY_ID': 'AKIA...',
        'AWS_SECRET_ACCESS_KEY': 'secret...',
    }

**Шаг 3: Настройка IAM политики**

Минимальные права доступа для S3:

.. code-block:: json

    {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::my-reports-bucket/*",
                "arn:aws:s3:::my-reports-bucket"
            ]
        }]
    }

**Шаг 4: Автоудаление старых файлов (рекомендуется)**

Настройте S3 Lifecycle Policy для автоматической очистки:

.. code-block:: json

    {
        "Rules": [{
            "Id": "DeleteOldReports",
            "Status": "Enabled",
            "Prefix": "keydev_reports/requested_reports/",
            "Expiration": {"Days": 7}
        }]
    }

Примеры использования
---------------------

Создание Excel отчёта
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from keydev_reports.report_tools import ExcelCreator

    # Создание отчёта
    report = ExcelCreator()
    sheet = report.book.add_worksheet('Sales Report')

    # Добавление данных
    data = [
        ['Product', 'Sales', 'Revenue'],
        ['Product A', 100, 15000],
        ['Product B', 150, 22500],
    ]
    report.populate_with_add_table(sheet, data, start_row=0)

    # Сохранение
    report.save_excel()
    content = report.get_bytes_io()

Работа с шаблонами Word
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from keydev_reports.report_tools import WordEditor

    # Загрузка шаблона
    editor = WordEditor('template.docx')

    # Замена переменных
    editor.docx_replace(
        company_name='ACME Corp',
        report_date='2026-01-15',
        total_sales='$45,000'
    )

    # Добавление таблицы
    table_data = [
        ['Item', 'Quantity', 'Price'],
        ['Product A', '10', '$150'],
        ['Product B', '5', '$200'],
    ]
    editor.add_table(table_data)

    # Сохранение
    editor.save('report.docx')

Использование провайдеров
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from keydev_reports.exporter import ReportExporter

    # Создание экспортёра
    exporter = ReportExporter(
        report_data={'table_data': data, 'title': 'Monthly Report'},
        user_name='john_doe',
        report_name='sales_report',
        extension='xlsx',
        provider_name='AddTableProvider'
    )

    # Генерация отчёта (путь к файлу или S3 URL)
    report_url = exporter.get_report()

Настройка Celery для асинхронной генерации
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # tasks.py
    from keydev_reports.tasks import get_no_template_report

    # Запуск асинхронной задачи
    task = get_no_template_report.delay(
        report_data=data,
        user_name='john_doe',
        report_name='sales_report',
        extension='xlsx',
        provider_name='AddTableProvider'
    )

    # Получение результата
    result = task.get()  # Путь к файлу или S3 URL

Параметры конфигурации
----------------------

KEYDEV_REPORTS_STORAGE
~~~~~~~~~~~~~~~~~~~~~~~

Все параметры конфигурации хранилища:

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Параметр
     - Тип
     - Описание
   * - ``STORAGE_BACKEND``
     - str
     - ``'local'`` или ``'s3'`` (по умолчанию: ``'local'``)
   * - ``S3_BUCKET``
     - str
     - Имя S3 бакета (обязательно для S3)
   * - ``S3_REGION``
     - str
     - AWS регион (по умолчанию: ``'us-east-1'``)
   * - ``S3_PREFIX``
     - str
     - Префикс пути для отчётов (по умолчанию: ``'keydev_reports/requested_reports/'``)
   * - ``S3_TEMPLATE_PREFIX``
     - str
     - Префикс пути для шаблонов (по умолчанию: ``'keydev_reports/report_templates'``)
   * - ``S3_PRESIGNED_URL_EXPIRATION``
     - int
     - Время жизни presigned URL в секундах (по умолчанию: ``3600``)
   * - ``AWS_ACCESS_KEY_ID``
     - str
     - AWS Access Key (опционально при использовании IAM ролей)
   * - ``AWS_SECRET_ACCESS_KEY``
     - str
     - AWS Secret Key (опционально при использовании IAM ролей)

Миграция между хранилищами
---------------------------

При переключении с локального хранилища на S3 (или наоборот):

* ✅ Существующие файлы остаются в старом хранилище
* ✅ Новые файлы создаются в новом хранилище
* ⚠️ Для миграции существующих файлов необходим собственный скрипт

Использование IAM ролей (EC2/ECS)
----------------------------------

При развёртывании на AWS EC2 или ECS можно использовать IAM роли вместо ключей доступа:

.. code-block:: python

    # settings.py
    KEYDEV_REPORTS_STORAGE = {
        'STORAGE_BACKEND': 's3',
        'S3_BUCKET': 'my-reports-bucket',
        # AWS_ACCESS_KEY_ID и AWS_SECRET_ACCESS_KEY не нужны
    }

Прикрепите IAM роль с необходимыми правами к вашему EC2 инстансу или ECS задаче.

Troubleshooting
---------------

**Ошибка: "boto3 is required for S3 storage"**
  Установите зависимости S3: ``pip install keydev-reports[s3]``

**Ошибка: "S3 bucket not found"**
  Проверьте имя бакета в настройках ``KEYDEV_REPORTS_STORAGE['S3_BUCKET']``

**Ошибка: "Access denied to S3 bucket"**
  Проверьте IAM права доступа. Необходимы: ``s3:PutObject``, ``s3:GetObject``, ``s3:DeleteObject``

**Presigned URL истекает слишком быстро**
  Увеличьте ``S3_PRESIGNED_URL_EXPIRATION`` в настройках (значение в секундах)

**Файлы не удаляются автоматически**
  Настройте S3 Lifecycle Policy для автоматического удаления старых файлов

Требования
----------

* Python >= 3.8
* Django >= 4.1.3
* openpyxl >= 3.0.10
* xlsxwriter >= 3.1.9
* python-docx >= 0.8.11
* celery
* boto3 >= 1.26.0 (только для S3)
* django-storages[s3] >= 1.13.0 (только для S3)

Лицензия
--------

BSD-3-Clause

Поддержка
---------

Если у вас возникли проблемы или есть предложения, создайте issue на GitHub.

Changelog
---------

**0.8.0** (2026-01-15)

* ✨ Добавлена поддержка Amazon S3 для хранения отчётов
* ✨ Поддержка загрузки шаблонов из S3
* ✨ Настраиваемое время жизни presigned URLs
* ♻️ Рефакторинг кода: замена NoReturn на None
* 🐛 Улучшена обработка ошибок
* 📚 Расширена документация

**0.7.6**

* 🐛 Исправления и улучшения стабильности
