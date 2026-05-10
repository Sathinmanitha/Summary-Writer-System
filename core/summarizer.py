import re
import math
import heapq
from collections import Counter
from typing import List, Tuple, Dict

# Common English stopwords
STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "shall", "should", "may", "might", "can", "could", "this", "that",
    "these", "those", "it", "its", "they", "their", "them", "we", "our",
    "you", "your", "he", "she", "his", "her", "i", "my", "me", "us",
    "about", "after", "before", "between", "into", "through", "during",
    "also", "than", "then", "when", "where", "which", "who", "whom",
    "what", "how", "not", "no", "nor", "so", "yet", "both", "either",
    "as", "if", "because", "although", "while", "since", "until",
    "up", "out", "over", "under", "again", "further", "once", "more",
    "just", "only", "very", "still", "well", "said", "says", "according"
}

def tokenise_sentences(text: str) -> List[str]:
    """
    Split a news article into individual sentences
    """
    abbrevs = [
        r'(?<!\w)([A-Z]\.[A-Z]\.)',      # U.S., U.K., etc.
        r'(?<!\w)(Mr|Mrs|Ms|Dr|Prof|Sr|Jr|vs|etc|Inc|Ltd|Corp)\.',
    ]
    protected = text
    for pattern in abbrevs:
        protected = re.sub(pattern, lambda m: m.group().replace('.', '<DOT>'), protected)

    # Split
    raw = re.split(r'(?<=[.!?])\s+(?=[A-Z])', protected)

    sentences = []
    for s in raw:
        clean = s.replace('<DOT>', '.').strip()
        if len(clean.split()) >= 4:    
            sentences.append(clean)
    return sentences


def clean_text(text: str) -> str:
    """Remove HTML tags, special chars, and normalise whitespace."""
    text = re.sub(r'<[^>]+>', ' ', text)          # Strip HTML
    text = re.sub(r'\s+', ' ', text)              # Collapse whitespace
    text = re.sub(r'[^\w\s.,!?;:\'-]', ' ', text) # Remove junk chars
    return text.strip()


def preprocess_sentence(sentence: str) -> List[str]:
    """
    Tokenise, lowercase, and remove stopwords.
    Returns a list of meaningful tokens.
    """
    tokens = re.findall(r"[a-z']+", sentence.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 2]


# TF-IDF Implementation
def compute_tf(tokens: List[str]) -> Dict[str, float]:
    """Term Frequency: normalised count of each token in a document."""
    if not tokens:
        return {}
    freq = Counter(tokens)
    total = len(tokens)
    return {word: count / total for word, count in freq.items()}


def compute_idf(all_token_lists: List[List[str]]) -> Dict[str, float]:
    """
    Inverse Document Frequency across all sentences.
    IDF(t) = log( N / (1 + df(t)) )
    """
    N = len(all_token_lists)
    df: Dict[str, int] = {}
    for tokens in all_token_lists:
        for token in set(tokens):
            df[token] = df.get(token, 0) + 1
    return {word: math.log(N / (1 + count)) for word, count in df.items()}


def build_tfidf_vectors(
    all_token_lists: List[List[str]],
    idf: Dict[str, float]
) -> List[Dict[str, float]]:
    """Compute TF-IDF vector for each sentence."""
    vectors = []
    for tokens in all_token_lists:
        tf = compute_tf(tokens)
        tfidf = {word: tf[word] * idf.get(word, 0.0) for word in tf}
        vectors.append(tfidf)
    return vectors


# Cosine Similarity
def cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    """
    Cosine similarity between two TF-IDF sparse vectors.
    cos(θ) = (A·B) / (||A|| × ||B||)
    """
    if not vec_a or not vec_b:
        return 0.0

    # Dot product
    shared_keys = set(vec_a) & set(vec_b)
    dot = sum(vec_a[k] * vec_b[k] for k in shared_keys)

    # Magnitudes
    mag_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
    mag_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))

    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


# Sentence Scoring
def score_sentences_tfidf(
    sentences: List[str],
    tfidf_vectors: List[Dict[str, float]]
) -> List[float]:
    """
    Score each sentence by summing its TF-IDF weights.
    """
    scores = []
    for vec in tfidf_vectors:
        scores.append(sum(vec.values()))
    return scores


def score_sentences_similarity(
    tfidf_vectors: List[Dict[str, float]]
) -> List[float]:
    """
    Score each sentence by average cosine similarity to ALL other sentences.
    """
    n = len(tfidf_vectors)
    scores = [0.0] * n
    for i in range(n):
        for j in range(n):
            if i != j:
                scores[i] += cosine_similarity(tfidf_vectors[i], tfidf_vectors[j])
        if n > 1:
            scores[i] /= (n - 1)
    return scores


def combine_scores(
    tfidf_scores: List[float],
    similarity_scores: List[float],
    tfidf_weight: float = 0.6,
    sim_weight: float = 0.4
) -> List[float]:
    """
    Blend TF-IDF importance with cosine-similarity centrality (Default: 60% TF-IDF importance + 40% centrality).
    """
    # Normalise both score lists 
    def normalise(lst):
        mx = max(lst) if max(lst) > 0 else 1.0
        return [v / mx for v in lst]

    norm_t = normalise(tfidf_scores)
    norm_s = normalise(similarity_scores)
    return [tfidf_weight * t + sim_weight * s for t, s in zip(norm_t, norm_s)]


