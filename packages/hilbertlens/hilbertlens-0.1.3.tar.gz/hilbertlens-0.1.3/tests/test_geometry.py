import numpy as np
import sys
import os
from sklearn.datasets import make_swiss_roll
from sklearn.metrics.pairwise import rbf_kernel

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from geometry import compute_geometry_score, project_quantum_state
from visualize import plot_manifold_3d

def test_geometry_preservation():
    print("Testing Geometry Preservation (Swiss Roll)...")
    
    # 1. Generate Swiss Roll Data
    # X_swiss is (N, 3), color is the position along the roll
    n_samples = 300
    X_swiss, color = make_swiss_roll(n_samples=n_samples, noise=0.1)
    
    # Normalize X to reasonable range for kernels
    X_swiss = (X_swiss - X_swiss.mean()) / X_swiss.std()

    # --- CASE 1: The "Good" Encoding ---
    # We use an RBF kernel (Gaussian) which is known to preserve local structure nicely.
    # K(x, y) = exp(-gamma * ||x-y||^2)
    print("\n[Case 1] Testing RBF Kernel (Structure Preserving)...")
    K_good = rbf_kernel(X_swiss, gamma=0.5)
    
    score_good = compute_geometry_score(X_swiss, K_good)
    print(f"Geometry Score (Correlation): {score_good:.3f}")
    
    # Visualize it
    X_proj_good = project_quantum_state(K_good)
    plot_manifold_3d(X_proj_good, color, 
                    title=f"RBF Kernel Projection (Score: {score_good:.2f})", 
                    save_path="test_geometry_good.png")

    # Assert that score is high (should be > 0.8 for RBF on Swiss Roll)
    assert score_good > 0.8, "RBF Kernel should have high geometry preservation!"


    # --- CASE 2: The "Bad" Encoding ---
    # A random kernel that ignores input structure
    print("\n[Case 2] Testing Random Kernel (Structure Destroying)...")
    np.random.seed(42)
    # Random symmetric matrix
    K_random = np.random.rand(n_samples, n_samples)
    K_random = (K_random + K_random.T) / 2
    
    score_bad = compute_geometry_score(X_swiss, K_random)
    print(f"Geometry Score (Correlation): {score_bad:.3f}")
    
    # Visualize it
    X_proj_bad = project_quantum_state(K_random)
    plot_manifold_3d(X_proj_bad, color, 
                    title=f"Random Kernel Projection (Score: {score_bad:.2f})",
                    save_path="test_geometry_bad.png")

    # Assert that score is low (close to 0)
    assert score_bad < 0.2, "Random Kernel should have low geometry preservation!"
    
    print("\nSUCCESS: HilbertLens correctly distinguished Good vs Bad geometry.")

if __name__ == "__main__":
    test_geometry_preservation()