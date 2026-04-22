from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
from sklearn.preprocessing import normalize
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import numpy as np
import pandas as pd

BANDIT_STATE_DIM = 620

class AbstractionLearning:
    def __init__(self):
        # --- Layer 1: SBERT full (768-dim) ---
        self.semantic_model = SentenceTransformer("all-MiniLM-L6-v2")

        # --- Layer 2: TF-IDF weighted (200-dim via PCA) ---
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
        parts = cat_string.split(";")
        for part in parts:
            key, value = part.split("-")
            result[key] = int(value)
        return result

    def fit(self, messages, labels=None, semantic_context=False):
        # --- Layer 2: TF-IDF ---
        print("[Abstraction] Fitting TF-IDF layer...")
        self.vectorizer.fit(messages)
        tfidf_matrix = self.vectorizer.transform(messages).toarray()  # (N, 5000)
        self.train_tfidf = tfidf_matrix

        print("[Abstraction] Fitting TF-IDF PCA (200-dim)...")
        self.tfidf_pca.fit(tfidf_matrix)
        print("[Abstraction] TF-IDF PCA fitted.")

        # --- Layer 1: SBERT ---
        if semantic_context:
            print("[Abstraction] Pre-encoding messages with SBERT...")
            self.train_sbert = self.semantic_model.encode(
                messages.tolist() if hasattr(messages, "tolist") else list(messages),
                show_progress_bar=True,
                batch_size=64
            )  # (N, 768) — stored for potential lookup
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

    def extract(self, message):
        # --- Layer 1: SBERT full (768-dim) ---
        sbert_vec = self.semantic_model.encode([message])[0]  # (768,)

        # --- Layer 2: TF-IDF → PCA (200-dim) ---
        tfidf_raw = self.vectorizer.transform([message]).toarray()  # (1, 5000)
        tfidf_vec = self.tfidf_pca.transform(tfidf_raw)[0]          # (200,)

        # --- Layer 3: Label co-occurrence (36-dim) ---
        if self.label_matrix is not None and self.label_pca is not None:
            similarities  = cosine_similarity(tfidf_raw, self.train_tfidf)  # (1, N)
            nearest_idx   = np.argmax(similarities)
            nearest_label = self.label_matrix[nearest_idx].reshape(1, -1)
            label_vec     = self.label_pca.transform(nearest_label)[0]      # (36,)
        else:
            label_vec = np.zeros(self.label_dim if self.label_dim else 36)

        # --- Combine: 768 + 200 + 36 = 1004 ---
        combined = np.concatenate([sbert_vec, tfidf_vec, label_vec])

        # Dimension guard
        if len(combined) != BANDIT_STATE_DIM:
            raise ValueError(
                f"State vector mismatch: expected {BANDIT_STATE_DIM}, got {len(combined)}"
            )

        combined = normalize(combined.reshape(1, -1))[0]
        return combined  # (1004,)


def init_abstraction():
    abstraction = AbstractionLearning()

    messages_df   = pd.read_csv("data/raw/disaster_messages.csv")
    categories_df = pd.read_csv("data/raw/disaster_categories.csv")
    df            = pd.merge(messages_df, categories_df, on="id")

    parsed    = df["categories"].apply(abstraction.parse_categories)
    parsed_df = pd.DataFrame(parsed.tolist())
    df        = pd.concat([df, parsed_df], axis=1)

    abstraction.fit(
        messages=df["message"],
        labels=parsed_df,
        semantic_context=True
    )

    return abstraction


if __name__ == "__main__":
    abstraction_learner = init_abstraction()
    test_message = "There is a fire in the city and people need help"
    state_vector = abstraction_learner.extract(test_message)
    print("Vector length  :", len(state_vector))
    print("Non-zero values:", (state_vector > 0).sum())
    print("Sample values  :", state_vector[:10])