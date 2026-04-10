# app/ai/rag_chatbot.py

import warnings
warnings.filterwarnings('ignore')
import os
import io
import requests
from PyPDF2 import PdfReader
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_groq.chat_models import ChatGroq
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import CrossEncoder

try:
    from dotenv import load_dotenv  # provided by python-dotenv
    load_dotenv()
except ModuleNotFoundError:
    # Allow running without dotenv; env vars can still be provided by the shell/host
    pass
# =========================
# CONFIG
# =========================
FAISS_INDEX_PATH = "faiss_index"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = "llama-3.1-8b-instant"

GOOGLE_DOC_PDF_URL = os.getenv("GOOGLE_DOC_PDF_URL")
# =========================
# INITIALIZE MODELS
# =========================
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
cross_encoder = CrossEncoder(CROSS_ENCODER_MODEL)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=600,
    chunk_overlap=250
)

# Global vectorstore
vectorstore = None

# =========================
# HELPER FUNCTIONS
# =========================

def download_google_doc_as_pdf(url: str) -> bytes:
    """Download Google Doc as PDF"""
    print("📥 Downloading medical knowledge base from Google Docs...")
    
    response = requests.get(url)
    
    if response.status_code == 200:
        print("✅ Downloaded successfully!")
        return response.content
    else:
        raise Exception(f"Failed to download: {response.status_code}")


def load_pdf_from_bytes(pdf_bytes: bytes):
    """Load PDF from bytes"""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    texts = []
    metadatas = []

    for i, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if page_text:
            chunks = text_splitter.split_text(page_text)
            for chunk in chunks:
                texts.append(chunk)
                metadatas.append({
                    "source": "Medical Knowledge Base",
                    "page": i + 1
                })

    return texts, metadatas


def initialize_vectorstore():
    """Download Google Doc and create vectorstore"""
    global vectorstore
    
    print("🚀 Initializing RAG System...\n")
    
    # Download PDF from Google Docs
    pdf_bytes = download_google_doc_as_pdf(GOOGLE_DOC_PDF_URL)
    
    # Extract text and create chunks
    print("📄 Processing medical knowledge...")
    texts, metadatas = load_pdf_from_bytes(pdf_bytes)
    
    # Create vectorstore
    print("🧠 Building vector database...")
    vectorstore = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
    
    # Save locally for faster future loads
    vectorstore.save_local(FAISS_INDEX_PATH)
    
    print(f"✅ RAG System Ready! ({len(texts)} chunks loaded)\n")


def rewrite_query(question: str) -> str:
    """Enhanced query rewriting"""
    llm = ChatGroq(
        model=LLM_MODEL,
        temperature=0,
        api_key=GROQ_API_KEY
    )

    prompt = f"""
Rewrite the following medical question into a clear, search-optimized query.
- Preserve key symptoms and medical terms
- Make it concise but comprehensive
- Return ONLY the rewritten question

Original Question:
{question}

Rewritten Query:
"""

    response = llm.invoke(prompt)
    return response.content.strip()


def rerank_documents(question: str, docs, top_k: int = 3):
    """Rerank documents using cross-encoder"""
    pairs = [(question, doc.page_content) for doc in docs]
    scores = cross_encoder.predict(pairs)

    scored_docs = list(zip(docs, scores))
    scored_docs.sort(key=lambda x: x[1], reverse=True)

    return [doc for doc, _ in scored_docs[:top_k]]


def get_answer(question: str) -> str:
    """Main function to get answer from RAG system"""
    global vectorstore
    
    if vectorstore is None:
        raise ValueError("Vectorstore not initialized. Run initialize_vectorstore() first.")
    
    # Step 1: Rewrite query
    rewritten_question = rewrite_query(question)
    
    # Step 2: Retrieve documents
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 15, "fetch_k": 40}
    )
    docs = retriever.get_relevant_documents(rewritten_question)
    
    # Step 3: Rerank
    top_docs = rerank_documents(rewritten_question, docs, top_k=3)
    
    # Step 4: Combine context
    context = "\n\n---\n\n".join([doc.page_content for doc in top_docs])
    
    # Step 5: Generate answer
    llm = ChatGroq(
        model=LLM_MODEL,
        temperature=0,
        api_key=GROQ_API_KEY
    )

    prompt = f"""You are a medical assistant helping with symptom analysis.

MEDICAL KNOWLEDGE:
{context}

PATIENT QUESTION:
{question}

Provide a clear, helpful response based on the medical knowledge provided.
Be professional and concise.

Answer:"""

    response = llm.invoke(prompt)
    return response.content.strip()


# =========================
# TERMINAL INTERFACE
# =========================

def chat():
    """Terminal-based chat interface"""
    global vectorstore
    
    print("=" * 60)
    print("🏥 MEDFLOW AI - Medical Assistant Chatbot")
    print("=" * 60)
    
    # Initialize on first run
    if vectorstore is None:
        initialize_vectorstore()
    
    print("💬 You can now ask medical questions!")
    print("   Type 'exit' or 'quit' to end the session.\n")
    
    while True:
        # Get user input
        user_input = input("You: ").strip()
        
        # Check for exit
        if user_input.lower() in ['exit', 'quit', 'q']:
            print("\n👋 Thank you for using MedFlow AI. Stay healthy!")
            break
        
        if not user_input:
            continue
        
        # Get answer
        try:
            print("\n🤔 Analyzing your symptoms...\n")
            answer = get_answer(user_input)
            print(f"🏥 Assistant: {answer}\n")
            print("-" * 60 + "\n")
        
        except Exception as e:
            print(f"❌ Error: {str(e)}\n")


# =========================
# RUN
# =========================

if __name__ == "__main__":
    chat()