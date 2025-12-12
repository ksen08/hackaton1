"""
Роуты (эндпоинты) API с интеграцией AgentCore.
"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import json
import tempfile
import base64
import asyncio

from core.dependencies import (
    get_parser,
    get_generator,
    get_validator,
    inject_parser,
    inject_generator,
    inject_validator,
    save_uploaded_file,
    cleanup_uploaded_file,
    handle_api_error
)
from models.schemas import (
    GenerationRequest,
    GenerationResponse,
    ValidationRequest,
    ValidationResponse,
    ErrorResponse,
    AgentRequest,      # Новый импорт!
    AgentResponse,     # Новый импорт!
    TestType
)

# Создаём Blueprint для API
api_bp = Blueprint('api', __name__)


# ==================== HEALTH CHECK ====================
@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    Проверка здоровья API и зависимостей.
    GET /api/health
    """
    try:
        # Проверяем доступность зависимостей
        parser = get_parser()
        generator = get_generator()
        validator = get_validator()

        # Определяем статус
        def get_status(obj, class_name):
            if obj is None:
                return 'missing'
            elif hasattr(obj, '__class__') and 'Stub' in obj.__class__.__name__:
                return 'stub'
            else:
                return 'implemented'

        dependencies_status = {
            'parser': get_status(parser, 'Parser'),
            'generator': get_status(generator, 'Generator'),
            'validator': get_status(validator, 'Validator'),
            'upload_folder': 'exists' if os.path.exists(current_app.config['UPLOAD_FOLDER']) else 'missing',
            'llm_available': hasattr(generator, 'llm_client') and generator.llm_client
        }

        return {
            'status': 'healthy',
            'service': 'Test Generation API',
            'version': '1.0.0',
            'environment': current_app.config.get('FLASK_ENV', 'unknown'),
            'dependencies': dependencies_status,
            'endpoints': {
                'upload': '/api/upload',
                'generate': '/api/generate',
                'generate_agent': '/api/generate/agent',  # Новый эндпоинт!
                'validate': '/api/validate',
                'health': '/api/health'
            }
        }, 200

    except Exception as e:
        return handle_api_error(e, 500)


# ==================== GENERATE TESTS (старый эндпоинт) ====================
@api_bp.route('/generate', methods=['POST'])
@inject_generator
def generate_tests(generator):
    """
    Генерация тестов по OpenAPI спецификации (старый интерфейс).
    POST /api/generate

    Пример тела запроса:
    {
        "spec": {...},           # Распарсенная OpenAPI спецификация
        "test_type": "auto_api", # manual_ui, manual_api, auto_api, auto_ui
        "options": {...}         # Опционально
    }
    """
    try:
        # Валидируем входные данные через Pydantic
        data = request.get_json()

        if not data:
            error = ErrorResponse(
                error='ValidationError',
                message='Требуется JSON тело запроса',
                status_code=400
            )
            return error.dict(), 400

        # Создаём Pydantic модель
        try:
            gen_request = GenerationRequest(**data)
        except Exception as e:
            error = ErrorResponse(
                error='ValidationError',
                message=f'Ошибка валидации входных данных: {str(e)}',
                status_code=400
            )
            return error.dict(), 400

        # Генерируем тесты (через старый интерфейс)
        try:
            code_text = generator.generate(
                spec=gen_request.spec,
                test_type=gen_request.test_type.value,
                options=gen_request.options
            )

            # Создаём ответ
            response = GenerationResponse(
                status='success',
                code_text=code_text,
                metadata={
                    'test_type': gen_request.test_type.value,
                    'lines_count': len(code_text.split('\n')),
                    'generated_at': '2024-01-15T12:00:00Z',
                    'language': 'python',
                    'framework': 'pytest + allure',
                    'spec_title': gen_request.spec.get('info', {}).get('title', 'Unknown API')
                }
            )

            return response.dict(), 200

        except Exception as e:
            current_app.logger.error(f'Ошибка генерации: {e}')
            error = ErrorResponse(
                error='GenerationError',
                message=f'Ошибка при генерации тестов: {str(e)}',
                status_code=500
            )
            return error.dict(), 500

    except Exception as e:
        return handle_api_error(e, 500)


