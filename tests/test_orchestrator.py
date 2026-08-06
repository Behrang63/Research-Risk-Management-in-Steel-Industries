import pytest
from agents.workflow_orchestrator import WorkflowOrchestrator


def test_orchestrator_max_retries_handling(mocker):
    """تست رفتار ارکستراتور هنگام رسیدن به سقف مجاز تلاش‌ها در صورت خروجی نامعتبر"""
    orchestrator = WorkflowOrchestrator(max_retries=2)
    
    # شبیه‌سازی خروجی نامعتبر از Analyzer
    mock_analyzer_output = {
        "strategic_alignment": [{"driver_id": "INVALID_ID", "reasoning_quote": ""}]
    }
    mocker.patch.object(orchestrator.analyzer, 'analyze', return_value=mock_analyzer_output)
    
    # اجرا pipeline
    result = orchestrator.process_proposal("متن نمونه پروپوزال R&D")
    
    assert result["status"] == "failed"
    assert result["attempts"] == 2
    assert "last_rejection_reason" in result