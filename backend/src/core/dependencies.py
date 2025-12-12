"""
Зависимости (Dependency Injection) для Flask приложения.
Управление созданием и внедрением сервисов в эндпоинты.
"""

import os
import functools
from typing import Callable, Any
from flask import g, current_app, request
import tempfile

from models.schemas import ErrorResponse


# ==================== ОСНОВНЫЕ ЗАВИСИМОСТИ ====================

def get_parser():
    """
    Получение или создание парсера OpenAPI.
    Использует Flask g-объект для хранения в рамках запроса.

    Returns:
        OpenAPIParser: Экземпляр парсера
    """
    if 'openapi_parser' not in g:
        try:
            # Пока используем заглушку, пока Роль 2 не сделает парсер
            from parser.openapi_parser import OpenAPIParser

            parser = OpenAPIParser(
                timeout=current_app.config.get('PARSER_TIMEOUT', 30),
                strict_mode=current_app.config.get('VALIDATOR_STRICT_MODE', True)
            )
            g.openapi_parser = parser
            current_app.logger.debug("✅ Парсер создан и сохранён в g")

        except ImportError:
            # Заглушка на время разработки
            current_app.logger.warning("⚠️  Парсер не найден, используем заглушку")

            class ParserStub:
                """Заглушка парсера для разработки."""

                def parse(self, file_path: str) -> dict:
                    return {
                        "services": [
                            {
                                "path": "/api/users",
                                "method": "GET",
                                "parameters": [],
                                "responses": {"200": {"description": "Success"}}
                            }
                        ],
                        "components": {},
                        "info": {"title": "Stub API", "version": "1.0.0"},
                        "source": "stub"
                    }

                def parse_from_content(self, content: str, content_type: str) -> dict:
                    return self.parse("stub.yaml")

            g.openapi_parser = ParserStub()

    return g.openapi_parser


def get_generator():
    """
    Получение или создание генератора тестов (AgentCore).

    Returns:
        AgentCore: Экземпляр генератора
    """
    if 'test_generator' not in g:
        try:
            from generator.agent_core import AgentCore

            # Конфигурация LLM
            llm_config = {
                "api_key": current_app.config.get('CLOUDRU_API_KEY'),
                "endpoint": current_app.config.get('CLOUDRU_ENDPOINT'),
                "model": current_app.config.get('LLM_MODEL', 'gpt-3.5-turbo'),
                "temperature": current_app.config.get('LLM_TEMPERATURE', 0.7),
                "max_tokens": current_app.config.get('LLM_MAX_TOKENS', 2000)
            }

            generator = AgentCore(
                llm_config=llm_config,
                debug=current_app.config.get('DEBUG', False)
            )
            g.test_generator = generator
            current_app.logger.debug("✅ Генератор создан и сохранён в g")

        except ImportError:
            # Заглушка на время разработки
            current_app.logger.warning("⚠️  Генератор не найден, используем заглушку")

            class GeneratorStub:
                """Заглушка генератора для разработки."""

                def generate(self, spec: dict, test_type: str, options: dict = None) -> str:
                    return f'''# Сгенерированные тесты ({test_type})
# Это заглушка. Реальный генератор будет подключен позже.

import pytest
import allure

@allure.title("Тест для {spec.get('info', {}).get('title', 'API')}")
def test_example():
    """Пример теста из заглушки"""
    assert True

@pytest.mark.parametrize("input_data,expected", [
    ({{"test": "data1"}}, True),
    ({{"test": "data2"}}, True)
])
def test_with_params(input_data, expected):
    """Параметризованный тест"""
    assert expected

# Всеure шаги
def test_with_allure_steps():
    """Тест с Allure шагами"""
    with allure.step("Шаг 1: Подготовка данных"):
        data = {{"id": 1, "name": "test"}}

    with allure.step("Шаг 2: Выполнение проверки"):
        assert data["id"] == 1

    with allure.step("Шаг 3: Завершение теста"):
        print("Тест завершён")'''

            g.test_generator = GeneratorStub()

    return g.test_generator


def get_validator():
    """
    Получение или создание валидатора кода.

    Returns:
        CodeValidator: Экземпляр валидатора
    """
    if 'code_validator' not in g:
        try:
            from validator.code_validator import CodeValidator

            validator = CodeValidator(
                strict_mode=current_app.config.get('VALIDATOR_STRICT_MODE', True)
            )
            g.code_validator = validator
            current_app.logger.debug("✅ Валидатор создан и сохранён в g")

        except ImportError:
            # Заглушка на время разработки
            current_app.logger.warning("⚠️  Валидатор не найден, используем заглушку")

            class ValidatorStub:
                """Заглушка валидатора для разработки."""

                def validate(self, code_text: str, check_types: list = None) -> dict:
                    # Простая проверка
                    checks = {
                        "syntax": True,
                        "imports": "import pytest" in code_text or "import allure" in code_text,
                        "structure": "def test_" in code_text,
                        "assertions": "assert " in code_text,
                        "allure": "@allure" in code_text or "import allure" in code_text
                    }

                    errors = []
                    warnings = []

                    if not checks["imports"]:
                        warnings.append("Рекомендуется добавить import pytest/allure")

                    if not checks["structure"]:
                        warnings.append("Не найдены тестовые функции (def test_)")

                    return {
                        "status": "valid" if all(checks.values()) else "warning",
                        "is_valid": all(checks.values()),
                        "checks": checks,
                        "errors": errors,
                        "warnings": warnings,
                        "suggestions": ["Используйте type hints", "Добавьте docstrings"],
                        "statistics": {
                            "lines_count": len(code_text.split('\n')),
                            "functions_count": code_text.count('def '),
                            "imports_count": code_text.count('import ')
                        }
                    }

            g.code_validator = ValidatorStub()

    return g.code_validator


