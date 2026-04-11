# app/ai/services/rag_service.py

import os
import io
import requests
from PyPDF2 import PdfReader
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import CrossEncoder
from dotenv import load_dotenv

from app.ai.services.input_service import PatientInput

load_dotenv()

# =========================
# CONFIG
# =========================
FAISS_INDEX_PATH = "faiss_index"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

GOOGLE_DOC_PDF_URL = os.getenv("GOOGLE_DOC_PDF_URL")

# =========================
# MODELS
# =========================
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=600,
    chunk_overlap=250
)

vectorstore = None


# =========================
# INIT VECTOR DB
# =========================
def initialize_vectorstore():
    global vectorstore

    response = requests.get(GOOGLE_DOC_PDF_URL)
    pdf_bytes = response.content

    reader = PdfReader(io.BytesIO(pdf_bytes))

    texts, metadatas = [], []

    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            chunks = text_splitter.split_text(text)
            for c in chunks:
                texts.append(c)
                metadatas.append({"page": i + 1})

    vectorstore = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
    vectorstore.save_local(FAISS_INDEX_PATH)


# =========================
# GET CONTEXT (UPDATED)
# =========================
def get_relevant_context(patient: PatientInput) -> str:
    global vectorstore

    if vectorstore is None:
        try:
            vectorstore = FAISS.load_local(
                FAISS_INDEX_PATH,
                embeddings,
                allow_dangerous_deserialization=True
            )
        except:
            initialize_vectorstore()

    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 15, "fetch_k": 40}
    )

    docs = retriever.get_relevant_documents(patient.symptoms)

    context = "\n\n---\n\n".join([d.page_content for d in docs])

    return context