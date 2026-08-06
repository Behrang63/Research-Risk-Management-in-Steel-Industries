import os
import json
import re
import time
from typing import Dict, Any, List

# وارد کردن ایمن موتور بازیابی معنایی (Semantic RAG)
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
    ollama = None


class ProposalAnalyzerAgent:
    """
    عامل هوشمند ارزیابی پروپوزال با پارسر مقاوم در برابر خطاهای JSON
    """

    def __init__(self, 
                 model_name: str = "llama3.2",
                 drivers_path: str = "config/drivers.json",
                 skills_dir: str = "skills"):
        self.model_name = model_name
        
        self.model_name = model_name
        self.drivers_path = drivers_path
        self.skills_dir = skills_dir
        
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

        if SemanticRagRetriever is not None:
            self.retriever = SemanticRagRetriever(threshold=0.15, max_evidence_count=8)
        else:
            self.retriever = None

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
        if self.retriever is not None:
            return self.retriever.retrieve_evidence(
                proposal_text=proposal_text,
                strategic_drivers=self.drivers_data.get("strategic_drivers", [])
            )
        sentences = re.split(r'[.!?\n]', proposal_text)
        return [s.strip() for s in sentences if len(s.strip()) > 25][:8]

    def _build_system_prompt(self, evidence_bank: List[str], previous_feedback: str = None) -> str:
        drivers_summary = json.dumps(self.drivers_data.get("strategic_drivers", []), ensure_ascii=False, indent=2)
        evidence_str = "\n".join([f"{i+1}. {ev}" for i, ev in enumerate(evidence_bank)])
        if not evidence_str:
            evidence_str = "هیچ شاهد مستقیمی در متن یافت نشد."

        feedback_section = ""
        if previous_feedback:
            feedback_section = f"""
\n🚨 [اخطار سیستم ممیزی - تلاش مجدد]:
در اجرای قبلی، خروجی شما به دلیل خطای زیر رد شد:
"{previous_feedback}"
حتماً خروجی را فقط در قالب JSON معتبر و بدون هیچ متن اضافه‌ای تولید کنید!
"""
        
        return f"""
شما «عامل ارزیابی پروپوزال‌های تافکو» هستید.{feedback_section}
پایگاه دانش پیشران‌ها:
{drivers_summary}

بانک شواهد (کپی کلمه‌به‌کلمه برای reasoning_quote):
{evidence_str}

قانون مطلق: خروجی فقط و فقط یک JSON معتبر باشد.

ساختار JSON:
{{
  "proposal_summary": {{
    "title": "عنوان طرح",
    "executive_summary": "خلاصه مدیریتی"
  }},
  "strategic_alignment": [
    {{
      "driver_id": "شناسه دقیق پیشران (مانند DRV_ENERGY_01)",
      "driver_title": "عنوان پیشران",
      "direct_alignment_score": 85,
      "reasoning_quote": "کپی دقیق جمله از بانک شواهد"
    }}
  ],
  "weighted_overall_score": 82.5,
  "trl_analysis": {{
    "claimed_trl": "TRL ادعا شده",
    "assessed_trl": "TRL ارزیابی‌شده",
    "gap_analysis": "تحلیل شکاف"
  }},
  "technical_critique": {{
    "strengths": ["نقطه قوت"],
    "weaknesses_and_risks": ["ریسک"],
    "red_flags": ["نکته مبهم"]
  }},
  "actionable_feedback_for_proposer": "بازخورد",
  "final_recommendation": "تایید اولیه"
}}
"""

        def analyze(self, proposal_text: str, previous_feedback: str = None, **kwargs) -> Dict[str, Any]:
        """
        اجرای چرخه تحلیل پروپوزال با قابلیت بازتلاش هوشمند در صورت قطعی شبکه یا خطای ۵۰۲
        """
        if not proposal_text or len(proposal_text.strip()) < 50:
            return {"error": "متن پروپوزال ورودی بسیار کوتاه است."}

        evidence_bank = self._extract_evidence_sentences(proposal_text)
        system_prompt = self._build_system_prompt(evidence_bank, previous_feedback)
        user_message = f"پروپوزال زیر را ارزیابی و فقط به صورت JSON پاسخ دهید:\n\n{proposal_text}"

        max_network_retries = 3
        for attempt in range(1, max_network_retries + 1):
            try:
                if ollama is None:
                    raise ImportError("کتابخانه ollama نصب نیست.")

                # ارسال درخواست به Ollama
                response = ollama.chat(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    format="json",
                    options={"temperature": 0.0, "top_p": 0.9}
                )

                raw_output = response['message']['content'].strip()
                return self._clean_and_parse_json(raw_output)

            except Exception as e:
                error_str = str(e)
                # اگر خطای شبکه یا 502 باشد، چند ثانیه صبر کرده و دوباره تلاش می‌کند
                if "502" in error_str or "connection" in error_str.lower():
                    if attempt < max_network_retries:
                        time.sleep(2)  # ۲ ثانیه مکث برای بازیابی سرور
                        continue
                
                return {
                    "parsing_error": True,
                    "message": f"خطای ارتباط با Ollama (تلاش {attempt}): {error_str}"
                }

    def _clean_and_parse_json(self, raw_text: str) -> Dict[str, Any]:
        """استخراج و پاک‌سازی هوشمند ساختار JSON از متن خام"""
        if not raw_text:
            return {"parsing_error": True, "message": "پاسخ دریافت شده خالی است."}

        # ۱. حذف علامت‌های بلوک کد مارک‌داون
        cleaned = re.sub(r'```(?:json)?', '', raw_text, flags=re.IGNORECASE).strip()
        cleaned = cleaned.rstrip('`').strip()

        # ۲. استخراج دقیق محدوده آکولادها
        start_idx = cleaned.find('{')
        end_idx = cleaned.rfind('}')

        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = cleaned[start_idx:end_idx + 1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # حذف کاماهای اضافه قبل از بستن آکولاد یا کروشه
                fixed_str = re.sub(r',\s*([}\]])', r'\1', json_str)
                try:
                    return json.loads(fixed_str)
                except json.JSONDecodeError:
                    pass

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            return {
                "parsing_error": True,
                "message": f"خطا در پارس JSON: {str(e)}",
                "raw_response": raw_text
            }


AnalyzerAgent = ProposalAnalyzerAgent