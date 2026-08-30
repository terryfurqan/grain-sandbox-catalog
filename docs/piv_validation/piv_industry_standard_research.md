# Standar Industri & Validasi Hasil PIV (Particle Image Velocimetry)

Laporan riset ini merangkum standar industri, metode validasi, dan praktik terbaik (best practices) untuk algoritma *Particle Image Velocimetry* (PIV), dengan perbandingan khusus antara PIV fluida tradisional dan penerapannya pada pemodelan analog (sandbox).

## 1. Validasi Angka dan Representasi Dunia Nyata (Real World)

Tidak ada satu standar ISO spesifik yang mengatur PIV secara keseluruhan. Alih-alih, industri dan akademisi bergantung pada panduan teknis komunitas (seperti ERCOFTAC) dan standar komite maritim seperti **ITTC (International Towing Tank Conference)**, misalnya *Guideline 7.5-01-03-03 (Uncertainty Analysis for PIV)*.

Untuk membuktikan bahwa nilai vektor kecepatan ($u, v$), magnitudo, dan *shear strain* merepresentasikan dunia nyata, standar saat ini bergerak dari "estimasi error global" menjadi **Uncertainty Quantification (UQ) a-posteriori**:

*   **Correlation-Based UQ:** Software standar industri mengkuantifikasi ketidakpastian secara lokal (per vektor) berdasarkan bentuk puncak korelasi (*correlation peak*). Metode utama meliputi *Primary Peak Ratio (PPR)* dan *Moment of Correlation (MC)*. Jika puncak korelasi tajam dan rasio sinyal-ke-derau (SNR) tinggi, data dianggap representatif.
*   **Benchmarking Sintetis:** Algoritma divalidasi dengan memproses gambar sintetis (*synthetic images*) yang *ground truth* deformasinya dihasilkan secara matematis (seperti pada *International PIV Challenge*). Kesalahan diukur dari nilai Root Mean Square Error (RMSE) antara hasil PIV dengan *ground truth*.
*   **Validasi Fisik:** Penggunaan objek padat yang digerakkan dengan presisi presisi tinggi (misal *micrometer translation stage*) untuk memastikan bahwa algoritma menghitung perpindahan dalam satuan piksel dan metrik dengan tepat.

## 2. PIV Fluida Tradisional vs PIV Pemodelan Analog (Sandbox)

Meskipun fondasi matematis *Cross-Correlation* pada keduanya sama, terdapat perbedaan (*discrepancy*) yang mendasar antara PIV Fluida dan aplikasinya di pemodelan analog (sering disebut *Geo-PIV* atau *Digital Image Correlation* / DIC):

| Fitur | PIV Fluida Tradisional | PIV Pemodelan Analog (Granular/Sandbox) |
| :--- | :--- | :--- |
| **Material & Iluminasi** | Fluida transparan dengan partikel *tracer* (seeding) sintetik. Diiluminasi menggunakan lembaran sinar laser (*laser sheet*) dalam gelap. | Butiran material alami (pasir, *glass beads*). Difoto dengan cahaya tampak konvensional tanpa *tracer* tambahan. |
| **Karakter Pelacakan** | Mengevaluasi pergerakan dinamis partikel (*Eulerian*). Partikel bisa keluar/masuk dari bidang laser (*out-of-plane motion*). | Melacak tekstur alami/pola *speckle* butiran di permukaan (*Lagrangian*). Lebih stabil, tetapi butiran yang "menggelinding" (*grain rolling*) atau longsor dapat merusak korelasi. |
| **Fokus Output** | Dominan mengukur medan vektor kecepatan sesaat (*velocity field*). | Dominan mengukur akumulasi pergeseran (displacement) dan **Shear Strain** untuk melacak patahan dan bidang geser. |
| **Algoritma Terapan** | Korelasi silang standar antar *frame* secara incremental. | Sering digabung dengan algoritma DIC (*shape functions*) untuk meminimalisasi akumulasi *error drift* dalam kuasi-statis, serta mengkalkulasi regangan secara langsung. |

## 3. Strategi Ukuran Interrogation Window (IW) & Resolusi Data

