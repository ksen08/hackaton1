"""
Генератор Python кода на основе шаблонов и данных из OpenAPI
"""

import ast
import black
import isort
from typing import Dict, Any, List, Optional
from pathlib import Path
import jinja2
from .template_engine import template_engine
from .prompt_builder import PromptBuilder, EndpointInfo


class CodeGenerator:
    """Генератор валидного Python кода тестов"""

    def __init__(self, openapi_spec_path: str):
        self.prompt_builder = PromptBuilder(openapi_spec_path)
        self.template_engine = template_engine
        self.openapi_spec_path = Path(openapi_spec_path)

    def generate_manual_tests(self, tag: str, output_dir: str) -> Dict[str, str]:
        """
        Генерация ручных тест-кейсов для указанного тега
        Возвращает словарь {filename: generated_code}
        """
        endpoints = self.prompt_builder.extract_endpoints_by_tag(tag)

        # Подготавливаем контекст для шаблона
        context = {
            'feature': self.prompt_builder._tag_to_feature_name(tag),  # 'VMS'
            'class_name': self.prompt_builder._tag_to_class_name(tag),  # 'VmsManualTests'
            'owner': 'backend_team',
            'suite': 'manual_api_tests',
            'story': f'API Testing for {tag.upper()}',
            'test_cases': self._prepare_endpoints_for_template(endpoints, tag),
            'description': f'Автоматически сгенерированные тесты для {tag.upper()} API'
        }

        # Генерируем код из шаблона - ИСПРАВЛЕННЫЙ ВЫЗОВ
        raw_code = self.template_engine.generate_manual_test_case(
            test_data=context,
            output_dir=output_dir  # передаем директорию для сохранения
        )

        # Если метод возвращает Path (файл), читаем его содержимое
        if isinstance(raw_code, Path):
            with open(raw_code, 'r', encoding='utf-8') as f:
                formatted_code = f.read()
            filename = raw_code.name
        else:
            # Если возвращает строку, форматируем
            formatted_code = self._format_code(raw_code)
            filename = f"test_{tag.lower()}.py"

        # Валидируем синтаксис
        self._validate_syntax(formatted_code)

        # Сохраняем в файл если еще не сохранен
        if not isinstance(raw_code, Path):
            output_path = Path(output_dir) / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(formatted_code)

        return {filename: formatted_code}

    def generate_all_manual_tests(self, output_dir: str) -> Dict[str, str]:
        """Генерация всех ручных тестов (VMs, Disks, Flavors)"""
        results = {}

        for tag in ['vms', 'disks', 'flavors']:
            print(f"Генерация тестов для {tag.upper()}...")
            try:
                tag_results = self.generate_manual_tests(tag, output_dir)
                results.update(tag_results)
                print(f"✓ Сгенерировано: {list(tag_results.keys())[0]}")
            except Exception as e:
                print(f"✗ Ошибка генерации {tag}: {e}")

        return results

    def generate_automated_tests(self, manual_test_path: str, output_dir: str) -> Dict[str, str]:
        """
        Преобразование ручных тестов в автоматизированные pytest тесты
        """
        # Читаем ручные тесты
        with open(manual_test_path, 'r', encoding='utf-8') as f:
            manual_code = f.read()

        # Парсим AST для извлечения структуры
        tree = ast.parse(manual_code)

        # Извлекаем информацию о тестах
        test_info = self._extract_test_info_from_ast(tree)

        # Генерируем pytest код
        pytest_code = self._generate_pytest_code(test_info)

        # Форматируем
        formatted_code = self._format_code(pytest_code)

        # Сохраняем
        filename = f"pytest_{Path(manual_test_path).stem}.py"
        output_path = Path(output_dir) / filename

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(formatted_code)

        return {filename: formatted_code}

    def _prepare_endpoints_for_template(self, endpoints: List[EndpointInfo], tag: str) -> List[Dict]:
        """Подготовка данных эндпоинтов для шаблона"""
        test_cases = []

        for i, endpoint in enumerate(endpoints):
            # Базовый тест-кейс
            test_case = {
                'title': self._generate_test_title(endpoint, is_negative=False),
                'description': endpoint.description or endpoint.summary or '',
                'method_name': f"test_{self._to_snake_case(endpoint.operation_id or f'endpoint_{i}')}",
                'priority': self._determine_priority(endpoint, is_negative=False),
                'priority_tag': 'NORMAL' if self._determine_priority(endpoint, False) == 'NORMAL' else 'CRITICAL',
                'jira_link': '#',
                'jira_name': 'TBD',
                'steps': self._create_test_steps(endpoint, is_negative=False)
            }
            test_cases.append(test_case)

            # Негативный тест-кейс если нужно
            if self._should_generate_negative_test(endpoint):
                negative_case = {
                    'title': self._generate_test_title(endpoint, is_negative=True),
                    'description': f"Negative test for {endpoint.summary or endpoint.operation_id}",
                    'method_name': f"test_{self._to_snake_case(endpoint.operation_id or f'endpoint_{i}')}_negative",
                    'priority': self._determine_priority(endpoint, is_negative=True),
                    'priority_tag': 'LOW',
                    'jira_link': '#',
                    'jira_name': 'TBD',
                    'steps': self._create_test_steps(endpoint, is_negative=True)
                }
                test_cases.append(negative_case)

        return test_cases

    def _create_test_steps(self, endpoint: EndpointInfo, is_negative: bool) -> List[Dict]:
        """Создание шагов теста"""
        if is_negative:
            return [
                {
                    'name': 'Подготовка невалидного запроса',
                    'action': f'# Подготовить невалидные данные для {endpoint.method} {endpoint.path}',
                    'expected_result': 'Данные подготовлены'
                },
                {
                    'name': 'Отправка запроса',
                    'action': f'# Отправить {endpoint.method} запрос с невалидными данными',
                    'expected_result': 'Запрос отправлен'
                },
                {
                    'name': 'Проверка ответа',
                    'action': '# Проверить код ошибки и сообщение',
                    'expected_result': f'Получен код ошибки {self._get_expected_status(endpoint, True)}'
                }
            ]
        else:
            return [
                {
                    'name': 'Подготовка запроса',
                    'action': f'# Подготовить данные для {endpoint.method} {endpoint.path}',
                    'expected_result': 'Данные подготовлены правильно'
                },
                {
                    'name': 'Отправка запроса',
                    'action': f'# Отправить {endpoint.method} запрос',
                    'expected_result': 'Запрос успешно отправлен'
                },
                {
                    'name': 'Проверка ответа',
                    'action': '# Проверить статус и данные ответа',
                    'expected_result': f'Получен статус {self._get_expected_status(endpoint, False)}, данные валидны'
                }
            ]

    def _to_snake_case(self, text: str) -> str:
        """Конвертация в snake_case"""
        import re
        if not text:
            return ''
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', text)
        text = re.sub(r'[-\s]+', '_', text)
        return text.lower().strip('_')

    def _generate_request_body_example(self, endpoint: EndpointInfo) -> Dict:
        """Генерация примера тела запроса на основе схемы"""
        if not endpoint.request_body:
            return {}

        example = {}
        content = endpoint.request_body.get('content', {})

        if 'application/json' in content:
            schema = content['application/json'].get('schema', {})
            example = self._generate_example_from_schema(schema)

        return example

    def _generate_example_from_schema(self, schema: Dict) -> Dict:
        """Генерация примера данных из JSON схемы"""
        schema_type = schema.get('type', 'object')

        if schema_type == 'object':
            example = {}
            properties = schema.get('properties', {})

            for prop_name, prop_schema in properties.items():
                prop_type = prop_schema.get('type', 'string')

                if prop_type == 'string':
                    if 'format' in prop_schema:
                        if prop_schema['format'] == 'uuid':
                            example[prop_name] = "uuid_example"
                        elif prop_schema['format'] == 'email':
                            example[prop_name] = "test@example.com"
                        else:
                            example[prop_name] = f"example_{prop_name}"
                    else:
                        example[prop_name] = f"example_{prop_name}"

                elif prop_type == 'integer':
                    example[prop_name] = 1

                elif prop_type == 'boolean':
                    example[prop_name] = True

                elif prop_type == 'array':
                    example[prop_name] = []

            return example

        elif schema_type == 'array':
            return []

        else:
            return {"value": "example"}

    def _format_code(self, code: str) -> str:
        """
        Форматирование Python кода с помощью black и isort
        """
        try:
            # Форматирование black
            formatted = black.format_str(
                code,
                mode=black.FileMode(
                    line_length=100,
                    string_normalization=True
                )
            )

            # Сортировка импортов
            formatted = isort.code(formatted)

            return formatted
        except Exception as e:
            print(f"Ошибка форматирования кода: {e}")
            return code

    def _validate_syntax(self, code: str) -> bool:
        """Валидация синтаксиса Python кода"""
        try:
            ast.parse(code)
            return True
        except SyntaxError as e:
            raise SyntaxError(f"Сгенерированный код содержит синтаксические ошибки: {e}")

    # Вспомогательные методы
    def _should_generate_negative_test(self, endpoint: EndpointInfo) -> bool:
        """Определяет, нужно ли генерировать негативный тест"""
        if endpoint.method in ['POST', 'PUT', 'PATCH']:
            return True
        if '{' in endpoint.path:  # Операции с ID
            return True
        return False

    def _get_expected_status(self, endpoint: EndpointInfo, is_negative: bool) -> str:
        """Определяет ожидаемый статус код"""
        if is_negative:
            if endpoint.method == 'POST':
                return '400'  # Bad Request
            elif '{' in endpoint.path:
                return '404'  # Not Found
            else:
                return '400'
        else:
            # Ищем успешный статус
            for status in ['200', '201', '202', '204']:
                if status in endpoint.responses:
                    return status
            return '200'

    def _extract_path_params(self, path: str) -> Dict[str, str]:
        """Извлечение параметров пути"""
        import re
        params = re.findall(r'{(\w+)}', path)
        return {param: f"uuid_{param}_example" for param in params}

    def _extract_query_params(self, parameters: List[Dict]) -> Dict[str, Any]:
        """Извлечение query параметров"""
        query_params = {}
        for param in parameters:
            if param.get('in') == 'query':
                param_name = param.get('name')
                param_type = param.get('schema', {}).get('type', 'string')

                if param_type == 'integer':
                    query_params[param_name] = 1
                elif param_type == 'boolean':
                    query_params[param_name] = True
                else:
                    query_params[param_name] = "example"

        return query_params

    def _extract_response_schema(self, responses: Dict, status: str) -> Optional[Dict]:
        """Извлечение схемы ответа"""
        if status in responses:
            response = responses[status]
            content = response.get('content', {})
            if 'application/json' in content:
                return content['application/json'].get('schema')
        return None

    def _get_expected_error_message(self, endpoint: EndpointInfo, is_negative: bool) -> str:
        """Генерация ожидаемого сообщения об ошибке"""
        if not is_negative:
            return ""

        if endpoint.method == 'POST':
            return "validation error"
        elif '{' in endpoint.path:
            return "not found"
        else:
            return "error"

    def _generate_test_title(self, endpoint: EndpointInfo, is_negative: bool) -> str:
        """Генерация заголовка теста"""
        method_map = {
            'GET': 'Получение',
            'POST': 'Создание',
            'PUT': 'Обновление',
            'PATCH': 'Частичное обновление',
            'DELETE': 'Удаление'
        }

        action = method_map.get(endpoint.method, endpoint.method)

        if '{' in endpoint.path:
            resource = "ресурса"
        else:
            resource = "списка ресурсов"

        if is_negative:
            return f"{action} {resource} - негативный сценарий"
        else:
            return f"{action} {resource} - позитивный сценарий"

    def _determine_priority(self, endpoint: EndpointInfo, is_negative: bool) -> str:
        """Определение приоритета теста"""
        # Критические операции
        if endpoint.method in ['POST', 'DELETE']:
            return 'CRITICAL'
        # Операции изменения
        elif endpoint.method in ['PUT', 'PATCH']:
            return 'NORMAL'
        # Операции чтения и негативные тесты
        else:
            return 'LOW' if is_negative else 'NORMAL'

    def _extract_test_info_from_ast(self, tree: ast.AST) -> Dict:
        """Извлечение информации о тестах из AST"""
        # Реализация парсинга AST для извлечения структуры тестов
        test_info = {
            'imports': [],
            'classes': [],
            'methods': []
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                test_info['imports'].append(ast.unparse(node))
            elif isinstance(node, ast.ClassDef):
                class_info = {
                    'name': node.name,
                    'decorators': [ast.unparse(d) for d in node.decorator_list],
                    'methods': []
                }
                test_info['classes'].append(class_info)
            elif isinstance(node, ast.FunctionDef):
                if node.name.startswith('test_'):
                    method_info = {
                        'name': node.name,
                        'decorators': [ast.unparse(d) for d in node.decorator_list],
                        'steps': self._extract_steps_from_function(node)
                    }
                    if test_info['classes']:
                        test_info['classes'][-1]['methods'].append(method_info)

        return test_info

    def _extract_steps_from_function(self, func_node: ast.FunctionDef) -> List[Dict]:
        """Извлечение шагов из функции теста"""
        steps = []

        for node in ast.walk(func_node):
            if isinstance(node, ast.With):
                # Ищем allure.step вызовы
                for item in node.items:
                    if isinstance(item.context_expr, ast.Call):
                        func_name = ast.unparse(item.context_expr.func)
                        if 'allure.step' in func_name:
                            step_description = ''
                            if item.context_expr.args:
                                step_description = ast.unparse(item.context_expr.args[0])
                            steps.append({
                                'description': step_description,
                                'type': self._classify_step(step_description)
                            })

        return steps

    def _classify_step(self, description: str) -> str:
        """Классификация шага по паттерну AAA"""
        description_lower = description.lower()

        if 'arrange' in description_lower:
            return 'arrange'
        elif 'act' in description_lower:
            return 'act'
        elif 'assert' in description_lower:
            return 'assert'
        else:
            return 'unknown'

    def _generate_pytest_code(self, test_info: Dict) -> str:
        """Генерация pytest кода на основе извлеченной информации"""
        # Шаблон для pytest тестов
        pytest_template = """
import pytest
import requests
import allure
from typing import Dict, Any
{% if imports %}
{% for imp in imports %}
{{ imp }}
{% endfor %}
{% endif %}

BASE_URL = "{{ base_url }}"

@pytest.fixture
def auth_token() -> str:
    \"\"\"Фикстура для получения токена аутентификации\"\"\"
    # Реализация получения токена
    return "test_token"

@pytest.fixture
def api_headers(auth_token: str) -> Dict[str, str]:
    \"\"\"Фикстура для заголовков запроса\"\"\"
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }

{% for class_info in classes %}
@allure.feature("{{ class_info.name.replace('Tests', '') }}")
class Test{{ class_info.name }}:

    {% for method_info in class_info.methods %}
    @allure.title("{{ method_info.name.replace('test_', '').replace('_', ' ').title() }}")
    {% for decorator in method_info.decorators %}
    {% if 'allure.tag' not in decorator and 'allure.manual' not in decorator %}
    {{ decorator }}
    {% endif %}
    {% endfor %}
    def {{ method_info.name }}(self, api_headers: Dict[str, str]) -> None:
        \"\"\"Автоматизированная версия ручного теста\"\"\"
        {% for step in method_info.steps %}
        with allure.step("{{ step.description }}"):
            {% if step.type == 'arrange' %}
            # Подготовка данных
            test_data = {{ step.test_data|default('{}') }}
            {% elif step.type == 'act' %}
            # Выполнение запроса
            response = requests.{{ step.http_method|default('get') }}(
                f"{{ '{{BASE_URL}}' }}{{ step.endpoint|default('') }}",
                headers=api_headers,
                {% if step.http_method|lower in ['post', 'put', 'patch'] %}
                json=test_data,
                {% endif %}
                timeout=30
            )
            {% elif step.type == 'assert' %}
            # Проверки
            assert response.status_code == {{ step.expected_status|default(200) }}
            {% if step.expected_schema %}
            # Проверка схемы
            assert self._validate_response_schema(response.json(), {{ step.expected_schema }})
            {% endif %}
            {% else %}
            # {{ step.description }}
            pass
            {% endif %}
        {% endfor %}

    {% endfor %}

    def _validate_response_schema(self, response: Dict, schema: Dict) -> bool:
        \"\"\"Валидация схемы ответа\"\"\"
        # Реализация валидации
        return True
{% endfor %}
"""

        # Используем Jinja2 для рендеринга
        from jinja2 import Template
        template = Template(pytest_template)

        context = {
            'imports': test_info['imports'],
            'classes': test_info['classes'],
            'base_url': self.prompt_builder.base_url
        }

        return template.render(**context)

    def _tag_to_feature_name(self, tag: str) -> str:
        """Конвертация тега в имя фичи"""
        return {
            'vms': 'Virtual Machines',
            'disks': 'Disks',
            'flavors': 'Flavors'
        }.get(tag.lower(), tag.upper())

    def _tag_to_class_name(self, tag: str) -> str:
        """Конвертация тега в имя класса"""
        return self._tag_to_feature_name(tag).replace(' ', '') + 'ManualTests'

# Пример использования
if __name__ == "__main__":
    # Инициализация генератора
    generator = CodeGenerator("openapi_spec.yaml")

    # Генерация ручных тестов
    print("Генерация ручных тестов...")
    manual_tests = generator.generate_all_manual_tests("generated_tests/manual")

    # Генерация автотестов на основе ручных
    print("\nГенерация автотестов...")
    for tag in ['vms', 'disks', 'flavors']:
        manual_file = f"generated_tests/manual/test_{tag}.py"
        if Path(manual_file).exists():
            auto_tests = generator.generate_automated_tests(
                manual_file,
                "generated_tests/auto"
            )
            print(f"✓ Автотесты для {tag}: {list(auto_tests.keys())[0]}")
