import pytest
from agents.checker_agent import CheckerAgent


def test_checker_initialization():
    """تست مقداردهی اولیه و وجود متدهای اصلی در ایجنت ممیزی"""
    checker = CheckerAgent()
    assert checker is not None
    assert hasattr(checker, "check")
    assert hasattr(checker, "validate_programmatically")


def test_validate_programmatically_valid_data():
    """تست تایید خروجی معتبر (بدون خطا)"""
    checker = CheckerAgent()
    checker.drivers_data = {
        "strategic_drivers": [{"id": "DRV_ENERGY_01", "title": "بهینه‌سازی مصرف انرژی"}]
    }
    
    proposal_text = "این پروپوزال شامل روش‌های پیشرفته کاهش مصرف انرژی کوره است."
    analysis_result = {
        "strategic_alignment": [
            {
                "driver_id": "DRV_ENERGY_01",
                "driver_title": "بهینه‌سازی مصرف انرژی",
                "reasoning_quote": "این پروپوزال شامل روش‌های پیشرفته کاهش مصرف انرژی کوره است."
            }
        ]
    }
    
    is_valid, issues = checker.validate_programmatically(proposal_text, analysis_result)
    assert is_valid is True
    assert len(issues) == 0


def test_validate_programmatically_invalid_driver_id():
    """تست شناسایی و رد کردن شناسه پیشران نامعتبر"""
    checker = CheckerAgent()
    checker.drivers_data = {
        "strategic_drivers": [{"id": "DRV_ENERGY_01", "title": "بهینه‌سازی مصرف انرژی"}]
    }
    
    proposal_text = "متن پروپوزال ارزیابی."
    analysis_result = {
        "strategic_alignment": [
            {
                "driver_id": "UNKNOWN_DRIVER_99",
                "reasoning_quote": "متن پروپوزال ارزیابی."
            }
        ]
    }
    
    is_valid, issues = checker.validate_programmatically(proposal_text, analysis_result)
    assert is_valid is False
    assert len(issues) > 0
    assert any("نامعتبر" in issue for issue in issues)


def test_check_execution_with_parsing_error():
    """تست واکنش ممیز به خطاهای پارس داده‌ها"""
    checker = CheckerAgent()
    invalid_analysis = {"parsing_error": True, "message": "فرمت JSON نامعتبر است."}
    
    result = checker.check("متن پروپوزال", invalid_analysis)
    assert result["is_valid"] is False
    assert "feedback" in result
    assert len(result["issues"]) > 0