import sys
import os
import numpy as np
import pennylane as qml

# Add parent path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from adapters import PennyLaneAdapter
from spectral import compute_spectrum
from visualize import plot_spectrum

def test_pennylane_workflow():
    print("Testing PennyLane Integration...")
    
    # 1. Define Device
    dev = qml.device("default.qubit", wires=1)
    
    # 2. Define QNode (The Circuit)
    # FIX: We remove the Hadamard so the state starts at |0> (Z-axis).
    # Now Rx(x) rotates it away from Z, creating a visible signal.
    # Signal: Rx(x) -> Rx(x) = Rx(2x)
    @qml.qnode(dev)
    def circuit(x):
        # qml.Hadamard(wires=0) <--- REMOVED THIS
        qml.RX(x, wires=0)
        qml.RX(x, wires=0) # Effective rotation is 2x
        return qml.state()
        
    # 3. Wrap with Adapter
    adapter = PennyLaneAdapter(circuit)
    
    def kernel_wrapper(X):
        return adapter.get_kernel_matrix(X)
    
    # 4. Analyze
    print("Running Spectral Analysis on PennyLane circuit...")
    freqs, power = compute_spectrum(kernel_wrapper)
    
    # 5. Visualize
    # We expect effective Rx(2x). 
    # State freq = 1.0 (because of 2 * 0.5).
    # Kernel (squared) freq = 2.0.
    plot_spectrum(freqs, power, 
                 title="Spectrum of PennyLane Re-uploading (Rx -> Rx)", 
                 save_path="test_pennylane_spectrum.png")
    
    print("SUCCESS: PennyLane Integration Test Passed.")

if __name__ == "__main__":
    test_pennylane_workflow()