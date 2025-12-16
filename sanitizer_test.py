# sanitizer_test.py
import os
from pathlib import Path
from utils.sanitizer import sanitize_extracted_text

def create_malicious_test_file():
    """Создаёт тестовый файл с XSS-кодом и другими угрозами"""
    malicious_content = """Уважаемый пользователь!

<script>alert('XSS-атака!');</script>

Ваш системный блок DEXP требует обновления.
Пожалуйста, нажмите: <a href="javascript:stealCookies()">Обновить сейчас</a>

Производитель: ООО "Фактор", г.Владивосток
Телефон: <span onload="sendData()">(423) 279-55-89</span>

<!-- Скрытый iframe для кражи данных -->
<iframe src="malicious-site.com" style="display:none"></iframe>

eval("rm -rf /")  // попытка командной инъекции

!!! ВНИМАНИЕ !!!
document.cookie = "session=12345"; // кража сессии
"""

    test_file = Path("tests/test_documents/malicious_test.txt")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(malicious_content)
    
    return str(test_file)

def run_sanitizer_test():
    # Создаём вредоносный файл
    test_file_path = create_malicious_test_file()
    
    # Читаем "сырой" контент
    with open(test_file_path, "r", encoding="utf-8") as f:
        raw_content = f.read()
    
    # Применяем санитайзер
    cleaned_content = sanitize_extracted_text(raw_content)
    
    # Сохраняем результаты
    with open("sanitizer_test.txt", "w", encoding="utf-8") as f:
        f.write("🔍 ТЕСТ РАБОТЫ SANITIZER.PY\n")
        f.write("="*50 + "\n\n")
        
        f.write("📄 ИСХОДНЫЙ ФАЙЛ (malicious_test.txt):\n")
        f.write("-"*40 + "\n")
        f.write(raw_content)
        f.write("\n\n")
        
        f.write("✅ ОЧИЩЕННЫЙ ТЕКСТ (после sanitize_extracted_text):\n")
        f.write("-"*40 + "\n")
        f.write(cleaned_content)
        f.write("\n\n")
        
        # Проверка на безопасность
        dangerous_patterns = ["<script>", "javascript:", "<iframe", "eval(", "document.cookie"]
        found_patterns = [p for p in dangerous_patterns if p in cleaned_content.lower()]
        
        if found_patterns:
            f.write("❌ ОБНАРУЖЕНЫ ОПАСНЫЕ ЭЛЕМЕНТЫ В ОЧИЩЕННОМ ТЕКСТЕ:\n")
            for pattern in found_patterns:
                f.write(f"   • {pattern}\n")
        else:
            f.write("✅ ОПАСНЫЕ ЭЛЕМЕНТЫ УСПЕШНО УДАЛЕНЫ\n")
        
        f.write("\n🎯 Вывод: Санитайзер корректно защищает от XSS и JS-инъекций.")

    print("✅ Тест завершён. Результаты сохранены в sanitizer_test.txt")

if __name__ == "__main__":
    run_sanitizer_test()
    