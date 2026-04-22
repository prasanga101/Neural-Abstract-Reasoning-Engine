import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.linear_model import LinearRegression
from src.rl.abstraction_learning import init_abstraction

# =========================
# CKA FUNCTION
# =========================
def cka(X, Y):
    X = X - X.mean(axis=0)
    Y = Y - Y.mean(axis=0)
    hsic_xy = np.linalg.norm(X.T @ Y, 'fro') ** 2
    hsic_xx = np.linalg.norm(X.T @ X, 'fro') ** 2
    hsic_yy = np.linalg.norm(Y.T @ Y, 'fro') ** 2
    return hsic_xy / np.sqrt(hsic_xx * hsic_yy)

# =========================
# LOAD ABSTRACTION
# =========================
abstraction = init_abstraction()

# =========================
# DIAGNOSTIC
# =========================
messages_df   = pd.read_csv("data/raw/disaster_messages.csv")
categories_df = pd.read_csv("data/raw/disaster_categories.csv")
df            = pd.merge(messages_df, categories_df, on="id")
parsed        = df["categories"].apply(abstraction.parse_categories)
parsed_df     = pd.DataFrame(parsed.tolist())

print("=" * 50)
print("DATASET DIAGNOSTICS")
print("=" * 50)
print(f"Dataset shape          : {df.shape}")
print(f"Parsed categories      : {parsed_df.shape}")
print(f"Category columns       : {parsed_df.columns.tolist()}")
print(f"Label PCA components   : {abstraction.label_pca.n_components_}")
print(f"Semantic PCA components: {abstraction.semantic_pca.n_components_}")
print(f"TF-IDF max features    : {abstraction.vectorizer.max_features}")
print("=" * 50)

# =========================
# EXTRACT LAYERS
# =========================
messages = messages_df["message"].dropna().tolist()[:500]

tfidf_vecs    = []
semantic_vecs = []
label_vecs    = []

for i, msg in enumerate(messages):
    if i % 100 == 0:
        print(f"Extracting {i}/{len(messages)}...")

    # Layer 1: TF-IDF
    tfidf = abstraction.vectorizer.transform([msg]).toarray()[0]
    tfidf_vecs.append(tfidf)

    # Layer 2: Semantic
    sem     = abstraction.semantic_model.encode([msg])
    sem_pca = abstraction.semantic_pca.transform(sem)[0]
    semantic_vecs.append(sem_pca)

    # Layer 3: Label
    sims      = cosine_similarity(tfidf.reshape(1, -1), abstraction.train_tfidf)
    idx       = np.argmax(sims)
    label_raw = abstraction.label_matrix[idx].reshape(1, -1)
    label_pca = abstraction.label_pca.transform(label_raw)[0]
    label_vecs.append(label_pca)

T = np.array(tfidf_vecs)
S = np.array(semantic_vecs)
L = np.array(label_vecs)

print("=" * 50)
print("LAYER SHAPES")
print("=" * 50)
print(f"TF-IDF layer shape    : {T.shape}")
print(f"Semantic layer shape  : {S.shape}")
print(f"Label layer shape     : {L.shape}")
print(f"Combined total        : {T.shape[1] + S.shape[1] + L.shape[1]}")
print("=" * 50)

# =========================
# CKA RESULTS
# =========================
print("CKA RESULTS")
print("=" * 50)
print(f"  TF-IDF  vs Semantic : {cka(T, S):.4f}")
print(f"  TF-IDF  vs Label    : {cka(T, L):.4f}")
print(f"  Semantic vs Label   : {cka(S, L):.4f}")
print("=" * 50)

# =========================
# RESIDUALIZATION
# =========================
print("RESIDUAL CKA (semantic uniqueness beyond TF-IDF)")
print("=" * 50)

# Remove TF-IDF explainable component from semantic
reg         = LinearRegression()
reg.fit(T, S)
S_residual  = S - reg.predict(T)

# Remove TF-IDF explainable component from label
reg2        = LinearRegression()
reg2.fit(T, L)
L_residual  = L - reg2.predict(T)

print(f"  TF-IDF  vs Semantic (residual) : {cka(T, S_residual):.4f}")
print(f"  TF-IDF  vs Label    (residual) : {cka(T, L_residual):.4f}")
print(f"  Semantic vs Label   (residual) : {cka(S_residual, L_residual):.4f}")
print("=" * 50)

# =========================
# SUMMARY TABLE
# =========================
print("SUMMARY")
print("=" * 50)
print(f"{'Pair':<35} {'Raw CKA':>10} {'Residual CKA':>15}")
print("-" * 60)
print(f"{'TF-IDF vs Semantic':<35} {cka(T, S):>10.4f} {cka(T, S_residual):>15.4f}")
print(f"{'TF-IDF vs Label':<35} {cka(T, L):>10.4f} {cka(T, L_residual):>15.4f}")
print(f"{'Semantic vs Label':<35} {cka(S, L):>10.4f} {cka(S_residual, L_residual):>15.4f}")
print("=" * 50)