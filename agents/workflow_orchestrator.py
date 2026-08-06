import logging
from typing import Dict, Any

try:
    from agents.analyzer_agent import ProposalAnalyzerAgent, AnalyzerAgent
    from agents.checker_agent import CheckerAgent, ProposalCheckerAgent
except ImportError:
    from analyzer_agent import ProposalAnalyzerAgent, AnalyzerAgent
    from checker_agent import CheckerAgent, ProposalCheckerAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ProposalWorkflowOrchestrator:
    def __init__(self, max_retries: int = 3, model_name: str = "llama3.2"):
        self.analyzer = ProposalAnalyzerAgent(model_name=model_name)
        self.checker = CheckerAgent(model_name=model_name)
        self.max_retries = max_retries
        # سایر بخش‌های کد بدون تغییر باقی می‌مانند...

    def _audit_output(self, proposal_text: str, analyzer_output: Dict[str, Any]) -> Dict[str, Any]:
        if hasattr(self.checker, "verify_and_audit"):
            return self.checker.verify_and_audit(
                original_proposal=proposal_text, 
                analyzer_output=analyzer_output
            )
        
        check_res = self.checker.check(
            proposal_text=proposal_text, 
            analysis_result=analyzer_output
        )
        
        is_passed = check_res.get("is_valid", False)
        return {
            "audit_passed": is_passed,
            "rejection_reason": check_res.get("feedback", "خروجی توسط ممیز رد شد."),
            "final_verified_output": analyzer_output if is_passed else None,
            "corrected_output": analyzer_output
        }

    def process_proposal(self, proposal_text: str) -> Dict[str, Any]:
        feedback_from_checker = None
        last_analyzer_output = {}

        for attempt in range(1, self.max_retries + 1):
            logging.info(f"شروع اجرای چرخه {attempt}/{self.max_retries}...")
            
            analyzer_output = self.analyzer.analyze(
                proposal_text=proposal_text, 
                previous_feedback=feedback_from_checker
            )
            last_analyzer_output = analyzer_output

            if "error" in analyzer_output or "parsing_error" in analyzer_output:
                feedback_from_checker = analyzer_output.get("message", "خطا در تولید JSON ساختاریافته.")
                logging.warning(f"چرخه {attempt} با خطای ساختاری متوقف شد: {feedback_from_checker}")
                
                if attempt == self.max_retries:
                    return {
                        "status": "failed",
                        "attempts": attempt,
                        "last_rejection_reason": f"عدم تولید JSON معتبر پس از {self.max_retries} تلاش: {feedback_from_checker}",
                        "partial_data": analyzer_output
                    }
                continue

            audit_result = self._audit_output(
                proposal_text=proposal_text, 
                analyzer_output=analyzer_output
            )

            if audit_result.get("audit_passed"):
                logging.info(f"✅ خروجی در چرخه {attempt} با موفقیت تایید شد.")
                return {
                    "status": "success",
                    "attempts": attempt,
                    "final_data": audit_result.get("final_verified_output", analyzer_output)
                }
            
            feedback_from_checker = audit_result.get("rejection_reason", "خروجی نامعتبر است.")
            logging.warning(f"❌ خروجی در چرخه {attempt} رد شد. دلیل: {feedback_from_checker}")

            if attempt == self.max_retries:
                logging.error("حداکثر تعداد تلاش‌های مجاز به پایان رسید.")
                return {
                    "status": "failed",
                    "attempts": attempt,
                    "last_rejection_reason": feedback_from_checker,
                    "partial_data": audit_result.get("corrected_output", analyzer_output)
                }

        return {
            "status": "failed",
            "attempts": self.max_retries,
            "last_rejection_reason": "فرآیند به حداکثر تلاش رسید.",
            "partial_data": last_analyzer_output
        }

    def run_pipeline(self, proposal_text: str = "", **kwargs) -> Dict[str, Any]:
        return self.process_proposal(proposal_text)


WorkflowOrchestrator = ProposalWorkflowOrchestrator