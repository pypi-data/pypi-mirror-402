"""
Adapters for Quantum Frameworks (Qiskit, PennyLane).

This module provides a unified interface for computing quantum kernels from different
software frameworks. It handles input validation, parameter binding, and statevector
simulation to generate the Gram matrix required for geometric analysis.
"""

import numpy as np
import warnings
from typing import List, Union, Optional, Any

# --- Optional Framework Imports ---
try:
    from qiskit import QuantumCircuit
    from qiskit.circuit import Parameter
    from qiskit.quantum_info import Statevector
    HAS_QISKIT = True
except ImportError:
    HAS_QISKIT = False

try:
    import pennylane as qml
    HAS_PENNYLANE = True
except ImportError:
    HAS_PENNYLANE = False


class BaseAdapter:
    """Base class defining the interface for all quantum adapters."""
    
    def get_kernel_matrix(self, X: np.ndarray) -> np.ndarray:
        raise NotImplementedError("Subclasses must implement get_kernel_matrix.")

    def _validate_input(self, X: np.ndarray, required_features: Optional[int] = None) -> np.ndarray:
        """
        Sanitizes and validates input data.
        
        Args:
            X: Input data.
            required_features: Expected number of columns (features).
            
        Returns:
            Cleaned numpy array of shape (N, d).
        """
        # 1. Convert to numpy array
        if not isinstance(X, np.ndarray):
            try:
                X = np.array(X)
            except Exception as e:
                raise TypeError(f"Input data must be convertible to a numpy array. Got {type(X)}.") from e

        # 2. Handle 1D Arrays (N,) -> (N, 1)
        if X.ndim == 1:
            X = X.reshape(-1, 1)
            
        # 3. Check for NaNs or Infinite values
        if not np.isfinite(X).all():
            raise ValueError("Input data contains NaNs or infinite values.")

        # 4. Dimension Check (Scalability Guardrail)
        if required_features is not None:
            n_features = X.shape[1]
            if n_features != required_features:
                raise ValueError(
                    f"Dimension Mismatch: Input data has {n_features} features, "
                    f"but the quantum circuit expects {required_features} parameters.\n"
                    f"  -> Input Shape: {X.shape}\n"
                    f"  -> Circuit Params: {required_features}\n"
                    "Resolution: Reduce data dimensionality (e.g., PCA) or increase circuit width."
                )
        
        return X


class QiskitAdapter(BaseAdapter):
    """
    Adapter for Qiskit QuantumCircuits.
    """
    
    def __init__(self, circuit: 'QuantumCircuit', data_params: Union[List['Parameter'], 'Parameter'], use_gpu: bool = False):
        """
        Wraps a Qiskit circuit to behave like a Kernel function.

        Args:
            circuit (QuantumCircuit): The ansatz circuit.
            data_params (list or Parameter): The parameter(s) representing input data.
            use_gpu (bool): Placeholder for future GPU acceleration (e.g., via qiskit-aer-gpu).
        """
        if not HAS_QISKIT:
            raise ImportError("Qiskit is not installed. Please install it via 'pip install qiskit'.")
        
        if not isinstance(circuit, QuantumCircuit):
            raise TypeError(f"Expected qiskit.QuantumCircuit, got {type(circuit)}.")

        self.circuit = circuit
        self.use_gpu = use_gpu

        # Normalize data_params to a list
        if isinstance(data_params, (list, tuple, np.ndarray)):
            self.data_params = list(data_params)
        else:
            self.data_params = [data_params]
            
        self.n_params = len(self.data_params)

    def get_kernel_matrix(self, X: np.ndarray) -> np.ndarray:
        """
        Computes the kernel matrix K(x, y) = |<psi(x)|psi(y)>|^2.
        
        Args:
            X (np.ndarray): Input data (N, d).
            
        Returns:
            np.ndarray: Kernel matrix (N, N).
        """
        # Validate and standardise input
        X = self._validate_input(X, required_features=self.n_params)
        
        N = X.shape[0]
        state_vectors = []

        # Optimization Note:
        # Ideally, we would use Qiskit Primitives (Sampler/Estimator) for this.
        # However, for pure statevector simulation of small circuits (common in QML research),
        # direct Statevector simulation is often faster and has less overhead than local primitives.
        
        try:
            for i in range(N):
                # Efficiently map parameters
                # We assume the order of columns in X matches the order of data_params
                param_dict = dict(zip(self.data_params, X[i]))
                
                # Bind parameters. Note: assign_parameters creates a COPY. 
                # Ideally, we bind in place or use a backend, but for raw SV this is standard.
                bound_circuit = self.circuit.assign_parameters(param_dict)
                
                # Extract statevector
                sv = Statevector(bound_circuit).data
                state_vectors.append(sv)
                
        except Exception as e:
            raise RuntimeError(f"Qiskit simulation failed at index {i}. Check parameter bindings.") from e

        # Compute Gram Matrix using vectorization
        # shape: (N, 2^n_qubits)
        M = np.array(state_vectors)
        
        # Inner products: <psi(x) | psi(y)>
        # M @ M.H (Conjugate Transpose)
        inner_products = M @ M.conj().T
        
        # Fidelity is magnitude squared
        kernel_matrix = np.abs(inner_products)**2
        
        return kernel_matrix

    def __repr__(self):
        return f"<QiskitAdapter: {self.n_params} params, {self.circuit.num_qubits} qubits>"


