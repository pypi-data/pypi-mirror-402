import numpy as np
import sys
import os

# Add the parent directory to path so we can import hilbertlens
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from spectral import compute_spectrum

def test_cosine_kernel():
    """
    Scientific Check: 
    If the kernel is exactly K(x, 0) = cos(x),
    HilbertLens MUST report a spike at Frequency = 1.0.
    """
    
    # 1. Define a dummy kernel function
    # It takes X (shape N,1) and returns an (N,N) matrix
    # But for our 'signal' extraction, we only care that K[i, 0] = cos(X[i])
    def dummy_kernel_cos1(X):
        # Create a matrix where col 0 is cos(X)
        N = X.shape[0]
        K = np.zeros((N, N))
        # We only populate the first column because compute_spectrum reads K[:, 0]
        K[:, 0] = np.cos(X.flatten()) 
        return K

    # 2. Run Analysis
    freqs, power = compute_spectrum(dummy_kernel_cos1, n_samples=1000, range_max=2*np.pi)
    
    # 3. Check Results
    # Find the frequency with the maximum power
    max_idx = np.argmax(power)
    dominant_freq = freqs[max_idx]
    
    print(f"\n[Test 1] Dominant Frequency detected: {dominant_freq:.2f}")
    
    # Allow small numerical error (e.g. 0.99 or 1.01)
    assert np.isclose(dominant_freq, 1.0, atol=0.1), f"Expected Freq 1.0, got {dominant_freq}"
    
    # 4. Test High Frequency (Freq = 5)
    def dummy_kernel_cos5(X):
        N = X.shape[0]
        K = np.zeros((N, N))
        # K(x) = cos(5x)
        K[:, 0] = np.cos(5 * X.flatten()) 
        return K

    freqs_5, power_5 = compute_spectrum(dummy_kernel_cos5, n_samples=1000, range_max=2*np.pi)
    max_idx_5 = np.argmax(power_5)
    dominant_freq_5 = freqs_5[max_idx_5]
    
    print(f"[Test 2] Dominant Frequency detected: {dominant_freq_5:.2f}")
    assert np.isclose(dominant_freq_5, 5.0, atol=0.1), f"Expected Freq 5.0, got {dominant_freq_5}"

if __name__ == "__main__":
    test_cosine_kernel()