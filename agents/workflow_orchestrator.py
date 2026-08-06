from typing import Dict, Any
import logging
from agents.analyzer_agent import ProposalAnalyzerAgent
from agents.checker_agent import CheckerAgent

# تنظیم پایه لاگر سیستم برای مانیتورینگ دقیق چرخه‌ها در ترمینال و فایل‌های لاگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ProposalWorkflowOrchestrator:
    """
    ارکستراتور گردش کار (Workflow Orchestrator)
    وظیفه: مدیریت چرخه خود‌اصلاحی (Self-Correction Loop) در حالت حلقه بسته.
    تا زمانی که خروجی Analyzer به تایید ممیز قطعی Checker نرسد، چرخه بازخورد ادامه دارد.
    """

    def __init__(self, max_retries: int = 3, model_name: str = "llama3:latest"):
        # رفع نقص هم‌پوشانی: متد سازنده تکراری حذف و با قابلیت تزریق پویای مدل یکپارچه شد.
        self.analyzer = ProposalAnalyzerAgent(model_name=model_name)
        self.checker = CheckerAgent(model_name=model_name)
        self.max_retries = max_retries

    def process_proposal(self, proposal_text: str) -> Dict[str, Any]:
        """
        اجرای چرخه خود‌اصلاحی (Self-Correction Pipeline) با پایش دقیق لایه‌ها
        """
        feedback_from_checker = None

        for attempt in range(1, self.max_retries + 1):
            logging.info(f"شروع اجرای چرخه {attempt}/{self.max_retries}...")
            
            # گام ۱: استخراج معنایی شواهد و تحلیل اولیه با تزریق فیدبک دورهای قبلی
            analyzer_output = self.analyzer.analyze(
                proposal_text=proposal_text, 
                previous_feedback=feedback_from_checker
            )

            # بررسی خطاهای ساختاری فیزیکی (خارج از کنترل مستقیم مدل)
            if "error" in analyzer_output or "parsing_error" in analyzer_output:
                feedback_from_checker = analyzer_output.get("message", "خطا در تولید JSON ساختاریافته.")
                logging.warning(f"چرخه {attempt} با خطای ساختاری متوقف شد: {feedback_from_checker}")
                continue

            # گام ۲: ارزیابی توسط سیستم قطعی Checker (ممیزی باینری پایتون + ممیزی معنایی LLM)
            logging.info("ارسال خروجی به موتور Checker برای اعتبارسنجی فیزیکی و منطقی...")
            audit_result = self.checker.verify_and_audit(
                original_proposal=proposal_text, 
                analyzer_output=analyzer_output
            )

            # گام ۳: تصمیم‌گیری سیستمیک بر اساس نتیجه ممیزی (Core Logic)
            if audit_result.get("audit_passed"):
                logging.info(f"✅ خروجی در چرخه {attempt} با موفقیت تایید شد.")
                return {
                    "status": "success",
                    "attempts": attempt,
                    "final_data": audit_result.get("final_verified_output")
                }
            
            # ثبت دلیل رد شدن و تزریق آن به عنوان اخطار سیستمی برای هدایت رفتار مدل در دور بعد
            feedback_from_checker = audit_result.get("rejection_reason", "خروجی نامعتبر است.")
            logging.warning(f"❌ خروجی در چرخه {attempt} رد شد. دلیل: {feedback_from_checker}")

            # در صورت رسیدن به سقف مجاز تلاش‌ها بدون اخذ تاییدیه ممیز
            if attempt == self.max_retries:
                logging.error("حداکثر تعداد تلاش‌های مجاز به پایان رسید. سیستم متوقف شد.")
                return {
                    "status": "failed",
                    "attempts": attempt,
                    "last_rejection_reason": feedback_from_checker,
                    "partial_data": audit_result.get("corrected_output", analyzer_output)
                }

        return {"status": "critical_error", "message": "خطای ناشناخته در گردش کار."}