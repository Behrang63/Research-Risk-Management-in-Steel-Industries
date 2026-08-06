import os
import json
import re
from typing import Dict, Any, List
try:
    import ollama
except ImportError:
    ollama = None  


class ProposalAnalyzerAgent:
    """
    عامل هوشمند ارزیابی پروپوزال با معماری تزریق شواهد قطعی (Evidence Injection)
    """

    def __init__(self, 
                 model_name: str = "llama3:latest",
                 drivers_path: str = "config/drivers.json",
                 skills_dir: str = "skills"):
        
        self.model_name = model_name
        self.drivers_path = drivers_path
        self.skills_dir = skills_dir
        
        self.drivers_data = self._load_json(self.drivers_path)
        self.skill_terminology = self._load_file(os.path.join(self.skills_dir, "SKILL_TERMINOLOGY.md"))
        self.skill_trl = self._load_file(os.path.join(self.skills_dir, "SKILL_TRL_EVAL.md"))
        self.skill_critique = self._load_file(os.path.join(self.skills_dir, "SKILL_PROPOSAL_CRITIQUE.md"))

    def _load_json(self, path: str) -> Dict[str, Any]:
        if not os.path.exists(path):
            return {"strategic_drivers": []}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_file(self, path: str) -> str:
        if not os.path.exists(path):
            return f"# Warning: Skill file {path} not found."
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _extract_evidence_sentences(self, proposal_text: str) -> List[str]:
        sentences = re.split(r'[.!?\n]', proposal_text)
        evidence_bank = []
        
        for driver in self.drivers_data.get("strategic_drivers", []):
            for kw in driver.get("keywords", []):
                for sentence in sentences:
                    clean_sentence = sentence.strip()
                    if kw.lower() in clean_sentence.lower() and len(clean_sentence) > 20:
                        if clean_sentence not in evidence_bank:
                            evidence_bank.append(clean_sentence)
        return evidence_bank

    def _build_system_prompt(self, evidence_bank: List[str], previous_feedback: str = None) -> str:
        drivers_summary = json.dumps(self.drivers_data.get("strategic_drivers", []), ensure_ascii=False, indent=2)
        
        evidence_str = "\n".join([f"{i+1}. {ev}" for i, ev in enumerate(evidence_bank)])
        if not evidence_str:
            evidence_str = "هیچ شاهد مستقیمی دارای کلیدواژه‌های استراتژیک در متن یافت نشد."

        feedback_section = ""
        if previous_feedback:
            feedback_section = f"""
\n🚨 [اخطار سیستم ممیزی - تلاش مجدد]:
در اجرای قبلی، خروجی شما به دلیل خطای زیر توسط سیستم کنترل کیفیت (QA) رد شد:
"{previous_feedback}"
شما موظف هستید این خطا را در این تلاش کاملاً برطرف کنید. تولید فیلد استنادی خالی یا نامعتبر مساوی با شکست سیستم است!
"""
        
        system_prompt = f"""
شما «عامل ارزیابی و غربالگری هوشمند پروپوزال‌های تافکو» هستید.{feedback_section}
وظیفه شما تحلیل دقیق فنی پروپوزال‌های R&D و تطبیق آن‌ها با پیشران‌های استراتژیک است.

---
### ۱. پایگاه دانش پیشران‌های استراتژیک تافکو:
{drivers_summary}

---
### ۲. فایل‌های مهارتی شما:
[مهارت ۱: واژگان تخصصی متالورژی]
{self.skill_terminology}

[مهارت ۲: سنجش و اصلاح TRL]
{self.skill_trl}

[مهارت ۳: نقد فنی و شناسایی نقاط ضعف]
{self.skill_critique}

---
### ۳. بانک شواهد استخراج‌شده (Evidence Bank) - قانون قطعی:
جملات زیر مستقیماً توسط موتور قطعی سیستم از متن پروپوزال استخراج شده‌اند. 
شما **فقط و فقط** مجاز هستید فیلد `reasoning_quote` را با کپی کردن دقیق یکی از جملات زیر پر کنید:

{evidence_str}

---
### ۴. دستورالعمل خروجی (خط قرمز):
- خروجی فقط و فقط فرمت JSON معتبر باشد.
- اگر برای پیشرانی در "بانک شواهد" جمله‌ای نیافتید، آن پیشران را استخراج نکنید.

ساختار دقیق JSON خروجی باید به شکل زیر باشد:
{{
  "proposal_summary": {{
    "title": "عنوان استخراج‌شده یا پیشنهادی طرح",
    "executive_summary": "خلاصه مدیریتی طرح در ۳ سطر کامل"
  }},
  "strategic_alignment": [
    {{
      "driver_id": "شناسه پیشران مرتبط",
      "driver_title": "عنوان پیشران",
      "direct_alignment_score": 85,
      "reasoning_quote": "الزامی: کپی دقیق و کلمه‌به‌کلمهِ یک جمله از بانک شواهد (بخش ۳). هرگز خالی نگذارید."
    }}
  ],
  "weighted_overall_score": 82.5,
  "trl_analysis": {{
    "claimed_trl": "TRL ادعا شده",
    "assessed_trl": "TRL ارزیابی‌شده",
    "gap_analysis": "نیازمندی‌ها برای TRL بالاتر"
  }},
  "technical_critique": {{
    "strengths": ["نقطه قوت ۱", "نقطه قوت ۲"],
    "weaknesses_and_risks": ["ریسک یا نقطه ضعف ۱", "ریسک ۲"],
    "red_flags": ["موارد مبهم"]
  }},
  "actionable_feedback_for_proposer": "پیشنهاد مشخص برای اصلاح",
  "final_recommendation": "یکی از موارد: [تایید اولیه / نیازمند اصلاح و بازنگری / رد اولیه]"
}}
"""
        return system_prompt

    # 🛡️ سپر دفاعی در پارامترها با استفاده از الگوی **kwargs
    def analyze(self, proposal_text: str, previous_feedback: str = None, **kwargs) -> Dict[str, Any]:
        """
        اجرای چرخه تحلیل پروپوزال.
        با استفاده از الگوی **kwargs، این لایه در برابر دریافت پارامترهای 
        پیش‌بینی‌نشده از سمت ارکستراتور، منعطف شده و دچار Crash نخواهد شد.
        """
        if not proposal_text or len(proposal_text.strip()) < 50:
            return {"error": "متن پروپوزال ورودی بسیار کوتاه یا نامعتبر است."}

        evidence_bank = self._extract_evidence_sentences(proposal_text)
        system_prompt = self._build_system_prompt(evidence_bank, previous_feedback)
        user_message = f"لطفاً پروپوزال زیر را با دقت بررسی و طبق دستورالعمل دقیقاً در قالب JSON خروجی دهید:\n\n{proposal_text}"

        try:
            if ollama is None:
                raise ImportError("کتابخانه ollama نصب نیست.")

            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                format="json",
                options={
                    "temperature": 0.0, 
                    "top_p": 0.9
                }
            )

            raw_output = response['message']['content'].strip()
            return self._clean_and_parse_json(raw_output)

        except Exception as e:
            return {
                "parsing_error": True,
                "error_message": str(e)
            }

    def _clean_and_parse_json(self, raw_text: str) -> Dict[str, Any]:
        try:
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if match:
                clean_json = match.group(0)
                return json.loads(clean_json)
            else:
                return json.loads(raw_text)
        except json.JSONDecodeError as e:
            return {
                "parsing_error": True,
                "message": f"خطا در پارس خروجی مدل: {str(e)}",
                "raw_response": raw_text
            }