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
print(f"SBERT output dim       : 384 (full, no PCA)")
print(f"TF-IDF PCA components  : {abstraction.tfidf_pca.n_components_}")
print(f"TF-IDF max features    : {abstraction.vectorizer.max_features}")
print(f"Total state dim        : {384 + abstraction.tfidf_pca.n_components_ + abstraction.label_pca.n_components_}")
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

    # Layer 1: SBERT full (384-dim)
    sem = abstraction.semantic_model.encode([msg])
    semantic_vecs.append(sem[0])

    # Layer 2: TF-IDF → PCA (200-dim)
    tfidf_raw = abstraction.vectorizer.transform([msg]).toarray()
    tfidf_pca = abstraction.tfidf_pca.transform(tfidf_raw)[0]
    tfidf_vecs.append(tfidf_pca)

    # Layer 3: Label (36-dim)
    sims      = cosine_similarity(tfidf_raw, abstraction.train_tfidf)
    idx       = np.argmax(sims)
    label_raw = abstraction.label_matrix[idx].reshape(1, -1)
    label_pca = abstraction.label_pca.transform(label_raw)[0]
    label_vecs.append(label_pca)

T = np.array(tfidf_vecs)    # (500, 200)
S = np.array(semantic_vecs) # (500, 384)
L = np.array(label_vecs)    # (500, 36)

print("=" * 50)
print("LAYER SHAPES")
print("=" * 50)
print(f"SBERT layer shape     : {S.shape}")
print(f"TF-IDF layer shape    : {T.shape}")
print(f"Label layer shape     : {L.shape}")
print(f"Combined total        : {S.shape[1] + T.shape[1] + L.shape[1]}")
print("=" * 50)

# =========================
# CKA RESULTS
# =========================
print("CKA RESULTS")
print("=" * 50)
print(f"  SBERT   vs TF-IDF   : {cka(S, T):.4f}")
print(f"  SBERT   vs Label    : {cka(S, L):.4f}")
print(f"  TF-IDF  vs Label    : {cka(T, L):.4f}")
print("=" * 50)

# =========================
# RESIDUALIZATION
# =========================
print("RESIDUAL CKA (uniqueness beyond TF-IDF)")
print("=" * 50)

reg        = LinearRegression()
reg.fit(T, S)
S_residual = S - reg.predict(T)

reg2       = LinearRegression()
reg2.fit(T, L)
L_residual = L - reg2.predict(T)

print(f"  SBERT  vs TF-IDF  (residual) : {cka(S, S_residual):.4f}")
print(f"  TF-IDF vs Label   (residual) : {cka(T, L_residual):.4f}")
print(f"  SBERT  vs Label   (residual) : {cka(S_residual, L_residual):.4f}")
print("=" * 50)

# =========================
# SUMMARY TABLE
# =========================
print("SUMMARY")
print("=" * 50)
print(f"{'Pair':<35} {'Raw CKA':>10} {'Residual CKA':>15}")
print("-" * 62)
print(f"{'SBERT vs TF-IDF':<35} {cka(S, T):>10.4f} {cka(S, S_residual):>15.4f}")
print(f"{'SBERT vs Label':<35} {cka(S, L):>10.4f} {cka(S_residual, L_residual):>15.4f}")
print(f"{'TF-IDF vs Label':<35} {cka(T, L):>10.4f} {cka(T, L_residual):>15.4f}")
print("=" * 50)