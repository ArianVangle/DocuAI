# agent_orchestrator.py
from langchain_gigachat import GigaChat
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
import json

# Импорт агентов
from agents.document_analyst import analyze_document
from agents.marketing_expert import generate_ab_tests
from agents.technical_reviewer import answer_technical_question
from agents.summarizer import summarize_document

# Описание агентов для LLM-диспетчера
AGENT_DESCRIPTIONS = """
Доступные агенты:
1. **summarizer** — даёт краткое содержание документа с учётом запроса пользователя.
2. **marketing_expert** — генерирует A/B-тесты и маркетинговые формулировки.
3. **technical_reviewer** — отвечает на технические вопросы по документу.
4. **document_analyst** — проводит глубокий анализ структуры и компонентов документа.
"""

def route_with_llm(user_query: str) -> dict:
    """
    Выбирает агента с помощью GigaChat и возвращает его имя + обоснование.
    """
    llm = GigaChat(
        credentials=os.getenv("API_KEY"),
        model="GigaChat",
        verify_ssl_certs=False
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Ты — диспетчер многоагентной системы. "
                   "Выбери ОДИН наиболее подходящий агент для запроса пользователя и кратко обоснуй выбор (1 предложение).\n\n"
                   f"{AGENT_DESCRIPTIONS}\n"
                   "Ответь строго в формате JSON:\n{{\"agent\": \"название_агента\", \"reasoning\": \"обоснование\"}}"),
        ("human", "Запрос пользователя: {query}")
    ])
    
    chain = prompt | llm | StrOutputParser()
    try:
        raw_response = chain.invoke({"query": user_query})
        data = json.loads(raw_response)
        agent_name = data.get("agent", "document_analyst")
        reasoning = data.get("reasoning", "Агент выбран по умолчанию.")
        
        # Валидация имени агента
        valid_agents = {"summarizer", "marketing_expert", "technical_reviewer", "document_analyst"}
        if agent_name not in valid_agents:
            agent_name = "document_analyst"
            reasoning = "Некорректный выбор агента — используется анализ по умолчанию."
            
        return {"agent_name": agent_name, "reasoning": reasoning}
        
    except Exception as e:
        return {
            "agent_name": "document_analyst",
            "reasoning": f"Ошибка роутинга — используется анализ по умолчанию. ({str(e)})"
        }

def route_query(document_text: str, user_query: str) -> dict:
    """
    Основная функция оркестратора.
    Возвращает: {"steps": [...], "final_answer": "..."}
    """
    steps = []
    
    # Шаг 1: Анализ запроса
    steps.append({
        "agent": "🧠",
        "message": "Анализирую ваш запрос для выбора подходящего агента..."
    })
    
    # Шаг 2: Выбор агента через LLM
    routing_result = route_with_llm(user_query)
    steps.append({
        "agent": "🧠",
        "message": f"Выбран агент: {routing_result['agent_name']} → {routing_result['reasoning']}"
    })
    
    # Шаг 3: Выполнение задачи выбранным агентом
    agent_name = routing_result["agent_name"]
    steps.append({
        "agent": f"🧑‍💼 {agent_name}",
        "message": "Обрабатываю документ и формирую ответ..."
    })
    
    try:
        if agent_name == "summarizer":
            final_answer = summarize_document(document_text, user_query)
            
        elif agent_name == "marketing_expert":
            final_answer = generate_ab_tests(document_text, user_query)
            
        elif agent_name == "technical_reviewer":
            final_answer = answer_technical_question(document_text, user_query)
            
        elif agent_name == "document_analyst":
            analysis = analyze_document(document_text, user_query)
            summary = summarize_document(document_text, user_query)
            final_answer = f"🔍 **Глубокий анализ документа**:\n{analysis}\n\n📝 **Краткое содержание**:\n{summary}"
            
        else:
            final_answer = "Неизвестный агент. Обратитесь к разработчикам системы."
            
    except Exception as e:
        final_answer = f"❌ Ошибка выполнения агента: {str(e)}"
        steps.append({
            "agent": "⚠️ Система",
            "message": "Произошла ошибка при генерации ответа."
        })
    
    return {
        "steps": steps,
        "final_answer": final_answer
    }