import sys
import os
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter

# Add parent path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from adapters import QiskitAdapter
from spectral import compute_spectrum
from visualize import plot_spectrum

def test_qiskit_workflow():
    print("Testing Qiskit Integration...")
    
    # 1. Create a Qiskit Circuit
    # We will create a simple 'Angle Encoding' circuit
    # H -> Rz(x) -> H  (This is a standard feature map)
    x = Parameter('x')
    qc = QuantumCircuit(1)
    qc.h(0)
    qc.rz(x, 0)
    # Note: Rz(x) introduces e^{-ix/2}. 
    # The kernel |<psi(x)|psi(0)>|^2 usually reveals cos(x/2) or cos(x) depending on measurement.
    
    print("Circuit created:")
    print(qc)
    
    # 2. Wrap it with our Adapter
    adapter = QiskitAdapter(circuit=qc, data_params=x)
    
    # 3. Define the function helper for our spectral tool
    # The spectral tool expects a function f(X) -> Matrix
    def kernel_wrapper(X):
        return adapter.get_kernel_matrix(X)
    
    # 4. Run Spectral Analysis
    print("Running Spectral Analysis on Qiskit circuit...")
    freqs, power = compute_spectrum(kernel_wrapper)
    
    # 5. Visualize
    print("Generating plot...")
    plot_spectrum(freqs, power, 
                 title="Spectrum of Qiskit Angle Encoding (Rz)", 
                 save_path="test_qiskit_spectrum.png")
    
    print("SUCCESS: Qiskit Integration Test Passed.")

if __name__ == "__main__":
    test_qiskit_workflow()