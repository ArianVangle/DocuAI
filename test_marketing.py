# marketing_accuracy_simple_test.py
import os
import sys
import time
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from langchain.document_loaders import PyPDFLoader
from agents.marketing_expert import generate_ab_tests
from utils.sanitizer import sanitize_extracted_text

load_dotenv()

PDF_PATH = "./tests/test_documents/20091.pdf"

# Упрощённые тестовые сценарии (без проверки релевантности A/B)
MARKETING_TEST_CASES = [
    "Сделай A/B-тесты для технических менеджеров",
    "Сгенерируй A/B-тесты для ИТ-специалистов",
    "Сделай рекламные гипотезы для корпоративных клиентов"
]

def extract_text_from_pdf(pdf_path: str) -> str:
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    text = "\n\n".join([doc.page_content for doc in docs])
    return sanitize_extracted_text(text)

def is_valid_ab_response(response: str) -> bool:
    """
    Проверяет только структуру ответа, без анализа содержания.
    """
    lower_resp = response.lower()
    return (
        "a:" in lower_resp and
        "b:" in lower_resp and
        "/10" in response and
        "рекомендация" in lower_resp and
        len(response.strip()) > 50  # не пустой
    )

def run_marketing_accuracy_simple_test():
    with open("marketing_simple_test.txt", "w", encoding="utf-8") as f:
        f.write("🔍 Тесты корректности формата рекламных A/B-тестов (без проверки релевантности)\n\n")

        if not os.path.exists(PDF_PATH):
            f.write(f"❌ Файл не найден: {PDF_PATH}\n")
            return

        try:
            document_text = extract_text_from_pdf(PDF_PATH)
            f.write(f"✅ Документ загружен. Размер: {len(document_text)} символов.\n\n")
        except Exception as e:
            f.write(f"❌ Ошибка загрузки: {e}\n")
            return

        passed = 0
        total = len(MARKETING_TEST_CASES)

        for i, query in enumerate(MARKETING_TEST_CASES, 1):
            f.write(f"[{i}/{total}] Запрос: {query}\n")

            start_time = time.time()
            response = generate_ab_tests(document_text, query)
            elapsed = time.time() - start_time

            f.write(f"⏱️ Время: {elapsed:.2f} сек\n")
            f.write(f"📄 Ответ:\n{response}\n\n")

            # Проверка только структуры
            is_valid = is_valid_ab_response(response)
            if is_valid:
                passed += 1
                f.write("✅ Структура ответа КОРРЕКТНА\n\n")
            else:
                f.write("❌ Структура ответа НЕ КОРРЕКТНА (нет A:/B:/оценки/рекомендации)\n\n")

        accuracy_percent = (passed / total) * 100
        f.write("=" * 60 + "\n")
        f.write(f"📊 МЕТРИКА КОРРЕКТНОСТИ ФОРМАТА A/B-ТЕСТОВ:\n")
        f.write(f"   • Успешно: {passed}/{total}\n")
        f.write(f"   • Точность: {accuracy_percent:.1f}%\n")

        if accuracy_percent == 100:
            f.write("🎯 Все ответы имеют корректную структуру A/B-тестов.\n")
        elif accuracy_percent >= 66:
            f.write("👍 Большинство ответов соответствуют формату.\n")
        else:
            f.write("⚠️ Многие ответы нарушают структуру A/B-тестов.\n")

if __name__ == "__main__":
    run_marketing_accuracy_simple_test()