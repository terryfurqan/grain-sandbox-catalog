import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import generic_filter
import os

def calculate_normalized_median_test(u, v, epsilon=0.1):
    """
    Calculate the normalized median test (Westerweel & Scarano, 2005)
    for a PIV vector field (u, v).
    """
    def westerweel_filter(x):
        # x is a 1D array of the 3x3 neighborhood. Center is index 4.
        center = x[4]
        neighbors = np.delete(x, 4)
        median_val = np.median(neighbors)
        
        # Residual of the center vector
        r_c = np.abs(center - median_val)
        
        # Median residual of the neighbors (deviation from median)
        r_m = np.median(np.abs(neighbors - median_val))
        
        # Normalized residual
        return r_c / (r_m + epsilon)

    # Apply the filter to u and v components
    u_norm = generic_filter(u, westerweel_filter, size=3)
    v_norm = generic_filter(v, westerweel_filter, size=3)
    
    # Combined normalized residual magnitude
    norm_res_mag = np.sqrt(u_norm**2 + v_norm**2)
    
    return norm_res_mag, u_norm, v_norm

def compute_uncertainty_map(u, v, snr, w_res=0.6, w_snr=0.4, epsilon=0.1):
    """
    Compute a composite Uncertainty Map based on Normalized Median Test and SNR.
    Uncertainty is high when normalized residual is high or SNR is low.
    """
    norm_res_mag, _, _ = calculate_normalized_median_test(u, v, epsilon)
    
    # Normalize residuals to 0-1 scale (cap at a typical outlier threshold, e.g., 2.0 or 3.0)
    res_threshold = 2.0
    norm_res_scaled = np.clip(norm_res_mag / res_threshold, 0, 1)
    
    # SNR typically ranges from 1.0 (noise level) to higher values (e.g. 5.0+ for good correlation)
    # Invert it so low SNR means high uncertainty
    snr_min = 1.2  # Below this is considered very noisy
    snr_max = 4.0  # Above this is considered clear signal
    snr_scaled = 1.0 - np.clip((snr - snr_min) / (snr_max - snr_min), 0, 1)
    
    # Composite Uncertainty
    uncertainty_map = w_res * norm_res_scaled + w_snr * snr_scaled
    uncertainty_map = np.clip(uncertainty_map, 0, 1)
    
    return uncertainty_map, norm_res_mag, snr_scaled

def create_mock_data(shape=(40, 60)):
    """Generate mock u, v matrices and an SNR matrix with some anomalies."""
    x = np.linspace(-5, 5, shape[1])
    y = np.linspace(-5, 5, shape[0])
    X, Y = np.meshgrid(x, y)
    
    # Smooth base velocity field (vortex-like)
    u = -Y
    v = X
    
    # Base SNR (good everywhere)
    snr = np.ones(shape) * 5.0
    
    # 1. Introduce an outlier region (high residual, bad vectors)
    u[15:20, 20:25] += 8.0 
    v[15:20, 20:25] -= 8.0
    
    # 2. Introduce a low SNR region (e.g. shadow, poor seeding, out-of-focus)
    # The vectors here might still be correct if interpolated or barely matched, 
    # but confidence should be low.
    snr[25:35, 40:50] = 1.1
    
    # 3. Single random spike (classic PIV outlier)
    u[5, 50] = 20.0
    v[5, 50] = -15.0
    
    return u, v, snr

def main():
    print("Generating mock PIV data...")
    u, v, snr = create_mock_data()
    
    print("Computing uncertainty map using Normalized Median Test...")
    uncertainty_map, norm_res_mag, snr_scaled = compute_uncertainty_map(u, v, snr)
    
    # Calculate confidence score (1 - uncertainty)
    confidence_score = 1.0 - uncertainty_map
    
    print("Plotting results...")
    fig, axs = plt.subplots(2, 2, figsize=(14, 10))
    
    # A. Plot Velocity Field
    step = 2
    Y_idx, X_idx = np.mgrid[0:u.shape[0], 0:u.shape[1]]
    axs[0, 0].quiver(X_idx[::step, ::step], Y_idx[::step, ::step], 
                     u[::step, ::step], v[::step, ::step], 
                     color='black', angles='xy', scale_units='xy', scale=1.0)
    axs[0, 0].set_title('A. Velocity Field (Mock Data w/ Outliers)')
    axs[0, 0].invert_yaxis()
    
    # B. Plot SNR
    im1 = axs[0, 1].imshow(snr, cmap='viridis', vmin=1.0, vmax=5.0)
    axs[0, 1].set_title('B. Signal-to-Noise Ratio (SNR)')
    fig.colorbar(im1, ax=axs[0, 1], label='SNR')
    
    # C. Plot Normalized Residuals
    im2 = axs[1, 0].imshow(norm_res_mag, cmap='magma', vmin=0, vmax=3.0)
    axs[1, 0].set_title('C. Normalized Median Residuals\n(Westerweel & Scarano, 2005)')
    fig.colorbar(im2, ax=axs[1, 0], label='Norm. Residual Mag.')
    
    # D. Plot Composite Uncertainty Map
    im3 = axs[1, 1].imshow(uncertainty_map, cmap='inferno', vmin=0, vmax=1.0)
    axs[1, 1].set_title('D. Composite Uncertainty Map\n(High = Uncertain, Low = Confident)')
    fig.colorbar(im3, ax=axs[1, 1], label='Uncertainty (0.0 - 1.0)')
    
    plt.tight_layout()
    output_path = os.path.join(os.path.dirname(__file__), "uncertainty_map.png")
    plt.savefig(output_path, dpi=300)
    print(f"Saved figure to: {output_path}")
    
    # Note: Using plt.show() might block in some headless environments,
    # but the image is saved safely.
    # plt.show()

if __name__ == "__main__":
    main()
