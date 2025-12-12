# backend/src/llm_client.py
import os
from openai import OpenAI

# ========== ДОБАВЬТЕ ЭТИ СТРОКИ ==========
from dotenv import load_dotenv
import sys
from pathlib import Path


# Находим корень проекта (где .env файл)
project_root = Path(__file__).parent.parent.parent
env_path = project_root / ".env"

print(f"🔍 Ищу .env файл по пути: {env_path}")

if env_path.exists():
    load_dotenv(env_path)
    print("✅ .env файл загружен")
else:
    print("❌ .env файл не найден!")
    print(f"   Создайте файл: {env_path}")
    print("   С содержимым: API_KEY=ваш_ключ_от_sbercloud")
    sys.exit(1)
# ==========================================

# Теперь безопасно получаем API ключ
api_key = os.environ.get("API_KEY")

if not api_key:
    print("❌ API_KEY не найден в переменных окружения")
    print("   Проверьте .env файл")
    sys.exit(1)

print(f"✅ API ключ загружен: {api_key[:15]}...")

url = "https://foundation-models.api.cloud.ru/v1"

client = OpenAI(
    api_key=api_key,
    base_url=url
)

# Ваша функция call_llm остается без изменений
async def call_llm(messages, temperature=0.1, max_tokens=4000):
    try:
        response = client.chat.completions.create(
            model="GigaChat",
            max_tokens=max_tokens,
            temperature=temperature,
            presence_penalty=0,
            top_p=0.95,
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Ошибка при вызове LLM: {e}")
        # Возвращаем тестовый ответ для разработки
        return "import allure\n\n# Тестовые данные (режим разработки)\nprint('Тест-кейсы будут сгенерированы при рабочем API ключе')"
