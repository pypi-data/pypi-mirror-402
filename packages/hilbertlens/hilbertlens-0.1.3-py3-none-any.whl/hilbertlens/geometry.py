import numpy as np
from scipy.stats import spearmanr
from sklearn.decomposition import KernelPCA
from sklearn.metrics import pairwise_distances

def compute_geometry_score(X, kernel_matrix):
    """
    Measures how well the quantum kernel preserves the classical distances.
    
    Args:
        X (array): Input data (N, d).
        kernel_matrix (array): Quantum Kernel matrix (N, N).
        
    Returns:
        score (float): Spearman correlation (-1 to 1). 
                       1.0 means perfect preservation of relative distances.
    """
    # 1. Classical Distances (Euclidean)
    # We take the upper triangle only (excluding diagonal) to avoid redundancy
    d_class = pairwise_distances(X, metric='euclidean')
    flat_class = d_class[np.triu_indices_from(d_class, k=1)]
    
    # 2. Quantum Distances
    # Derived from Kernel: d_Q(x, y)^2 = K(x,x) + K(y,y) - 2K(x,y)
    # For normalized states, K(x,x)=1, so d_Q^2 = 2 - 2K(x,y)
    # We can just correlate with (1 - K) or sqrt(2 - 2K). 
    # Since Spearman is rank-based, correlating with -K is sufficient 
    # (higher similarity = lower distance).
    
    # We use the raw kernel values. High K = Low Distance.
    # So we expect a NEGATIVE correlation between Distance and Kernel.
    flat_kernel = kernel_matrix[np.triu_indices_from(kernel_matrix, k=1)]
    
    # We compute correlation between Classical Distance and Quantum Kernel
    corr, _ = spearmanr(flat_class, flat_kernel)
    
    # Invert sign so positive is "good"
    # (Distance goes UP, Kernel should go DOWN -> Correlation is approx -1)
    # So we return -corr.
    return -corr

def project_quantum_state(kernel_matrix, n_components=3):
    """
    Uses Kernel PCA to project the quantum state back to 3D for visualization.
    """
    kpca = KernelPCA(n_components=n_components, kernel='precomputed')
    X_projected = kpca.fit_transform(kernel_matrix)
    return X_projected