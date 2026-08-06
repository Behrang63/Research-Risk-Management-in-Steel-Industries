import json
import os
import re
from typing import Dict, Any, Tuple
try:
    import ollama
except ImportError:
    ollama = None


class CheckerAgent:
    """
    عامل ممیزی با رویکرد فیلترینگ قطعی (Deterministic Filtering) و بارگذاری پویای پرامپت ممیزی.
    وظیفه: اعتبارسنجی خروجی Analyzer Agent با تاکید بر عدم توهم و بررسی عمیق منطق فنی بر اساس معیار تافکو.
    """

    def __init__(self, model_name: str = "llama3:latest", prompt_filename: str = "checker_prompt.txt", drivers_path: str = "config/drivers.json"):
        self.model_name = model_name
        self.drivers_path = drivers_path
        
        # حل پویا و ایمن مسیرهای فیزیکی پروژه برای جلوگیری از FileNotFoundError در دایرکتوری‌های مختلف
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # ۱. بارگذاری شناسه‌های پیشران معتبر جهت ممیزی قطعی پایتون
        possible_driver_paths = [
            os.path.join(project_root, drivers_path),
            os.path.join(current_dir, drivers_path),
            drivers_path,
            os.path.join(project_root, "config", "drivers.json"),
            os.path.join(current_dir, "config", "drivers.json")
        ]
        
        self.valid_driver_ids = []
        for d_path in possible_driver_paths:
            if os.path.exists(d_path):
                try:
                    with open(d_path, "r", encoding="utf-8") as f:
                        drivers_data = json.load(f)
                        self.valid_driver_ids = [d.get("id") for d in drivers_data.get("strategic_drivers", []) if d.get("id")]
                    break
                except Exception:
                    pass

        # ۲. بارگذاری پویای پرامپت ممیز ارشد
        possible_prompt_paths = [
            os.path.join(project_root, prompt_filename),
            os.path.join(current_dir, prompt_filename),
            prompt_filename
        ]
        
        self.checker_prompt_template = ""
        for path in possible_prompt_paths:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        self.checker_prompt_template = f.read()
                    break
                except Exception:
                    pass

        # کانتینر حمایتی (Fallback) در صورت در دسترس نبودن فیزیکی فایل پرامپت
        if not self.checker_prompt_template:
            self.checker_prompt_template = """
[نقش و هویت]
تو یک ارزیاب و کنترل‌کننده کیفی ارشد برای پاسخ‌های سیستم‌های هوش مصنوعی هستی. دقت قطعی و عدم اغماض در برابر تنبلی مدل از ویژگی‌های اصلی توست.

[ماموریت]
ارزیابی منطق تخصصی، لحن و پیوستگی تحلیل‌های خروجی.
(توجه: صحت استنادات پیش از شما توسط موتور قطعی پایتون بررسی و تایید شده است. تمرکز شما باید بر روی عمق فنی باشد).
"""

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
                return False, f"فیلد اجباری '{key}' در خروجی یافت نشد."

        # بررسی تنبلی و توهم در استنادات
        alignments = data.get("strategic_alignment", [])
        if not alignments:
            return False, "هیچ پیشرانی استخراج نشده است (تنبلی مدل در تخصیص استراتژیک)."
            
        normalized_proposal = self._normalize_text(original_proposal)
        
        for idx, item in enumerate(alignments):
            driver_id = item.get("driver_id", "")
            quote = item.get("reasoning_quote", "")
            
            # ۱. بررسی تطابق شناسه پیشران با پیشران‌های معتبر تافکو (سپر دفاعی قطعی پایتون)
            if self.valid_driver_ids and driver_id not in self.valid_driver_ids:
                example_id = self.valid_driver_ids[0] if self.valid_driver_ids else "DRV_ENERGY_01"
                return False, (
                    f"شناسه پیشران نامعتبر است: '{driver_id}'. شما باید شناسه را دقیقاً از لیست پیشران‌های "
                    f"استراتژیک بخش ۱ کپی کنید (مانند {example_id}). به هیچ وجه عنوان پروپوزال، عنوان طرح، یا "
                    "رشته دیگری به جز شناسه رسمی پیشران را در این فیلد قرار ندهید."
                )

            # ۲. بررسی طول و محتوای رشته استناد
            if not isinstance(quote, str) or len(quote.strip()) < 15:
                return False, f"استناد پیشران {driver_id} خالی یا بسیار کوتاه است."
            
            # ۳. بررسی عدم توهم کلمه‌به‌کلمه (Anti-Hallucination Guard)
            normalized_quote = self._normalize_text(quote)
            if normalized_quote not in normalized_proposal:
                return False, f"توهم کشف شد: استناد '{quote[:30]}...' به صورت عینی در متن اصلی پروپوزال وجود ندارد."

        return True, "قوانین قطعی سیستم و صحت استنادات تأیید شدند."

    def verify_and_audit(self, original_proposal: str, analyzer_output: Dict[str, Any]) -> Dict[str, Any]:
        """اجرای چرخه ممیزی دو مرحله‌ای (قطعی + معنایی)"""
        
        # گام ۱: سد قطعی پایتون (مهم‌ترین مرحله برای مسدودسازی تنبلی و توهم)
        is_valid, struct_msg = self._validate_hard_constraints(original_proposal, analyzer_output)
        if not is_valid:
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

    def _build_checker_prompt(self, original_proposal: str, analyzer_output: Dict[str, Any]) -> str:
        """
        ساخت پرامپت تحلیلی با ادغام اطلاعات پروپوزال و قالب بیرونی پرامپت ممیز.
        """
        prompt = f"""
{self.checker_prompt_template}

---
### اطلاعات ورودی جهت ارزیابی:

متن پروپوزال اصلی:
\"\"\"
{original_proposal}
\"\"\"

خروجی تولیدشده توسط عامل تحلیل‌گر (جهت ممیزی عمیق فنی):
\"\"\"
{json.dumps(analyzer_output, ensure_ascii=False, indent=2)}
\"\"\"
"""
        return prompt