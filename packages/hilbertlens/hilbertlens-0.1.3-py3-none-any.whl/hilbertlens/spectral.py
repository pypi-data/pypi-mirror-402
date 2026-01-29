import numpy as np

def compute_spectrum(kernel_fn, n_samples=1000, range_max=4*np.pi):
    """
    Analyzes the frequency spectrum of a quantum kernel.

    Args:
        kernel_fn (callable): A function that takes a numpy array of shape (N, 1)
                              and returns the kernel matrix (N, N) or vector (N,).
                              We assume K(x, 0) captures the structure.
        n_samples (int): Number of points to sample for the FFT. 
                         Higher = better resolution, less aliasing.
        range_max (float): The interval to sample [0, range_max].
                           For standard Pauli encodings, 2*pi or 4*pi is standard.

    Returns:
        freqs (np.array): The detected integer frequencies (0, 1, 2...).
        power (np.array): The normalized power (importance) of each frequency.
    """
    
    # 1. Sweep
    X_sweep = np.linspace(0, range_max, n_samples).reshape(-1, 1)
    
    # 2. Get Signal (K(x, 0))
    K_matrix = kernel_fn(X_sweep)
    signal = K_matrix[:, 0]
    
    # 3. FFT
    # Normalize signal by subtracting mean (removes the DC component/Frequency 0 spike)
    # This helps us see the 'structure' frequencies better.
    signal_centered = signal - np.mean(signal)
    
    fft_coeffs = np.fft.rfft(signal_centered)
    power_spectrum = np.abs(fft_coeffs)**2
    
    # 4. Map to Frequencies
    # fft_freqs returns 'cycles per radian'
    fft_freqs = np.fft.rfftfreq(n_samples, d=(range_max/n_samples))
    
    # Convert to 'k' in e^{ikx}
    # If wave is cos(x), period is 2pi, so k=1.
    # rfftfreq gives 1/(2pi) for that wave. 
    # So we multiply by 2pi to get 'k'.
    freqs_k = fft_freqs * (2 * np.pi)
    
    # Normalize power
    if np.sum(power_spectrum) > 1e-10:
        power_normalized = power_spectrum / np.sum(power_spectrum)
    else:
        power_normalized = power_spectrum
    
    return freqs_k, power_normalized