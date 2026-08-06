import re
from typing import List, Dict, Any

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    TfidfVectorizer = None
    cosine_similarity = None


class SemanticRagRetriever:
    """موتور بازیابی معنایی شواهد (RAG)"""

    def __init__(self, threshold: float = 0.15, max_evidence_count: int = 8):
        self.threshold = threshold
        self.max_evidence_count = max_evidence_count

    def _split_into_sentences(self, text: str) -> List[str]:
        sentences = re.split(r'[.!?\n]', text)
        return [s.strip() for s in sentences if len(s.strip()) > 25]

    def retrieve_evidence(self, proposal_text: str, strategic_drivers: List[Dict[str, Any]]) -> List[str]:
        sentences = self._split_into_sentences(proposal_text)
        if not sentences or TfidfVectorizer is None:
            return sentences[:10]

        driver_targets = []
        for d in strategic_drivers:
            driver_text = f"{d.get('title', '')} " + " ".join(d.get('keywords', []))
            driver_targets.append(driver_text)

        evidence_candidates = []

        try:
            vectorizer = TfidfVectorizer(token_pattern=r'(?u)\b\w+\b')
            all_documents = sentences + driver_targets
            tfidf_matrix = vectorizer.fit_transform(all_documents)

            proposal_vectors = tfidf_matrix[:len(sentences)]
            driver_vectors = tfidf_matrix[len(sentences):]

            similarity_matrix = cosine_similarity(proposal_vectors, driver_vectors)

            for idx, sentence in enumerate(sentences):
                max_sim = float(similarity_matrix[idx].max())
                if max_sim >= self.threshold:
                    evidence_candidates.append((sentence, max_sim))

            evidence_candidates.sort(key=lambda x: x[1], reverse=True)
            
            final_evidence = []
            for item in evidence_candidates:
                if item[0] not in final_evidence:
                    final_evidence.append(item[0])
                if len(final_evidence) >= self.max_evidence_count:
                    break
                    
            return final_evidence

        except Exception:
            return sentences[:self.max_evidence_count]

    def retrieve(self, query: str = "", proposal_text: str = "", strategic_drivers: List[Dict[str, Any]] = None, **kwargs) -> List[str]:
        if strategic_drivers is None:
            strategic_drivers = []
        text_to_search = proposal_text if proposal_text else query
        return self.retrieve_evidence(text_to_search, strategic_drivers)

    # افزودن متد query جهت پاسخگویی به فراخوانی Mock در pytest
    def query(self, search_text: str = "", **kwargs) -> List[str]:
        """متد پوششی جهت تطابق با متد مورد انتظار در تست‌ها"""
        return self.retrieve(query=search_text, **kwargs)


# نام‌های مستعار برای تست pytest
RAGRetriever = SemanticRagRetriever
RagRetriever = SemanticRagRetriever