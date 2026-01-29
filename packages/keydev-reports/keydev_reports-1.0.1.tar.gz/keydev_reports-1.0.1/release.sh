#!/bin/bash

# Скрипт для управления версиями и публикацией пакета на PyPI
# Использование:
#   ./release.sh         - интерактивный режим
#   ./release.sh 0.8.0   - указать версию напрямую

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода цветных сообщений
print_info() {
    echo -e "${BLUE}ℹ ${1}${NC}"
}

print_success() {
    echo -e "${GREEN}✓ ${1}${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ ${1}${NC}"
}

print_error() {
    echo -e "${RED}✗ ${1}${NC}"
}

# Обновление версии в pyproject.toml
update_pyproject_toml() {
    local new_version=$1
    sed -i "s/^version = \".*\"/version = \"${new_version}\"/" pyproject.toml
}

# Обновление changelog в README.rst
update_changelog() {
    local new_version=$1
    local current_date=$(date +%Y-%m-%d)

    print_info "Открываю README.rst для редактирования changelog..."
    print_warning "Добавьте информацию о версии ${new_version} в раздел Changelog"
    read -p "Нажмите Enter когда будете готовы продолжить..."

    ${EDITOR:-nano} README.rst

    print_success "Changelog обновлён"
}

# Сборка пакета
build_package() {
    print_info "Очистка старых сборок..."
    rm -rf dist/ build/ *.egg-info

    print_info "Сборка пакета..."
    if command -v poetry &> /dev/null; then
        poetry build
    else
        python setup.py sdist bdist_wheel
    fi

    print_success "Пакет собран"
}

# Запуск тестов
run_tests() {
    print_info "Запуск тестов..."
    if pytest .; then
        print_success "Все тесты пройдены"
        return 0
    else
        print_error "Тесты не прошли!"
        return 1
    fi
}

# Публикация на Test PyPI
publish_test() {
    print_info "Публикация на Test PyPI..."
    print_warning "Убедитесь, что у вас настроен ~/.pypirc с токеном для test.pypi.org"

    read -p "Продолжить публикацию на Test PyPI? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if command -v poetry &> /dev/null; then
            poetry publish -r testpypi
        else
            python -m twine upload --repository testpypi dist/*
        fi
        print_success "Опубликовано на Test PyPI: https://test.pypi.org/project/keydev-reports/"
    else
        print_warning "Публикация на Test PyPI отменена"
    fi
}

# Публикация на Production PyPI
publish_prod() {
    print_info "Публикация на Production PyPI..."
    print_warning "ЭТО БОЕВОЙ РЕЛИЗ! Убедитесь, что всё протестировано!"

    read -p "Вы уверены, что хотите опубликовать на PyPI? (yes/no): " confirm
    if [[ $confirm == "yes" ]]; then
        if command -v poetry &> /dev/null; then
            poetry publish
        else
            python -m twine upload dist/*
        fi
        print_success "Опубликовано на PyPI: https://pypi.org/project/keydev-reports/"
    else
        print_warning "Публикация на PyPI отменена"
    fi
}

# Создание git тега
create_git_tag() {
    local version=$1

    print_info "Создание git коммита и тега..."

    if git diff --quiet && git diff --cached --quiet; then
        print_warning "Нет изменений для коммита"
    else
        git add pyproject.toml README.rst MANIFEST.in .github/workflows/publish.yml
        git commit -m "Release version ${version}"
        print_success "Изменения закоммичены"
    fi

    if git tag -l "v${version}" | grep -q "v${version}"; then
        print_warning "Тег v${version} уже существует"
    else
        git tag -a "v${version}" -m "Version ${version}"
        print_success "Создан тег v${version}"

        read -p "Отправить изменения в remote репозиторий? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git push && git push --tags
            print_success "Изменения отправлены в remote"
        fi
    fi
}

# Проверка установки необходимых инструментов
check_dependencies() {
    if ! command -v python &> /dev/null; then
        print_error "Python не установлен!"
        exit 1
    fi

    if ! command -v poetry &> /dev/null && ! command -v twine &> /dev/null; then
        print_error "Не установлен ни poetry, ни twine!"
        print_info "Установите: pip install poetry или pip install twine"
        exit 1
    fi
}

# Главное меню
show_menu() {
    echo ""
    echo "=================================="
    echo "  PyPI Release Management"
    echo "=================================="
    echo "1. Полный релиз (версия + сборка + test pypi)"
    echo "2. Только обновить версию"
    echo "3. Только собрать пакет"
    echo "4. Запустить тесты"
    echo "5. Опубликовать на Test PyPI"
    echo "6. Опубликовать на Production PyPI"
    echo "7. Создать git тег"
    echo "0. Выход"
    echo "=================================="
}

# Основная логика
main() {
    check_dependencies

    local current_version=$(get_current_version)
    print_info "Текущая версия: ${current_version}"

    # Если версия передана как аргумент
    if [ $# -eq 1 ]; then
        local new_version=$1

        print_info "Обновление версии до ${new_version}..."
        update_pyproject_toml "$new_version"
        print_success "Версия обновлена в pyproject.toml"

        update_changelog "$new_version"

        if run_tests; then
            build_package
            create_git_tag "$new_version"
            publish_test
        else
            print_error "Релиз прерван из-за ошибок в тестах"
            exit 1
        fi

        return
    fi

    # Интерактивный режим
    while true; do
        show_menu
        read -p "Выберите действие: " choice

        case $choice in
            1)
                read -p "Введите новую версию (текущая: ${current_version}): " new_version
                if [ -z "$new_version" ]; then
                    print_error "Версия не может быть пустой"
                    continue
                fi

                update_setup_cfg "$new_version"
                update_pyproject_toml "$new_version"
                print_success "Версия обновлена"

                update_changelog "$new_version"

                if run_tests; then
                    build_package
                    create_git_tag "$new_version"
                    publish_test

                    read -p "Опубликовать на Production PyPI? (y/n): " -n 1 -r
                    echo
                    if [[ $REPLY =~ ^[Yy]$ ]]; then
                        publish_prod
                    fi
                fi
                ;;
            2)
                read -p "Введите новую версию (текущая: ${current_version}): " new_version
                if [ -z "$new_version" ]; then
                    print_error "Версия не может быть пустой"
                    continue
                fi
                update_setup_cfg "$new_version"
                update_pyproject_toml "$new_version"
                print_success "Версия обновлена до ${new_version}"
                ;;
            3)
                build_package
                ;;
            4)
                run_tests
                ;;
            5)
                build_package
                publish_test
                ;;
            6)
                build_package
                publish_prod
                ;;
            7)
                read -p "Введите версию для тега: " tag_version
                create_git_tag "$tag_version"
                ;;
            0)
                print_info "Выход..."
                exit 0
                ;;
            *)
                print_error "Неверный выбор"
                ;;
        esac
    done
}

# Запуск скрипта
main "$@"
