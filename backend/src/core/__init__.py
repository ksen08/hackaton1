"""
Ядро Flask приложения.
Фабрика для создания приложения с разными конфигурациями.
"""

import os
from flask import Flask
from flask_cors import CORS
from .config import get_config
from .dependencies import teardown_dependencies


def create_app(config_name: str = None) -> Flask:
    """
    Фабрика для создания Flask приложения.

    Args:
        config_name: Имя конфигурации ('development', 'testing', 'production')
                    Если None, определяется из переменных окружения.

    Returns:
        Flask: Настроенное Flask приложение
    """
    # Создаем приложение
    app = Flask(__name__)

    # Загружаем конфигурацию
    config = get_config(config_name)
    app.config.from_object(config)

    # Создаем необходимые папки
    _create_directories(app)

    # Настраиваем CORS
    CORS(app, origins=app.config['CORS_ORIGINS'])

    # Регистрируем blueprints (позже)
    _register_blueprints(app)

    # Регистрируем обработчики ошибок
    _register_error_handlers(app)

    # Создаем базовые роуты
    _create_basic_routes(app)

    app.teardown_appcontext(teardown_dependencies)

    from api.routes import api_bp
    app.register_blueprint(api_bp)

    return app


def _create_directories(app: Flask):
    """Создает необходимые директории."""
    directories = [
        app.config['UPLOAD_FOLDER'],
        app.config['PARSER_OUTPUT_DIR'],
        app.config['GENERATED_TESTS_DIR'],
        app.config['VALIDATION_REPORTS_DIR'],
        app.config['LOG_DIR']
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def _register_blueprints(app: Flask):
    """Регистрирует blueprints (роуты)."""
    # Пока не регистрируем - сделаем позже
    pass


def _register_error_handlers(app: Flask):
    """Регистрирует обработчики ошибок."""

    @app.errorhandler(404)
    def not_found(error):
        return {
            'error': 'Not Found',
            'message': 'Запрашиваемый ресурс не найден',
            'status_code': 404
        }, 404

    @app.errorhandler(400)
    def bad_request(error):
        return {
            'error': 'Bad Request',
            'message': str(error.description) if hasattr(error, 'description') else 'Неверный запрос',
            'status_code': 400
        }, 400

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Internal server error: {error}')
        return {
            'error': 'Internal Server Error',
            'message': 'Произошла внутренняя ошибка сервера',
            'status_code': 500
        }, 500


def _create_basic_routes(app: Flask):
    """Создает базовые роуты."""

    @app.route('/')
    def index():
        """Корневой эндпоинт."""
        return {
            'service': 'Test Generation API',
            'version': '1.0.0',
            'status': 'running',
            'environment': app.config.get('FLASK_ENV', 'unknown'),
            'documentation': {
                'swagger': '/docs',
                'redoc': '/redoc'
            },
            'endpoints': {
                'upload': '/api/upload',
                'generate': '/api/generate',
                'validate': '/api/validate',
                'health': '/api/health'
            }
        }

    @app.route('/api/health')
    def health():
        """Проверка здоровья приложения."""
        return {
            'status': 'healthy',
            'timestamp': '2024-01-15T12:00:00Z',
            'service': 'test-generation-api',
            'dependencies': {
                'parser': 'not_implemented',
                'generator': 'not_implemented',
                'validator': 'not_implemented'
            }
        }

    @app.route('/api/config')
    def config_info():
        """Информация о текущей конфигурации (только для разработки)."""
        if app.config['DEBUG']:
            safe_config = {k: v for k, v in app.config.items()
                           if not any(secret in k.lower() for secret in ['key', 'secret', 'password'])}
            return {'config': safe_config}
        return {'message': 'Config endpoint available only in debug mode'}, 403