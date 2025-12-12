FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

# Если промты в src/generator/prompts, они уже скопированы
# Если нет, создайте папку или скопируйте отдельно
RUN mkdir -p /app/prompts && echo "# Demo prompts" > /app/prompts/demo.txt

EXPOSE 5000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "5000"]