# Positional Boost
def positional_weights(n: int) -> List[float]:
    weights = []
    for i in range(n):
        if i == 0:
            weights.append(1.3)          # Lead sentence boost
        elif i == n - 1:
            weights.append(1.1)          # Conclusion sentence boost
        elif i < n * 0.25:
            weights.append(1.15)         # Early paragraph boost
        else:
            weights.append(1.0)
    return weights


# 60-Word Assembler
def build_60_word_summary(
    sentences: List[str],
    ranked_indices: List[int],
    target_words: int = 60
) -> str:
    """
    Add top-ranked sentences 
    """
    # Preserve document order of selected sentences 
    selected = sorted(ranked_indices, key=lambda i: i)

    summary_words: List[str] = []

    for idx in selected:
        sentence_words = sentences[idx].split()
        remaining = target_words - len(summary_words)

        if remaining <= 0:
            break

        if len(sentence_words) <= remaining:
            summary_words.extend(sentence_words)
        else:
            truncated = sentence_words[:remaining]
            while truncated and truncated[-1][-1] not in '.!?,;:':
                truncated = truncated[:-1]
                if not truncated:
                    truncated = sentence_words[:remaining]
                    break
            if len(truncated) < remaining:
                truncated = sentence_words[:remaining]
            summary_words.extend(truncated)
            break

    summary = ' '.join(summary_words)

    # Final word-count adjustment
    words = summary.split()
    if len(words) > target_words:
        words = words[:target_words]
        summary = ' '.join(words)

    # Summary end the period
    if summary and summary[-1] not in '.!?':
        summary = summary.rstrip(',;:') + '.'

    return summary


# Main Summarizer API
class SummaryWriter:

    def __init__(self, target_words: int = 60, tfidf_weight: float = 0.6):
        self.target_words = target_words
        self.tfidf_weight = tfidf_weight
        self.sim_weight = 1.0 - tfidf_weight
        self._last_debug: Dict = {}

    def summarise(self, article: str) -> Tuple[str, Dict]:
        # Step 1: Clean & preprocess text 
        article = clean_text(article)

        # Step 2: Sentence tokenisation 
        sentences = tokenise_sentences(article)
        if not sentences:
            return "Insufficient content to summarise.", {}

        if len(sentences) == 1:
            words = sentences[0].split()[:self.target_words]
            return ' '.join(words) + '.', {}

        # Step 3:  Token preprocessing (lowercase, stop-word removal) 
        token_lists = [preprocess_sentence(s) for s in sentences]

        # Step 4: TF-IDF vectorisation
        idf = compute_idf(token_lists)
        tfidf_vectors = build_tfidf_vectors(token_lists, idf)

        # Step 5: Cosine-similarity sentence ranking (Scoring)
        tfidf_scores = score_sentences_tfidf(sentences, tfidf_vectors)
        sim_scores   = score_sentences_similarity(tfidf_vectors)
        combined     = combine_scores(tfidf_scores, sim_scores,
                                      self.tfidf_weight, self.sim_weight)

        # Step 6: Positional weight adjustment
        pos_weights = positional_weights(len(sentences))
        final_scores = [c * p for c, p in zip(combined, pos_weights)]

        # Step 7: Select top sentences
        word_budget = self.target_words
        candidate_indices = sorted(range(len(final_scores)),
                                   key=lambda i: final_scores[i],
                                   reverse=True)
        selected: List[int] = []
        accumulated = 0
        for idx in candidate_indices:
            selected.append(idx)
            accumulated += len(sentences[idx].split())
            if accumulated >= word_budget:
                break

        # Step 8: 60-word assembly 
        summary = build_60_word_summary(sentences, selected, self.target_words)

        # Debug payload for transparency
        debug = {
            "sentence_count": len(sentences),
            "sentence_scores": [
                {
                    "rank": rank + 1,
                    "index": idx,
                    "sentence": sentences[idx][:80] + ("…" if len(sentences[idx]) > 80 else ""),
                    "tfidf_score": round(tfidf_scores[idx], 4),
                    "sim_score": round(sim_scores[idx], 4),
                    "final_score": round(final_scores[idx], 4),
                }
                for rank, idx in enumerate(
                    sorted(range(len(final_scores)),
                           key=lambda i: final_scores[i], reverse=True)
                )
            ],
            "selected_indices": selected,
            "word_count": len(summary.split()),
        }
        self._last_debug = debug
        return summary, debug


#CLI Entry Point
if __name__ == "__main__":
    import sys
    import json

    SAMPLE_ARTICLE = ""

    sw = SummaryWriter(target_words=60)
    summary, debug = sw.summarise(SAMPLE_ARTICLE)

    print("=" * 60)
    print("SUMMARY WRITER SYSTEM – 60-Word Extractive Summariser")
    print("=" * 60)
    print(f"\nSUMMARY ({debug.get('word_count', '?')} words):\n")
    print(summary)
    print(f"\nArticle sentences analysed : {debug.get('sentence_count', '?')}")
    print("\nTop-5 Ranked Sentences:")
    for s in debug.get("sentence_scores", [])[:5]:
        print(f"  [{s['rank']}] Score={s['final_score']:.4f}  '{s['sentence']}'")
