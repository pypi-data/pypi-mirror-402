# keydev-reports: AI Coding Agent Guide

## Project Overview
Django-библиотека для создания и экспорта отчётов в Excel, Word и PDF форматах с поддержкой шаблонов и гибкой настройкой хранилища (локальное или S3). Published to PyPI as `keydev-reports`.

## Architecture & Core Concepts

### Provider Pattern (Critical)
The codebase uses a **provider registration pattern** for extensible report generation:

- **Base**: `BaseProvider` (abstract) defines `export()` method
- **Registration**: Use `@provider_registration()` decorator to auto-register providers in `ProviderRegistry`
- **Provider Types**:
  - `ProxyModelProvider` - template-based reports from Django proxy models
  - `TableProvider` - inserts tables into Excel templates (finds `${table}` placeholders)
  - `ColorfulTableProvider` - generates new Excel files with colored tables
  - `WordTableProvider` - inserts tables into Word templates
  - `TemplateProvider` - combines replacements + tables (Excel/Word)

**Example** from [providers/template_provider.py](keydev_reports/providers/template_provider.py):
```python
@provider_registration(kwargs={'data': 'report_data', 'file_name': 'new_file_path', 'table_data': 'table_data'})
class TableProvider(BaseProvider):
    def export(self):
        # implementation
```

### Storage Backend Abstraction
Two modes via `storage.py`:
- **LocalStorage**: Files in `MEDIA_ROOT/keydev_reports/requested_reports/`
- **S3Storage**: Files uploaded to S3 with presigned URLs (requires `pip install keydev-reports[s3]`)

**Key pattern**: All file operations go through `get_storage_backend()` which returns `StorageBackend` interface (`save()`, `load()`, `exists()`, `delete()`). Never write files directly.

### Exporter Classes
Entry point for report generation:
- `BaseExporter` - orchestrates provider selection via `create_provider_instance()`
- `TemplateReportExporter` - uses `ReportTemplate` model + template files
- Both use `storage.save(io.BytesIO(content), relative_path)` for file persistence

## Development Workflow

### Version Management
- **Makefile commands**: `make bump-patch` / `make bump-minor` / `make bump-major`
  - Updates BOTH `pyproject.toml` AND `setup.cfg` (dual version sources)
- **Release process**: `./release.sh` (interactive) or `./release.sh 0.8.0` (direct)
  - Creates git tags, runs tests, builds package, publishes to PyPI

### Testing
- **Runner**: `pytest` (not unittest)
- **Config**: [pyproject.toml](pyproject.toml) defines `testpaths = ["keydev_reports/"]`
- **Django setup**: [tests/conftest.py](keydev_reports/tests/conftest.py) configures in-memory SQLite
- **Fixtures**: Use `pytest.fixture` with `mocker.patch()` for dependencies (see [test_excel_editor.py](keydev_reports/tests/test_report_tools/test_excel_editor.py))
- **Run tests**: `make test` or `pytest .`

### Code Quality
- **Linter**: Ruff (not Flake8 alone) - single quotes enforced via `quote-style = 'single'`
- **Line length**: 120 chars
- **Ignore migrations**: `**/migrations/*.py` excluded from linting
- **Auto-fix**: `ruff check --fix .` (run before commits)

## Project-Specific Patterns

### Django Integration
- **Model**: `ReportTemplate` stores template files using `FileField` with custom storage (`report_template_storage`)
- **Views**: Class-based views inherit from `BaseReportView` → `SqlReportView` → specialized views
  - Use `FileNameMixin` for custom file naming
  - Return `JsonResponse` with `task_id` for async Celery tasks
- **Admin**: Templates managed via `/admin/keydev_reports/reporttemplate/`

### Celery Tasks
All report generation happens via Celery for async processing:
```python
from .tasks import get_template_report
result = get_template_report.delay(report_data, user_name, report_id, provider_name)
# Check result.id, result.status
```

### Template Placeholder Convention
- **Excel/Word templates**: Use `${variable_name}` syntax (e.g., `${company_name}`)
- **Table insertion**: `${table}` placeholder replaced via `ExcelEditor.find_target_cell()`
- **Replacements**: `replace_data` dict passed to `ExcelEditor.replace_data()` or `WordEditor.replace_data()`

## File Structure Essentials

```
keydev_reports/
├── exporter.py          # Entry point classes (BaseExporter, TemplateReportExporter)
├── storage.py           # Storage abstraction (LocalStorage, S3Storage)
├── models.py            # ReportTemplate model
├── tasks.py             # Celery tasks for report generation
├── views.py             # Django CBVs (BaseReportView hierarchy)
├── providers/
│   ├── base_provider.py       # Abstract base
│   ├── providers_config.py    # @provider_registration decorator
│   ├── template_provider.py   # ProxyModelProvider, TableProvider, etc.
│   └── generate_provider.py   # ColorfulTableProvider, AddTableProvider
└── report_tools/
    ├── excel_editor.py   # ExcelEditor (openpyxl wrapper)
    ├── word_editor.py    # WordEditor (python-docx wrapper)
    └── converter.py      # File format conversion (PDF/JPG)
```

## Common Operations

### Adding New Provider
1. Create class inheriting `BaseProvider` in `providers/`
2. Implement `export()` method returning file path/URL
3. Decorate with `@provider_registration(kwargs={'data': 'report_data', 'file_name': 'new_file_path'})`
4. Provider auto-available via `ProviderRegistry.get_provider_config('ClassName')`

### Modifying Excel Reports
Use `ExcelEditor` from `report_tools.excel_editor`:
```python
editor = ExcelEditor(file_name=template_path)
editor.replace_cell_value('${date}', '2026-01-15')  # Text replacement
cell = editor.find_target_cell(sheet, '${table}')   # Find placeholder
editor.populate_sheet_data(sheet, data, cell.row, cell.column)  # Insert table
editor.save()  # Writes to self.output (BytesIO)
```

### Storage Configuration
Check [apps.py](keydev_reports/apps.py) → `ReportsConfig.ready()` validates `KEYDEV_REPORTS_STORAGE` settings:
- S3 mode requires: `STORAGE_BACKEND='s3'`, `S3_BUCKET`, optional `S3_PREFIX`/`AWS_ACCESS_KEY_ID`

## Dependencies & Extras
- **Core**: Django 4.1+, openpyxl, xlsxwriter, python-docx, celery, pydantic
- **Optional S3**: `pip install keydev-reports[s3]` → adds boto3, django-storages
- **Dev**: pytest, pytest-django, pytest-mock, ruff (single quotes!)

## Publishing to PyPI
```bash
make clean build      # Build dist/
make publish-test     # Test on test.pypi.org
make publish          # Production (requires confirmation)
```
Version sync: `setup.cfg` and `pyproject.toml` must match (handled by `make bump-*` or `release.sh`).
