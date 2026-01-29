import numpy as np
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from spectral import compute_spectrum
from visualize import plot_spectrum

def test_visual_spectrum():
    print("Testing 4pi range with visualization and saving...")

    # Case 1: The "Quantum Rotation" Simulator (k=0.5)
    def quantum_rotation_kernel(X):
        return np.cos(0.5 * X) 

    freqs, power = compute_spectrum(quantum_rotation_kernel)
    
    # Define save location
    save_file = "test_spectrum_k0.5.png"
    
    # Clean up old test file if it exists
    if os.path.exists(save_file):
        os.remove(save_file)
        
    print("\n[Case 1: Rotation Gate (k=0.5)]")
    # This should generate a file instead of popping up a window
    plot_spectrum(freqs, power, title="Spectrum of Standard Rotation Gate (Expected k=0.5)", save_path=save_file)
    
    # Verification
    if os.path.exists(save_file):
        print(f"SUCCESS: File {save_file} was created.")
    else:
        print(f"FAILURE: File {save_file} was NOT created.")
        
    # Case 2: Multi-Frequency (k=1, k=3) - Show this one interactively
    def complex_kernel(X):
        return 0.5 * np.cos(1.0 * X) + 0.5 * np.cos(3.0 * X)

    freqs, power = compute_spectrum(complex_kernel)
    print("\n[Case 2: Multi-Frequency (k=1, k=3)]")
    # Define save location
    save_file = "test_spectrum_k1_k3.png"
    plot_spectrum(freqs, power, title="Spectrum of Complex Encoding", save_path=save_file) # No save_path -> show window

if __name__ == "__main__":
    test_visual_spectrum()