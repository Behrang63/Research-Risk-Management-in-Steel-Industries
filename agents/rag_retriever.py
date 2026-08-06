import re
from typing import List, Dict, Any
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    TfidfVectorizer = None
    cosine_similarity = None


class SemanticRagRetriever:
    """
    موتور سبک بازیابی معنایی (Semantic RAG) بر اساس اصول اوليه ریاضی
    جهت استخراج شواهد عینی از میان پروپوزال‌های R&D تافکو
    """

    def __init__(self, threshold: float = 0.15, max_evidence_count: int = 8):
        self.threshold = threshold
        self.max_evidence_count = max_evidence_count

    def _split_into_sentences(self, text: str) -> List[str]:
        """تقسیم پروپوزال به جملات معنادار بر اساس علائم نگارشی فارسی و خط جدید"""
        sentences = re.split(r'[.!?\n]', text)
        return [s.strip() for s in sentences if len(s.strip()) > 25]

    def retrieve_evidence(self, proposal_text: str, strategic_drivers: List[Dict[str, Any]]) -> List[str]:
        """
        محاسبه فاصله کسینوسی و همبستگی معنایی جملات با پیشران‌های استراتژیک تافکو
        """
        sentences = self._split_into_sentences(proposal_text)
        if not sentences or TfidfVectorizer is None:
            # Fallback در صورت عدم نصب کتابخانه‌ها یا نبود متن کافی
            return sentences[:10]

        # تجمیع اهداف و کلیدواژه‌های پیشران‌ها به عنوان متون مرجع برای مقایسه معنایی
        driver_targets = []
        for d in strategic_drivers:
            driver_text = f"{d.get('title', '')} " + " ".join(d.get('keywords', []))
            driver_targets.append(driver_text)

        evidence_candidates = []

        try:
            # برداری‌سازی متون بر اساس مدل فرکانس کلمات (TF-IDF)
            vectorizer = TfidfVectorizer(token_pattern=r'(?u)\b\w+\b')
            all_documents = sentences + driver_targets
            tfidf_matrix = vectorizer.fit_transform(all_documents)

            # تفکیک ماتریس‌ها برای جملات پروپوزال و اهداف پیشران‌ها
            proposal_vectors = tfidf_matrix[:len(sentences)]
            driver_vectors = tfidf_matrix[len(sentences):]

            # محاسبه شباهت کسینوسی تک‌تک جملات با اهداف پیشران‌ها
            similarity_matrix = cosine_similarity(proposal_vectors, driver_vectors)

            # رتبه‌بندی جملات بر اساس حداکثر امتیاز همبستگی معنایی با هر پیشران
            for idx, sentence in enumerate(sentences):
                max_sim = float(similarity_matrix[idx].max())
                if max_sim >= self.threshold:
                    evidence_candidates.append((sentence, max_sim))

            # مرتب‌سازی بر اساس امتیاز همبستگی (نزولی)
            evidence_candidates.sort(key=lambda x: x[1], reverse=True)
            
            # استخراج جملات نهایی فاقد تکرار
            final_evidence = []
            for item in evidence_candidates:
                if item[0] not in final_evidence:
                    final_evidence.append(item[0])
                if len(final_evidence) >= self.max_evidence_count:
                    break
                    
            return final_evidence

        except Exception:
            # مکانیزم لایه دفاعی تدافعی (Graceful Fallback)
            return sentences[:self.max_evidence_count]