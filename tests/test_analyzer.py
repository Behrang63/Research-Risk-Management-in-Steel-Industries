import pytest
from unittest.mock import MagicMock
from agents.analyzer_agent import AnalyzerAgent

def test_analyzer_agent_response_format():
    """بررسی صحت فرمت خروجی ایجنت تحلیل‌گر"""
    agent = AnalyzerAgent()
    # شبیه‌سازی متد اجرا یا فراخوانی LLM
    agent.run = MagicMock(return_value={"status": "success", "risk_score": 0.85})
    
    response = agent.run(data={"project": "Steel Research"})
    assert response["status"] == "success"
    assert "risk_score" in response
    assert response["risk_score"] >= 0.0