class PennyLaneAdapter(BaseAdapter):
    """
    Adapter for PennyLane QNodes.
    """
    
    def __init__(self, qnode: Any):
        """
        Wraps a PennyLane QNode.

        Args:
            qnode (qml.QNode): A PennyLane QNode that returns qml.state().
                               Must accept data 'x' as its first argument.
        """
        if not HAS_PENNYLANE:
            raise ImportError("PennyLane is not installed. Run 'pip install pennylane'.")
        
        # Basic duck-typing check
        if not hasattr(qnode, "func") and not hasattr(qnode, "device"):
             warnings.warn("The provided object does not look like a standard PennyLane QNode. "
                           "Ensure it returns a state vector.")

        self.qnode = qnode
        
        # Attempt to infer number of parameters (Heuristic)
        # PennyLane doesn't always expose this easily without inspection.
        self.n_params = None 

    def get_kernel_matrix(self, X: np.ndarray) -> np.ndarray:
        """
        Computes the kernel matrix using the QNode.
        """
        # Validate input (Can't check n_params strictly yet, so pass None)
        X = self._validate_input(X, required_features=None)
        
        N = X.shape[0]
        state_vectors = []
        
        # 1. Compute States
        for i in range(N):
            row = X[i] # Shape (d,)
            
            # Handle Scalar vs Vector inputs for PennyLane
            # Some QNodes expect x to be a float, others a list/array.
            if row.size == 1:
                qnode_input = row[0]
            else:
                qnode_input = row

            try:
                state = self.qnode(qnode_input)
            except Exception as e:
                raise RuntimeError(
                    f"PennyLane QNode execution failed on sample {i}.\n"
                    f"Input shape: {row.shape}. Value: {row}\n"
                    "Ensure your QNode accepts this input format."
                ) from e
            
            # Convert generic tensor types (Torch/TF/Autograd) to Numpy
            if hasattr(state, "numpy"):
                state = state.numpy()
            elif hasattr(state, "detach"): # PyTorch
                 state = state.detach().numpy()
            
            state_vectors.append(state)
            
            # Heuristic: Set n_params after first successful run if unknown
            if self.n_params is None:
                self.n_params = row.size

        # 2. Compute Gram Matrix
        M = np.array(state_vectors)
        
        # Check if M is actually a matrix of numbers (not objects)
        if M.dtype == object:
             raise ValueError("PennyLane returned non-numeric state vectors. Ensure QNode returns qml.state().")

        inner_products = M @ M.conj().T
        kernel_matrix = np.abs(inner_products)**2
        
        return kernel_matrix

    def __repr__(self):
        return f"<PennyLaneAdapter: {self.n_params if self.n_params else '?'} params>"