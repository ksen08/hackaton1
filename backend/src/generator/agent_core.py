"""
Упрощённый AgentCore для интеграции с Flask бэкендом
"""

import os
import json
import tempfile
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

from models.schemas import AgentRequest, AgentResponse


class AgentCore:
    """
    Главный генератор тестов.
    Интегрирует простой генератор и LLM.
    """

    def __init__(self, llm_config: dict = None):
        self.llm_config = llm_config or {}

        # Пытаемся загрузить LLM клиент
        self.llm_client = None
        try:
            from .llm_client import call_llm, call_llm_sync
            self.call_llm = call_llm
            self.call_llm_sync = call_llm_sync
            self.llm_client = True
            print("✅ LLM клиент загружен")
        except ImportError as e:
            print(f"⚠️  LLM клиент не доступен: {e}")
            self.llm_client = False

        # Загружаем простой генератор
        try:
            from .pytest_generator import PytestGenerator
            self.pytest_generator = PytestGenerator()
            print("✅ PytestGenerator загружен")
        except ImportError as e:
            print(f"⚠️  PytestGenerator не доступен: {e}")
            self.pytest_generator = None

        # Загружаем промпты
        self.prompts = {}
        self._load_prompts()

    def _load_prompts(self):
        """Загрузка промптов из файлов"""
        prompts_dir = Path(__file__).parent / "prompts"

        prompt_files = {
            "manual": "prompt_for_manual_tests.md",
            "auto": "prompt_for_autotests.md"
        }

        for key, filename in prompt_files.items():
            filepath = prompts_dir / filename
            if filepath.exists():
                with open(filepath, "r", encoding="utf-8") as f:
                    self.prompts[key] = f.read()
                print(f"✅ Загружен промпт: {filename}")
            else:
                self.prompts[key] = f"# {key} prompt placeholder"
                print(f"⚠️  Промпт {filename} не найден, используем заглушку")

    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        Основной метод обработки запроса.

        Args:
            request: Запрос на генерацию тестов

        Returns:
            AgentResponse: Сгенерированный код или ошибки
        """
        try:
            print(f"🔧 Обрабатываю запрос типа: {request.type}")

            # Вариант 1: Есть allure_code → конвертируем в автотесты
            if request.allure_code and self.pytest_generator:
                print("📋 Конвертирую ручные тесты в автотесты...")
                return await self._convert_to_autotests(request)

            # Вариант 2: Нет allure_code → генерируем ручные тесты через LLM
            elif self.llm_client:
                print("🧠 Генерирую тесты через LLM...")
                return await self._generate_with_llm(request)

            # Вариант 3: LLM не доступен → возвращаем заглушку
            else:
                print("⚠️  LLM не доступен, возвращаю заглушку")
                return self._generate_stub(request)

        except Exception as e:
            print(f"❌ Ошибка в AgentCore.process: {e}")
            return AgentResponse(
                code="",
                errors=[f"Ошибка генерации: {str(e)}"]
            )

    async def _convert_to_autotests(self, request: AgentRequest) -> AgentResponse:
        """Конвертация ручных тестов в автотесты"""
        try:
            # Сохраняем временно
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".py", delete=False) as tmp:
                tmp.write(request.allure_code)
                temp_path = tmp.name

            try:
                # Генерируем автотесты
                result = self.pytest_generator.convert_manual_to_pytest(
                    manual_file=temp_path,
                    output_dir=""  # В памяти, не сохраняем
                )

                # Берём первый файл
                if result:
                    auto_code = list(result.values())[0]

                    # Форматируем код
                    formatted_code = self._format_code(auto_code)

                    return AgentResponse(
                        code=formatted_code,
                        errors=[]
                    )
                else:
                    return AgentResponse(
                        code="",
                        errors=["Не удалось сгенерировать автотесты"]
                    )

            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

        except Exception as e:
            return AgentResponse(
                code="",
                errors=[f"Ошибка конвертации: {str(e)}"]
            )

    async def _generate_with_llm(self, request: AgentRequest) -> AgentResponse:
        """Генерация тестов через LLM"""
        try:
            # Выбираем промпт
            prompt_template = self.prompts.get("manual", "")

            # Заполняем промпт
            full_prompt = prompt_template.replace(
                "{spec}",
                json.dumps(request.spec, ensure_ascii=False, indent=2)
            )

            # Подготавливаем сообщения для LLM
            messages = [
                {
                    "role": "system",
                    "content": "Ты — QA инженер, генерирующий тесты в формате Allure TestOps as Code."
                },
                {
                    "role": "user",
                    "content": full_prompt
                }
            ]

            # Вызываем LLM
            raw_code = await self.call_llm(
                messages=messages,
                temperature=0.1,
                max_tokens=4000
            )

            # Форматируем код
            formatted_code = self._format_code(raw_code)

            # Проверяем синтаксис
            self._validate_syntax(formatted_code)

            return AgentResponse(
                code=formatted_code,
                errors=[]
            )

        except Exception as e:
            print(f"❌ Ошибка LLM: {e}")
            # Fallback: генерируем заглушку
            return self._generate_stub(request)

    def _generate_stub(self, request: AgentRequest) -> AgentResponse:
        """Генерация заглушки тестов"""
        stub_code = f'''"""