# ==================== ДЕКОРАТОРЫ ДЛЯ ВНЕДРЕНИЯ ====================

def inject_parser(func: Callable) -> Callable:
    """
    Декоратор для автоматического внедрения парсера в функцию.

    Использование:
    @app.route('/parse')
    @inject_parser
    def parse_endpoint(parser):
        # parser уже доступен!
        result = parser.parse(...)
        return result
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        parser = get_parser()
        return func(parser, *args, **kwargs)

    return wrapper


def inject_generator(func: Callable) -> Callable:
    """
    Декоратор для автоматического внедрения генератора.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        generator = get_generator()
        return func(generator, *args, **kwargs)

    return wrapper


def inject_validator(func: Callable) -> Callable:
    """
    Декоратор для автоматического внедрения валидатора.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        validator = get_validator()
        return func(validator, *args, **kwargs)

    return wrapper


def inject_all(func: Callable) -> Callable:
    """
    Декоратор для внедрения ВСЕХ зависимостей.

    Использование:
    @app.route('/full-process')
    @inject_all
    def full_process(parser, generator, validator):
        # Все зависимости доступны!
        spec = parser.parse(...)
        code = generator.generate(spec, ...)
        report = validator.validate(code)
        return report
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        parser = get_parser()
        generator = get_generator()
        validator = get_validator()
        return func(parser, generator, validator, *args, **kwargs)

    return wrapper


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def get_upload_path(filename: str = None) -> str:
    """
    Получение пути для сохранения загруженного файла.

    Args:
        filename: Имя файла (если None, генерируется временное имя)

    Returns:
        str: Полный путь к файлу
    """
    upload_dir = current_app.config.get('UPLOAD_FOLDER', './uploads')
    os.makedirs(upload_dir, exist_ok=True)

    if filename:
        # Безопасное имя файла
        safe_name = "".join(c for c in filename if c.isalnum() or c in '._- ').strip()
        return os.path.join(upload_dir, safe_name)
    else:
        # Временный файл
        return tempfile.mktemp(dir=upload_dir, suffix='.yaml')


def save_uploaded_file(file_content: bytes, filename: str = None) -> str:
    """
    Сохранение загруженного файла на диск.

    Args:
        file_content: Бинарное содержимое файла
        filename: Имя файла (опционально)

    Returns:
        str: Путь к сохраненному файлу
    """
    file_path = get_upload_path(filename)

    with open(file_path, 'wb') as f:
        f.write(file_content)

    current_app.logger.info(f"Файл сохранён: {file_path} ({len(file_content)} bytes)")
    return file_path


def cleanup_uploaded_file(file_path: str):
    """
    Удаление временного файла.

    Args:
        file_path: Путь к файлу для удаления
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            current_app.logger.debug(f"Файл удалён: {file_path}")
    except Exception as e:
        current_app.logger.warning(f"Не удалось удалить файл {file_path}: {e}")


def handle_api_error(error: Exception, status_code: int = 500) -> tuple:
    """
    Обработка ошибок API и создание стандартизированного ответа.

    Args:
        error: Исключение
        status_code: HTTP статус код

    Returns:
        tuple: (response_dict, status_code)
    """
    current_app.logger.error(f"API ошибка: {error}", exc_info=True)

    error_response = ErrorResponse(
        error=error.__class__.__name__,
        message=str(error),
        status_code=status_code
    )

    return error_response.dict(), status_code


# ==================== ОЧИСТКА ЗАВИСИМОСТЕЙ ====================

def teardown_dependencies(exception=None):
    """
    Очистка зависимостей после завершения запроса.
    Автоматически вызывается Flask в конце каждого запроса.
    """
    # Очищаем g-объект
    dependencies = ['openapi_parser', 'test_generator', 'code_validator']

    for dep_name in dependencies:
        dependency = g.pop(dep_name, None)

        # Если у зависимости есть метод cleanup/close, вызываем его
        if dependency and hasattr(dependency, 'cleanup'):
            try:
                dependency.cleanup()
                current_app.logger.debug(f"Очищен {dep_name}")
            except Exception as e:
                current_app.logger.warning(f"Ошибка при очистке {dep_name}: {e}")