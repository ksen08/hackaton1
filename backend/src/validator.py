# backend/src/validator.py
import ast
import re
from typing import Dict, List

class AllureTestValidator:
    def validate_code(self, code: str) -> Dict:
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Синтаксис
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(f"Синтаксическая ошибка: {e}")

        # 2. Обязательные декораторы
        required = [
            "@allure.feature",
            "@allure.label(\"owner\"",
            "@allure.title",
            "@allure.tag",
        ]
        for dec in required:
            if dec not in code:
                errors.append(f"Отсутствует: {dec}")

        # 3. Паттерн AAA
        if not re.search(r"allure\.step\([\"']Arrange", code, re.IGNORECASE):
            warnings.append("Нет шага Arrange")
        if not re.search(r"allure\.step\([\"']Act", code, re.IGNORECASE):
            warnings.append("Нет шага Act")
        if not re.search(r"allure\.step\([\"']Assert", code, re.IGNORECASE):
            warnings.append("Нет шага Assert")

        # 4. Токен
        if "token" not in code.lower() and "bearer" not in code.lower():
            warnings.append("Нет упоминания токена аутентификации")

        # 5. @allure.manual (для ручных)
        if "@allure.manual" not in code:
            warnings.append("Нет метки @allure.manual")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "score": 100 - len(errors) * 20 - len(warnings) * 5
        }
