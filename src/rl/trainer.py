import pandas as pd
import pickle
import csv
from datetime import datetime
from pathlib import Path
from src.rl.abstraction_learning import init_abstraction
from src.rl.bandit import BanditAgent

RESULTS_PATH = "TRAINING_RESULTS.md"


def _write_results_md(path, section, metrics: dict):
    existing = Path(path).read_text() if Path(path).exists() else "# Training Results\n"
    header = f"## {section}"
    block = (
        f"\n{header}\n"
        f"_Last trained: {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n\n"
        + "\n".join(f"- **{k}**: {v}" for k, v in metrics.items())
        + "\n"
    )
    if header in existing:
        import re
        existing = re.sub(rf"{re.escape(header)}.*?(?=\n## |\Z)", block.lstrip("\n"), existing, flags=re.DOTALL)
    else:
        existing = existing.rstrip("\n") + "\n" + block
    Path(path).write_text(existing)

# =========================
# CONFIG
# =========================
DATA_PATH = "data/processed/router_multilabel_dataset.csv"
MODEL_PATH = "src/rl/bandit.pkl"
LOG_PATH   = "src/rl/training_log.csv"
EPOCHS      = 300
MAX_SAMPLES = None
USE_FAST_MODE = False

# =========================
# LOAD DATA
# =========================
df = pd.read_csv(DATA_PATH)

if MAX_SAMPLES:
    df = df.sample(MAX_SAMPLES, random_state=42)

rows = df.to_dict("records")
actions = [col for col in df.columns if col != "message"]

print(f"Dataset size  : {len(rows)}")
print(f"Actions       : {len(actions)}")
print(f"Epochs        : {EPOCHS}")
print("=" * 40)

# =========================
# INIT
# =========================
abstraction = init_abstraction()
agent       = BanditAgent(actions=actions)
state_cache = {}
best_reward = -999
log         = []

# =========================
# TRAIN LOOP
# =========================
for epoch in range(EPOCHS):
    epoch_rewards = []

    for i, row in enumerate(rows):
        if i % 500 == 0:
            print(f"[Epoch {epoch+1}] Processing {i}/{len(rows)}")

        message = row["message"]

        # STATE EXTRACTION
        if USE_FAST_MODE:
            state = message
        else:
            if message in state_cache:
                state = state_cache[message]
            else:
                state = abstraction.extract(message)
                state_cache[message] = state

        # ACTION + REWARD
        correct_actions = [a for a in actions if row[a] == 1]
        action  = agent.select_action(state)
        reward  = 1 if action in correct_actions else -0.2
        agent.update_q_value(state, action, reward)
        epoch_rewards.append(reward)

    # METRICS
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

    # CONVERGENCE CHECK
    if abs(avg_reward - best_reward) < 0.001 and epoch > 50:
        print(f"Converged at epoch {epoch+1} — stopping early")
        break

    best_reward = avg_reward

print("\nTraining complete")

# =========================
# SAVE MODEL
# =========================
with open(MODEL_PATH, "wb") as f:
    pickle.dump(agent, f)
print(f"Model saved → {MODEL_PATH}")
with open(LOG_PATH, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["epoch", "avg_reward", "accuracy"])
    writer.writeheader()
    writer.writerows(log)

final = log[-1] if log else {}
_write_results_md(RESULTS_PATH, "RL (Bandit)", {
    "Epochs": len(log),
    "Final Accuracy": f"{final.get('accuracy', 0):.2f}%",
    "Final Avg Reward": f"{final.get('avg_reward', 0):.4f}",
})
print(f"Log saved → {LOG_PATH}")