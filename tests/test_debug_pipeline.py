import sys
import os
import json
import pytest

# تنظیم کدگذاری UTF-8 برای خروجی‌های ویندوز
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

agents_dir = os.path.join(PROJECT_ROOT, "agents")
if os.path.exists(agents_dir) and agents_dir not in sys.path:
    sys.path.insert(0, agents_dir)

try:
    from agents.workflow_orchestrator import ProposalWorkflowOrchestrator
except ImportError:
    from workflow_orchestrator import ProposalWorkflowOrchestrator

TEST_PROPOSAL = """موضوع پروپوزال: بومی‌سازی کاتالیست‌های نیکلی ریفرمر مدول‌های احیاء مستقیم هلدینگ فولاد خوزستان

شرح فنی پروژه:
کاتالیست‌های ریفرمر از اجزای استراتژیک تولید گاز احیایی هستند. در این طرح با فرمولاسیون جدید پایه کاتالیست موفق به کاهش رسوب کربن شده‌ایم.

سطح بلوغ فناوری (TRL):
تیم پژوهشی نمونه‌ها را در مقیاس آزمایشگاهی تست کرده و پایداری آن اثبات شده است (TRL 4)."""


def test_run_pipeline_diagnostic():
    """
    تست خط لوله ارزیابی اختصاصی برای مدل llama3.2
    """
    print("\n==================================================")
    print("[SEARCH] [1/3] Initializing ProposalWorkflowOrchestrator with llama3.2...")
    print("==================================================")
    
    orchestrator = ProposalWorkflowOrchestrator(max_retries=3, model_name="llama3.2")
    print("[OK] Orchestrator instance created successfully.")

    print("\n==================================================")
    print("[START] [2/3] Executing process_proposal pipeline...")
    print("==================================================")
    
    result = orchestrator.process_proposal(TEST_PROPOSAL)
    
    print("\n==================================================")
    print("[RESULT] [3/3] Evaluating output structure:")
    print("==================================================")
    print(f"* Output Status: '{result.get('status')}'")
    print(f"* Total Attempts: {result.get('attempts')}")
    
    if result.get("status") == "success":
        print("\n[SUCCESS] Proposal evaluated and approved.")
    else:
        print(f"\n[INFO] Pipeline finished with status: {result.get('status')}")
        if "last_rejection_reason" in result:
            print(f"* Reason: {result.get('last_rejection_reason')}")
            
    assert result.get("status") in ["success", "failed"], f"Unexpected status: {result.get('status')}"