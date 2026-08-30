import os
import numpy as np
from scipy.ndimage import map_coordinates
from skimage import io, color

class SyntheticGenerator:
    """
    Kelas untuk menghasilkan data sintetis PIV berdasarkan gambar riil eksperimen.
    
    Tujuan modul ini adalah menguji hipotesis: 
    "Apakah satu ukuran Interrogation Window (IW) cukup akurat untuk seluruh fase 
    eksperimen (awal yang datar vs akhir yang bergunung/terdeformasi tinggi)?"
    """
    
    def __init__(self, base_image_dir, output_dir=None):
        """
        Inisialisasi generator.
        
        Args:
            base_image_dir (str): Path ke folder gambar eksperimen asli.
            output_dir (str, optional): Path untuk menyimpan output sintetis.
        """
        self.base_image_dir = base_image_dir
        self.output_dir = output_dir
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
    def get_representative_frames(self, num_zones=10, skip_initial=10):
        """
        Membaca isi direktori gambar dan membagi rentang waktu menjadi beberapa zona.
        Mengambil 1 frame representatif dari tiap zona spasial/temporal.
        
        Args:
            num_zones (int): Jumlah zona/fase waktu yang akan dibagi.
            skip_initial (int): Jumlah frame awal yang diabaikan (karena sering belum ada deformasi signifikan).
            
        Returns:
            list: Daftar path lengkap dari frame yang terpilih untuk tiap zona.
        """
        valid_exts = ('.png', '.jpg', '.jpeg', '.tif', '.tiff')
        all_files = sorted([f for f in os.listdir(self.base_image_dir) if f.lower().endswith(valid_exts)])
        
        if len(all_files) <= skip_initial:
            raise ValueError(f"Total frame ({len(all_files)}) lebih sedikit atau sama dengan frame awal yang dilewati ({skip_initial}).")
            
        valid_files = all_files[skip_initial:]
        total_valid = len(valid_files)
        
        frames_per_zone = total_valid / num_zones
        selected_frames = []
        
        for i in range(num_zones):
            # Ambil frame di tengah-tengah zona tersebut (representatif)
            idx = int((i + 0.5) * frames_per_zone)
            if idx >= total_valid:
                idx = total_valid - 1
            selected_frames.append(os.path.join(self.base_image_dir, valid_files[idx]))
            
        return selected_frames

    def _apply_displacement(self, image, u, v):
        """
        Fungsi internal untuk menerapkan perpindahan matriks u dan v 
        pada citra menggunakan subpixel bicubic interpolation.
        
        Args:
            image (ndarray): Matriks gambar dasar (grayscale 2D).
            u (ndarray): Matriks perpindahan komponen X.
            v (ndarray): Matriks perpindahan komponen Y.
            
        Returns:
            ndarray: Gambar hasil transformasi (Frame B).
        """
        h, w = image.shape
        y, x = np.mgrid[0:h, 0:w]
        
        # Mencari koordinat asli sebelum bergeser
        # Karena kita melakukan backward mapping (mengambil nilai pixel asli untuk posisi baru)
        new_x = x - u
        new_y = y - v
        
        # map_coordinates dengan order=3 (bicubic), mode 'reflect' untuk boundary
        warped_image = map_coordinates(image, [new_y, new_x], order=3, mode='reflect')
        return warped_image
        
    def apply_rigid_translation(self, image, u_shift, v_shift):
        """
        Kasus 1: Rigid Translation
        Semua pixel bergeser dengan vektor konstan yang sama (misal u=1.0, v=0.5).
        
        Args:
            image (ndarray): Frame A
            u_shift (float): Nilai geseran sumbu X (px)
            v_shift (float): Nilai geseran sumbu Y (px)
        """
        h, w = image.shape
        u = np.full((h, w), u_shift, dtype=np.float32)
        v = np.full((h, w), v_shift, dtype=np.float32)
        
        warped = self._apply_displacement(image, u, v)
        return warped, u, v
        
    def apply_shear_fault_band(self, image, max_u, band_center_y, band_width):
        """
        Kasus 2: Sesar Geser (Fault Band)
        Membuat gradien pergeseran linier diskrit di area tertentu untuk simulasi zona sesar.
        
        Args:
            image (ndarray): Frame A
            max_u (float): Perpindahan X maksimum di blok atas.
            band_center_y (float): Posisi Y tengah sesar (px).
            band_width (float): Lebar zona transisi/deformasi (px).
        """
        h, w = image.shape
        u = np.zeros((h, w), dtype=np.float32)
        v = np.zeros((h, w), dtype=np.float32)
        
        y, x = np.mgrid[0:h, 0:w]
        
        top_edge = band_center_y - band_width / 2.0
        bottom_edge = band_center_y + band_width / 2.0
        
        # Blok di atas sesar bergeser maksimal
        u[y <= top_edge] = max_u
        # Blok di bawah sesar diam (0)
        u[y >= bottom_edge] = 0.0
        
        # Di zona sesar, buat gradien linier
        mask_band = (y > top_edge) & (y < bottom_edge)
        u[mask_band] = max_u * (bottom_edge - y[mask_band]) / band_width
        
        warped = self._apply_displacement(image, u, v)
        return warped, u, v
        
    def apply_vortex(self, image, center_x, center_y, core_radius, max_velocity):
        """
        Kasus 3: Vortex / Rotasi
        Membuat pusaran dengan inti berotasi solid (solid body rotation) dan bagian luar 
        memudar terbalik terhadap radius (potential vortex).
        Menguji kepekaan IW terhadap gradien kecepatan tinggi (spatial gradient).
        
        Args:
            image (ndarray): Frame A
            center_x, center_y (float): Koordinat pusat vortex.
            core_radius (float): Radius inti pusaran.
            max_velocity (float): Kecepatan tangential maksimum di pinggir inti.
        """
        h, w = image.shape
        u = np.zeros((h, w), dtype=np.float32)
        v = np.zeros((h, w), dtype=np.float32)
        
        y, x = np.mgrid[0:h, 0:w]
        
        dx = x - center_x
        dy = y - center_y
        r = np.sqrt(dx**2 + dy**2)
        
        omega_core = max_velocity / core_radius
        
        # Zona 1: Dalam inti pusaran (v = w * r)
        mask_in = r <= core_radius
        r_in = r[mask_in]
        r_in[r_in == 0] = 1e-6 # cegah pembagian nol pada pusat
        v_theta_in = omega_core * r_in
        u[mask_in] = -v_theta_in * (dy[mask_in] / r_in)
        v[mask_in] =  v_theta_in * (dx[mask_in] / r_in)
        
        # Zona 2: Luar pusaran (v ~ 1/r)
        mask_out = r > core_radius
        r_out = r[mask_out]
        v_theta_out = (omega_core * core_radius**2) / r_out
        u[mask_out] = -v_theta_out * (dy[mask_out] / r_out)
        v[mask_out] =  v_theta_out * (dx[mask_out] / r_out)
        
        warped = self._apply_displacement(image, u, v)
        return warped, u, v

    def process_zone(self, image_path, zone_name):
        """
        Memproses 1 frame (sebagai base texture), melakukan konversi grayscale, 
        lalu menerapkan 3 jenis deformasi. Menyimpan matriks Frame A, Frame B, u_gt, dan v_gt.
        """
        img_color = io.imread(image_path)
        
        # Pastikan format citra 2D (grayscale)
        if len(img_color.shape) == 3:
            img = color.rgb2gray(img_color)
        else:
            img = img_color.astype(np.float64) / 255.0
            
        # Normalisasi ke 0-1
        if img.max() > 1.5:
            img = img / 255.0
            
        results = {'original': img}
        h, w = img.shape
        
        # Kasus 1: Rigid Translation (bergeser secara homogen)
        w_rigid, u_rigid, v_rigid = self.apply_rigid_translation(img, u_shift=1.0, v_shift=0.5)
        results['rigid'] = (w_rigid, u_rigid, v_rigid)
        
        # Kasus 2: Shear / Fault Band (gradien sesar diskrit)
        w_shear, u_shear, v_shear = self.apply_shear_fault_band(
            img, max_u=5.0, band_center_y=h/2.0, band_width=h/10.0
        )
        results['shear'] = (w_shear, u_shear, v_shear)
        
        # Kasus 3: Vortex Rotational (gradien spasial pusaran)
        w_vortex, u_vortex, v_vortex = self.apply_vortex(
            img, center_x=w/2.0, center_y=h/2.0, core_radius=h/4.0, max_velocity=4.0
        )
        results['vortex'] = (w_vortex, u_vortex, v_vortex)
        
        # Menyimpan matriks (IO operations) jika output_dir dispesifikasikan
        if self.output_dir:
            zone_dir = os.path.join(self.output_dir, zone_name)
            os.makedirs(zone_dir, exist_ok=True)
            
            # Simpan Frame A (t=0)
            io.imsave(os.path.join(zone_dir, "frame_A.tif"), (img * 255).astype(np.uint8), check_contrast=False)
            
            # Simpan setiap skenario deformasi (t=1) + Ground Truth (u, v)
            tests = ['rigid', 'shear', 'vortex']
            for t_name in tests:
                w_img, u_gt, v_gt = results[t_name]
                t_dir = os.path.join(zone_dir, t_name)
                os.makedirs(t_dir, exist_ok=True)
                
                io.imsave(os.path.join(t_dir, "frame_B.tif"), (w_img * 255).astype(np.uint8), check_contrast=False)
                np.savez_compressed(os.path.join(t_dir, "ground_truth.npz"), u=u_gt, v=v_gt)
                
        return results

    def run_full_suite(self, num_zones=10, skip_initial=10):
        """
        Mengeksekusi pipeline seluruh zona. Memilih frame dari tiap fase waktu
        eksperimen dan mengekspor pasangan Falsification Suite-nya.
        """
        frames = self.get_representative_frames(num_zones=num_zones, skip_initial=skip_initial)
        
        print(f"[*] Menemukan {len(frames)} zona temporal di base directory.")
        for i, frame_path in enumerate(frames):
            zone_name = f"zone_{i+1:02d}"
            print(f"  -> Generating '{zone_name}' dengan base texture: {os.path.basename(frame_path)}")
            self.process_zone(frame_path, zone_name)
            
        print("[*] Sintesis deformasi sukses. Data siap digunakan untuk uji hipotesis Interrogation Window.")

if __name__ == "__main__":
    # Contoh eksekusi (Opsional, hanya jika script di run secara langsung)
    case_study_dir = r"C:\CROP_ 4cm _ 0 deg _ thrust fault_ada gunung - 0"
    output_target = os.path.join(os.path.dirname(__file__), "output_synthetic_suite")
    
    # Inisialisasi generator
    generator = SyntheticGenerator(base_image_dir=case_study_dir, output_dir=output_target)
    
    # Men-generate dataset (di-comment secara default)
    # generator.run_full_suite(num_zones=10, skip_initial=10)
