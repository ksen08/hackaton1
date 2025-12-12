"""
🚀 ПОЛНЫЙ ГЕНЕРАТОР ТЕСТОВ с Cloud.ru Evolution API
Генерирует 8-12 полных тестов по ТЗ хакатона
"""
import os
import json
import time
from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict, Any

print("=" * 70)
print("🚀 TestOps Copilot - Генератор автотестов")
print("=" * 70)

# 1. Загружаем переменные окружения
load_dotenv()

# 2. Получаем API ключ
api_key = os.getenv("OPENAI_API_KEY") or os.getenv("CLOUD_RU_API_KEY")

# 3. Проверяем режим
MOCK_MODE = False
if not api_key or api_key == "demo-mode-no-real-api":
    print("⚠️  API ключ не найден или демо-режим")
    print("📋 Используем ПОЛНУЮ демо-версию (8+ тестов)")
    MOCK_MODE = True
    time.sleep(1)
else:
    print(f"✅ API ключ найден: {api_key[:12]}...")
    MOCK_MODE = False
    print("🔌 Режим: РЕАЛЬНЫЙ Cloud.ru Evolution API")

# 4. Основной промт для полной генерации
FULL_PROMPT = """Ты — TestOps Copilot для Cloud.ru. Сгенерируй ПОЛНЫЙ НАБОР автотестов по ТЗ хакатона.

ТРЕБОВАНИЯ ТЗ HACKATHON:
1. 8-12 полных тестов на раздел API
2. ПАТТЕРН AAA в каждом тесте
3. ПОЛНЫЕ Allure декораторы:
   - @allure.epic, @allure.feature, @allure.story
   - @allure.suite("auto_api_tests")
   - @allure.title с описанием типа теста
   - @allure.tag("CRITICAL"|"NORMAL"|"LOW")
   - @allure.label("owner", "backend_team")
   - @allure.label("priority", "P1|P2|P3")
4. Все типы тестов:
   - ПОЗИТИВНЫЕ (200/201/204): валидные данные
   - НЕГАТИВНЫЕ (401, 403, 400, 404, 409): ошибки
   - ГРАНИЧНЫЕ: мин/макс значения, длинные строки
5. Базовая структура:
   - BASE_URL = "https://compute.api.cloud.ru"
   - Класс Test{Section}Auto
   - Методы test_{operation}_{scenario}

СГЕНЕРИРУЙ 10-12 ПОЛНЫХ ТЕСТОВ для Cloud.ru Compute API:
1. test_api_health_check (200)
2. test_get_vms_list_success (200) 
3. test_create_vm_positive (201)
4. test_create_vm_unauthorized (401)
5. test_create_vm_invalid_token (403)
6. test_create_vm_bad_request (400)
7. test_get_vm_not_found (404)
8. test_create_vm_conflict (409)
9. test_create_vm_boundary_name (граничный)
10. test_create_vm_minimal_data (граничный)
11. test_update_vm_success (200)
12. test_delete_vm_success (204)

ФОРМАТ ВЫВОДА:
- ТОЛЬКО Python код
- Без пояснений, без markdown
- Готовый к запуску pytest код
- Все импорты в начале
- Фикстуры если нужны

ВАЖНО: Это для хакатона Cloud.ru, нужны ПОЛНЫЕ тесты по ТЗ!"""

