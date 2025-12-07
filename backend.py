# main.py
import os
import shutil
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from langchain_gigachat import GigaChat
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
from agent_orchestrator import route_query
from utils.sanitizer import sanitize_extracted_text, is_text_safe

# Для эмбеддингов на русском
from langchain_community.embeddings import HuggingFaceEmbeddings

# Загружаем переменные окружения
load_dotenv()

app = FastAPI()

# Папки
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
STATIC_DIR = Path("static")
STATIC_DIR.mkdir(exist_ok=True)

# Монтируем статику
app.mount("/static", StaticFiles(directory="static"), name="static")

# Глобальные переменные
document_text = ""
vectorstore = None  # ← НОВОЕ: векторное хранилище для RAG

# Инициализация GigaChat
llm = GigaChat(
    credentials=os.getenv("API_KEY"), 
    model="GigaChat",
    verify_ssl_certs=False,
)

@app.get("/", response_class=HTMLResponse)
async def get_chat():
    with open("static/index.html", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    global document_text, vectorstore  # ← ДОБАВЛЕНО vectorstore
    if not file.filename:
        raise HTTPException(status_code=400, detail="Файл не выбран")

    ext = file.filename.split(".")[-1].lower()
    if ext not in ["txt", "pdf", "docx"]:
        raise HTTPException(status_code=400, detail="Поддерживаются только .txt, .pdf, .docx")

    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        if ext == "txt":
            loader = TextLoader(file_path, encoding="utf-8")
        elif ext == "pdf":
            loader = PyPDFLoader(str(file_path))
        elif ext == "docx":
            loader = Docx2txtLoader(str(file_path))
        else:
            raise ValueError("Неподдерживаемый формат")

        docs = loader.load()
        document_text = "\n\n".join([doc.page_content for doc in docs])
        
        # === САНИТАЙЗАЦИЯ ===
        if not is_text_safe(document_text):
            raise ValueError("Файл содержит недопустимый контент")
    
        sanitized_text = sanitize_extracted_text(document_text)
    
        if len(sanitized_text) < 10:
            raise ValueError("Файл не содержит допустимого текста")

        document_text = sanitized_text  # ← ИСПОЛЬЗУЕМ ОЧИЩЕННЫЙ ТЕКСТ

        # === СОЗДАНИЕ RAG (НОВОЕ) ===
        # Разбиваем текст на чанки
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = text_splitter.split_text(document_text)

        # Создаём эмбеддинги для русского языка
        embeddings = HuggingFaceEmbeddings(
            model_name="cointegrated/rubert-tiny2",
            model_kwargs={"device": "cpu"}
        )

        # Создаём векторное хранилище
        vectorstore = FAISS.from_texts(chunks, embeddings)

        return {"message": f"✅ Документ '{file.filename}' загружен. RAG активирован."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки файла: {str(e)}")


@app.post("/chat")
async def chat(request: Request):
    global document_text, vectorstore  # ← ПЕРЕДАЁМ vectorstore
    body = await request.json()
    user_message = body.get("message", "").strip()

    if not document_text:
        return {"response": "⚠️ Сначала загрузите документ."}
    if not user_message:
        return {"response": "💬 Пожалуйста, введите запрос."}

    try:
        # Передаём и текст, и vectorstore в оркестратор
        final_response = route_query(document_text, user_message, vectorstore)
        return final_response
    except Exception as e:
        return {"response": f"❌ Ошибка агентов: {str(e)}"}