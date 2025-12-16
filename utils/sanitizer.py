# utils/sanitizer.py
import re
import html
from typing import Optional

def sanitize_extracted_text(text: str) -> str:
    """
    Очищает текст от XSS, JS-инъекций и потенциально опасного содержимого.
    Гарантирует, что результат безопасен для передачи в LLM и отображения в HTML.
    """
    if not text or not isinstance(text, str):
        return ""
    
    # 1. Экранируем ВСЕ HTML-сущности (базовая защита от XSS при выводе)
    text = html.escape(text, quote=False)
    
    # 2. Удаляем HTML-теги (на случай, если остались)
    text = re.sub(r'<[^>]*>', '', text)
    
    # 3. Удаляем JavaScript- и браузерные инъекции (строго по шаблонам)
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
        r'[^A-Za-z0-9]on\w+\s*=',
        r'<script[^>]*>.*?</script>',
        r'<iframe[^>]*>.*?</iframe>',
        r'<img[^>]*\s+on\w+[^>]*>',
        r'alert\s*\(',
        r'confirm\s*\(',
        r'prompt\s*\(',
        r'console\s*\.\s*\w+',
        r'innerHTML\s*=',
        r'outerHTML\s*=',
        r'execScript\s*\(',
        r'base64\s*,',
    ]
    
    for pattern in dangerous_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # 4. Удаляем невидимые/непечатаемые символы (кроме \n и \t)
    text = re.sub(
        r'[^\u0009\u000A\u0020-\u007E\u00A0-\u00FF\u2000-\u206F\u20A0-\u20CF\u2100-\u214F\u2200-\u22FF]',
        '',
        text,
        flags=re.UNICODE
    )
    
    # 5. Ограничиваем повторяющиеся спецсимволы (защита от "бомб")
    text = re.sub(r'([!?.]){5,}', r'\1\1\1', text)
    text = re.sub(r'([*-_=]){15,}', r'\1\1\1', text)
    
    # 6. Удаляем лишние пробелы и пустые строки
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    text = '\n'.join(lines)
    
    return text.strip()


def is_text_safe(text: str, max_length: int = 100000) -> bool:
    """
    Быстрая проверка: безопасен ли текст для обработки?
    """
    if not text or len(text) > max_length:
        return False
    
    # Проверяем на наличие явных угроз (даже после экранирования)
    unsafe_fragments = [
        '<script', 'javascript:', 'vbscript:', 'data:',
        'document.', 'window.', 'eval(', 'Function(',
        'onload=', 'onerror=', 'onmouseover='
    ]
    
    text_lower = text.lower()
    return not any(frag in text_lower for frag in unsafe_fragments)