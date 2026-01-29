import numpy as np

def analyze_spectrum_richness(freqs, power, threshold=0.05):
    """
    Analyzes the full spectrum to check for 'Richness' vs 'Single Spike'.
    Replaces the old simple capacity check.
    
    Args:
        freqs (array): Frequency values.
        power (array): Normalized power values.
        threshold (float): Minimum power to count a frequency as "active".
    
    Returns:
        dict: Stats including max_freq, n_active_freqs, category, and advice.
    """
    # 1. Identify Active Frequencies (Power > Threshold and not DC component)
    mask = (power > threshold) & (freqs > 0.1)
    active_freqs = freqs[mask]
    
    # Handle "Silent" circuit
    if len(active_freqs) == 0:
        return {
            "category": "Silent (Constant)",
            "assessment": "The circuit is not encoding the data (Output is constant).",
            "advice": "CRITICAL: Check parameter binding. Data is not rotating the state.",
            "max_freq": 0.0,
            "n_active": 0
        }

    max_freq = np.max(active_freqs)
    n_active = len(active_freqs)
    
    # 2. Categorize based on Richness (The "Painter" Logic)
    
    # Case A: Single Frequency (Lazy or Manic Painter)
    if n_active == 1:
        if max_freq <= 1.5:
            cat = "Low Capacity (Standard Linear)"
            assess = "Behaves like a linear kernel (Single brush size). Can only learn smooth boundaries."
            advice = "Safe but simple. Suitable for Iris/Cancer. For Moons/Spirals, add 'Data Re-uploading'."
        elif max_freq > 8.0:
            cat = "Extreme Frequency (High Variance)"
            assess = f"Highly oscillatory single tone (k={max_freq:.1f}). Forces rapid changes."
            advice = "RISK: Likely to overfit noise. Reduce data scaling factors."
        else:
            cat = "Sparse Spectrum"
            assess = f"Uses a single medium frequency (k={max_freq:.1f}). Lacks base structure."
            advice = "Potential 'Swiss Cheese' gaps. Add diversity to your gates."
            
    # Case B: Rich Spectrum (Master Painter)
    else:
        if max_freq <= 2.5:
            cat = "Moderate Capacity (Balanced)"
            assess = f"Uses {n_active} frequencies. Good balance of global structure and local detail."
            advice = "Good for most standard datasets."
        else:
            cat = "High Capacity (Rich Expressibility)"
            assess = f"Complex spectrum with {n_active} active frequencies. Capable of deep nuance."
            advice = "Gold Standard. Capable of universal classification."

    return {
        "category": cat,
        "assessment": assess,
        "advice": advice,
        "max_freq": max_freq,
        "n_active": n_active
    }

def analyze_geometry(score):
    """
    Interprets the Spearman Correlation score.
    Returns: (Category, Assessment)
    """
    if score >= 0.8:
        return (
            "Excellent Preservation", 
            "The quantum kernel faithfully preserves the topological structure of the input data."
        )
    elif 0.5 <= score < 0.8:
        return (
            "Moderate Distortion", 
            "Some geometric relationships are warped, but the global structure is mostly intact."
        )
    elif 0.0 <= score < 0.5:
        return (
            "High Distortion", 
            "The encoding destroys local neighborhoods. Close points become far in Hilbert space."
        )
    else:
        return (
            "Anti-Correlated / Broken", 
            "The encoding inverts the geometry (close becomes far). This is rare and usually bad."
        )

def print_report(spec_stats, geom_stats):
    """
    Prints a formatted research report combining detailed layout with deep insights.
    """
    # Extract raw data
    freqs = spec_stats.get('freqs', np.array([spec_stats['dominant_freq']]))
    power = spec_stats.get('power', np.array([spec_stats['max_power']]))
    score = geom_stats.get('score', 0)

    # Run Deep Analysis
    spec_analysis = analyze_spectrum_richness(freqs, power)
    geo_cat, geo_assess = analyze_geometry(score)

    # Format Variables for Clean Printing
    k_val = spec_analysis['max_freq']
    n_act = spec_analysis['n_active']

    print("\n" + "="*65)
    print(f"   HILBERTLENS DIAGNOSIS REPORT")
    print("="*65)
    
    # --- SECTION 1: CAPACITY ---
    print(f"\n[1] SPECTRUM ANALYSIS (Capacity & Expressibility)")
    print(f"    • Active Frequencies: {n_act} (Richness)")
    print(f"    • Max Frequency:      k={k_val:.1f} (Bandwidth)")
    print(f"    • Category:           {spec_analysis['category']}")
    print(f"    • Assessment:         {spec_analysis['assessment']}")
    print(f"    • Advice:             {spec_analysis['advice']}")

    # --- SECTION 2: GEOMETRY ---
    print(f"\n[2] GEOMETRY ANALYSIS (Inductive Bias)")
    print(f"    • Preservation Score: {score:.4f} (Spearman rho)")
    print(f"    • Category:           {geo_cat}")
    print(f"    • Assessment:         {geo_assess}")

    # --- SECTION 3: FINAL VERDICT ---
    print(f"\n[3] FINAL VERDICT")
    
    # Logic: Combine Richness AND Geometry
    if score > 0.8 and n_act > 1:
        print("    >>> [GOLD STANDARD] READY FOR RESEARCH.")
        print("        Your circuit has High Capacity (Rich Spectrum) AND Stable Geometry.")
        print("        It can learn complex boundaries without breaking data topology.")
        
    elif score > 0.8 and n_act == 1 and k_val <= 1.5:
        print("    >>> [SAFE BUT SIMPLE] GOOD FOR BASICS.")
        print("        Reliable geometry, but low capacity. Will work for Iris/Breast Cancer.")
        print("        Likely to UNDERFIT on Moons/Spirals.")
        
    elif score > 0.8 and n_act == 1 and k_val > 1.5:
        print("    >>> [POTENTIAL GAPS] SPARSE SPECTRUM.")
        print("        Geometry is good, but you rely on a single higher frequency.")
        print("        Check if the model struggles with simple linear trends.")

    elif score < 0.5:
        print("    >>> [ARCHITECTURE ISSUE] BROKEN GEOMETRY.")
        print("        The encoding scrambles the data. Capacity doesn't matter if map is bad.")
    
    else:
        print("    >>> [MIXED RESULTS] PROCEED WITH CAUTION.")
        print("        Metrics are conflicting. Check the 3D manifold plot manually.")
        
    print("="*65 + "\n")