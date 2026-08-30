import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from skimage import io
import torch

# Append skill path to import the GPU PIV engine
sys.path.insert(0, r"C:\Users\Sandbox_Main\.gemini\config\skills\grain-piv\scripts")
try:
    from grain_piv_v2 import detect_hardware, run_3pass_piv_gpu, validate_and_smooth_gpu
except ImportError:
    print("Error: Module grain_piv_v2 tidak ditemukan.")
    print("Pastikan path ke grain-piv/scripts benar.")
    sys.exit(1)

def calculate_peak_locking_bias(frac_array, num_bins=20):
    """
    Menghitung Peak-Locking Bias Metric.
    Jika distribusi merata (uniform), frekuensi setiap bin idealnya adalah 1/num_bins.
    Metrik ini adalah RMS (Root Mean Square) dari deviasi frekuensi histogram 
    terhadap frekuensi ideal. Nilai lebih tinggi menunjukkan peak-locking yang lebih parah.
    """
    hist, _ = np.histogram(frac_array, bins=num_bins, range=(0.0, 1.0), density=True)
    # density=True berarti integral adalah 1. Lebar setiap bin adalah 1/num_bins.
    # Jadi kepadatan frekuensi ideal untuk uniform adalah 1.0 di setiap bin.
    ideal_density = 1.0
    rms_deviation = np.sqrt(np.mean((hist - ideal_density)**2))
    return rms_deviation

def plot_peak_locking_histogram(u_frac, v_frac, u_bias, v_bias, output_filename="peak_locking_histogram.png"):
    """
    Membuat dan menyimpan plot histogram dari u_frac dan v_frac.
    """
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Plot U fractional
    axes[0].hist(u_frac.flatten(), bins=20, range=(0.0, 1.0), color='blue', alpha=0.7, edgecolor='black', density=True)
    axes[0].set_title(f'Distribusi Fraksional U\nPeak-Locking Bias (RMS): {u_bias:.3f}')
    axes[0].set_xlabel('Fractional Part of U (px)')
    axes[0].set_ylabel('Density')
    axes[0].axhline(y=1.0, color='r', linestyle='--', label='Ideal Uniform')
    axes[0].set_xticks([0.0, 0.25, 0.5, 0.75, 1.0])
    axes[0].legend()
    
    # Plot V fractional
    axes[1].hist(v_frac.flatten(), bins=20, range=(0.0, 1.0), color='green', alpha=0.7, edgecolor='black', density=True)
    axes[1].set_title(f'Distribusi Fraksional V\nPeak-Locking Bias (RMS): {v_bias:.3f}')
    axes[1].set_xlabel('Fractional Part of V (px)')
    axes[1].set_ylabel('Density')
    axes[1].axhline(y=1.0, color='r', linestyle='--', label='Ideal Uniform')
    axes[1].set_xticks([0.0, 0.25, 0.5, 0.75, 1.0])
    axes[1].legend()
    
    plt.tight_layout()
    plt.savefig(output_filename, dpi=150)
    print(f"[*] Histogram berhasil disimpan sebagai: {output_filename}")
    plt.close()

def main():
    print("=== Pilar 2: Uji Artefak Peak-Locking ===")
    
    # Menggunakan salah satu data sintetik (misal: zone_01/shear atau vortex)
    dataset_dir = r"C:\TERR\4. WORK\7.1 PIV study pakai Synth data\synthetic_dataset"
    zone = "zone_01"
    scenario = "shear" # Kita gunakan shear karena memiliki rentang gradien linier
    
    zone_dir = os.path.join(dataset_dir, zone)
    frame_a_path = os.path.join(zone_dir, "frame_A.tif")
    frame_b_path = os.path.join(zone_dir, scenario, "frame_B.tif")
    
    if not os.path.exists(frame_a_path) or not os.path.exists(frame_b_path):
        print(f"Error: Gambar untuk pengujian tidak ditemukan di {zone_dir}\\{scenario}")
        return
        
    print(f"[*] Memproses gambar: {zone} - {scenario}")
    
    device, desc, _ = detect_hardware('auto')
    print(f"[*] Engine berjalan dengan: {desc}")
    
    img_a = io.imread(frame_a_path).astype(np.float32)
    img_b = io.imread(frame_b_path).astype(np.float32)
    
    tensor_a = torch.from_numpy(img_a).to(device)
    tensor_b = torch.from_numpy(img_b).to(device)
    
    print("[*] Menjalankan PIV...")
    u, v, x, y, snr = run_3pass_piv_gpu(tensor_a, tensor_b, device)
    
    # Optional: validasi dan smoothing
    us, vs, velmag, shear, out = validate_and_smooth_gpu(u, v, snr, x, y, device)
    
    # Mengambil nilai array perpindahan
    u_np = us.cpu().numpy()
    v_np = vs.cpu().numpy()
    
    # Ekstrak nilai fraksional
    print("[*] Mengekstrak bagian desimal (fraksional)...")
    u_frac = u_np - np.floor(u_np)
    v_frac = v_np - np.floor(v_np)
    
    # Hitung metrik Peak-Locking Bias
    u_bias = calculate_peak_locking_bias(u_frac, num_bins=20)
    v_bias = calculate_peak_locking_bias(v_frac, num_bins=20)
    
    print(f" -> Peak-Locking Bias U: {u_bias:.4f}")
    print(f" -> Peak-Locking Bias V: {v_bias:.4f}")
    
    if u_bias > 0.5 or v_bias > 0.5:
        print("[!] Peringatan: Bias Peak-Locking cukup tinggi. Mungkin ada penumpukan pada nilai integer/half-integer.")
    else:
        print("[*] Distribusi fraksional cukup seragam. Peak-Locking terkendali.")
    
    # Buat Histogram
    output_filename = "peak_locking_histogram.png"
    plot_peak_locking_histogram(u_frac, v_frac, u_bias, v_bias, output_filename=output_filename)

if __name__ == '__main__':
    main()
