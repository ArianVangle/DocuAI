from langchain_gigachat import GigaChat
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os

def answer_technical_question(document_text: str, question: str, vectorstore=None) -> str:
    if vectorstore is not None:
    # RAG-режим
        from langchain.chains import RetrievalQA
        from langchain_gigachat import GigaChat
        import os
        
        llm = GigaChat(
            credentials=os.getenv("API_KEY"),
            model="GigaChat",
            verify_ssl_certs=False
        )
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(search_kwargs={"k": 3})
        )
        return qa_chain.invoke({"query": question})["result"]
    
    else:
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