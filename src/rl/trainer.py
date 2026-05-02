import pandas as pd
import pickle
import csv
from src.rl.abstraction_learning import init_abstraction, DEVICE, STATE_DIMS
from src.rl.bandit import BanditAgent

# =========================
# CONFIG
# =========================
ABLATION_MODE = "full"       # "tfidf_only" | "sbert_only" | "full"
DATA_PATH     = "data/processed/router_multilabel_dataset.csv"
MODEL_PATH    = f"src/rl/bandit_{ABLATION_MODE}.pkl"
LOG_PATH      = f"src/rl/training_log_{ABLATION_MODE}.csv"
EPOCHS        = 100
MAX_SAMPLES   = None

# =========================
# LOAD DATA
# =========================
df = pd.read_csv(DATA_PATH)

if MAX_SAMPLES:
    df = df.sample(MAX_SAMPLES, random_state=42)

rows    = df.to_dict("records")
actions = [col for col in df.columns if col != "message"]

print(f"Device        : {DEVICE}")
print(f"Ablation mode : {ABLATION_MODE}")
print(f"State dim     : {STATE_DIMS[ABLATION_MODE]}")
print(f"Dataset size  : {len(rows)}")
print(f"Actions       : {len(actions)}")
print(f"Epochs        : {EPOCHS}")
print(f"Model path    : {MODEL_PATH}")
print("=" * 40)

# =========================
# INIT
# =========================
abstraction = init_abstraction()
agent       = BanditAgent(actions=actions, state_dim=STATE_DIMS[ABLATION_MODE])  # ← fixed
best_reward = -999
log         = []

# Pre-warm cache
all_messages = [row["message"] for row in rows]
state_cache  = abstraction.batch_extract(all_messages, mode=ABLATION_MODE)

# =========================
# TRAIN LOOP
# =========================
for epoch in range(EPOCHS):
    epoch_rewards = []

    for i, row in enumerate(rows):
        if i % 500 == 0:
            print(f"[Epoch {epoch+1}] Processing {i}/{len(rows)}")

        message         = row["message"]
        state           = state_cache[message]
        correct_actions = [a for a in actions if row[a] == 1]
        action          = agent.select_action(state)
        reward          = 1 if action in correct_actions else -0.2
        agent.update_q_value(state, action, reward)
        epoch_rewards.append(reward)

    if len(epoch_rewards) == 0:
        print("No data — exiting")
        break

    avg_reward    = sum(epoch_rewards) / len(epoch_rewards)
    correct_count = epoch_rewards.count(1)
    accuracy      = (correct_count / len(epoch_rewards)) * 100

    print(f"Epoch {epoch+1}/{EPOCHS} | Avg Reward: {avg_reward:.4f} | Accuracy: {accuracy:.2f}%")

    log.append({
        "epoch"      : epoch + 1,
        "avg_reward" : avg_reward,
        "accuracy"   : accuracy
    })

    if abs(avg_reward - best_reward) < 0.001 and epoch > 50:
        print(f"Converged at epoch {epoch+1} — stopping early")
        break

    best_reward = avg_reward

print("\nTraining complete")

# =========================
# SAVE
# =========================
with open(MODEL_PATH, "wb") as f:
    pickle.dump(agent, f)
print(f"Model saved → {MODEL_PATH}")

with open(LOG_PATH, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["epoch", "avg_reward", "accuracy"])
    writer.writeheader()
    writer.writerows(log)
print(f"Log saved → {LOG_PATH}")