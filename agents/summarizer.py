from langchain_gigachat import GigaChat
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os

def summarize_document(document_text: str, user_query: str) -> str:
    llm = GigaChat(
        credentials=os.getenv("API_KEY"),
        model="GigaChat",
        verify_ssl_certs=False
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Сделай краткое содержание документа (3-5 предложений)."),
        ("human", "Документ:\n{document}, запрос пользователя {user_query}")
    ])
    
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"document": document_text, "user_query": user_query})