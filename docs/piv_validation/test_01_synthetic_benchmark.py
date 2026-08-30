import os
import sys
import numpy as np
from skimage import io
import torch

# Append skill path to import the GPU PIV engine
sys.path.insert(0, r"C:\Users\Sandbox_Main\.gemini\config\skills\grain-piv\scripts")
from grain_piv_v2 import detect_hardware, run_3pass_piv_gpu, validate_and_smooth_gpu

def calculate_metrics(pred_u, pred_v, gt_u, gt_v):
    """Kalkulasi RMSE dan MAE."""
    err_u = pred_u - gt_u
    err_v = pred_v - gt_v
    
    mae_u = np.mean(np.abs(err_u))
    mae_v = np.mean(np.abs(err_v))
    
    rmse_u = np.sqrt(np.mean(err_u**2))
    rmse_v = np.sqrt(np.mean(err_v**2))
    
    mae_mag = np.mean(np.sqrt(err_u**2 + err_v**2))
    
    return mae_u, mae_v, rmse_u, rmse_v, mae_mag

def main():
    print("=== GRAIN 2.0 PIV Falsification Suite ===")
    
    dataset_dir = r"C:\TERR\4. WORK\7.1 PIV study pakai Synth data\synthetic_dataset"
    if not os.path.exists(dataset_dir):
        print(f"Dataset tidak ditemukan di: {dataset_dir}")
        return
        
    device, desc, _ = detect_hardware('auto')
    print(f"[*] Engine berjalan dengan: {desc}")
    
    zones = sorted([d for d in os.listdir(dataset_dir) if d.startswith('zone_')])
    scenarios = ['rigid', 'shear', 'vortex']
    
    print("\n--- Mulai Uji Benchmark ---")
    
    # Header tabel
    print(f"{'Zona':<10} | {'Skenario':<10} | {'MAE u (px)':<12} | {'MAE v (px)':<12} | {'RMSE u':<10} | {'RMSE v':<10} | {'MAE Mag':<10}")
    print("-" * 85)
    
    results = {}
    
    for zone in zones:
        zone_dir = os.path.join(dataset_dir, zone)
        frame_a_path = os.path.join(zone_dir, "frame_A.tif")
        
        if not os.path.exists(frame_a_path):
            continue
            
        img_a = io.imread(frame_a_path).astype(np.float32)
        tensor_a = torch.from_numpy(img_a).to(device)
        
        for sc in scenarios:
            sc_dir = os.path.join(zone_dir, sc)
            frame_b_path = os.path.join(sc_dir, "frame_B.tif")
            gt_path = os.path.join(sc_dir, "ground_truth.npz")
            
            if not os.path.exists(frame_b_path) or not os.path.exists(gt_path):
                continue
                
            img_b = io.imread(frame_b_path).astype(np.float32)
            tensor_b = torch.from_numpy(img_b).to(device)
            
            # Load Ground Truth
            gt_data = np.load(gt_path)
            u_gt_dense = gt_data['u']
            v_gt_dense = gt_data['v']
            
            # Run PIV
            u, v, x, y, snr = run_3pass_piv_gpu(tensor_a, tensor_b, device)
            us, vs, velmag, shear, out = validate_and_smooth_gpu(u, v, snr, x, y, device)
            
            # Convert to CPU numpy
            us_np = us.cpu().numpy()
            vs_np = vs.cpu().numpy()
            x_np = x if isinstance(x, np.ndarray) else x.cpu().numpy()
            y_np = y if isinstance(y, np.ndarray) else y.cpu().numpy()
            
            # Evaluasi dense ground truth di grid points
            # Koordinat grid x dan y adalah float, kita bulatkan untuk indeks integer array 
            # atau pakai grid data. Karena x, y berkorespondensi ke dense indeks:
            x_idx = np.clip(np.round(x_np).astype(int), 0, u_gt_dense.shape[1]-1)
            y_idx = np.clip(np.round(y_np).astype(int), 0, u_gt_dense.shape[0]-1)
            
            u_gt_grid = u_gt_dense[y_idx, x_idx]
            v_gt_grid = v_gt_dense[y_idx, x_idx]
            
            # Mask out the edge artifacts (optional)
            mae_u, mae_v, rmse_u, rmse_v, mae_mag = calculate_metrics(us_np, vs_np, u_gt_grid, v_gt_grid)
            
            key = f"{zone}_{sc}"
            results[key] = {
                'mae_u': mae_u, 'mae_v': mae_v, 
                'rmse_u': rmse_u, 'rmse_v': rmse_v, 'mae_mag': mae_mag
            }
            
            print(f"{zone:<10} | {sc:<10} | {mae_u:<12.4f} | {mae_v:<12.4f} | {rmse_u:<10.4f} | {rmse_v:<10.4f} | {mae_mag:<10.4f}")

    print("-" * 85)
    print("\n[*] Benchmark Selesai.")

if __name__ == '__main__':
    main()
