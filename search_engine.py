import json
from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime


@dataclass
class Document:
    id: int
    title: str
    content: str
    location: str
    category: str
    time_tag: str  # "morning", "evening", "any"


@dataclass
class UserContext:
    query_history: List[str] = field(default_factory=list)
    location: str = "Kyiv"
    time_segment: str = "any"  # "morning", "evening", "any"
    preferences: Dict[str, float] = field(default_factory=dict)

    def add_query(self, query: str):
        self.query_history.append(query.lower())


def load_documents(path: str) -> List[Document]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    docs = []
    for d in raw:
        docs.append(
            Document(
                id=d["id"],
                title=d["title"],
                content=d["content"],
                location=d["location"],
                category=d["category"],
                time_tag=d.get("time_tag", "any")
            )
        )
    return docs


def tokenize(text: str) -> List[str]:
    separators = ",.;:!?()[]{}\"'«»\n\r\t"
    text = text.lower()
    for s in separators:
        text = text.replace(s, " ")
    tokens = [t for t in text.split(" ") if t]
    return tokens


class BasicSearchEngine:
    def __init__(self, documents: List[Document]):
        self.documents = documents

    def search(self, query: str) -> List[Dict[str, Any]]:
        query_tokens = tokenize(query)
        results = []

        for doc in self.documents:
            text = (doc.title + " " + doc.content).lower()
            score = 0.0
            for qt in query_tokens:
                if qt in text:
                    score += 1.0
            if score > 0:
                results.append({
                    "doc": doc,
                    "base_score": score
                })

        results.sort(key=lambda x: x["base_score"], reverse=True)
        return results


class ContextSearchEngine(BasicSearchEngine):
    def __init__(self, documents: List[Document]):
        super().__init__(documents)

    def build_history_preferences(self, context: UserContext) -> Dict[str, float]:
        prefs = {cat: 0.0 for cat in ["food", "news", "education", "sport"]}
        for q in context.query_history:
            if "кафе" in q or "ресторан" in q or "їжа" in q:
                prefs["food"] += 1.0
            if "новини" in q or "news" in q:
                prefs["news"] += 1.0
            if "курс" in q or "навчання" in q or "python" in q:
                prefs["education"] += 1.0
            if "спорт" in q or "фітнес" in q or "басейн" in q:
                prefs["sport"] += 1.0

        for k, v in prefs.items():
            if v > 0:
                prefs[k] = 1.0 + v * 0.5
            else:
                prefs[k] = 1.0
        return prefs

    def search_with_context(self, query: str, context: UserContext) -> List[Dict[str, Any]]:
        base_results = super().search(query)
        if not base_results:
            return []

        history_prefs = self.build_history_preferences(context)
        combined_prefs = history_prefs.copy()
        for cat, w in context.preferences.items():
            combined_prefs[cat] = combined_prefs.get(cat, 1.0) * w

        adapted_results = []
        for item in base_results:
            doc = item["doc"]
            base_score = item["base_score"]
            score = base_score

            # Геолокація
            if doc.location.lower() == context.location.lower():
                score *= 1.5

            # Час
            if doc.time_tag == context.time_segment:
                score *= 1.3
            elif doc.time_tag == "any":
                score *= 1.0
            else:
                score *= 0.9

            # Категорії
            cat_weight = combined_prefs.get(doc.category, 1.0)
            score *= cat_weight

            adapted_results.append({
                "doc": doc,
                "base_score": base_score,
                "final_score": score,
                "context_info": {
                    "matched_location": doc.location.lower() == context.location.lower(),
                    "time_segment": context.time_segment,
                    "doc_time_tag": doc.time_tag,
                    "category_weight": cat_weight
                }
            })

        adapted_results.sort(key=lambda x: x["final_score"], reverse=True)
        return adapted_results
