# utils/sanitizer.py
import re
import html
from typing import Optional

def sanitize_text(text: str) -> str:
    """
    Очищает текст от потенциально опасного содержимого:
    - HTML-теги и скрипты (XSS-защита)
    - Непечатаемые/управляющие символы
    - Чрезмерное количество спецсимволов
    - Опасные последовательности
    
    Возвращает безопасный текст, пригодный для передачи в LLM.
    """
    # utils/sanitizer.py

    """
    Очищает текст от XSS, JavaScript-инъекций и потенциально опасного содержимого.
    Возвращает безопасный текст, пригодный для передачи в LLM и отображения в интерфейсе.
    """
    if not text or not isinstance(text, str):
        return ""

    
    # 1. Удаляем JavaScript-инъекции ДО экранирования
    js_patterns = [
        r'javascript\s*:',
        r'vbscript\s*:',
        r'expression\s*\(',
        r'eval\s*\(',
        r'Function\s*\(',
        r'setTimeout\s*\(',
        r'setInterval\s*\(',
        r'location\s*=',
        r'window\s*\.',
        r'document\s*\.',
        r'cookie\s*=',
        r'[^A-Za-z0-9]on\w+\s*=',
        r'alert\s*\(',
        r'confirm\s*\(',
        r'prompt\s*\(',
        r'console\s*\.\s*\w+',
        r'innerHTML\s*=',
        r'outerHTML\s*=',
        r'execScript\s*\(',
        r'base64\s*,',
        r'rm\s+-rf',
        r'rm\s+[-/]\w*',
    ]
    
    for pattern in js_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # 2. Удаляем HTML-теги (на случай, если остались)
    text = re.sub(r'<[^>]*>', '', text)
    
    # 3. Экранируем остатки (защита на случай вывода в HTML)
    text = html.escape(text, quote=False)
    
    # 4. Удаляем невидимые символы и "мусор"
    text = re.sub(r'[^\u0009\u000A\u0020-\u007E\u00A0-\u00FF\u2000-\u206F]', '', text, flags=re.UNICODE)
    
    # 5. Очищаем пустые строки и лишние пробелы
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    text = '\n'.join(lines)
    
    return text.strip()



def sanitize_extracted_text(text: str) -> str:
    if not text or not isinstance(text, str):
        return ""
    
    # 1. Разбиваем текст на строки
    lines = text.split('\n')
    cleaned_lines = []
    
    # 2. Фильтруем строки: удаляем те, что содержат JS/XSS-паттерны
    dangerous_patterns = [
        r'javascript\s*:',
        r'vbscript\s*:',
        r'expression\s*\(',
        r'eval\s*\(',
        r'Function\s*\(',
        r'setTimeout\s*\(',
        r'setInterval\s*\(',
        r'location\s*=',
        r'window\s*\.',
        r'document\s*\.',
        r'cookie\s*=',
        r'on\w+\s*=',
        r'<script',
        r'<iframe',
        r'alert\s*\(',
        r'confirm\s*\(',
        r'prompt\s*\(',
        r'console\s*\.\s*\w+',
        r'innerHTML\s*=',
        r'outerHTML\s*=',
        r'execScript\s*\(',
        r'base64\s*,',
        r'rm\s+-rf',
        r'document\.cookie',
        r'\.cookie\s*=',
        r'localStorage\s*=',
        r'sessionStorage\s*=',
        r'stealCookies',      # ← явно удаляем опасные имена
        r'sendData',          # ← даже если они остались после обрезки
        r'session\s*=',
    ]
    
    for line in lines:
        # Проверяем строку на наличие ЛЮБОГО опасного паттерна
        is_safe = True
        for pattern in dangerous_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                is_safe = False
                break
        if is_safe:
            cleaned_lines.append(line)
    
    # 3. Объединяем обратно
    text = '\n'.join(cleaned_lines)
    
    # 4. Удаляем оставшиеся HTML-теги (на случай, если остались)
    text = re.sub(r'<[^>]*>', '', text)
    
    # 5. Экранируем остатки (защита при выводе в HTML)
    text = html.escape(text, quote=False)
    
    # 6. Очищаем мусор
    text = re.sub(r'[^\u0009\u000A\u0020-\u007E\u00A0-\u00FF\u2000-\u206F]', '', text, flags=re.UNICODE)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    text = '\n'.join(lines)
    
    return text.strip()


def is_text_safe(text: str, max_length: int = 100000) -> bool:
    """
    Быстрая проверка: безопасен ли текст для обработки?
    """
    if not text or len(text) > max_length:
        return False
    
    # Проверяем на наличие опасных фрагментов (даже после очистки)
    unsafe_fragments = [
        '<script', 'vbscript:', 'expression(',
        'eval(', 'Function(', 'setTimeout(', 'setInterval(',
        'location=', 'window.', 'document.', 'cookie=',
        'onload=', 'onerror=', 'onmouseover=',
        'innerHTML=', 'outerHTML=', 'execScript(',
        'document.cookie', '.cookie=', 'rm -rf'
    ]
    
    text_lower = text.lower()
    return not any(frag in text_lower for frag in unsafe_fragments)