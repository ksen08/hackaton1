# TestOps Copilot   
## AI-ассистент, который автоматизирует рутинную работу QA-инженера

* Решаемые задачи:
1. Генерация ручных тест-кейсов для UI калькулятора   
2. Генерация ручных тест-кейсов для API VMs   
3. Генерация автоматизированных e2e тестов   
4. Генерация автоматизированных API тестов   
5. Интеграция с Cloud.ru Evolution Foundation Model   
6. Работающий Docker setup
7. Режимы работы:   
* demo (без API ключей и ограниченным количеством тестов)  
* real (с API ключами)      

* Инструкция по запуску:

1. Склонируйте репозиторий     

`git clone git@gitlab.com:ksusha08ost/hackaton.git`

2. Перейдите в терминале на ветку develop  

`git checkout develop`

3. Создайте виртуальное окружение   

`python -m venv .venv`   

`source .venv/bin/activate`

4. Создайте файл .env в корневой директории проекта на основе шаблона:

`API_KEY=ZjhkN2QxNmUtMGZmYS00Yjk5LWIxZmYtMTBiMjI4MzIyZWU5.5bf8a2a2e9cf577de691e589d9bfdda3`

## Два варианта запуска:

* Без Docker  
* C Docker   

1. Вариант запуска без Docker:   

2. Установка для backenda:   

3. Переходим в папку backend/src и прописываем команду для установки всех необходимых пакетов:   

`pip install -r requirements.txt`

4. Запускаем FastAPI бэкенд сервер:

`python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 5000`   

5. На странице http://localhost:5000/ в браузере можно увидеть главную страницу API.  

6. На странице http://localhost:5000/docs в браузере можно увидеть автоматическую документацию Swagger UI.   

7. Открываем новый терминал и выполяем установку для Frontenda:   

8. Переходим из корневой папки в папку frontend  `cd frontend`   

9. Устанавливаем зависимости:   

`npm install`   

10. Компилируем React:   

`npm run build`  

11. На странице http://localhost:3000/ в браузере можно увидеть интерфейс и обратиться к нему (инструкцию, как обращаться см. ниже)   

12. Вариант запуска с Docker(рекомендуемый):   

13. Запускаем Docker, собираем проект:   

`docker-compose up --build`   

14. В браузере будут доступны:   

###   Фронтенд: http://localhost:3000
###   Бэкенд API: http://localhost:5000
###   Документация API: http://localhost:5000/docs


15. На странице фронтенда в поле "Введите описание требований" введите требования.   

> Готовые промты можете найти в папке backend/src/generator/promts.   

16. Получите результат. Система сгенерирует готовые Python тесты в формате Allure TestOps as Code:  

Пример генерируемых тестов:   

```python
import pytest
import allure
import requests

@allure.feature("Virtual Machines")
class TestVMOperations:
    @allure.title("Get VM by ID")
    def test_get_vm_by_id(self):
        # Arrange
        vm_id = "test-vm-id"
        vm_url = f"/vms/{vm_id}"

        # Act
        response = requests.get(vm_url)

        # Assert
        assert response.status_code == 200
        assert response.json()["name"] == "test-vm"

    @allure.title("Delete VM by ID")
    def test_delete_vm_by_id(self):
        # Arrange
        vm_id = "test-vm-id"
        vm_url = f"/vms/{vm_id}"

        # Act
        response = requests.delete(vm_url)

        # Assert
        assert response.status_code == 204
```






