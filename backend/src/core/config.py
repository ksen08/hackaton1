"""
Конфигурация Flask приложения (упрощенная версия).
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    Базовый класс конфигурации.
    """

    # ==================== FLASK НАСТРОЙКИ ====================
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False

    # ==================== CORS НАСТРОЙКИ ====================
    CORS_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000']

    # ==================== ПУТИ И ФАЙЛЫ ====================
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))

    # Папки для других модулей
    PARSER_OUTPUT_DIR = os.getenv('PARSER_OUTPUT_DIR', './parser_output')
    GENERATED_TESTS_DIR = os.getenv('GENERATED_TESTS_DIR', './generated_tests')
    VALIDATION_REPORTS_DIR = os.getenv('VALIDATION_REPORTS_DIR', './validation_reports')
    LOG_DIR = os.getenv('LOG_DIR', './logs')

    # ==================== LLM НАСТРОЙКИ ====================
    CLOUDRU_API_KEY = os.getenv('CLOUDRU_API_KEY')
    CLOUDRU_ENDPOINT = os.getenv('CLOUDRU_ENDPOINT', 'https://api.cloud.ru/v1/chat/completions')
    LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-3.5-turbo')
    LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', 0.7))
    LLM_MAX_TOKENS = int(os.getenv('LLM_MAX_TOKENS', 2000))

    # ==================== НАСТРОЙКИ ПАРСЕРА ====================
    PARSER_TIMEOUT = int(os.getenv('PARSER_TIMEOUT', 30))

    # ==================== НАСТРОЙКИ ВАЛИДАТОРА ====================
    VALIDATOR_MODE = os.getenv('VALIDATOR_MODE', 'strict')

    # ==================== ЛОГИРОВАНИЕ ====================
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_TO_FILE = os.getenv('LOG_TO_FILE', 'false').lower() == 'true'

    # ==================== СЕРВЕР ====================
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))


class DevelopmentConfig(Config):
    """Конфигурация для разработки."""
    DEBUG = True
    CORS_ORIGINS = ['*']
    LOG_LEVEL = 'DEBUG'


class TestingConfig(Config):
    """Конфигурация для тестирования."""
    TESTING = True
    DEBUG = True
    CLOUDRU_API_KEY = 'test-api-key'
    CLOUDRU_ENDPOINT = 'http://test-mock-server/api'


class ProductionConfig(Config):
    """Конфигурация для продакшена."""
    DEBUG = False
    CORS_ORIGINS = [
        'https://наш-сайт.ru',
        'https://api.наш-сайт.ru'
    ]
    LOG_LEVEL = 'WARNING'
    LOG_TO_FILE = True


# Словарь для выбора конфигурации
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}


def get_config(config_name: str = None):
    """Получение конфигурации."""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    config_class = config_by_name.get(config_name, DevelopmentConfig)
    return config_class()