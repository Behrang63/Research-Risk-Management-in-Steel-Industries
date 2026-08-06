import os
import json
import re
from typing import Dict, Any, List

# وارد کردن ایمن موتور بازیابی معنایی (Semantic RAG) با گارد مسیردهی مطلق
try:
    from agents.rag_retriever import SemanticRagRetriever
except ImportError:
    try:
        from rag_retriever import SemanticRagRetriever
    except ImportError:
        SemanticRagRetriever = None

try:
    import ollama
except ImportError:
    ollama = None  # مدیریت عدم وجود کتابخانه در محیط‌های ایزوله


class ProposalAnalyzerAgent:
    """
    عامل هوشمند ارزیابی پروپوزال با معماری تزریق شواهد قطعی (Evidence Injection)،
    پشتیبانی از لایه بازیابی معنایی (Semantic RAG) و حلقه بازخورد اصلاح خودکار.
    """

    def __init__(self, 
                 model_name: str = "llama3:latest",
                 drivers_path: str = "config/drivers.json",
                 skills_dir: str = "skills"):
        
        self.model_name = model_name
        self.drivers_path = drivers_path
        self.skills_dir = skills_dir
        
        # حل پویا و ایمن مسیر فایل پیشران‌ها جهت هماهنگی با Streamlit
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
                
        self.skill_terminology = self._load_file(os.path.join(self.skills_dir, "SKILL_TERMINOLOGY.md"))
        self.skill_trl = self._load_file(os.path.join(self.skills_dir, "SKILL_TRL_EVAL.md"))
        self.skill_critique = self._load_file(os.path.join(self.skills_dir, "SKILL_PROPOSAL_CRITIQUE.md"))

        # نمونه‌سازی موتور بازیابی معنایی با شرایط بهینه محاسباتی
        if SemanticRagRetriever is not None:
            self.retriever = SemanticRagRetriever(threshold=0.15, max_evidence_count=8)
        else:
            self.retriever = None

    def _load_json(self, path: str) -> Dict[str, Any]:
        """بارگذاری فایل JSON کانفیگ پیشران‌ها"""
        if not os.path.exists(path):
            return {"strategic_drivers": []}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_file(self, path: str) -> str:
        """بارگذاری متن فایل‌های مهارتی"""
        if not os.path.exists(path):
            return f"# Warning: Skill file {path} not found."
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _extract_evidence_sentences(self, proposal_text: str) -> List[str]:
        """
        تغییر معماری: استفاده از موتور RAG معنایی پایتون به جای جستجوی کاراکتری سنتی
        جهت استخراج عمیق‌ترین همبستگی‌ها و مسدودسازی تنبلی (Model Laziness).
        """
        if self.retriever is not None:
            return self.retriever.retrieve_evidence(
                proposal_text=proposal_text,
                strategic_drivers=self.drivers_data.get("strategic_drivers", [])
            )
        
        # مکانیزم لایه دفاعی پایتون (Fallback) در صورت عدم لود ماژول RAG
        sentences = re.split(r'[.!?\n]', proposal_text)
        return [s.strip() for s in sentences if len(s.strip()) > 25][:8]

    def _build_system_prompt(self, evidence_bank: List[str], previous_feedback: str = None) -> str:
        """
        ساخت پرامپت سیستمی تدافعی به همراه اعمال اهرم جریمه روانی (Loss Aversion) در چرخه‌های تکرار
        """
        drivers_summary = json.dumps(self.drivers_data.get("strategic_drivers", []), ensure_ascii=False, indent=2)
        
        # قالب‌بندی شواهد برداری‌شده جهت انتقال به کانتکست مدل زبانی
        evidence_str = "\n".join([f"{i+1}. {ev}" for i, ev in enumerate(evidence_bank)])
        if not evidence_str:
            evidence_str = "هیچ شاهد مستقیمی دارای همبستگی معنایی با پیشران‌های استراتژیک در متن یافت نشد."

        feedback_section = ""
        if previous_feedback:
            feedback_section = f"""
\n🚨 [اخطار سیستم ممیزی - تلاش مجدد]:
در اجرای قبلی، خروجی شما به دلیل خطای زیر توسط سیستم کنترل کیفیت (QA) رد شد:
"{previous_feedback}"
شما موظف هستید این خطا را در این تلاش کاملاً برطرف کنید. تولید فیلد استنادی خالی، نامعتبر یا عدم استفاده از شناسه‌های بخش ۱ مساوی با شکست سیستم است!
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
### ۳. بانک شواهد استخراج‌شده معنایی (Evidence Bank) - قانون قطعی:
جملات زیر توسط موتور بازیابی معنایی (RAG) از متن پروپوزال استخراج شده‌اند. 
شما **فقط و حداقل** مجاز هستید فیلد `reasoning_quote` را با کپی کردن دقیق یکی از جملات زیر پر کنید:

{evidence_str}

---
### ۴. دستورالعمل خروجی (خط قرمز بسیار مهم):
- خروجی فقط و فقط فرمت JSON معتبر باشد.
- اگر برای پیشرانی در "بانک شواهد" جمله‌ای نیافتید، آن پیشران را کلاً از آرایه خروجی حذف کنید.
- قانون طلایی شناسه‌ها (خط قرمز مطلق): فیلد `driver_id` در بخش `strategic_alignment` باید دقیقاً معادل فیلد `id` پیشران استراتژیک مرتبط در بخش ۱ باشد (مانند DRV_ENERGY_01). به هیچ عنوان عنوان پروپوزال، عنوان طرح، یا هیچ رشته دیگری به جز شناسه رسمی پیشران را در این فیلد قرار ندهید.
- فیلد `driver_title` باید دقیقاً معادل فیلد `title` همان پیشران در بخش ۱ باشد.

ساختار دقیق JSON خروجی باید به شکل زیر باشد:
{{
  "proposal_summary": {{
    "title": "عنوان استخراج‌شده یا پیشنهادی طرح",
    "executive_summary": "خلاصه مدیریتی طرح در ۳ سطر کامل"
  }},
  "strategic_alignment": [
    {{
      "driver_id": "شناسه پیشران مرتبط (باید دقیقاً یکی از شناسه‌ها مانند 'DRV_ENERGY_01' از لیست بخش ۱ باشد. به هیچ عنوان عنوان یا موضوع پروپوزال را در این فیلد قرار ندهید)",
      "driver_title": "عنوان پیشران (باید دقیقاً عنوان مرتبط از لیست بخش ۱ باشد)",
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

    def analyze(self, proposal_text: str, previous_feedback: str = None, **kwargs) -> Dict[str, Any]:
        """
        اجرای چرخه تحلیل پروپوزال (نقطه اتصال به موتور ارکستراتور)
        * مجهز به سپر دفاعی **kwargs جهت تاب‌آوری در برابر تغییر آرگومان‌ها
        """
        if not proposal_text or len(proposal_text.strip()) < 50:
            return {"error": "متن پروپوزال ورودی بسیار کوتاه یا نامعتبر است."}

        # گام اول: تولید بانک شواهد بر اساس موتور RAG معنایی
        evidence_bank = self._extract_evidence_sentences(proposal_text)
        
        # گام دوم: ساخت پرامپت استراتژیک به همراه تزریق بازخورد در صورت وجود
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
                    "temperature": 0.0, # قفل شدن دما روی صفر مطلق برای رفتارهای کاملاً تحلیلی و تکرارپذیر
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
        """
        استخراج ساختاریافته خروجی (ایزوله کردن JSON از متون اضافه)
        """
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