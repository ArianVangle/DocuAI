from langchain_gigachat import GigaChat
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os

def answer_technical_question(document_text: str, question: str) -> str:
    
    llm = GigaChat(
        credentials=os.getenv("API_KEY"),
        model="GigaChat",
        verify_ssl_certs=False
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Ты — технический эксперт. Отвечай ТОЛЬКО на основе документа. Если информации нет — скажи об этом.\n\nДокумент:\n{document}"),
        ("human", "{question}")
    ])
    
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"document": document_text, "question": question})