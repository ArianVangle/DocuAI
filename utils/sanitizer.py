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
    if not text or not isinstance(text, str):
        return ""
    
    # 1. Экранируем HTML-сущности (защита от XSS при выводе)
    text = html.escape(text, quote=False)
    
    # 2. Удаляем HTML-теги (на случай, если остались)
    text = re.sub(r'<[^>]*>', '', text)
    
    # 3. Удаляем JavaScript-подобные конструкции
    js_patterns = [
        r'javascript\s*:',
        r'on\w+\s*=',
        r'<script[^>]*>.*?</script>',
        r'<iframe[^>]*>.*?</iframe>',
        r'eval\s*\(',
        r'expression\s*\(',
        r'alert\s*\('
    ]
    for pattern in js_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # 4. Удаляем непечатаемые символы (кроме табуляции и перевода строк)
    # Сохраняем: буквы, цифры, пробелы, пунктуацию, \n, \t
    text = re.sub(
        r'[^\u0020-\u007E\u00A0-\u00FF\u2000-\u206F\u20A0-\u20CF\u2100-\u214F\u2200-\u22FF\n\t]',
        '',
        text,
        flags=re.UNICODE
    )
    
    # 5. Ограничиваем повторяющиеся спецсимволы (защита от "бомб")
    # Например: !!!!!!!!!! → !
    text = re.sub(r'([!?.]){4,}', r'\1', text)
    text = re.sub(r'([*-_=]){10,}', r'\1\1\1', text)
    
    # 6. Удаляем чрезмерные пробелы и пустые строки
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    text = '\n'.join(lines)
    
    return text.strip()


def is_text_safe(text: str, max_length: int = 100000) -> bool:
    """
    Быстрая проверка: безопасен ли текст для обработки?
    """
    if not text:
        return False
    if len(text) > max_length:
        return False
    if '<script' in text.lower():
        return False
    if 'javascript:' in text.lower():
        return False
    return True


# === Для PDF и DOCX: дополнительная очистка после извлечения текста ===

def sanitize_extracted_text(text: str) -> str:
    """
    Очистка текста, извлечённого из PDF/DOCX.
    Удаляет артефакты парсинга и оставляет только читаемый текст.
    """
    if not text:
        return ""
    
    # Удаляем артефакты из PDF (часто встречаются)
    text = re.sub(r'\u200b', '', text)  # Zero-width space
    text = re.sub(r'\u00ad', '', text)  # Soft hyphen
    text = re.sub(r'\u2028', '\n', text)  # Line separator
    text = re.sub(r'\u2029', '\n\n', text)  # Paragraph separator
    
    # Удаляем последовательности из одного символа (артефакты OCR/парсинга)
    text = re.sub(r'(.)\1{10,}', r'\1\1\1', text)
    
    # Применяем основную санитизацию
    return sanitize_text(text)