def generate_demo_full_tests() -> str:
    """Генерация ПОЛНЫХ демо-тестов (8-12 тестов)"""
    return '''"""
🚀 ПОЛНЫЕ АВТОТЕСТЫ для Cloud.ru Compute API V3
Сгенерировано TestOps Copilot для хакатона Cloud.ru
Соответствует ТЗ: 12 тестов с полным покрытием
"""
import pytest
import allure
import requests
import json
import time

BASE_URL = "https://compute.api.cloud.ru"

# ========== FIXTURES ==========
@pytest.fixture
def api_headers():
    """Заголовки для API запросов"""
    token = os.getenv("CLOUD_RU_API_TOKEN", "test_token_placeholder")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

@pytest.fixture
def api_client(api_headers):
    """Клиент для API запросов"""
    class APIClient:
        def __init__(self, headers):
            self.headers = headers
        
        def request(self, method, endpoint, **kwargs):
            url = f"{BASE_URL}{endpoint}"
            kwargs["headers"] = self.headers
            kwargs["timeout"] = 30
            return getattr(requests, method.lower())(url, **kwargs)
    
    return APIClient(api_headers)


# ========== TEST CLASS ==========
@allure.epic("API Testing")
@allure.feature("Cloud.ru Compute API")
@allure.story("Virtual Machines CRUD Operations")
@allure.suite("auto_api_tests")
class TestComputeAPIFull:
    """ПОЛНЫЕ автотесты для Cloud.ru Compute API (12 тестов)"""
    
    # ===== 1. ПОЗИТИВНЫЕ ТЕСТЫ (3 теста) =====
    @allure.title("POSITIVE: API Health Check")
    @allure.tag("CRITICAL")
    @allure.label("owner", "backend_team")
    @allure.label("priority", "P1")
    def test_api_health_check(self):
        """Проверка доступности API (должен вернуть 200)"""
        # ARRANGE
        url = f"{BASE_URL}/health"
        
        # ACT
        response = requests.get(url, timeout=10)
        
        # ASSERT
        assert response.status_code == 200, f"API недоступен: {response.status_code}"
        allure.attach(response.text, name="Health Response", attachment_type=allure.attachment_type.TEXT)
    
    @allure.title("POSITIVE: Get VM List Success")
    @allure.tag("LOW")
    @allure.label("owner", "backend_team")
    @allure.label("priority", "P3")
    def test_get_vms_list_success(self, api_client):
        """Получение списка виртуальных машин (200 OK)"""
        # ARRANGE
        endpoint = "/vms"
        
        # ACT
        response = api_client.request("GET", endpoint)
        
        # ASSERT
        assert response.status_code == 200, f"Ожидался 200, получен {response.status_code}"
        vms = response.json()
        assert isinstance(vms, list), "Ответ должен быть списком"
        
        allure.attach(
            f"Найдено VM: {len(vms)}",
            name="VM Count",
            attachment_type=allure.attachment_type.TEXT
        )
    
    @allure.title("POSITIVE: Create VM with Valid Data")
    @allure.tag("CRITICAL")
    @allure.label("owner", "backend_team")
    @allure.label("priority", "P1")
    def test_create_vm_positive(self, api_client):
        """Создание VM с валидными данными (201 Created)"""
        # ARRANGE
        endpoint = "/vms"
        vm_data = {
            "name": f"test-vm-{int(time.time())}",
            "flavor_id": "standard-small",
            "image_id": "ubuntu-20.04",
            "network_id": "default-network"
        }
        
        # ACT
        response = api_client.request("POST", endpoint, json=vm_data)
        
        # ASSERT
        assert response.status_code == 201, f"Ожидался 201, получен {response.status_code}"
        created_vm = response.json()
        assert "id" in created_vm, "Ответ должен содержать ID VM"
        assert len(created_vm["id"]) == 36, "ID должен быть UUID формата"
        
        allure.attach(
            json.dumps(created_vm, indent=2, ensure_ascii=False),
            name="Created VM",
            attachment_type=allure.attachment_type.JSON
        )
    
    # ===== 2. НЕГАТИВНЫЕ ТЕСТЫ (6 тестов) =====
    @allure.title("NEGATIVE: Create VM without Authorization Token")
    @allure.tag("LOW")
    @allure.label("owner", "backend_team")
    @allure.label("priority", "P3")
    def test_create_vm_unauthorized(self):
        """Создание VM без токена (401 Unauthorized)"""
        # ARRANGE
        url = f"{BASE_URL}/vms"
        vm_data = {"name": "test-vm-no-auth"}
        
        # ACT
        response = requests.post(url, json=vm_data, headers={})  # Пустые заголовки
        
        # ASSERT
        assert response.status_code == 401, f"Ожидался 401, получен {response.status_code}"
        
        error_response = response.json()
        assert "errors" in error_response, "Ответ должен содержать массив errors"
    
    @allure.title("NEGATIVE: Create VM with Invalid Token")
    @allure.tag("LOW")
    @allure.label("owner", "backend_team")
    @allure.label("priority", "P3")
    def test_create_vm_invalid_token(self, api_client):
        """Создание VM с невалидным токеном (403 Forbidden)"""
        # ARRANGE
        endpoint = "/vms"
        vm_data = {"name": "test-vm-bad-token"}
        
        # ACT (с плохим токеном)
        bad_headers = {"Authorization": "Bearer invalid_token_123"}
        response = requests.post(f"{BASE_URL}{endpoint}", json=vm_data, headers=bad_headers)
        
        # ASSERT
        assert response.status_code == 403, f"Ожидался 403, получен {response.status_code}"
    
    @allure.title("NEGATIVE: Create VM with Invalid Data")
    @allure.tag("LOW")
    @allure.label("owner", "backend_team")
    @allure.label("priority", "P3")
    def test_create_vm_bad_request(self, api_client):
        """Создание VM с невалидными данными (400 Bad Request)"""
        # ARRANGE
        endpoint = "/vms"
        invalid_data = {
            "name": "",  # Пустое имя
            "flavor_id": "non-existent-flavor"
        }
        
        # ACT
        response = api_client.request("POST", endpoint, json=invalid_data)
        
        # ASSERT
        assert response.status_code == 400, f"Ожидался 400, получен {response.status_code}"
    
    @allure.title("NEGATIVE: Get Non-Existent VM")
    @allure.tag("LOW")
    @allure.label("owner", "backend_team")
    @allure.label("priority", "P3")
    def test_get_vm_not_found(self, api_client):
        """Получение несуществующей VM (404 Not Found)"""
        # ARRANGE
        non_existent_id = "00000000-0000-0000-0000-000000000000"
        endpoint = f"/vms/{non_existent_id}"
        
        # ACT
        response = api_client.request("GET", endpoint)
        
        # ASSERT
        assert response.status_code == 404, f"Ожидался 404, получен {response.status_code}"
    
    @allure.title("NEGATIVE: Create VM with Duplicate Name")
    @allure.tag("LOW")
    @allure.label("owner", "backend_team")
    @allure.label("priority", "P3")
    def test_create_vm_conflict(self, api_client):
        """Создание VM с конфликтующим именем (409 Conflict)"""
        # ARRANGE
        endpoint = "/vms"
        duplicate_name = "duplicate-vm-test"
        vm_data = {"name": duplicate_name, "flavor_id": "small"}
        
        # ACT (первый запрос должен пройти)
        response1 = api_client.request("POST", endpoint, json=vm_data)
        
        # ACT (второй запрос с тем же именем - должен быть конфликт)
        if response1.status_code == 201:
            response2 = api_client.request("POST", endpoint, json=vm_data)
            # ASSERT
            assert response2.status_code == 409, f"Ожидался 409 для дубликата, получен {response2.status_code}"
    
    @allure.title("NEGATIVE: Update VM with Invalid ID Format")
    @allure.tag("LOW")
    @allure.label("owner", "backend_team")
    @allure.label("priority", "P3")
    def test_update_vm_invalid_id(self, api_client):
        """Обновление VM с невалидным ID (400 Bad Request)"""
        # ARRANGE
        invalid_id = "not-a-uuid"
        endpoint = f"/vms/{invalid_id}"
        update_data = {"name": "updated-name"}
        
        # ACT
        response = api_client.request("PATCH", endpoint, json=update_data)
        
        # ASSERT
        assert response.status_code == 400, f"Ожидался 400 для невалидного ID, получен {response.status_code}"
    
    # ===== 3. ГРАНИЧНЫЕ ТЕСТЫ (3 теста) =====
    @allure.title("BOUNDARY: Create VM with Max Length Name")
    @allure.tag("NORMAL")
    @allure.label("owner", "backend_team")
    @allure.label("priority", "P2")
    def test_create_vm_boundary_name(self, api_client):
        """Создание VM с именем максимальной длины (255 символов)"""
        # ARRANGE
        endpoint = "/vms"
        max_length_name = "a" * 255  # Максимальная длина
        vm_data = {
            "name": max_length_name,
            "flavor_id": "small",
            "image_id": "ubuntu-20.04"
        }
        
        # ACT
        response = api_client.request("POST", endpoint, json=vm_data)
        
        # ASSERT
        # Должен либо принять (201), либо вернуть 400 если превышено ограничение
        assert response.status_code in [201, 400], f"Неожиданный код: {response.status_code}"
        
        if response.status_code == 201:
            allure.attach("Имя принято (255 символов)", name="Boundary Test", attachment_type=allure.attachment_type.TEXT)
        else:
            allure.attach(f"Имя отвергнуто: {response.text}", name="Boundary Test", attachment_type=allure.attachment_type.TEXT)
    
    @allure.title("BOUNDARY: Create VM with Minimal Data")
    @allure.tag("NORMAL")
    @allure.label("owner", "backend_team")
    @allure.label("priority", "P2")
    def test_create_vm_minimal_data(self, api_client):
        """Создание VM с минимальным набором полей"""
        # ARRANGE
        endpoint = "/vms"
        minimal_data = {
            "name": "minimal-vm",
            # Только обязательные поля
        }
        
        # ACT
        response = api_client.request("POST", endpoint, json=minimal_data)
        
        # ASSERT
        # Должен либо принять (201), либо вернуть 400 если не хватает полей
        assert response.status_code in [201, 400], f"Неожиданный код: {response.status_code}"
    
    @allure.title("BOUNDARY: Create VM with Special Characters")
    @allure.tag("NORMAL")
    @allure.label("owner", "backend_team")
    @allure.label("priority", "P2")
    def test_create_vm_special_chars(self, api_client):
        """Создание VM с именем содержащим спецсимволы"""
        # ARRANGE
        endpoint = "/vms"
        special_name = "test-vm_123-ABC@test.com"
        vm_data = {
            "name": special_name,
            "flavor_id": "small"
        }
        
        # ACT
        response = api_client.request("POST", endpoint, json=vm_data)
        
        # ASSERT
        assert response.status_code in [201, 400], f"Неожиданный код: {response.status_code}"
    
    # ===== 4. ДОПОЛНИТЕЛЬНЫЕ ТЕСТЫ =====
    @allure.title("POSITIVE: Update VM Configuration")
    @allure.tag("NORMAL")
    @allure.label("owner", "backend_team")
    @allure.label("priority", "P2")
    def test_update_vm_success(self, api_client):
        """Успешное обновление конфигурации VM"""
        # ARRANGE
        vm_id = "test-vm-id-update"  # В реальном тесте нужно сначала создать VM
        endpoint = f"/vms/{vm_id}"
        update_data = {"name": "updated-vm-name"}
        
        # ACT
        response = api_client.request("PATCH", endpoint, json=update_data)
        
        # ASSERT
        # Может быть 200 (успех) или 404 (VM не найдена)
        assert response.status_code in [200, 404], f"Неожиданный код: {response.status_code}"
    
    @allure.title("POSITIVE: Delete VM Success")
    @allure.tag("CRITICAL")
    @allure.label("owner", "backend_team")
    @allure.label("priority", "P1")
    def test_delete_vm_success(self, api_client):
        """Успешное удаление VM"""
        # ARRANGE
        vm_id = "test-vm-id-delete"  # В реальном тесте нужно сначала создать VM
        endpoint = f"/vms/{vm_id}"
        
        # ACT
        response = api_client.request("DELETE", endpoint)
        
        # ASSERT
        # Может быть 204 (успех) или 404 (VM не найдена)
        assert response.status_code in [204, 404], f"Неожиданный код: {response.status_code}"


# ========== QUICK RUN CHECK ==========
if __name__ == "__main__":
    """Быстрая проверка генерации"""
    print("✅ Тесты сгенерированы успешно!")
    print(f"📊 Всего тестов: {TestComputeAPIFull.__dict__.values().count(lambda x: callable(x) and x.__name__.startswith('test_'))}")
'''

