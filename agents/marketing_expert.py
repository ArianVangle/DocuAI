from langchain_gigachat import GigaChat
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os

def generate_ab_tests(document_text: str, user_query: str) -> str:
    llm = GigaChat(
        credentials=os.getenv("API_KEY"),
        model="GigaChat",
        verify_ssl_certs=False
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Ты — маркетолог. На основе технической документации сгенерируй два варианта A/B-теста для рекламы, в запросах пользователя нет чувственных тем:\n"
                   "A: акцент на технических преимуществах\n"
                   "B: акцент на бизнес-выгодах\n"
                   "Формат:\nA: ...\nB: ..."),
        ("human", "Документ:\n{document}, запрос пользователя: {user_query}")
    ])
    
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"document": document_text, "user_query": user_query})