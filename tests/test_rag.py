import pytest
from unittest.mock import Mock, patch
from agents.rag_retriever import RAGRetriever

def test_rag_retriever_initialization():
    """بررسی مقداردهی اولیه RAGRetriever"""
    retriever = RAGRetriever()
    assert retriever is not None

@patch('agents.rag_retriever.RAGRetriever.query')
def test_rag_retriever_query_mock(mock_query):
    """بررسی بازیابی اسناد با Mock"""
    mock_query.return_value = ["مستند نمونه ارزیابی ریسک صنعت فولاد"]
    retriever = RAGRetriever()
    result = retriever.query("ریسک تولید فولاد")
    
    assert len(result) > 0
    assert "فولاد" in result[0]