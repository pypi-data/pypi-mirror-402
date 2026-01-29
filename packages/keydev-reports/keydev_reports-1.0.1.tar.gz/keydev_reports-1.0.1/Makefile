.PHONY: help test clean build publish-test publish release version

# Цвета для вывода
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

help: ## Показать это сообщение помощи
	@echo "$(BLUE)Доступные команды:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Примеры использования:$(NC)"
	@echo "  make test            # Запустить все тесты"
	@echo "  make build           # Собрать пакет"
	@echo "  make release         # Полный процесс релиза"

test: ## Запустить все тесты
	@echo "$(BLUE)Запуск тестов...$(NC)"
	pytest .

clean: ## Удалить временные файлы и кэш
	@echo "$(BLUE)Очистка временных файлов...$(NC)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

build: clean ## Собрать пакет для публикации
	@echo "$(BLUE)Сборка пакета...$(NC)"
	@if command -v poetry >/dev/null 2>&1; then \
		poetry build; \
	else \
		python -m build; \
	fi
	@echo "$(GREEN)✓ Пакет собран в директории dist/$(NC)"

publish-test: build ## Опубликовать пакет на Test PyPI
	@echo "$(BLUE)Публикация на Test PyPI...$(NC)"
	@if command -v poetry >/dev/null 2>&1; then \
		poetry publish -r testpypi; \
	else \
		twine upload --repository testpypi dist/*; \
	fi
	@echo "$(GREEN)✓ Опубликовано на Test PyPI: https://test.pypi.org/project/keydev-reports/$(NC)"

publish: build ## Опубликовать пакет на Production PyPI
	@echo "$(YELLOW)⚠ ВНИМАНИЕ: Публикация на Production PyPI!$(NC)"
	@read -p "Вы уверены? [yes/N]: " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		if command -v poetry >/dev/null 2>&1; then \
			poetry publish; \
		else \
			twine upload dist/*; \
		fi; \
		echo "$(GREEN)✓ Опубликовано на PyPI: https://pypi.org/project/keydev-reports/$(NC)"; \
	else \
		echo "$(YELLOW)Публикация отменена$(NC)"; \
	fi

release: ## Запустить интерактивный скрипт релиза
	@echo "$(BLUE)Запуск скрипта релиза...$(NC)"
	./release.sh

release-version: ## Создать релиз с указанием версии (make release-version VERSION=0.8.0)
	@if [ -z "$(VERSION)" ]; then \
		echo "$(YELLOW)Использование: make release-version VERSION=0.8.0$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Создание релиза версии $(VERSION)...$(NC)"
	./release.sh $(VERSION)

version: ## Показать текущую версию пакета
	@echo "$(BLUE)Текущая версия:$(NC)"
	@if command -v poetry >/dev/null 2>&1; then \
		poetry version -s; \
	else \
		grep '^version = ' pyproject.toml | cut -d '"' -f 2; \
	fi

bump-patch: ## Увеличить patch версию (0.7.6 -> 0.7.7)
	@echo "$(BLUE)Увеличение patch версии...$(NC)"
	@if command -v poetry >/dev/null 2>&1; then \
		poetry version patch; \
		NEW_VERSION=$$(poetry version -s); \
		echo "$(GREEN)✓ Версия обновлена до $$NEW_VERSION$(NC)"; \
	else \
		echo "$(YELLOW)Poetry не установлен. Используйте: make release-version VERSION=X.Y.Z$(NC)"; \
	fi

bump-minor: ## Увеличить minor версию (0.7.6 -> 0.8.0)
	@echo "$(BLUE)Увеличение minor версии...$(NC)"
	@if command -v poetry >/dev/null 2>&1; then \
		poetry version minor; \
		NEW_VERSION=$$(poetry version -s); \
		echo "$(GREEN)✓ Версия обновлена до $$NEW_VERSION$(NC)"; \
	else \
		echo "$(YELLOW)Poetry не установлен. Используйте: make release-version VERSION=X.Y.Z$(NC)"; \
	fi

bump-major: ## Увеличить major версию (0.7.6 -> 1.0.0)
	@echo "$(BLUE)Увеличение major версии...$(NC)"
	@if command -v poetry >/dev/null 2>&1; then \
		poetry version major; \
		NEW_VERSION=$$(poetry version -s); \
		echo "$(GREEN)✓ Версия обновлена до $$NEW_VERSION$(NC)"; \
	else \
		echo "$(YELLOW)Poetry не установлен. Используйте: make release-version VERSION=X.Y.Z$(NC)"; \
	fi

git-tag: ## Создать git тег для текущей версии
	@if command -v poetry >/dev/null 2>&1; then \
		VERSION=$$(poetry version -s); \
	else \
		VERSION=$$(grep '^version = ' pyproject.toml | cut -d '"' -f 2); \
	fi; \
	echo "$(BLUE)Создание тега v$$VERSION...$(NC)"; \
	git tag -a "v$$VERSION" -m "Version $$VERSION"; \
	echo "$(GREEN)✓ Тег v$$VERSION создан$(NC)"; \
	echo "$(YELLOW)Для отправки в remote: git push origin v$$VERSION$(NC)"
