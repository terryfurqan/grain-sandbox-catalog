import numpy as np
import argparse
import sys
import os

def check_physical_constraints(u, v, dx=1.0, dy=1.0):
    """
    Menghitung batas fisik dan inkompresibilitas dari medan vektor PIV (u, v).
    """
    print("=== Pilar 3: Verifikasi Batas Fisik ===")
    
    # 1. & 2. Ekstrak area Left Boundary (kolom paling kiri pada array u)
    # Asumsi: array u berbentuk (y, x), sehingga u[:, 0] adalah kolom kiri.
    left_boundary_u = u[:, 0]
    
    # 3. Hitung rata-rata kecepatan piksel di kolom kiri
    avg_left_u = np.nanmean(left_boundary_u)
    
    theoretical_v = 3.197 # px/frame
    
    error_abs = abs(avg_left_u - theoretical_v)
    error_rel = (error_abs / theoretical_v) * 100
    
    print(f"Kecepatan Dinding Pendorong (Teoretis): {theoretical_v:.4f} px/frame")
    print(f"Rata-rata kecepatan pada batas kiri (u)  : {avg_left_u:.4f} px/frame")
    print(f"Selisih Error                            : {error_abs:.4f} px/frame ({error_rel:.2f}%)")
    
    if error_rel < 5.0:
        print("-> STATUS: MEMENUHI (Error < 5%)")
    else:
        print("-> STATUS: TIDAK MEMENUHI (Error >= 5%)")
        
    print("\n=== Uji Hukum Inkompresibilitas (Divergensi) ===")
    # 4. Divergensi V = du/dx + dv/dy
    # Menggunakan np.gradient untuk turunan numerik
    # gradient mengembalikan (turunan thd axis 0 (y), turunan thd axis 1 (x))
    du_dy, du_dx = np.gradient(u, dy, dx)
    dv_dy, dv_dx = np.gradient(v, dy, dx)
    
    divergence = du_dx + dv_dy
    
    avg_div = np.nanmean(divergence)
    std_div = np.nanstd(divergence)
    max_div = np.nanmax(np.abs(divergence))
    
    print(f"Rata-rata Divergensi : {avg_div:.6f}")
    print(f"Std Dev Divergensi   : {std_div:.6f}")
    print(f"Max Abs Divergensi   : {max_div:.6f}")
    
    # Untuk material granular dense, divergensi mendekati 0 kecuali di zona dilatasi (sesar).
    # Jika rata-rata mendekati 0, maka secara umum memenuhi inkompresibilitas (volume konstan).
    if abs(avg_div) < 0.1:
        print("-> STATUS: MEMENUHI Inkompresibilitas (Rata-rata Divergensi mendekati 0)")
    else:
        print("-> STATUS: DILATASI/KOMPAKSI SIGNIFIKAN (Cek keberadaan sesar atau error)")
        
    return error_rel, avg_div


def main():
    parser = argparse.ArgumentParser(description="Verifikasi Batas Fisik dan Inkompresibilitas pada Data PIV.")
    parser.add_argument('--npz', type=str, help='Path ke file .npz hasil PIV (harus mengandung array "u" dan "v")', default=None)
    args = parser.parse_args()
    
    if args.npz and os.path.exists(args.npz):
        print(f"Memuat data dari: {args.npz}")
        data = np.load(args.npz)
        if 'u' in data and 'v' in data:
            u = data['u']
            v = data['v']
        elif 'u_vel' in data and 'v_vel' in data:
            u = data['u_vel']
            v = data['v_vel']
        else:
            print("Kunci 'u' dan 'v' tidak ditemukan dalam file .npz.")
            sys.exit(1)
    else:
        print("Data .npz tidak diberikan atau tidak ditemukan. Menggunakan MOCK DATA.")
        # Membuat array mock dengan noise
        # Shape misal 100 y, 150 x
        shape = (100, 150)
        # Bikin u yang di sebelah kiri mendekati 3.197, lalu meluruh ke kanan
        x = np.linspace(0, 10, shape[1])
        u = np.zeros(shape)
        u[:] = 3.197 * np.exp(-x / 5.0)  # meluruh
        
        # Tambahkan noise gaussian (simulasi error sub-pixel)
        u += np.random.normal(0, 0.05, shape)
        
        # v mendekati 0 dengan sedikit noise
        v = np.random.normal(0, 0.05, shape)
        
    check_physical_constraints(u, v)

if __name__ == '__main__':
    main()
