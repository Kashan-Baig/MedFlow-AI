"""Wrapper for RAG retrieval."""
from app.ai.rag.rag_pipeline import run_rag

def get_context(symptoms: str):
    return run_rag(symptoms)