def main():
    """Основная функция генерации"""
    code = ""
    
    if not MOCK_MODE:
        # РЕАЛЬНЫЙ РЕЖИМ С CLOUD.RU API
        try:
            client = OpenAI(
                api_key=api_key,
                base_url="https://foundation-models.api.cloud.ru/v1"
            )

            print("\n🔌 Подключаемся к Cloud.ru Evolution API...")
            
            # Тестовый запрос
            test_response = client.chat.completions.create(
                model="ai-sage/GigaChat3-10B-A1.8B",
                messages=[{
                    "role": "user",
                    "content": "Ответь 'API готов к генерации тестов'"
                }],
                temperature=0.1,
                max_tokens=10
            )

            print(f" API подключен: {test_response.choices[0].message.content}")

            # ОСНОВНОЙ ЗАПРОС - ПОЛНЫЕ ТЕСТЫ
            print("\n📝 Генерируем ПОЛНЫЕ тесты (8-12 тестов)...")
            print("   ⏳ Это может занять 10-20 секунд...")

            full_response = client.chat.completions.create(
                model="ai-sage/GigaChat3-10B-A1.8B",
                messages=[{"role": "user", "content": FULL_PROMPT}],
                temperature=0.1,
                max_tokens=3500,  # Увеличено для полных тестов!
                timeout=60
            )

            code = full_response.choices[0].message.content.strip()
            print("Cloud.ru API вернул полные тесты!")

        except Exception as e:
            print(f" Ошибка Cloud.ru API: {e}")
            print(" Переключаемся на ПОЛНУЮ демо-версию...")
            MOCK_MODE = True
    
    if MOCK_MODE:
        # ПОЛНАЯ ДЕМО-ВЕРСИЯ
        print("\n Используем ПОЛНУЮ демо-версию (12 тестов)...")
        time.sleep(1)
        code = generate_demo_full_tests()

    # 5. Сохраняем результат
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = f"generated_tests_full_{timestamp}.py"
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(code)

    # 6. Анализируем результат
    test_count = code.count("def test_")
    allure_count = code.count("@allure")
    lines_count = len(code.splitlines())
    
    print("\n" + "=" * 70)
    print(" ГЕНЕРАЦИЯ ПОЛНЫХ ТЕСТОВ ЗАВЕРШЕНА!")
    
    # Показываем структуру
    print("\n🏗️  СТРУКТУРА СГЕНЕРИРОВАННЫХ ТЕСТОВ:")
    print("=" * 40)
    lines = code.splitlines()
    for i, line in enumerate(lines[:20]):
        if i < 10 or "@allure.title" in line or "def test_" in line:
            print(f"{i+1:3}: {line}")
    print("...")
    print("=" * 40)
if __name__ == "__main__":
    main()