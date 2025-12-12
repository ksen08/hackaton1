"""
Конфигурация системы генерации тестов
"""

import os
from pathlib import Path

# Базовые настройки
BASE_DIR = Path(__file__).parent.parent
OPENAPI_SPEC = BASE_DIR / "openapi_spec.yaml"  # Путь к OpenAPI спецификации
BASE_URL = "https://compute.api.cloud.ru"  # Базовый URL API

# Настройки вывода
OUTPUT_DIR = BASE_DIR / "generated_tests"

# Теги API для генерации тестов
TAGS_TO_GENERATE = ["vms", "disks", "flavors"]

# Настройки LLM (Cloud.ru Evolution Foundation Model)
LLM_API_KEY = os.getenv("CLOUD_RU_LLM_API_KEY")
LLM_API_URL = "https://api.cloud.ru/evolution/v1/completions"
LLM_MODEL = "evolution-foundation"
LLM_TEMPERATURE = 0.3
LLM_MAX_TOKENS = 4000

# Настройки валидации
VALIDATION_STANDARDS = {
    "required_decorators": [
        "@allure.feature",
        "@allure.story",
        "@allure.title",
        "@allure.tag",
        'allure.label("owner"',
        'allure.label("priority"'
    ],
    "aaa_pattern_strict": True,
    "min_test_steps": 3,
    "max_line_length": 100,
    "require_type_hints": True,
    "require_docstrings": True
}

# Настройки генерации автотестов
AUTO_TEST_CONFIG = {
    "generate_fixtures": True,
    "generate_utils": True,
    "generate_test_data": True,
    "timeout": 30,
    "retry_attempts": 3
}

# Настройки отчетов
REPORT_CONFIG = {
    "generate_html": True,
    "generate_json": True,
    "generate_markdown": True,
    "include_coverage": True,
    "include_recommendations": True
}

# Настройки логирования
LOG_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": BASE_DIR / "logs" / "test_generation.log"
}
