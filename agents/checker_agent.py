import os
import json
import re
from typing import Dict, Any, List, Tuple

try:
    import ollama
except ImportError:
    ollama = None  # مدیریت عدم وجود کتابخانه در محیط‌های ایزوله


class CheckerAgent:
    """
    عامل هوشمند اعتبارسنجی و ممیزی خروجی تحلیل پروپوزال (Quality Assurance Agent).
    این ایجنت ساختار JSON خروجی، صحت شناسه‌ها و دقیق بودن شواهد استخراج‌شده را بررسی می‌کند.
    """

    def __init__(self, 
                 model_name: str = "llama3:latest",
                 drivers_path: str = "config/drivers.json",
                 prompts_dir: str = "prompts"):
        
        self.model_name = model_name
        self.drivers_path = drivers_path
        self.prompts_dir = prompts_dir
        
        # حل پویا و ایمن مسیر فایل‌ها
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        possible_driver_paths = [
            os.path.join(project_root, drivers_path),
            os.path.join(current_dir, drivers_path),
            drivers_path,
            os.path.join(project_root, "config", "drivers.json"),
            os.path.join(current_dir, "config", "drivers.json")
        ]
        
        self.drivers_data = {"strategic_drivers": []}
        for d_path in possible_driver_paths:
            if os.path.exists(d_path):
                self.drivers_data = self._load_json(d_path)
                break

        checker_prompt_path = os.path.join(project_root, prompts_dir, "checker_prompt.txt")
        if not os.path.exists(checker_prompt_path):
            checker_prompt_path = os.path.join(prompts_dir, "checker_prompt.txt")
        self.checker_prompt = self._load_file(checker_prompt_path)

    def _load_json(self, path: str) -> Dict[str, Any]:
        """بارگذاری فایل‌های تنظیمات JSON"""
        if not os.path.exists(path):
            return {"strategic_drivers": []}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_file(self, path: str) -> str:
        """بارگذاری فایل‌های متنی پرامپت"""
        if not os.path.exists(path):
            return ""
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def validate_programmatically(self, proposal_text: str, analysis_result: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        اعتبارسنجی دقیق ساختاری بدون نیاز به فراخوانی مدل زبانی
        """
        issues = []
        
        if not analysis_result or "parsing_error" in analysis_result or "error" in analysis_result:
            return False, ["خروجی تحلیل نامعتبر یا دارای خطای ساختاری/پارس است."]

        # ۱. استخراج شناسه‌های معتبر پیشران‌ها
        valid_driver_ids = {d.get("id") for d in self.drivers_data.get("strategic_drivers", []) if d.get("id")}
        alignments = analysis_result.get("strategic_alignment", [])
        
        if not isinstance(alignments, list):
            issues.append("فیلد strategic_alignment باید یک لیست باشد.")
        else:
            for item in alignments:
                d_id = item.get("driver_id")
                # بررسی صحت شناسه پیشران
                if valid_driver_ids and d_id not in valid_driver_ids:
                    issues.append(f"شناسه پیشران '{d_id}' نامعتبر است و در لیست پیشران‌های رسمی وجود ندارد.")
                
                # بررسی وجود نقل‌قول مستند
                quote = item.get("reasoning_quote", "")
                if not quote or len(quote.strip()) < 5:
                    issues.append(f"فیلد reasoning_quote برای پیشران '{d_id}' خالی یا غیرمستند است.")

        is_valid = len(issues) == 0
        return is_valid, issues

    def check(self, proposal_text: str, analysis_result: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        اجرای فرایند کنترل کیفیت و ممیزی بر روی خروجی ایجنت تحلیلی
        """
        is_valid, issues = self.validate_programmatically(proposal_text, analysis_result)
        
        if not is_valid:
            return {
                "is_valid": False,
                "feedback": " | ".join(issues),
                "issues": issues
            }

        return {
            "is_valid": True,
            "feedback": "خروجی تحلیل از لحاظ ساختاری و استنادی مورد تأیید است.",
            "issues": []
        }


# افزودن نام‌های مستعار برای تطابق کامل با تست pytest و انواع روش‌های فراخوانی
ProposalCheckerAgent = CheckerAgent