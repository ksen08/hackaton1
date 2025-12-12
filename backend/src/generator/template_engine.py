"""
Template Engine для генерации тестов на основе Jinja2 шаблонов
Соответствует структуре проекта с templates/manual/, templates/auto/, templates/base/
"""
import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound, TemplateSyntaxError


class TemplateEngine:
    """Движок шаблонов для генерации тест-кейсов и автотестов"""

    def __init__(self, base_templates_dir: Optional[str] = None):
        """
        Инициализация TemplateEngine

        Args:
            base_templates_dir: Базовая директория с шаблонами
        """
        # Определяем пути к шаблонам
        if base_templates_dir is None:
            # Стандартный путь: backend/generator/templates/
            base_dir = Path(__file__).parent
            self.templates_dir = base_dir / "templates"
        else:
            self.templates_dir = Path(base_templates_dir)

        # Проверяем существование директории
        if not self.templates_dir.exists():
            raise FileNotFoundError(f"Директория с шаблонами не найдена: {self.templates_dir}")

        # Создаем поддиректории, если их нет
        for subdir in ["manual", "auto", "base"]:
            (self.templates_dir / subdir).mkdir(parents=True, exist_ok=True)

        # Инициализируем Jinja2 environment
        self._init_jinja_environment()

        # Кэш загруженных шаблонов
        self._template_cache: Dict[str, Template] = {}

        # Создаем стандартные шаблоны при необходимости
        self._ensure_default_templates()

    def _init_jinja_environment(self):
        """Инициализация Jinja2 environment с пользовательскими фильтрами"""
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
            autoescape=False,
            extensions=['jinja2.ext.loopcontrols']
        )

        # Регистрируем пользовательские фильтры
        self.env.filters.update({
            'to_snake_case': self._to_snake_case,
            'snake_case': self._to_snake_case,  # Псевдоним
            'to_json': self._to_json,           # Новый
            'to_yaml': self._to_yaml,           # Новый
            'to_camel_case': self._to_camel_case,
            'capitalize_words': self._capitalize_words,
            'escape_quotes': self._escape_quotes,
            'indent': self._indent,
            'python_type': self._python_type,
            'format_example': self._format_example,
        })

        # Регистрируем пользовательские функции
        self.env.globals.update({
            'now': self._now_timestamp,
            'uuid': self._generate_uuid,
            'is_list': lambda x: isinstance(x, list),
            'is_dict': lambda x: isinstance(x, dict),
        })

    def _ensure_default_templates(self):
        """Создание стандартных шаблонов, если их нет"""
        default_templates = {
            "manual/test_class.py.j2": '''"""
Ручные тест-кейсы для {{ feature_name }}
{% if description %}
{{ description }}
{% endif %}
"""
import allure
import pytest
from typing import Dict, Any, Optional

{% for import_item in imports %}
{{ import_item }}
{% endfor %}

@allure.manual
@allure.label("owner", "{{ owner|default('test_team') }}")
@allure.feature("{{ feature_name }}")
@allure.story("{{ story|default('API Testing') }}")
@allure.suite("{{ suite|default('manual_tests') }}")
@pytest.mark.manual
class {{ class_name }}:
    """{{ class_description|default('') }}"""

    {% for test_case in test_cases %}
    @allure.title("{{ test_case.title }}")
    @allure.link("{{ test_case.jira_link|default('#') }}", name="{{ test_case.jira_name|default('JIRA') }}")
    @allure.tag("{{ test_case.priority_tag|default('NORMAL') }}")
    @allure.label("priority", "{{ test_case.priority|default('P2') }}")
    @allure.description("{{ test_case.description|default('') }}")
    def {{ test_case.method_name }}(self) -> None:
        """
        {{ test_case.description|default('') }}

        Шаги теста:
        {% for step in test_case.steps %}
        {{ loop.index }}. {{ step.name }}
        {% endfor %}
        """
        {% for step in test_case.steps %}
        with allure.step("{{ step.name }}"):
            {{ step.action|default('# TODO: Выполнить действие') }}
            {% if step.expected_result %}
            # Ожидаемый результат: {{ step.expected_result }}
            {% endif %}
        {% endfor %}
        {% if test_case.attachments %}
        {% for attachment in test_case.attachments %}
        allure.attach.file(
            "{{ attachment.path }}",
            name="{{ attachment.name }}",
            attachment_type=allure.attachment_type.{{ attachment.type|default('PNG') }}
        )
        {% endfor %}
        {% endif %}

    {% endfor %}''',

            "manual/test_method.py.j2": '''@allure.title("{{ title }}")
@allure.tag("{{ priority_tag|default('NORMAL') }}")
@allure.label("priority", "{{ priority|default('P2') }}")
@allure.description("{{ description|default('') }}")
def {{ method_name }}(self{% if params %}, {{ params|join(', ') }}{% endif %}) -> None:
    """
    {{ description|default('') }}

    Шаги теста:
    {% for step in steps %}
    {{ loop.index }}. {{ step.name }}
    {% endfor %}
    """
    {% for step in steps %}
    with allure.step("{{ step.name }}"):
        {{ step.action|default('pass') }}
        {% if step.expected_result %}
        # Ожидаемый результат: {{ step.expected_result }}
        {% endif %}
    {% endfor %}''',

            "auto/pytest_test.py.j2": '''"""
Автоматизированные тесты для {{ endpoint_name }}
Сгенерировано на основе OpenAPI спецификации
"""
import pytest
import allure
import requests
from typing import Dict, Any, List, Optional
import json
import time
{% for import_item in imports %}
{{ import_item }}
{% endfor %}

@allure.feature("{{ feature }}")
@allure.story("{{ story|default('API Testing') }}")
class {{ class_name }}:
    """{{ class_description|default('') }}"""

    {% for fixture in fixtures %}
    {{ fixture }}

    {% endfor %}
    {% for test in tests %}
    @allure.title("{{ test.title }}")
    @allure.tag("{{ test.priority|default('NORMAL') }}")
    @allure.severity(allure.severity_level.{{ test.severity|default('NORMAL') }})
    def {{ test.method_name }}(self{{ test.fixture_params }}) -> None:
        """{{ test.description|default('') }}"""

        # ===== ARRANGE =====
        {% for arrange_line in test.arrange %}
        {{ arrange_line }}
        {% endfor %}

        # ===== ACT =====
        {% for act_line in test.act %}
        {{ act_line }}
        {% endfor %}

        # ===== ASSERT =====
        {% for assert_line in test.assertions %}
        {{ assert_line }}
        {% endfor %}
        {% if test.allure_attach %}
        # Дополнительные вложения Allure
        {% for attach in test.allure_attach %}
        allure.attach(
            {{ attach.content }},
            name="{{ attach.name }}",
            attachment_type=allure.attachment_type.{{ attach.type|default('TEXT') }}
        )
        {% endfor %}
        {% endif %}

    {% endfor %}'''
        }

        # Создаем стандартные шаблоны
        for template_path, content in default_templates.items():
            full_path = self.templates_dir / template_path
            if not full_path.exists():
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content, encoding='utf-8')
                print(f"Создан шаблон: {template_path}")

    def load_template(self, template_name: str) -> Template:
        """
        Загрузка шаблона с кэшированием

        Args:
            template_name: Имя шаблона (относительный путь)

        Returns:
            Загруженный шаблон
        """
        if template_name in self._template_cache:
            return self._template_cache[template_name]

        try:
            template = self.env.get_template(template_name)
            self._template_cache[template_name] = template
            return template
        except TemplateNotFound as e:
            raise FileNotFoundError(
                f"Шаблон '{template_name}' не найден в {self.templates_dir}. "
                f"Доступные шаблоны: {list(self.env.list_templates())}"
            )
        except TemplateSyntaxError as e:
            raise SyntaxError(f"Синтаксическая ошибка в шаблоне '{template_name}': {e}")

    def render_template(
            self,
            template_name: str,
            context: Dict[str, Any],
            output_path: Optional[str] = None
    ) -> Union[str, Path]:
        """
        Рендеринг шаблона с сохранением в файл

        Args:
            template_name: Имя шаблона
            context: Контекст для рендеринга
            output_path: Путь для сохранения результата (если None, возвращается строка)

        Returns:
            Отрендеренный текст или путь к файлу
        """
        try:
            template = self.load_template(template_name)
            rendered = template.render(**context)

            if output_path is not None:
                output_file = Path(output_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text(rendered, encoding='utf-8')
                return output_file

            return rendered

        except Exception as e:
            raise RuntimeError(f"Ошибка при рендеринге шаблона '{template_name}': {str(e)}")

    def generate_manual_test_case(
            self,
            test_data: Dict[str, Any],
            output_dir: Optional[str] = None
    ) -> Union[str, Path]:
        """
        Генерация ручного тест-кейса

        Args:
            test_data: Данные тест-кейса
            output_dir: Директория для сохранения

        Returns:
            Сгенерированный код или путь к файлу
        """
        # Подготавливаем контекст
        context = {
            'owner': test_data.get('owner', 'test_team'),
            'feature_name': test_data.get('feature', 'Unknown Feature'),
            'class_name': self._generate_class_name(test_data.get('feature')),
            'story': test_data.get('story', 'API Testing'),
            'suite': test_data.get('suite', 'manual_tests'),
            'test_cases': test_data.get('test_cases', []),
            'imports': test_data.get('imports', [
                'import pytest',
                'import allure',
                'from typing import Dict, Any'
            ])
        }

        # Добавляем недостающие поля в тест-кейсы
        for test_case in context['test_cases']:
            if 'method_name' not in test_case:
                test_case['method_name'] = self._to_snake_case(test_case.get('title', 'test_case'))

            if 'steps' not in test_case:
                test_case['steps'] = [{'name': 'TODO: Добавить шаги теста'}]

        # Рендерим шаблон
        if output_dir:
            output_file = Path(output_dir) / f"test_{context['class_name'].lower()}.py"
            return self.render_template(
                "manual/test_class.py.j2",
                context,
                str(output_file)
            )
        else:
            return self.render_template("manual/test_class.py.j2", context)

    def generate_automated_test(
            self,
            api_spec: Dict[str, Any],
            endpoint_data: Dict[str, Any],
            output_dir: Optional[str] = None
    ) -> Union[str, Path]:
        """
        Генерация автоматизированного теста на основе OpenAPI

        Args:
            api_spec: OpenAPI спецификация
            endpoint_data: Данные эндпоинта
            output_dir: Директория для сохранения

        Returns:
            Сгенерированный код или путь к файлу
        """
        endpoint = endpoint_data.get('endpoint', {})
        method = endpoint_data.get('method', 'GET').upper()

        # Формируем контекст для теста
        context = {
            'feature': endpoint_data.get('feature', 'API'),
            'endpoint_name': endpoint.get('summary', 'Unknown Endpoint'),
            'class_name': self._generate_test_class_name(endpoint),
            'class_description': endpoint.get('description', ''),
            'imports': [
                'import pytest',
                'import allure',
                'import requests',
                'import json',
                'from typing import Dict, Any'
            ],
            'fixtures': self._generate_fixtures(api_spec, endpoint_data),
            'tests': self._generate_test_methods(api_spec, endpoint_data)
        }

        # Рендерим шаблон
        template_name = "auto/pytest_test.py.j2"

        if output_dir:
            filename = f"test_{self._to_snake_case(context['class_name'])}.py"
            output_file = Path(output_dir) / filename
            return self.render_template(template_name, context, str(output_file))
        else:
            return self.render_template(template_name, context)

    def _generate_test_class_name(self, endpoint: Dict[str, Any]) -> str:
        """Генерация имени класса теста"""
        summary = endpoint.get('summary', 'Unknown')
        # Убираем спецсимволы и делаем CamelCase
        name = re.sub(r'[^\w\s]', '', summary)
        words = name.split()
        return ''.join(word.capitalize() for word in words) + 'Tests'

    def _generate_class_name(self, feature_name: str) -> str:
        """Генерация имени класса для ручных тестов"""
        name = re.sub(r'[^\w\s]', '', feature_name)
        words = name.split()
        return ''.join(word.capitalize() for word in words) + 'ManualTests'

    def _generate_fixtures(self, api_spec: Dict[str, Any], endpoint_data: Dict[str, Any]) -> List[str]:
        """Генерация фикстур pytest"""
        fixtures = []

        # Базовая фикстура для API клиента
        fixtures.append('''@pytest.fixture(scope="session")
def api_client():
    """Клиент для работы с API"""
    import requests
    session = requests.Session()

    # Настройка заголовков
    session.headers.update({
        "Authorization": "Bearer YOUR_TOKEN_HERE",
        "Content-Type": "application/json",
        "Accept": "application/json"
    })

    # Настройка базового URL
    session.base_url = "https://compute.api.cloud.ru"

    return session''')

        # Фикстура для тестовых данных
        if endpoint_data.get('method') in ['POST', 'PUT', 'PATCH']:
            fixtures.append('''@pytest.fixture
def test_data():
    """Тестовые данные для запроса"""
    return {
        "name": "test_vm_" + str(hash(str(time.time())))[:8],
        "cpu": 2,
        "memory": 4096,
        "disk": 20
    }''')

        return fixtures

    def _generate_test_methods(self, api_spec: Dict[str, Any], endpoint_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Генерация тестовых методов"""
        endpoint = endpoint_data.get('endpoint', {})
        method = endpoint_data.get('method', 'GET').upper()
        path = endpoint_data.get('path', '')

        test_methods = []

        # Основной тест для успешного сценария
        test_method = {
            'title': f"Test {method} {path} - Success",
            'method_name': f"test_{method.lower()}_{self._to_snake_case(path)}",
            'description': endpoint.get('description', f'Test {method} {path}'),
            'priority': 'NORMAL',
            'severity': 'NORMAL',
            'fixture_params': ', api_client, test_data' if method in ['POST', 'PUT', 'PATCH'] else ', api_client',
            'arrange': self._generate_arrange_lines(method, path, endpoint),
            'act': self._generate_act_lines(method, path),
            'assertions': self._generate_assertions(endpoint),
            'allure_attach': self._generate_allure_attachments()
        }

        test_methods.append(test_method)

        # Тест для ошибок (если есть в спецификации)
        if 'responses' in endpoint and '4' in str(endpoint.get('responses', {})):
            error_test = test_method.copy()
            error_test['title'] = f"Test {method} {path} - Error Handling"
            error_test['method_name'] = f"test_{method.lower()}_{self._to_snake_case(path)}_error"
            error_test['description'] = f"Test error handling for {method} {path}"
            error_test['arrange'] = ['# Используем невалидные данные для теста ошибки']
            error_test['assertions'] = [
                'assert response.status_code in [400, 401, 403, 404, 500], f"Expected error status, got {response.status_code}"',
                'assert "error" in response.json() or "message" in response.json(), "Error response should contain error details"'
            ]
            test_methods.append(error_test)

        return test_methods

    def _generate_arrange_lines(self, method: str, path: str, endpoint: Dict[str, Any]) -> List[str]:
        """Генерация строк для блока Arrange"""
        lines = []

        if method in ['POST', 'PUT', 'PATCH']:
            lines.append(f'url = f"{{api_client.base_url}}{path}"')
            lines.append('# Подготовка данных запроса')
            lines.append('request_data = test_data.copy()')

            # Добавляем валидацию обязательных полей
            if 'requestBody' in endpoint:
                lines.append('# Валидация обязательных полей')
                lines.append('required_fields = ["name", "cpu", "memory"]')
                lines.append('for field in required_fields:')
                lines.append('    assert field in request_data, f"Missing required field: {field}"')
        else:
            lines.append(f'url = f"{{api_client.base_url}}{path}"')

        return lines

    def _generate_act_lines(self, method: str, path: str) -> List[str]:
        """Генерация строк для блока Act"""
        lines = []

        if method == 'GET':
            lines.append('response = api_client.get(url)')
        elif method == 'POST':
            lines.append('response = api_client.post(url, json=request_data)')
        elif method == 'PUT':
            lines.append('response = api_client.put(url, json=request_data)')
        elif method == 'PATCH':
            lines.append('response = api_client.patch(url, json=request_data)')
        elif method == 'DELETE':
            lines.append('response = api_client.delete(url)')
        else:
            lines.append(f'# TODO: Implement {method} request')

        lines.append('response_data = response.json() if response.content else {}')
        return lines

    def _generate_assertions(self, endpoint: Dict[str, Any]) -> List[str]:
        """Генерация проверок для блока Assert"""
        assertions = []

        # Проверка статуса
        if 'responses' in endpoint:
            for status_code, response_spec in endpoint['responses'].items():
                if status_code.startswith('2'):
                    assertions.append(
                        f'assert response.status_code == {status_code}, f"Expected {status_code}, got {{response.status_code}}"')
                    break
            else:
                assertions.append('assert response.status_code == 200, f"Expected 200, got {response.status_code}"')
        else:
            assertions.append(
                'assert response.status_code in [200, 201, 204], f"Unexpected status: {response.status_code}"')

        # Проверка структуры ответа
        assertions.append('assert isinstance(response_data, (dict, list)), "Response should be JSON object or array"')

        # Проверка обязательных полей в ответе (если есть схема)
        if 'responses' in endpoint:
            for status_code, response_spec in endpoint['responses'].items():
                if status_code.startswith('2') and 'content' in response_spec:
                    content = response_spec['content']
                    if 'application/json' in content and 'schema' in content['application/json']:
                        assertions.append('# TODO: Add schema validation based on OpenAPI spec')

        return assertions

    def _generate_allure_attachments(self) -> List[Dict[str, Any]]:
        """Генерация вложений для Allure"""
        return [
            {
                'name': 'Request Details',
                'content': 'json.dumps({"url": url, "method": method, "data": request_data if method in ["POST", "PUT", "PATCH"] else {}}, indent=2)',
                'type': 'JSON'
            },
            {
                'name': 'Response Details',
                'content': 'json.dumps({"status": response.status_code, "headers": dict(response.headers), "body": response_data}, indent=2)',
                'type': 'JSON'
            }
        ]

    # ========== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ==========

    @staticmethod
    def _to_snake_case(text: str) -> str:
        """Конвертация в snake_case"""
        if not text:
            return ''

        # Убираем спецсимволы
        text = re.sub(r'[^\w\s]', ' ', text)
        # Заменяем пробелы и заглавные буквы на подчеркивания
        text = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', text)
        text = re.sub(r'[-\s]+', '_', text)
        return text.lower().strip('_')

    @staticmethod
    def _to_camel_case(text: str) -> str:
        """Конвертация в CamelCase"""
        if not text:
            return ''

        words = re.split(r'[_\s-]+', text)
        return ''.join(word.capitalize() for word in words)

    @staticmethod
    def _capitalize_words(text: str) -> str:
        """Каждое слово с заглавной буквы"""
        return ' '.join(word.capitalize() for word in text.split())

    @staticmethod
    def _escape_quotes(text: str) -> str:
        """Экранирование кавычек для Python строк"""
        if not text:
            return ''
        return text.replace('"', '\\"').replace("'", "\\'")

    @staticmethod
    def _indent(text: str, spaces: int = 4) -> str:
        """Добавление отступов"""
        if not text:
            return ''
        indent_str = ' ' * spaces
        return '\n'.join(indent_str + line for line in text.split('\n'))

    @staticmethod
    def _python_type(openapi_type: str) -> str:
        """Конвертация OpenAPI типов в Python типы"""
        type_map = {
            'string': 'str',
            'integer': 'int',
            'number': 'float',
            'boolean': 'bool',
            'array': 'List',
            'object': 'Dict[str, Any]'
        }
        return type_map.get(openapi_type.lower(), 'Any')

    @staticmethod
    def _format_example(example: Any) -> str:
        """Форматирование примера значения для Python кода"""
        if isinstance(example, dict):
            return json.dumps(example, indent=2, ensure_ascii=False)
        elif isinstance(example, list):
            return json.dumps(example, indent=2, ensure_ascii=False)
        elif isinstance(example, str):
            return f"'{example}'"
        else:
            return str(example)

    @staticmethod
    def _now_timestamp() -> str:
        """Текущая временная метка"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _generate_uuid() -> str:
        """Генерация UUID"""
        import uuid
        return str(uuid.uuid4())

    @staticmethod
    def _to_json(data: Any) -> str:
        """Конвертация в JSON строку для Jinja2 шаблона"""
        import json
        try:
            if isinstance(data, dict) or isinstance(data, list):
                return json.dumps(data, indent=2, ensure_ascii=False)
            else:
                return json.dumps(str(data), ensure_ascii=False)
        except:
            return str(data)

    @staticmethod
    def _to_yaml(data: Any) -> str:
        """Конвертация в YAML строку (упрощенная версия)"""
        import yaml
        try:
            return yaml.dump(data, default_flow_style=False, allow_unicode=True)
        except ImportError:
            # Если yaml не установлен, используем JSON
            import json
            return json.dumps(data, indent=2, ensure_ascii=False)
        except:
            return str(data)



# Экспорт синглтон инстанса
template_engine = TemplateEngine()
