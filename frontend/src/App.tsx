import React, { useState, useRef, useEffect } from 'react';
import './App.css';

function App() {
  const [input, setInput] = useState('');
  const [output, setOutput] = useState('Здесь появится Python-код в формате Allure TestOps as Code');
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<Array<{ timestamp: string, requirements: string, code: string }>>([]);

  const API_URL = 'http://localhost:5000';
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.focus();
    }

    const savedHistory = localStorage.getItem('testops_history');
    if (savedHistory) {
      setHistory(JSON.parse(savedHistory));
    }
  }, []);

  const createOpenAPIFromText = (text: string) => {
    return {
      "openapi": "3.0.0",
      "info": {
        "title": `TestOps - ${text.substring(0, 30)}${text.length > 30 ? '...' : ''}`,
        "version": "1.0.0",
        "description": text
      },
      "paths": {
        "/test": {
          "get": {
            "responses": {
              "200": {
                "description": "Auto-generated test endpoint"
              }
            }
          }
        }
      }
    };
  };

  const getTestType = (text: string): string => {
    const lower = text.toLowerCase();
    if (lower.includes('ui') || lower.includes('интерфейс') || lower.includes('калькулятор')) {
      return "manual_ui";
    }
    return "auto_api";
  };

  const saveToHistory = (requirements: string, code: string) => {
    const newHistoryItem = {
      timestamp: new Date().toISOString(),
      requirements,
      code: code.substring(0, 500) + (code.length > 500 ? '...' : '')
    };

    const updatedHistory = [newHistoryItem, ...history.slice(0, 9)];
    setHistory(updatedHistory);
    localStorage.setItem('testops_history', JSON.stringify(updatedHistory));
  };

  const handleGenerate = async () => {
    const text = input.trim();
    if (!text) {
      setOutput("Введите описание требований");
      return;
    }

    setLoading(true);
    setOutput("Отправка запроса на сервер...");

    try {
      const openapiSpec = createOpenAPIFromText(text);
      const testType = getTestType(text);

      const response = await fetch(`${API_URL}/api/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          spec: openapiSpec,
          test_type: testType
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      if (data.status === "success") {
        setOutput(data.code_text);
        saveToHistory(text, data.code_text);
      } else {
        setOutput(`Ошибка бекенда: ${data.message || 'Неизвестная ошибка'}`);
      }
    } catch (error: any) {
      setOutput(`Ошибка: ${error.message}\n\nНеверный формат требования`);
      console.error('Детали ошибки:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setInput('');
    setOutput('Здесь появится Python-код в формате Allure TestOps as Code');
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  const handleCopyCode = () => {
    navigator.clipboard.writeText(output)
      .then(() => alert('Код скопирован в буфер обмена'))
      .catch(err => console.error('Ошибка копирования:', err));
  };

  const loadFromHistory = (item: { requirements: string, code: string }) => {
    setInput(item.requirements);
    setOutput(item.code);
  };

  const clearHistory = () => {
    setHistory([]);
    localStorage.removeItem('testops_history');
  };

  return (
    <div className="app">
      <header className="header">
        <div className="title">TestOps Copilot</div>
        <div className="subtitle">AI-ассистент, который автоматизирует рутинную работу QA-инженера</div>
      </header>

      <main className="main">
        <div className="input-area">
          <div className="input-label">Введите описание требований:</div>
          <textarea
            ref={textareaRef}
            className="input-textarea"
            placeholder="Пример: Создай тест-кейсы для API создания виртуальной машины в Cloud.ru"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                handleGenerate();
              }
            }}
          />
          <div className="buttons">
            <button
              className="generate-btn"
              onClick={handleGenerate}
              disabled={loading}
            >
              {loading ? 'Генерация...' : 'Сгенерировать код'}
            </button>
            <button className="clear-btn" onClick={handleClear}>
              Очистить
            </button>
          </div>
        </div>

        <div className="output-area">
          <div className="output-header">
            <div className="output-label">Результат:</div>
            <div className="output-actions">
              <button className="copy-btn" onClick={handleCopyCode}>
                Копировать код
              </button>
            </div>
          </div>
          <pre className="output-code">
            {output}
          </pre>
        </div>

        {history.length > 0 && (
          <div className="history-area">
            <div className="history-header">
              <div className="history-label">История запросов:</div>
              <button className="clear-history-btn" onClick={clearHistory}>
                Очистить историю
              </button>
            </div>
            <div className="history-list">
              {history.map((item, index) => (
                <div
                  key={index}
                  className="history-item"
                  onClick={() => loadFromHistory(item)}
                >
                  <div className="history-requirements">
                    {item.requirements.substring(0, 80)}...
                  </div>
                  <div className="history-time">
                    {new Date(item.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      <footer className="footer">
        Cloud.ru Evolution Foundation Model
      </footer>
    </div>
  );
}

export default App;