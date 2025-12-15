# accuracy_test.py
import os
import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from langchain.document_loaders import PyPDFLoader
from agents.technical_reviewer import answer_technical_question
from utils.sanitizer import sanitize_extracted_text

# Загрузка переменных окружения
load_dotenv()

# Путь к вашему PDF
PDF_PATH = "./tests/test_documents/20091.pdf"

# Тестовые кейсы на основе реального содержимого документа
TEST_CASES = [
    {
        "query": "Какой производитель системного блока указан в документе?",
        "expected": "ООО \"Фактор\", г.Владивосток",
        "type": "exact"
    },
    {
        "query": "Какое напряжение требуется для питания системного блока?",
        "expected": "220 В",
        "type": "exact"
    },
    {
        "query": "Какой максимальный объём оперативной памяти можно установить?",
        "expected": "информация не указана",
        "type": "no_info"
    },
    {
        "query": "Какие интерфейсы используются для подключения монитора?",
        "expected": ["VGA", "DVI", "HDMI"],
        "type": "keywords"
    },
    {
        "query": "Какой телефон у производителя?",
        "expected": "(423) 279-55-89",
        "type": "exact"
    },
    {
        "query": "Сколько времени нужно выдержать компьютер после привоза с улицы зимой?",
        "expected": "не менее 2–х часов",
        "type": "exact"
    },
    {
        "query": "Какие типы дисков поддерживает привод DVD±R/RW?",
        "expected": ["Audio–CD", "CD–R", "CD–RW", "DVD–Video", "DVD±R", "DVD±RW"],
        "type": "keywords"
    },
    {
        "query": "Какие меры предосторожности нужно соблюдать при чистке системного блока?",
        "expected": ["отключить от сети", "мягкая ткань", "не использовать растворители"],
        "type": "keywords"
    },
    {
        "query": "Что делать, если на экране появилось сообщение 'CMOS Checksum Error'?",
        "expected": "Замените батарею, настройте параметры с помощью BIOS Setup",
        "type": "exact"
    },
    {
        "query": "Какие порты используются для подключения клавиатуры?",
        "expected": ["PS/2", "USB"],
        "type": "keywords"
    }
]

def extract_text_from_pdf(pdf_path: str) -> str:
    """Извлекает и санирует текст из PDF (как в backend.py)"""
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    text = "\n\n".join([doc.page_content for doc in docs])
    return sanitize_extracted_text(text)

def check_answer(response: str, expected, test_type: str) -> bool:
    """Проверяет ответ в зависимости от типа теста"""
    response_lower = response.lower()
    
    if test_type == "exact":
        return expected.lower() in response_lower
    
    elif test_type == "no_info":
        no_info_phrases = ["нет информации", "отсутствует", "не указано", "в документе нет"]
        return any(phrase in response_lower for phrase in no_info_phrases)
    
    elif test_type == "keywords":
        return all(keyword.lower() in response_lower for keyword in expected)
    
    return False

def run_accuracy_test():
    print("🔍 Запуск тестов точности извлечения информации...\n")
    
    # Загрузка и обработка документа
    if not os.path.exists(PDF_PATH):
        print(f"❌ Ошибка: файл {PDF_PATH} не найден.")
        return
    
    try:
        document_text = extract_text_from_pdf(PDF_PATH)
        print(f"✅ Документ загружен. Размер: {len(document_text)} символов.\n")
    except Exception as e:
        print(f"❌ Ошибка при загрузке документа: {e}")
        return

    # Прогон тестов
    passed = 0
    total = len(TEST_CASES)

    for i, case in enumerate(TEST_CASES, 1):
        query = case["query"]
        print(f"[{i}/{total}] Запрос: {query}")
        
        
            # Вызов агента technical_reviewer (как в оркестраторе)
        response = answer_technical_question(document_text, query)
        print(response)




if __name__ == "__main__":
    run_accuracy_test()