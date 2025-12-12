# backend/src/text_parser.py
import json
import re
from typing import Dict, Any, List
import os


def parse_user_request_to_json(user_text: str) -> Dict[str, Any]:
    """
    Парсит текстовый запрос пользователя в JSON структуру для OpenAPI
    """
    # Инициализируем базовую структуру
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "API из пользовательского запроса",
            "version": "v1",
            "description": user_text[:100] + "..."
        },
        "paths": {}
    }

    # Парсим endpoints из текста
    endpoints = []

    # Паттерны для поиска endpoints
    patterns = [
        r'/([a-zA-Z0-9_\-/{]+)',  # /endpoint или /endpoint/{id}
        r'GET\s+/([a-zA-Z0-9_\-/{]+)',
        r'POST\s+/([a-zA-Z0-9_\-/{]+)',
        r'PUT\s+/([a-zA-Z0-9_\-/{]+)',
        r'DELETE\s+/([a-zA-Z0-9_\-/{]+)',
        r'PATCH\s+/([a-zA-Z0-9_\-/{]+)'
    ]

    for pattern in patterns:
        matches = re.findall(pattern, user_text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                endpoint = match[0]
            else:
                endpoint = match

            # Нормализуем endpoint
            if not endpoint.startswith('/'):
                endpoint = '/' + endpoint

            if endpoint not in endpoints:
                endpoints.append(endpoint)

    # Если endpoints не найдены, создаем дефолтные
    if not endpoints:
        endpoints = ['/vms', '/vms/{id}', '/disks', '/flavors']

    # Создаем структуру для каждого endpoint
    for endpoint in endpoints:
        spec["paths"][endpoint] = {}

        # Определяем методы из текста
        if re.search(r'GET', user_text, re.IGNORECASE) or 'получить' in user_text.lower():
            spec["paths"][endpoint]["get"] = {
                "summary": f"Получить {endpoint}",
                "responses": {"200": {"description": "Успешно"}}
            }

        if re.search(r'POST', user_text, re.IGNORECASE) or 'создать' in user_text.lower():
            spec["paths"][endpoint]["post"] = {
                "summary": f"Создать {endpoint}",
                "responses": {"201": {"description": "Создано"}}
            }

        if re.search(r'PUT', user_text, re.IGNORECASE) or 'обновить' in user_text.lower():
            spec["paths"][endpoint]["put"] = {
                "summary": f"Обновить {endpoint}",
                "responses": {"200": {"description": "Обновлено"}}
            }

        if re.search(r'DELETE', user_text, re.IGNORECASE) or 'удалить' in user_text.lower():
            spec["paths"][endpoint]["delete"] = {
                "summary": f"Удалить {endpoint}",
                "responses": {"204": {"description": "Удалено"}}
            }

        # Если методы не определены, добавляем все основные
        if not spec["paths"][endpoint]:
            spec["paths"][endpoint] = {
                "get": {"summary": f"Получить {endpoint}"},
                "post": {"summary": f"Создать {endpoint}"},
                "put": {"summary": f"Обновить {endpoint}"},
                "delete": {"summary": f"Удалить {endpoint}"}
            }

    return spec


def extract_endpoints(text: str) -> List[Dict[str, Any]]:
    """Извлекает endpoints из текста (для обратной совместимости)"""
    endpoints = []

    endpoint_pattern = r'/(?:[\w\-]+/?)+(?:{\w+})?'
    found = re.findall(endpoint_pattern, text)

    for endpoint in found:
        endpoints.append({
            "path": endpoint,
            "methods": ["GET", "POST"],
            "description": f"Endpoint найден в запросе"
        })

    return endpoints


def save_to_file(filename: str, content: str, directory: str = "output") -> str:
    """Сохраняет содержимое в файл"""
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return filepath
