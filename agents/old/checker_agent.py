import json
import re
from typing import Dict, Any, Tuple
try:
    import ollama
except ImportError:
    ollama = None


class CheckerAgent:
    """
    عامل ممیزی با رویکرد فیلترینگ قطعی (Deterministic Filtering)
    وظیفه: اعتبارسنجی خروجی Analyzer Agent با تاکید بر عدم توهم و بررسی عمیق منطق فنی
    """

    def __init__(self, model_name: str = "llama3:latest"):
        self.model_name = model_name

    def _normalize_text(self, text: str) -> str:
        """حذف فاصله‌ها و کاراکترهای نامرئی برای مقایسه دقیق و قطعی پایتونی"""
        return re.sub(r'\s+', '', text).strip()

    def _validate_hard_constraints(self, original_proposal: str, data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        بررسی قوانین فیزیکی و قطعی که LLM حق نقض آن‌ها را ندارد (فیلتر اول - بدون دخالت هوش مصنوعی).
        """
        if "error" in data or "parsing_error" in data:
            return False, "خطای ساختاری در JSON خروجی."

        required_keys = [
            "proposal_summary", "strategic_alignment", "weighted_overall_score", 
            "trl_analysis", "technical_critique", "actionable_feedback_for_proposer", 
            "final_recommendation"
        ]

        for key in required_keys:
            if key not in data:
                return False, f"فیلد اجباری '{key}' یافت نشد."

        # بررسی تنبلی و توهم در استنادات
        alignments = data.get("strategic_alignment", [])
        if not alignments:
            return False, "هیچ پیشرانی استخراج نشده است (تنبلی مدل در تخصیص استراتژیک)."
            
        normalized_proposal = self._normalize_text(original_proposal)
        
        for idx, item in enumerate(alignments):
            quote = item.get("reasoning_quote", "")
            
            # فیلتر فیزیکی اول: بررسی طول و محتوای رشته
            if not isinstance(quote, str) or len(quote.strip()) < 15:
                return False, f"استناد پیشران {item.get('driver_id', f'شماره {idx}')} خالی یا بسیار کوتاه است."
            
            # فیلتر فیزیکی دوم (Anti-Hallucination): آیا این استناد واقعاً در متن وجود دارد؟
            normalized_quote = self._normalize_text(quote)
            if normalized_quote not in normalized_proposal:
                return False, f"توهم کشف شد: استناد '{quote[:30]}...' به صورت عینی در متن اصلی پروپوزال وجود ندارد."

        return True, "قوانین قطعی سیستم و صحت استنادات تأیید شدند."

    def _build_checker_prompt(self, original_proposal: str, analyzer_output: Dict[str, Any]) -> str:
        """
        ساخت پرامپت تحلیلی. از آنجایی که استنادات قبلا توسط پایتون تایید شده، 
        تمرکز مدل ممیز صرفاً روی منطق و عمق فنی خواهد بود.
        """
        prompt = f"""
شما «ممیز ارشد کیفی سیستم‌های هوش مصنوعی (QA Agent)» هستید.
خروجی ارائه شده از نظر «قوانین قطعی استناد» توسط هسته پایتون سیستم تایید شده است (استنادات ۱۰۰٪ واقعی هستند).
وظیفه شما اکنون صرفاً بررسی «منطق تخصصی، عدم کلی‌گویی و لحن مهندسی» است.

خروجی تولیدشده (جهت ممیزی عمیق فنی):
\"\"\"
{json.dumps(analyzer_output, ensure_ascii=False, indent=2)}
\"\"\"

بررسی کنید:
۱. آیا تحلیل TRL منطقی و مبتنی بر شواهد است؟
۲. آیا نقاط ضعف و قوت تخصصی نوشته شده‌اند (آیا از کلی‌گویی و بدیهیات پرهیز شده است)؟

خروجی دقیقاً قالب JSON زیر باشد:
{{
  "is_passed": true/false,
  "audit_score": 90,
  "detected_issues": [
    "شرح دقیق خطای منطقی یافت‌شده (مثلاً عدم تطابق TRL با فاز توسعه)"
  ],
  "reasoning": "علت تایید یا رد تخصصی",
  "corrected_output": {{
    // فقط در صورت false بودن is_passed، جیسون اصلاح‌شده با ارتقاء لحن و عمق فنی را اینجا درج کنید.
  }}
}}
"""
        return prompt

    def verify_and_audit(self, original_proposal: str, analyzer_output: Dict[str, Any]) -> Dict[str, Any]:
        """اجرای چرخه ممیزی دو مرحله‌ای (قطعی + معنایی)"""
        
        # گام ۱: سد قطعی پایتون (مهم‌ترین مرحله برای مسدودسازی تنبلی و توهم)
        is_valid, struct_msg = self._validate_hard_constraints(original_proposal, analyzer_output)
        if not is_valid:
            # رد شدن در این مرحله نیازی به فراخوانی LLM ندارد و در مصرف منابع صرفه‌جویی می‌کند
            return {
                "audit_passed": False,
                "audit_source": "Deterministic_Python_Engine",
                "rejection_reason": struct_msg,
                "action_required": "فراخوانی مجدد Analyzer به دلیل نقض قوانین فیزیکی سیستم (تنبلی یا توهم)."
            }

        # گام ۲: بررسی مفهومی و عمق فنی توسط LLM ممیز
        if ollama is None:
            return {
                "audit_passed": True,
                "audit_source": "Deterministic_Only",
                "warning": "کتابخانه ollama نصب نیست، تاییدیه بر اساس قوانین قطعی صادر شد.",
                "verified_output": analyzer_output
            }

        try:
            checker_prompt = self._build_checker_prompt(original_proposal, analyzer_output)
            
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "فقط JSON معتبر خروجی دهید."},
                    {"role": "user", "content": checker_prompt}
                ],
                format="json",
                options={
                    "temperature": 0.0 # قفل کردن دما برای رویکرد تحلیلی قطعی
                }
            )

            raw_text = response['message']['content'].strip()
            audit_result = self._clean_json_str(raw_text)

            if audit_result.get("is_passed", False):
                return {
                    "audit_passed": True,
                    "audit_score": audit_result.get("audit_score", 100),
                    "audit_notes": audit_result.get("reasoning", "تایید کامل کیفی"),
                    "final_verified_output": analyzer_output
                }
            else:
                corrected = audit_result.get("corrected_output")
                return {
                    "audit_passed": False,
                    "audit_source": "LLM_Logic_Audit",
                    "audit_score": audit_result.get("audit_score", 0),
                    "rejection_reason": audit_result.get("reasoning", "خروجی اولیه رد شد."),
                    "detected_issues": audit_result.get("detected_issues", []),
                    "corrected_output": corrected if corrected else analyzer_output
                }

        except Exception as e:
            return {
                "audit_passed": True,
                "audit_source": "Programmatic_Fallback",
                "warning": f"خطا در اجرای ممیزی عمیق LLM: {str(e)}",
                "final_verified_output": analyzer_output
            }

    def _clean_json_str(self, text: str) -> Dict[str, Any]:
        """استخراج JSON از متون"""
        try:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return json.loads(text)
        except json.JSONDecodeError:
            return {"is_passed": False, "reasoning": "Failed to parse Checker output."}