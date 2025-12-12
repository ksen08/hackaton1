"""
Комбинатор промтов с данными из OpenAPI спецификации
ЗАМЕНЯЕТ все отдельные txt файлы с промтами
"""

import json
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass
import re


@dataclass
class EndpointInfo:
    """Информация об эндпоинте из OpenAPI"""
    path: str
    method: str
    operation_id: str
    summary: str
    description: str
    tags: List[str]
    parameters: List[Dict]
    request_body: Optional[Dict]
    responses: Dict
    security: List[Dict]


class PromptBuilder:
    """
    Строитель промтов на основе OpenAPI спецификации
    Автоматически комбинирует шаблоны промтов с данными спецификации
    """

    # ШАБЛОНЫ ПРОМТОВ (в коде вместо отдельных файлов)
    SYSTEM_PROMPT_TEMPLATE = """
Ты — AI-агент для генерации тест-кейсов в формате Allure TestOps as Code на Python.
Продукт: Evolution Compute Public API v3
Base URL: {base_url}
Аутентификация: Bearer-токен (userPlaneApiToken)

ТРЕБОВАНИЯ:
1. Паттерн AAA (Arrange-Act-Assert)
2. Формат Allure TestOps as Code
3. Декораторы: @allure.feature, @allure.story, @allure.title, @allure.tag
4. Метки: owner=backend_team, priority=critical/normal/low
5. Классы: CamelCase + Tests, Методы: test_ + snake_case
6. Все шаги в allure.step()

ТЕХНИЧЕСКИЕ ДЕТАЛИ:
• Идентификаторы: UUIDv4 формата
• Заголовок: Authorization: Bearer {{token}}
• Ошибки: ExceptionSchema массив
"""

    ENDPOINT_PROMPT_TEMPLATE = """
СГЕНЕРИРУЙ тест-кейсы для эндпоинта:

{method} {path}
{summary}

ТЕХНИЧЕСКАЯ ИНФОРМАЦИЯ:
• Операция: {operation_id}
• Теги: {tags}
• Параметры: {parameters_info}
• Тело запроса: {request_body_info}
• Ответы: {responses_info}

ТРЕБУЕМЫЕ ТЕСТ-КЕЙСЫ:
1. ПОЗИТИВНЫЙ СЦЕНАРИЙ:
   • Валидные данные
   • Проверка статуса {success_status}
   • Проверка структуры ответа

2. НЕГАТИВНЫЕ СЦЕНАРИИ:
{negative_scenarios}

3. ГРАНИЧНЫЕ ЗНАЧЕНИЯ:
{boundary_cases}

ФОРМАТ ВЫВОДА:
• Класс: {class_name}Tests
• Feature: {feature_name}
• Story: {story_name}
"""

    def __init__(self, openapi_spec_path: str, base_url: str = "https://compute.api.cloud.ru"):
        self.openapi_spec_path = Path(openapi_spec_path)
        self.base_url = base_url
        self.spec_data = self._load_spec()

    def _load_spec(self) -> Dict[str, Any]:
        """Загрузка OpenAPI спецификации"""
        with open(self.openapi_spec_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if self.openapi_spec_path.suffix.lower() in ['.yaml', '.yml']:
                return yaml.safe_load(content)
            return json.loads(content)

    def extract_endpoints_by_tag(self, tag: str) -> List[EndpointInfo]:
        """Извлечение эндпоинтов по тегу"""
        endpoints = []

        for path, methods in self.spec_data.get('paths', {}).items():
            for method, details in methods.items():
                if tag.lower() not in [t.lower() for t in details.get('tags', [])]:
                    continue

                endpoint = EndpointInfo(
                    path=path,
                    method=method.upper(),
                    operation_id=details.get('operationId', ''),
                    summary=details.get('summary', ''),
                    description=details.get('description', ''),
                    tags=details.get('tags', []),
                    parameters=details.get('parameters', []),
                    request_body=details.get('requestBody'),
                    responses=details.get('responses', {}),
                    security=details.get('security', [])
                )
                endpoints.append(endpoint)

        return endpoints

    def build_prompt_for_tag(self, tag: str) -> str:
        """
        Строит полный промт для тега (VMs, Disks, Flavors)
        АВТОМАТИЧЕСКАЯ ЗАМЕНА отдельных txt файлов
        """
        endpoints = self.extract_endpoints_by_tag(tag)

        # Системный промт
        system_prompt = self.SYSTEM_PROMPT_TEMPLATE.format(base_url=self.base_url)

        # Промты для каждого эндпоинта
        endpoint_prompts = []
        for endpoint in endpoints:
            endpoint_prompt = self._build_endpoint_prompt(endpoint, tag)
            endpoint_prompts.append(endpoint_prompt)

        # Объединяем все
        full_prompt = f"""{system_prompt}

РАЗДЕЛ API: {tag.upper()}

ЭНДПОИНТЫ ДЛЯ ТЕСТИРОВАНИЯ:
{len(endpoints)} endpoints found

{'=' * 60}
""".join(endpoint_prompts)

        return full_prompt

    def _build_endpoint_prompt(self, endpoint: EndpointInfo, tag: str) -> str:
        """Строит промт для конкретного эндпоинта"""

        # Определяем успешный статус код
        success_status = self._get_success_status(endpoint.responses)

        # Генерируем негативные сценарии
        negative_scenarios = self._generate_negative_scenarios(endpoint)

        # Генерируем граничные случаи
        boundary_cases = self._generate_boundary_cases(endpoint)

        # Определяем имя класса и фичи
        class_name = self._tag_to_class_name(tag)
        feature_name = self._tag_to_feature_name(tag)

        # Форматируем информацию
        params_info = self._format_parameters(endpoint.parameters)
        body_info = self._format_request_body(endpoint.request_body)
        responses_info = self._format_responses(endpoint.responses)

        return self.ENDPOINT_PROMPT_TEMPLATE.format(
            method=endpoint.method,
            path=endpoint.path,
            summary=endpoint.summary,
            operation_id=endpoint.operation_id,
            tags=', '.join(endpoint.tags),
            parameters_info=params_info,
            request_body_info=body_info,
            responses_info=responses_info,
            success_status=success_status,
            negative_scenarios=negative_scenarios,
            boundary_cases=boundary_cases,
            class_name=class_name,
            feature_name=feature_name,
            story_name=endpoint.operation_id.replace('_', ' ').title()
        )

    def _get_success_status(self, responses: Dict) -> str:
        """Определяет успешный статус код из спецификации"""
        for status in ['200', '201', '202', '204']:
            if status in responses:
                return status
        return '200'

    def _generate_negative_scenarios(self, endpoint: EndpointInfo) -> str:
        """Генерация негативных сценариев на основе спецификации"""
        scenarios = []

        # Общие негативные сценарии
        scenarios.append("   • Неверный токен аутентификации (401)")
        scenarios.append("   • Отсутствие токена (401)")
        scenarios.append("   • Недостаточно прав (403)")

        # Для GET по ID
        if '{' in endpoint.path and endpoint.method == 'GET':
            scenarios.append("   • Несуществующий ID (404)")
            scenarios.append("   • Невалидный формат ID (400)")

        # Для POST/PUT/PATCH
        if endpoint.method in ['POST', 'PUT', 'PATCH']:
            scenarios.append("   • Отсутствие обязательных полей (400)")
            scenarios.append("   • Невалидные типы данных (400)")
            scenarios.append("   • Нарушение уникальности (409)")

        # Для DELETE
        if endpoint.method == 'DELETE':
            scenarios.append("   • Несуществующий ресурс (404)")
            scenarios.append("   • Конфликт зависимостей (409)")

        return '\n'.join(scenarios)

    def _generate_boundary_cases(self, endpoint: EndpointInfo) -> str:
        """Генерация граничных случаев"""
        cases = []

        # Для параметров с числовыми значениями
        for param in endpoint.parameters:
            if param.get('schema', {}).get('type') in ['integer', 'number']:
                param_name = param.get('name')
                cases.append(f"   • {param_name}: минимальное значение")
                cases.append(f"   • {param_name}: максимальное значение")
                cases.append(f"   • {param_name}: отрицательное значение")

        # Для строковых параметров
        for param in endpoint.parameters:
            if param.get('schema', {}).get('type') == 'string':
                param_name = param.get('name')
                cases.append(f"   • {param_name}: пустая строка")
                cases.append(f"   • {param_name}: очень длинная строка")

        return '\n'.join(cases) if cases else "   • (граничные случаи не определены)"

    def _format_parameters(self, parameters: List[Dict]) -> str:
        """Форматирование информации о параметрах"""
        if not parameters:
            return "Нет параметров"

        formatted = []
        for param in parameters:
            param_info = f"    - {param.get('name')} ({param.get('in')}): "
            if param.get('required', False):
                param_info += "[ОБЯЗАТЕЛЬНЫЙ] "
            param_info += param.get('description', 'Без описания')
            formatted.append(param_info)

        return '\n'.join(formatted)

    def _format_request_body(self, request_body: Optional[Dict]) -> str:
        """Форматирование информации о теле запроса"""
        if not request_body:
            return "Нет тела запроса"

        # Извлекаем схему
        content = request_body.get('content', {})
        if 'application/json' in content:
            schema = content['application/json'].get('schema', {})
            return f"JSON схема: {schema.get('type', 'object')}"

        return "Тело запроса присутствует"

    def _format_responses(self, responses: Dict) -> str:
        """Форматирование информации об ответах"""
        formatted = []
        for status, details in responses.items():
            formatted.append(f"    - {status}: {details.get('description', 'Без описания')}")
        return '\n'.join(formatted)

    def _tag_to_class_name(self, tag: str) -> str:
        """Конвертация тега в имя класса"""
        mappings = {
            'vms': 'Vm',
            'disks': 'Disk',
            'flavors': 'Flavor',
            'virtual-machines': 'Vm',
            'virtual-machines': 'VmCrud'
        }
        return mappings.get(tag.lower(), tag.title().replace('-', ''))

    def _tag_to_feature_name(self, tag: str) -> str:
        """Конвертация тега в имя фичи"""
        mappings = {
            'vms': 'Virtual Machines',
            'disks': 'Disk Management',
            'flavors': 'Flavors',
            'virtual-machines': 'Virtual Machines'
        }
        return mappings.get(tag.lower(), tag.replace('-', ' ').title())


# Пример использования
if __name__ == "__main__":
    builder = PromptBuilder("openapi_spec.yaml")

    # Генерация промта для VMs (ЗАМЕНА vms_promts.txt)
    vms_prompt = builder.build_prompt_for_tag("vms")
    print(f"Промт для VMs ({len(vms_prompt)} символов)")

    # Генерация промта для Disks (ЗАМЕНА disks_promts.txt)
    disks_prompt = builder.build_prompt_for_tag("disks")

    # Генерация промта для Flavors (ЗАМЕНА flavors_promts.txt)
    flavors_prompt = builder.build_prompt_for_tag("flavors")
