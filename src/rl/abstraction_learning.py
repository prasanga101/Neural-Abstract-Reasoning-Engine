from pathlib import Path

try:
    import torch
    _TORCH_AVAILABLE = torch.cuda.is_available()
except ImportError:
    _TORCH_AVAILABLE = False

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
from sklearn.preprocessing import normalize
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import numpy as np
import pandas as pd
import torch

_SBERT_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Dimensions per ablation mode
STATE_DIMS = {
    "tfidf_only": 200,
    "sbert_only": 384,
    "full":       620,
}
BANDIT_STATE_DIM = STATE_DIMS["full"]
DEVICE           = "cuda" if _TORCH_AVAILABLE else "cpu"
REPO_ROOT        = Path(__file__).resolve().parents[2]
RAW_DATA_DIR     = REPO_ROOT / "data" / "raw"


class AbstractionLearning:
    def __init__(self):
        # --- Layer 1: SBERT full (384-dim for all-MiniLM-L6-v2) ---
        self.semantic_model = SentenceTransformer("all-MiniLM-L6-v2", device=_SBERT_DEVICE)

        # --- Layer 1: SBERT (384-dim) ---
        self.semantic_model = SentenceTransformer("all-MiniLM-L6-v2", device=DEVICE)

        # --- Layer 2: TF-IDF → PCA (200-dim) ---
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=5000
        )
        self.tfidf_pca = PCA(n_components=200)

        # --- Layer 3: Label co-occurrence (36-dim) ---
        self.label_matrix  = None
        self.label_columns = None
        self.label_pca     = None
        self.label_dim     = None
        self.train_tfidf   = None

    def parse_categories(self, cat_string):
        result = {}
        parts  = cat_string.split(";")
        for part in parts:
            key, value = part.split("-")
            result[key] = int(value)
        return result

    def fit(self, messages, labels=None, semantic_context=False):
        # --- Layer 2: TF-IDF ---
        print("[Abstraction] Fitting TF-IDF layer...")
        self.vectorizer.fit(messages)
        tfidf_matrix     = self.vectorizer.transform(messages).toarray()
        self.train_tfidf = tfidf_matrix.astype(np.float32)  # float32 saves ~250MB RAM

        print("[Abstraction] Fitting TF-IDF PCA (200-dim)...")
        self.tfidf_pca.fit(tfidf_matrix)
        print("[Abstraction] TF-IDF PCA fitted.")

        # --- Layer 1: SBERT ---
        if semantic_context:
            print("[Abstraction] Pre-encoding messages with SBERT...")
            self.train_sbert = self.semantic_model.encode(
                messages.tolist() if hasattr(messages, "tolist") else list(messages),
                show_progress_bar=True,
                batch_size=128,
                convert_to_numpy=True,
            )  # (N, 384)
            print("[Abstraction] SBERT encoding complete.")

        # --- Layer 3: Label ---
        if labels is not None:
            print("[Abstraction] Fitting label co-occurrence layer...")
            self.label_columns = labels.columns.tolist()
            label_array        = labels.fillna(0).values.astype(float)
            self.label_matrix  = label_array
            self.label_dim     = label_array.shape[1]  # 36
            self.label_pca     = PCA(n_components=self.label_dim)
            self.label_pca.fit(label_array)
            print(f"[Abstraction] Label PCA fitted with dim={self.label_dim}")

    def batch_extract(self, messages, mode="full", batch_size=128):
        if mode not in STATE_DIMS:
            raise ValueError(f"Unknown mode '{mode}'. Choose from: {list(STATE_DIMS)}")

        unique_messages = list(dict.fromkeys(messages))
        n               = len(unique_messages)
        print(f"[Abstraction] batch_extract: {n} unique messages, mode={mode}, device={DEVICE}")

        # Layer 2 — TF-IDF
        if mode in ("tfidf_only", "full"):
            tfidf_raw  = self.vectorizer.transform(unique_messages).toarray().astype(np.float32)
            tfidf_vecs = self.tfidf_pca.transform(tfidf_raw)  # (N, 200)

        # Layer 1 — SBERT batch
        if mode in ("sbert_only", "full"):
            sbert_vecs = self.semantic_model.encode(
                unique_messages,
                batch_size=batch_size,
                show_progress_bar=True,
                convert_to_numpy=True,
            )  # (N, 384)

        # Layer 3 — label lookup
        if mode == "full":
            if self.label_matrix is not None and self.label_pca is not None:
                sims         = cosine_similarity(tfidf_raw, self.train_tfidf)  # (N, train_N)
                nearest_idxs = np.argmax(sims, axis=1)                         # (N,)
                nearest_lbls = self.label_matrix[nearest_idxs]                 # (N, 36)
                label_vecs   = self.label_pca.transform(nearest_lbls)          # (N, 36)
            else:
                dim        = self.label_dim if self.label_dim else 36
                label_vecs = np.zeros((n, dim))

        # Assemble cache
        result = {}
        for i, msg in enumerate(unique_messages):
            if mode == "tfidf_only":
                vec = tfidf_vecs[i]
            elif mode == "sbert_only":
                vec = sbert_vecs[i]
            else:
                vec = np.concatenate([sbert_vecs[i], tfidf_vecs[i], label_vecs[i]])
            result[msg] = normalize(vec.reshape(1, -1))[0]

        print(f"[Abstraction] Cache ready: {len(result)} vectors, dim={STATE_DIMS[mode]}")
        return result

    def extract(self, message, mode="full"):
        if mode not in STATE_DIMS:
            raise ValueError(f"Unknown mode '{mode}'. Choose from: {list(STATE_DIMS)}")

        tfidf_raw = self.vectorizer.transform([message]).toarray()
        tfidf_vec = self.tfidf_pca.transform(tfidf_raw)[0]  # (200,)

        if mode == "tfidf_only":
            combined = tfidf_vec

        elif mode == "sbert_only":
            combined = self.semantic_model.encode([message])[0]  # (384,)

        else:  # full
            sbert_vec = self.semantic_model.encode([message])[0]  # (384,)
            if self.label_matrix is not None and self.label_pca is not None:
                sims          = cosine_similarity(tfidf_raw, self.train_tfidf)
                nearest_idx   = np.argmax(sims)
                nearest_label = self.label_matrix[nearest_idx].reshape(1, -1)
                label_vec     = self.label_pca.transform(nearest_label)[0]
            else:
                label_vec = np.zeros(self.label_dim if self.label_dim else 36)
            combined = np.concatenate([sbert_vec, tfidf_vec, label_vec])  # (620,)

        combined = normalize(combined.reshape(1, -1))[0]
        return combined


def init_abstraction():
    abstraction   = AbstractionLearning()
    messages_df   = pd.read_csv(RAW_DATA_DIR / "disaster_messages.csv")
    categories_df = pd.read_csv(RAW_DATA_DIR / "disaster_categories.csv")
    df            = pd.merge(messages_df, categories_df, on="id")

    parsed    = df["categories"].apply(abstraction.parse_categories)
    parsed_df = pd.DataFrame(parsed.tolist())
    df        = pd.concat([df, parsed_df], axis=1)

    abstraction.fit(
        messages=df["message"],
        labels=parsed_df,
        semantic_context=True   # ← fixed
    )

    return abstraction


if __name__ == "__main__":
    abstraction_learner = init_abstraction()
    test_message = "There is a fire in the city and people need help"
    for mode in STATE_DIMS:
        vec = abstraction_learner.extract(test_message, mode=mode)
        print(f"[{mode}] dim={len(vec)}  non-zero={(vec > 0).sum()}  sample={vec[:5]}")