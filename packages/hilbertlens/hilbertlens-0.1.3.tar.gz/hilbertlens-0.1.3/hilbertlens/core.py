import numpy as np
import os
from .adapters import QiskitAdapter, PennyLaneAdapter, HAS_PENNYLANE
from .spectral import compute_spectrum
from .geometry import compute_geometry_score, project_quantum_state
from .visualize import plot_spectrum, plot_manifold_3d
from .diagnose import print_report 
from sklearn.datasets import make_swiss_roll



class QuantumLens:
    def __init__(self, object_to_analyze, params=None, framework="auto"):
        """
        The main interface for HilbertLens.
        
        Args:
            object_to_analyze: The Qiskit Circuit, PennyLane QNode, or raw Python function.
            params: (Optional) The data parameter(s) for Qiskit circuits.
            framework: 'qiskit', 'pennylane', or 'auto'.
        """
        self.adapter = self._load_adapter(object_to_analyze, params, framework)

        # State to store results
        self.last_spectrum_stats = None
        self.last_geometry_stats = None
        
    def _load_adapter(self, obj, params, framework):
        # 1. Automatic Detection
        if framework == "auto":
            obj_type = str(type(obj))
            if "qiskit" in obj_type:
                framework = "qiskit"
            elif "pennylane" in obj_type:
                framework = "pennylane"
            else:
                raise ValueError(f"Could not auto-detect framework for {obj_type}. Please specify 'framework='.")

        # 2. Initialize specific adapter
        print(f"[HilbertLens] Initialized for framework: {framework}")
        
        if framework == "qiskit":
            if params is None:
                raise ValueError("For Qiskit, you must provide the 'params' argument (the input data parameters).")
            return QiskitAdapter(obj, params)
            
        elif framework == "pennylane":
            if not HAS_PENNYLANE:
                raise ImportError("PennyLane not installed.")
            return PennyLaneAdapter(obj)
            
        else:
            raise ValueError(f"Unknown framework: {framework}")

    def spectrum(self, mode='local', feature_index=0, save_path=None):
        """
        Analyzes and plots the frequency spectrum.
        
        Args:
            mode (str): 'local' (sweep one feature, freeze others) 
                        or 'global' (sweep all features together: x1=t, x2=t...).
            feature_index (int): If mode='local', which feature index to sweep.
            save_path (str): Path to save the plot.
        """
        print(f"[HilbertLens] Computing Spectrum (Mode: {mode})...")
        
        # --- SMART WRAPPER ---
        def kernel_wrapper(X_sweep):
            """
            X_sweep is (N, 1).
            We need to map this 1D sweep to the circuit's full input dimensions.
            """
            # 1. Ask the adapter how many features it needs
            if hasattr(self.adapter, 'n_params') and self.adapter.n_params is not None:
                n_required = self.adapter.n_params # <--- DYNAMIC!
            else:
                n_required = 1 # Fallback
            
            # 2. Create the Input Matrix (N, n_required)
            N = X_sweep.shape[0]
            X_full = np.zeros((N, n_required))
            
            if mode == 'global':
                # Broadcast t to ALL features
                for col in range(n_required):
                    X_full[:, col] = X_sweep.flatten()
            elif mode == 'local':
                if feature_index >= n_required:
                    raise ValueError(f"Index {feature_index} out of bounds for {n_required}-feature circuit.")
                X_full[:, feature_index] = X_sweep.flatten()
            
            return self.adapter.get_kernel_matrix(X_full)
        # --- END WRAPPER ---

        freqs, power = compute_spectrum(kernel_wrapper)
        
        title = f"Spectrum ({mode.title()} Sweep)"
        if mode == 'local':
            title += f" - Feature {feature_index}"
            
        plot_spectrum(freqs, power, title=title, save_path=save_path)
        
        top_idx = np.argmax(power)
        
        # STORE FULL RESULTS (Updated)
        
        self.last_spectrum_stats = {
            "dominant_freq": freqs[top_idx], 
            "max_power": power[top_idx],
            "freqs": freqs,  
            "power": power  
        }
        return self.last_spectrum_stats

    def geometry(self, X_data=None, n_samples=200, save_path=None):
        """
        Analyzes geometry preservation. 
        If X_data is None, automatically generates a Swiss Roll.
        """
        print("[HilbertLens] Analyzing Geometry...")
        
        if X_data is None:
            print("  - No data provided. Generating synthetic Swiss Roll (n=200)...")
            X_data, color = make_swiss_roll(n_samples=n_samples, noise=0.1)
            # Normalize
            X_data = (X_data - X_data.mean()) / X_data.std()
            # Scale to fit into standard rotation range (approx -1 to 1) 
            # so we don't spin the qubit 1000 times
            X_data = X_data * 1.5 
        else:
            # If user provided data, we assume they have 'color' or labels for plotting?
            # For this simple version, we just use the first dimension as color
            color = X_data[:, 0]

        # 1. Compute Kernel
        # If the input is multidimensional, our current adapters handle it.
        # However, simple 1-qubit circuits might expect 1D data.
        # We'll try passing it directly.
        
        try:
            K_matrix = self.adapter.get_kernel_matrix(X_data)
        except Exception as e:
            print(f"Error computing kernel: {e}")
            print("Hint: Does your circuit have enough parameters for {X_data.shape[1]} features?")
            return None

        # 2. Score
        score = compute_geometry_score(X_data, K_matrix)
        print(f"  - Geometry Score (Spearman Correlation): {score:.4f}")
        
        # 3. Project & Plot
        X_proj = project_quantum_state(K_matrix)
        
        title = f"Geometry Projection (Score: {score:.2f})"
        plot_manifold_3d(X_proj, color, title=title, save_path=save_path)
        
        # STORE RESULTS
        self.last_geometry_stats = {"score": score}
        return self.last_geometry_stats
    
    def diagnose(self):
        """
        Generates the full research report based on previous runs.
        Auto-runs components if they are missing.
        """
        # If user hasn't run geometry yet, run it with default Swiss Roll
        if self.last_geometry_stats is None:
            print("[Auto-Run] Geometry data missing. Running default Swiss Roll check...")
            self.geometry()

        # If user hasn't run spectrum yet, run it with default Global Sweep
        if self.last_spectrum_stats is None:
            print("[Auto-Run] Spectrum data missing. Running default 'global' sweep...")
            self.spectrum(mode='global')

            
        # Generate Report
        print_report(self.last_spectrum_stats, self.last_geometry_stats)