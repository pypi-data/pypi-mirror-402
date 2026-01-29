
import numpy as np
import pandas as pd
import subprocess
import os
import sys
import re
import pytest

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from robustbase import LMROB

def run_r_lmrob(data_path, n_resample=500):
    r_script = f"""
    .libPaths(c('r_libs', .libPaths()))
    if (!requireNamespace("robustbase", quietly = TRUE)) {{
        stop("robustbase not installed")
    }}
    library(robustbase)
    
    df <- read.csv("{data_path}")
    # Assume last col is y, others are X
    y <- df$y
    X_cols <- grep("X", names(df))
    if (length(X_cols) > 0) {{
        X <- as.matrix(df[, X_cols])
        # Need strict formula?
        # y ~ X - 1 works if X is a matrix in environment or df.
        # But lmrob(y ~ ., data=df) might be easier but includes intercept unless -1
        # Let's use matrix interface via formula
    }} else {{
        stop("No X columns")
    }}
    
    set.seed(42)
    # nResample control
    ctrl <- lmrob.control(nResample={n_resample})
    
    # We fit without intercept if data generator doesn't include it or X includes it?
    # Our data generator X is N(0,1), true beta ones.
    # Python code: y = X @ beta + noise. X doesn't have 1s column.
    
    fit <- lmrob(y ~ X - 1, method="MM", control=ctrl)
    
    # Print formatted output for parsing
    cat("COEF_START\\n")
    cat(coef(fit), "\\n")
    cat("COEF_END\\n")
    
    cat("SCALE_START\\n")
    cat(fit$scale, "\\n")
    cat("SCALE_END\\n")
    """
    
    script_path = f"{data_path}.R"
    with open(script_path, "w") as f:
        f.write(r_script)
        
    cmd = ["Rscript", script_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # cleanup
    if os.path.exists(script_path):
        os.remove(script_path)
        
    if result.returncode != 0:
        raise RuntimeError(f"R script failed:\n{result.stderr}")
        
    return result.stdout

def parse_r_output(output):
    coef_match = re.search(r"COEF_START\s+(.*?)\s+COEF_END", output, re.DOTALL)
    scale_match = re.search(r"SCALE_START\s+(.*?)\s+SCALE_END", output, re.DOTALL)
    
    if not coef_match or not scale_match:
        raise ValueError("Could not parse R output")
        
    coef_str = coef_match.group(1).strip()
    coefs = np.array([float(x) for x in coef_str.split()])
    
    scale_str = scale_match.group(1).strip()
    scale = float(scale_str)
    
    return coefs, scale

@pytest.mark.parametrize("n, p, outlier_frac, seed", [
    (100, 2, 0.1, 42),
    (200, 5, 0.2, 10),
    (50, 1, 0.0, 99), # No outliers
    (150, 3, 0.3, 123)
])
def test_simulation_equivalence(n, p, outlier_frac, seed):
    # Generate data
    rng = np.random.default_rng(seed)
    X = rng.standard_normal((n, p))
    true_beta = np.ones(p) #* rng.uniform(0.5, 1.5, p)
    y = X @ true_beta + rng.standard_normal(n)
    
    # Add outliers
    n_outliers = int(n * outlier_frac)
    if n_outliers > 0:
        outlier_indices = rng.choice(n, n_outliers, replace=False)
        y[outlier_indices] = y[outlier_indices] + 10 * rng.choice([-1, 1], n_outliers) * rng.uniform(2, 5, n_outliers)
    
    # Save for R
    df = pd.DataFrame(X, columns=[f"X{i}" for i in range(p)])
    df['y'] = y
    data_filename = f"temp_data_{seed}_{n}_{p}.csv"
    df.to_csv(data_filename, index=False)
    
    try:
        # Run Python
        # Set seed for reproducibility of subsampling
        model = LMROB(n_resample=500, seed=42) # Use fixed seed 42 to match R's set.seed(42) in script?
        # Note: R script sets set.seed(42) explicitly. 
        # Python LMROB uses numpy RNG initialized with seed passed to __init__.
        # Even if we use same seed, RNG algos differ between R and Numpy.
        # But for well-posed robust problems, they should converge to the same global optimum.
        
        model.fit(X, y)
        py_coef = model.coef_
        py_scale = model.scale_
        
        # Run R
        r_out = run_r_lmrob(data_filename, n_resample=500)
        r_coef, r_scale = parse_r_output(r_out)
        
        print(f"\nScenario: n={n}, p={p}, frac={outlier_frac}")
        print("Python Coef:", py_coef)
        print("R Coef:     ", r_coef)
        print("Python Scale:", py_scale)
        print("R Scale:     ", r_scale)
        
        # Comparison tolerance
        # Scale checking
        assert np.isclose(py_scale, r_scale, rtol=1e-2), f"Scales differ: Py={py_scale}, R={r_scale}"
        
        # Coef checking
        # If scale matches, coefs should match well.
        # Sometimes MM iterations might stick to slightly different local optima if very complex, 
        # but usually unique.
        assert np.allclose(py_coef, r_coef, rtol=1e-2, atol=1e-2), f"Coefs differ"
        
    finally:
        if os.path.exists(data_filename):
            os.remove(data_filename)

if __name__ == "__main__":
    # Allow running directly
    sys.exit(pytest.main(["-v", __file__]))