Заглушка тестов для типа: {request.type}
Спецификация: {len(json.dumps(request.spec))} символов
"""
import allure
import pytest

@allure.feature("Stub Tests")
@allure.suite("manual_tests")
class TestStub:
    """Тесты-заглушки (LLM недоступен)"""

    @allure.title("Пример позитивного теста")
    @allure.tag("NORMAL")
    @allure.label("priority", "P2")
    def test_example_positive(self):
        """Позитивный тест-заглушка"""
        with allure.step("Подготовка данных"):
            # TODO: Подготовить данные

        with allure.step("Отправка запроса"):
            # TODO: Отправить запрос к API

        with allure.step("Проверка ответа"):
            # TODO: Проверить статус код и данные

    @allure.title("Пример негативного теста")
    @allure.tag("LOW")
    def test_example_negative(self):
        """Негативный тест-заглушка"""
        with allure.step("Подготовка невалидных данных"):
            # TODO: Подготовить невалидные данные

        with allure.step("Отправка запроса с ошибкой"):
            # TODO: Отправить запрос с невалидными данными

        with allure.step("Проверка ошибки"):
            # TODO: Проверить код ошибки
'''

        return AgentResponse(
            code=stub_code,
            errors=["⚠️  LLM недоступен, использованы тесты-заглушки"]
        )

    def _format_code(self, code: str) -> str:
        """Простое форматирование кода"""
        # Убираем лишние пробелы в начале строк
        lines = [line.rstrip() for line in code.split('\n')]
        # Убираем пустые строки в начале
        while lines and not lines[0].strip():
            lines.pop(0)
        # Убираем пустые строки в конце
        while lines and not lines[-1].strip():
            lines.pop()

        return '\n'.join(lines)

    def _validate_syntax(self, code: str):
        """Простая валидация синтаксиса"""
        try:
            import ast
            ast.parse(code)
        except SyntaxError as e:
            print(f"⚠️  Синтаксическая ошибка в сгенерированном коде: {e}")
            # Пока не падаем, только логируем

    def generate(self, spec: dict, test_type: str, options: dict = None) -> str:
        """
        Синхронный интерфейс для DI системы.

        Args:
            spec: OpenAPI спецификация
            test_type: Тип тестов ("manual_api", "auto_api", etc.)
            options: Дополнительные опции

        Returns:
            str: Сгенерированный код тестов
        """
        # Создаём запрос
        request = AgentRequest(
            type="api",
            spec=spec,
            allure_code=None  # Пока без ручных тестов
        )

        # Запускаем асинхронно
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(self.process(request))
            return response.code
        finally:
            loop.close()