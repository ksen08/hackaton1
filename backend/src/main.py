from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import sys
import os
from pathlib import Path

# ===== СОЗДАЕМ FastAPI ПРИЛОЖЕНИЕ =====
app = FastAPI(
    title="TestOps Copilot API",
    description="API для генерации тестов из OpenAPI спецификаций",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ===== CORS ДЛЯ РЕАКТА =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== МОДЕЛИ ДАННЫХ =====
class AgentRequest(BaseModel):
    spec: Dict[str, Any]
    test_type: str  # "manual_ui" или "auto_api"
    requirements: Optional[str] = None
    options: Optional[Dict[str, Any]] = None

class AgentResponse(BaseModel):
    status: str
    code_text: str
    metadata: Dict[str, Any]

# ===== AGENT CORE (РЕАЛЬНЫЙ ИЛИ ЗАГЛУШКА) =====
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from backend.src.generator.agent_core import AgentCore
    print("✅ Импортирован реальный AgentCore")
    agent = AgentCore()
except ImportError:
    print("⚠️  Используем улучшенную заглушку AgentCore")
    
    class AgentCore:
        async def process(self, request: AgentRequest) -> AgentResponse:
            """Генерация тестов - улучшенная заглушка"""
            import json
            
            # Определяем тип тестов из фронтенда
            test_type_name = "UI тесты" if request.test_type == "manual_ui" else "API тесты"
            
            # Генерируем код в зависимости от типа
            if request.test_type == "manual_ui":
                test_code = f'''"""
Ручные UI тесты для: {request.requirements or 'UI приложения'}
Сгенерировано TestOps Copilot
"""
import allure

@allure.epic("UI Testing")
@allure.feature("Cloud.ru Calculator")
class TestCalculatorUI:
    """Тесты UI калькулятора Cloud.ru"""
    
    @allure.title("Проверка отображения калькулятора")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_calculator_display(self):
        """Проверка отображения основных элементов калькулятора"""
        with allure.step("Открыть страницу калькулятора"):
            # Arrange
            pass
        with allure.step("Проверить заголовок страницы"):
            # Act
            pass
        with allure.step("Убедиться что калькулятор отображается"):
            # Assert
            pass
    
    @allure.title("Расчет стоимости конфигурации")
    @allure.severity(allure.severity_level.NORMAL)
    def test_price_calculation(self):
        """Тест расчета стоимости выбранной конфигурации"""
        with allure.step("Выбрать продукт Compute"):
            pass
        with allure.step("Настроить параметры (CPU=2, RAM=4GB)"):
            pass
        with allure.step("Нажать кнопку расчета"):
            pass
        with allure.step("Проверить отображение цены"):
            pass'''
            else:
                # API тесты
                endpoint_count = len(request.spec.get("paths", {}))
                test_code = f'''"""
Автоматизированные API тесты для: {request.requirements or 'REST API'}
Эндпоинтов в спецификации: {endpoint_count}
Сгенерировано TestOps Copilot
"""
import pytest
import allure
import requests
import json

BASE_URL = "https://compute.api.cloud.ru"

@allure.epic("API Testing")
@allure.feature("Cloud.ru Compute API")
class TestComputeAPI:
    """Тесты API Cloud.ru Compute"""
    
    @allure.title("Проверка доступности API")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_api_health(self):
        """Проверка что API отвечает"""
        # Arrange
        url = f"{{BASE_URL}}/health"
        
        # Act
        response = requests.get(url)
        
        # Assert
        assert response.status_code == 200
        allure.attach(response.text, name="Response", attachment_type=allure.attachment_type.TEXT)
    
    @allure.title("Создание виртуальной машины")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_vm(self):
        """Тест создания VM через API"""
        # Arrange
        vm_data = {{
            "name": "test-vm-generated",
            "flavor": "small",
            "image": "ubuntu-20.04"
        }}
        
        # Act
        response = requests.post(
            f"{{BASE_URL}}/vms",
            json=vm_data,
            headers={{"Authorization": "Bearer ${{TOKEN}}"}}
        )
        
        # Assert
        assert response.status_code == 201
        response_json = response.json()
        assert "id" in response_json
        
        allure.attach(
            json.dumps(response_json, indent=2, ensure_ascii=False),
            name="Created VM",
            attachment_type=allure.attachment_type.JSON
        )'''
            
            return AgentResponse(
                status="success",
                code_text=test_code,
                metadata={
                    "tests": 2,
                    "type": request.test_type,
                    "requirements": request.requirements[:50] + "..." if request.requirements else "No requirements",
                    "timestamp": "2024-01-15T10:30:00Z"
                }
            )
    
    agent = AgentCore()

# ===== ОСНОВНЫЕ ЭНДПОИНТЫ =====
@app.get("/")
async def root():
    return {
        "service": "TestOps Copilot",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/generate", response_model=AgentResponse)
async def generate_tests(request: AgentRequest):
    try:
        print(f"📨 Запрос: {request.test_type}")
        
        result = await agent.process(request)
        
        # Сохраняем в файл
        import datetime
        filename = f"generated_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(result.code_text)
        print(f"💾 Сохранено: {filename}")
        
        return AgentResponse(
            status="success",
            code_text=result.code_text,
            metadata=result.metadata
        )
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)