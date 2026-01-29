
import numpy as np
import pandas as pd
import subprocess
import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from robustbase import LMROB

def generate_data(n=100, p=3, outlier_frac=0.2, seed=42):
    rng = np.random.default_rng(seed)
    X = rng.standard_normal((n, p))
    true_beta = np.ones(p)
    y = X @ true_beta + rng.standard_normal(n)
    
    # Add outliers
    n_outliers = int(n * outlier_frac)
    outlier_indices = rng.choice(n, n_outliers, replace=False)
    y[outlier_indices] = 100 # Vertical outliers
    
    return X, y, true_beta

def run_r_lmrob(data_path):
    r_script = f"""
    .libPaths(c('r_libs', .libPaths()))
    library(robustbase)
    # Load data
    df <- read.csv("{data_path}")
    X <- as.matrix(df[, grep("X", names(df))])
    y <- df$y
    
    # Run lmrob
    # We enforce the seed to try and match subsampling if possible, but 
    # capturing the EXACT subsampling sequence across languages is hard.
    # So we might check if the result is 'close' or if we can fix the seed in R.
    # R's set.seed works for R's RNG. 
    # My Python random subsampling uses numpy RNG.
    # They won't match exactly on subsampling choices unless I manually 
    # feed the indices or use the exact same algorithm and RNG (hard).
    
    # However, for a clear outlier problem, S-estimator should converge to the 
    # same global minimum if nResample is large enough.
    
    set.seed(42) 
    fit <- lmrob(y ~ X - 1, method="MM", control=lmrob.control(nResample=500))
    
    cat("Coefficients:", coef(fit), "\\n")
    cat("Scale:", fit$scale, "\\n")
    """
    
    with open("temp_script.R", "w") as f:
        f.write(r_script)
        
    cmd = ["Rscript", "temp_script.R"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("R failed:")
        print(result.stderr)
    return result.stdout

def test_equivalence():
    X, y, true_beta = generate_data(n=100, p=2, outlier_frac=0.1, seed=42)
    
    # Save to CSV for R
    df = pd.DataFrame(X, columns=[f"X{i}" for i in range(X.shape[1])])
    df['y'] = y
    data_path = "temp_data.csv"
    df.to_csv(data_path, index=False)
    
    # Run Python LMROB
    # We use a fixed seed for Python side subsampling
    # But since we can't easily sync RNG with R, we rely on the robustness 
    # ensuring they find the same mode.
    model = LMROB(seed=42 if hasattr(LMROB, 'seed') else None)
    # Wait, I didn't pass seed to LMROB __init__. I should update LMROB to accept seed.
    # For now, I'll update the test to mock or just run it. 
    # Actually, I should pass seed to fast_s.
    
    # Let's verify fast_s call.  LMROB calls fast_s. I should probably allow passing seed.
    # I'll update LMROB code slightly or fast_s call.
    # For this test, I'll instantiate fast_s directly or monkeypath if needed, 
    # but better: Update LMROB class.
    
    # Let's run it first to see if it crashes.
    try:
        model.fit(X, y)
        print("Python LMROB coef:", model.coef_)
        print("Python LMROB scale:", model.scale_)
    except Exception as e:
        print("Python run failed:", e)
        return

    # Run R
    r_output = run_r_lmrob(data_path)
    print("R Output:")
    print(r_output)
    
    # Cleanup
    if os.path.exists("temp_script.R"): os.remove("temp_script.R")
    if os.path.exists(data_path): os.remove(data_path)

if __name__ == "__main__":
    test_equivalence()
