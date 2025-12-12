"""
Pydantic схемы (модели данных) для API.
Определяют структуру запросов и ответов.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from enum import Enum


# ==================== ENUMS (перечисления) ====================

class TestType(str, Enum):
    """
    Типы тестов, которые можно генерировать.
    """
    MANUAL_UI = "manual_ui"  # Ручные UI тесты
    MANUAL_API = "manual_api"  # Ручные API тесты
    AUTO_API = "auto_api"  # Автотесты API
    AUTO_UI = "auto_ui"  # Автотесты UI


class ValidationStatus(str, Enum):
    """
    Статусы валидации кода.
    """
    VALID = "valid"  # Код валиден
    INVALID = "invalid"  # Код невалиден
    WARNING = "warning"  # Есть предупреждения


# ==================== ЗАПРОСЫ ====================

class OpenAPIUpload(BaseModel):
    """
    Модель для загрузки OpenAPI файла.
    Используется в эндпоинте /upload.
    """
    filename: str = Field(
        ...,
        description="Имя файла",
        example="petstore.yaml"
    )
    content: str = Field(
        ...,
        description="Содержимое файла в base64",
        example="IyBPcGVuQVBJIDMuMC4wCiMg... (base64 string)"
    )
    content_type: str = Field(
        default="application/x-yaml",
        description="Тип содержимого",
        example="application/x-yaml"
    )

    @validator('content_type')
    def validate_content_type(cls, v):
        """Проверяем допустимый тип файла."""
        allowed_types = [
            'application/x-yaml',
            'text/yaml',
            'application/x-yaml',
            'application/json'
        ]
        if v not in allowed_types:
            raise ValueError(f'Недопустимый тип файла. Допустимы: {allowed_types}')
        return v

    @validator('filename')
    def validate_filename(cls, v):
        """Проверяем расширение файла."""
        allowed_extensions = ['.yaml', '.yml', '.json']
        if not any(v.endswith(ext) for ext in allowed_extensions):
            raise ValueError(f'Файл должен иметь расширение: {allowed_extensions}')
        return v


class GenerationRequest(BaseModel):
    """
    Модель для запроса генерации тестов.
    Используется в эндпоинте /generate.
    """
    spec: Dict[str, Any] = Field(
        ...,
        description="Распарсенная OpenAPI спецификация",
        example={
            "openapi": "3.0.0",
            "info": {"title": "Petstore API"},
            "paths": {"/pets": {"get": {}}}
        }
    )
    test_type: TestType = Field(
        ...,
        description="Тип тестов для генерации",
        example=TestType.AUTO_API
    )
    options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Дополнительные опции генерации",
        example={"include_negative_tests": True, "language": "python"}
    )

    class Config:
        # Для красивого отображения в документации
        json_schema_extra = {
            "example": {
                "spec": {
                    "openapi": "3.0.0",
                    "info": {"title": "Example API"},
                    "paths": {
                        "/users": {
                            "get": {
                                "responses": {"200": {"description": "OK"}}
                            }
                        }
                    }
                },
                "test_type": "auto_api",
                "options": {"language": "python"}
            }
        }


class ValidationRequest(BaseModel):
    """
    Модель для запроса валидации кода.
    Используется в эндпоинте /validate.
    """
    code_text: str = Field(
        ...,
        description="Текст кода для валидации",
        example="import pytest\n\ndef test_example():\n    assert True"
    )
    check_types: List[str] = Field(
        default=["syntax", "imports", "structure"],
        description="Типы проверок для выполнения",
        example=["syntax", "imports"]
    )

    @validator('check_types')
    def validate_check_types(cls, v):
        """Проверяем допустимые типы проверок."""
        allowed_checks = ["syntax", "imports", "structure", "style", "security"]
        for check in v:
            if check not in allowed_checks:
                raise ValueError(f'Недопустимый тип проверки: {check}. Допустимы: {allowed_checks}')
        return v


# ==================== ОТВЕТЫ ====================

class GenerationResponse(BaseModel):
    """
    Модель для ответа с сгенерированными тестами.
    Возвращается из эндпоинта /generate.
    """
    status: str = Field(
        ...,
        description="Статус генерации",
        example="success"
    )
    code_text: str = Field(
        ...,
        description="Сгенерированный код тестов",
        example="import pytest\nimport allure\n\n@allure.title('Test')\ndef test_example():\n    assert True"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Метаданные генерации",
        example={
            "test_type": "auto_api",
            "lines_count": 50,
            "language": "python",
            "generated_at": "2024-01-15T12:00:00Z",
            "llm_model": "gpt-3.5-turbo"
        }
    )
    warnings: Optional[List[str]] = Field(
        default=None,
        description="Предупреждения при генерации",
        example=["Код требует ручной проверки", "Отсутствуют некоторые импорты"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "code_text": "import pytest\n\ndef test_example():\n    assert True",
                "metadata": {
                    "test_type": "auto_api",
                    "lines_count": 10,
                    "generated_at": "2024-01-15T12:00:00Z"
                },
                "warnings": ["Код требует ручной проверки"]
            }
        }


class ValidationResponse(BaseModel):
    """
    Модель для ответа с результатами валидации.
    Возвращается из эндпоинта /validate.
    """
    status: ValidationStatus = Field(
        ...,
        description="Общий статус валидации",
        example=ValidationStatus.VALID
    )
    is_valid: bool = Field(
        ...,
        description="Прошел ли код валидацию",
        example=True
    )
    checks: Dict[str, bool] = Field(
        ...,
        description="Результаты отдельных проверок",
        example={
            "syntax": True,
            "imports": True,
            "structure": False
        }
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Список ошибок",
        example=["Отсутствует import pytest", "Синтаксическая ошибка в строке 5"]
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Список предупреждений",
        example=["Код не содержит docstrings", "Слишком длинные строки"]
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Предложения по улучшению",
        example=["Добавить type hints", "Использовать f-strings вместо конкатенации"]
    )
    statistics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Статистика кода",
        example={
            "lines_count": 50,
            "functions_count": 5,
            "imports_count": 3,
            "complexity_score": 2.5
        }
    )


class ErrorResponse(BaseModel):
    """
    Стандартная модель для ошибок API.
    Используется во всех эндпоинтах при ошибках.
    """
    error: str = Field(
        ...,
        description="Тип ошибки",
        example="ValidationError"
    )
    message: str = Field(
        ...,
        description="Сообщение об ошибке",
        example="Неверный формат файла"
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Детали ошибки",
        example={"field": "filename", "reason": "Неверное расширение"}
    )
    status_code: int = Field(
        ...,
        description="HTTP статус код",
        example=400
    )

    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Неверный формат файла",
                "details": {"field": "filename", "reason": "Требуется .yaml или .json"},
                "status_code": 400
            }
        }


# ==================== ВСПОМОГАТЕЛЬНЫЕ МОДЕЛИ ====================

class ParsedOpenAPI(BaseModel):
    """
    Модель для распарсенной OpenAPI спецификации.
    Используется между парсером и генератором.
    """
    services: List[Dict[str, Any]] = Field(
        ...,
        description="Список endpoint'ов API",
        example=[
            {
                "path": "/pets",
                "method": "GET",
                "parameters": [],
                "request_body": None,
                "responses": {"200": {"description": "OK"}}
            }
        ]
    )
    components: Dict[str, Any] = Field(
        default_factory=dict,
        description="Компоненты OpenAPI (схемы, параметры)",
        example={
            "schemas": {
                "Pet": {
                    "type": "object",
                    "properties": {"id": {"type": "integer"}}
                }
            }
        }
    )
    info: Dict[str, Any] = Field(
        ...,
        description="Информация о API",
        example={"title": "Petstore API", "version": "1.0.0"}
    )
    security: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Настройки безопасности API"
    )


class HealthCheckResponse(BaseModel):
    """
    Модель для ответа health check.
    """
    status: str = Field(..., example="healthy")
    service: str = Field(..., example="test-generation-api")
    timestamp: str = Field(..., example="2024-01-15T12:00:00Z")
    version: str = Field(..., example="1.0.0")
    dependencies: Dict[str, str] = Field(
        ...,
        example={
            "parser": "available",
            "generator": "available",
            "validator": "available",
            "database": "connected"
        }
    )

# backend/src/schemas/models.py
from pydantic import BaseModel, Field
from typing import Optional

class AgentRequest(BaseModel):
    type: str = Field(..., description="Тип: 'api' или 'ui'")
    spec: dict = Field(..., description="OpenAPI spec или UI описание")
    allure_code: Optional[str] = Field(None, description="Для автотестов: Allure-код из предыдущего шага")

class AgentResponse(BaseModel):
    code: str = Field(..., description="Сгенерированный Python-код")
    errors: list[str] = Field(default=[], description="Ошибки, если есть")