# ==================== GENERATE TESTS (новый AgentCore эндпоинт) ====================
@api_bp.route('/generate/agent', methods=['POST'])
@inject_generator
def generate_tests_agent(generator):
    """
    Генерация тестов через AgentCore (новый интерфейс).
    POST /api/generate/agent

    Пример тела запроса:
    {
        "type": "api",           # "api" или "ui"
        "spec": {...},           # OpenAPI спецификация
        "allure_code": "..."     # Опционально: ручные тесты для конвертации в автотесты
    }
    """
    try:
        # Валидируем входные данные
        data = request.get_json()

        if not data:
            error = ErrorResponse(
                error='ValidationError',
                message='Требуется JSON тело запроса',
                status_code=400
            )
            return error.dict(), 400

        # Создаём AgentRequest
        try:
            agent_request = AgentRequest(**data)
        except Exception as e:
            error = ErrorResponse(
                error='ValidationError',
                message=f'Ошибка валидации AgentRequest: {str(e)}',
                status_code=400
            )
            return error.dict(), 400

        # Вызываем AgentCore.process() асинхронно
        try:
            # Создаём event loop для асинхронного вызова
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Запускаем AgentCore
            agent_response = loop.run_until_complete(generator.process(agent_request))
            loop.close()

            # Формируем ответ
            return jsonify({
                'status': 'success',
                'code': agent_response.code,
                'errors': agent_response.errors,
                'metadata': {
                    'lines_count': len(agent_response.code.split('\n')) if agent_response.code else 0,
                    'has_errors': len(agent_response.errors) > 0,
                    'generation_type': 'agent_core',
                    'used_llm': hasattr(generator, 'llm_client') and generator.llm_client
                }
            }), 200

        except Exception as e:
            current_app.logger.error(f'Ошибка AgentCore: {e}', exc_info=True)
            error = ErrorResponse(
                error='AgentCoreError',
                message=f'Ошибка при работе AgentCore: {str(e)}',
                status_code=500
            )
            return error.dict(), 500

    except Exception as e:
        return handle_api_error(e, 500)


# ==================== VALIDATE CODE ====================
@api_bp.route('/validate', methods=['POST'])
@inject_validator
def validate_code(validator):
    """
    Валидация сгенерированного кода тестов.
    POST /api/validate

    Пример тела запроса:
    {
        "code_text": "import pytest\\n\\ndef test_example():\\n    assert True",
        "check_types": ["syntax", "imports", "structure"]
    }
    """
    try:
        # Валидируем входные данные
        data = request.get_json()

        if not data:
            error = ErrorResponse(
                error='ValidationError',
                message='Требуется JSON тело запроса',
                status_code=400
            )
            return error.dict(), 400

        # Создаём Pydantic модель
        try:
            validation_request = ValidationRequest(**data)
        except Exception as e:
            error = ErrorResponse(
                error='ValidationError',
                message=f'Ошибка валидации входных данных: {str(e)}',
                status_code=400
            )
            return error.dict(), 400

        # Валидируем код
        try:
            validation_result = validator.validate(
                code_text=validation_request.code_text,
                check_types=validation_request.check_types
            )

            # Создаём структурированный ответ
            response = ValidationResponse(
                status=validation_result.get('status', 'valid'),
                is_valid=validation_result.get('is_valid', False),
                checks=validation_result.get('checks', {}),
                errors=validation_result.get('errors', []),
                warnings=validation_result.get('warnings', []),
                suggestions=validation_result.get('suggestions', []),
                statistics=validation_result.get('statistics', {})
            )

            return response.dict(), 200

        except Exception as e:
            current_app.logger.error(f'Ошибка валидации: {e}')
            error = ErrorResponse(
                error='ValidationError',
                message=f'Ошибка при валидации кода: {str(e)}',
                status_code=500
            )
            return error.dict(), 500

    except Exception as e:
        return handle_api_error(e, 500)


# ==================== UPLOAD OPENAPI ====================
@api_bp.route('/upload', methods=['POST'])
def upload_openapi():
    """
    Загрузка и парсинг OpenAPI файла.
    POST /api/upload
    """
    try:
        # Существующий код upload...
        # (оставь текущую реализацию без изменений)

        if 'file' in request.files:
            # ... существующий код ...
            pass
        else:
            error = ErrorResponse(
                error='ValidationError',
                message='Требуется файл',
                status_code=400
            )
            return error.dict(), 400

    except Exception as e:
        return handle_api_error(e, 500)


# ==================== LIST ENDPOINTS ====================
@api_bp.route('/', methods=['GET'])
def list_endpoints():
    """
    Список всех доступных эндпоинтов.
    GET /api/
    """
    endpoints = []

    for rule in current_app.url_map.iter_rules():
        if rule.endpoint.startswith('api.'):
            methods = ','.join(sorted(rule.methods - {'OPTIONS', 'HEAD'}))
            endpoints.append({
                'endpoint': rule.rule,
                'methods': methods,
                'description': get_endpoint_description(rule.endpoint)
            })

    return {
        'service': 'Test Generation API',
        'version': '1.0.0',
        'endpoints': endpoints
    }, 200


def get_endpoint_description(endpoint_name: str) -> str:
    """Получение описания эндпоинта по его имени."""
    descriptions = {
        'api.health_check': 'Проверка здоровья API и зависимостей',
        'api.upload_openapi': 'Загрузка и парсинг OpenAPI файла',
        'api.generate_tests': 'Генерация тестов по спецификации (старый интерфейс)',
        'api.generate_tests_agent': 'Генерация тестов через AgentCore (новый интерфейс)',
        'api.validate_code': 'Валидация сгенерированного кода',
        'api.full_process': 'Полный цикл: загрузка → парсинг → генерация → валидация',
        'api.list_endpoints': 'Список всех доступных эндпоинтов'
    }
    return descriptions.get(endpoint_name, 'Описание отсутствует')