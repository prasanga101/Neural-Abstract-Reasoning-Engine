from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
from sklearn.preprocessing import normalize
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import numpy as np
import pandas as pd

# 3000 + 200 + 36 = 3236
BANDIT_STATE_DIM = 3236

class AbstractionLearning:
    def __init__(self):
        # --- Layer 1: TF-IDF (3000-dim) ---
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=3000
        )

        # --- Layer 2: Semantic (200-dim) ---
        self.semantic_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.semantic_pca = PCA(n_components=200)

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
        print("[Abstraction] Fitting TF-IDF layer...")
        self.vectorizer.fit(messages)
        self.train_tfidf = self.vectorizer.transform(messages).toarray()  # (N, 3000)

        if semantic_context:
            print("[Abstraction] Fitting semantic layer...")
            semantic_vecs = self.semantic_model.encode(
                messages.tolist() if hasattr(messages, "tolist") else list(messages),
                show_progress_bar=True,
                batch_size=64
            )
            self.semantic_pca.fit(semantic_vecs)
            print("[Abstraction] Semantic PCA fitted.")

        if labels is not None:
            print("[Abstraction] Fitting label co-occurrence layer...")
            self.label_columns = labels.columns.tolist()
            label_array        = labels.fillna(0).values.astype(float)  # (N, 36)
            self.label_matrix  = label_array

            # Fit PCA on real label dimensions — no padding
            self.label_dim = label_array.shape[1]  # 36
            self.label_pca = PCA(n_components=self.label_dim)
            self.label_pca.fit(label_array)
            print(f"[Abstraction] Label PCA fitted with dim={self.label_dim}")

    def extract(self, message):
        # --- Layer 1: TF-IDF (3000-dim) ---
        tfidf_vec = self.vectorizer.transform([message]).toarray()  # (1, 3000)

        # --- Layer 2: Semantic (200-dim) ---
        if hasattr(self.semantic_pca, "components_"):
            raw_semantic = self.semantic_model.encode([message])
            semantic_vec = self.semantic_pca.transform(raw_semantic)[0]  # (200,)
        else:
            semantic_vec = np.zeros(200)

        # --- Layer 3: Label co-occurrence (36-dim) ---
        if self.label_matrix is not None and self.label_pca is not None:
            similarities     = cosine_similarity(tfidf_vec, self.train_tfidf)  # (1, N)
            nearest_idx      = np.argmax(similarities)
            nearest_label    = self.label_matrix[nearest_idx].reshape(1, -1)   # (1, 36)
            label_vec        = self.label_pca.transform(nearest_label)[0]      # (36,)
        else:
            label_vec = np.zeros(self.label_dim if self.label_dim else 36)

        # --- Combine: 3000 + 200 + 36 = 3236 ---
        combined = np.concatenate([tfidf_vec[0], semantic_vec, label_vec])

        # Dimension guard
        if len(combined) != BANDIT_STATE_DIM:
            raise ValueError(
                f"State vector mismatch: expected {BANDIT_STATE_DIM}, got {len(combined)}"
            )

        combined = normalize(combined.reshape(1, -1))[0]
        return combined  # (3236,)


def init_abstraction():
    abstraction = AbstractionLearning()

    messages_df  = pd.read_csv("data/raw/disaster_messages.csv")
    categories_df = pd.read_csv("data/raw/disaster_categories.csv")
    df           = pd.merge(messages_df, categories_df, on="id")

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
    print("Vector length :", len(state_vector))
    print("Non-zero values:", (state_vector > 0).sum())
    print("Sample values  :", state_vector[:10])