Dalam PIV, ukuran *Interrogation Window* (IW) bertindak sebagai *spatial low-pass filter*. Menggunakan ukuran IW tunggal untuk seluruh domain gambar **tidak direkomendasikan** karena meratakan detail penting di area regangan tinggi (patahan aktif).

**Aturan Baku (Rule of Thumb):**
*   **Kepadatan Pola:** Sebuah jendela IW idealnya memuat minimal **5–15 pola partikel/butiran** untuk menjamin puncak korelasi yang valid.
*   **Aturan Seperempat (1/4 Rule):** Jarak perpindahan butiran pasir maksimum antar *frame* tidak boleh melebihi seperempat (25%) dari dimensi lintang IW, agar pasangan piksel tetap berada dalam window yang sama.

**Mencapai "Maximum Achievable Data Resolution":**
Strategi standar industri untuk mendapatkan resolusi maksimal (IW terkecil yang tetap reliabel) didasarkan pada teknik **Multi-Pass / Multi-Grid dengan Continuous Window Shifting (CWS)**:
1.  **Pass Awal (IW Besar):** Memulai kalkulasi dengan jendela besar (misal $64 \times 64$ atau $128 \times 128$ piksel). IW besar memberi rasio keandalan statistik tinggi untuk menangkap vektor kasaran tanpa kehilangan partikel.
2.  **Pass Lanjut (IW Mengecil):** Memanfaatkan medan referensi kasar tadi, vektor diinterpolasi untuk mendistorsi bidang evaluasi (Window Deformation). Kalkulasi dilakukan lagi di grid yang lebih kecil (misal $32 \times 32$ lalu berlanjut ke $16 \times 16$). Hal ini mereduksi pergerakan relatif dalam window menjadi hampir nol, memungkinkan resolusi lokal tajam terbentuk.
3.  **Overlap (Tumpang Tindih):** Menggunakan *overlap* berdekatan setinggi 50% hingga 75% untuk meningkatkan kepadatan titik grid vektor (spatial resolution) tanpa memicu derau *spurious* berlebih.

## 4. Dampak Distorsi Lensa dan Mitigasinya

Distorsi lensa kamera (seperti varian *barrel* pada lensa sudut lebar) menjadi problem fatal saat berurusan dengan pengukuran regangan geologis.

**Dampak pada Akurasi:**
Distorsi merusak hubungan linear nyata. Efek pembesaran (*magnification factor*) akan lebih besar di tengah sensor dan mengecil menuju pinggir tepi lensa. Pergeseran mekanis 1 mm mungkin dibaca sebagai perpindahan 10 piksel di sentral, tapi 8 piksel di sudut foto. Konsekuensinya, algoritma PIV akan mendeteksi sebuah gradien perpindahan yang direpresentasikan menjadi **Spurious Strain** (medan regangan palsu). Ini dapat menyesatkan analisis struktur sesar geologi.

**Strategi Mitigasi Industri:**
1.  **Kalibrasi Kamera (Target-Based Calibration):**
    Menggunakan sebuah target *dot grid* atau *checkerboard* presisi tinggi yang ditempatkan *in-situ* pada elevasi permukaan kotak pasir. Model geometris (terutama formulasi *Brown-Conrady*) dikalkulasi untuk menemukan pusat optik dan koefisien distorsi radial-tangensial kamera.
2.  **Image Dewarping (Orthorectification):**
    Sebelum algoritma *Cross-Correlation* dijalankan, tahap pra-pemrosesan diwajibkan untuk seluruh rangkaian gambar *timelapse*. Gambar "diluruskan" (*dewarped* atau *undistorted*), di-remap balik ke dalam ruang piksel kartesian sejati.
3.  **Alternative Post-Vector Correction:** 
    Pada kasus tertinggal, PIV dikerjakan di atas piksel terdistorsi, lalu koefisien fungsi kalibrasi diterapkan untuk mendistorsi balik titik grid pada *velocity field* hasil akhirnya. (Namun, pendekatan nomor 2 jauh lebih dominan di industri solid DIC/Geo-PIV).
