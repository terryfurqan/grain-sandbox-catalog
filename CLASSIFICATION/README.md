# 🧭 GRAIN 2.0 Sandbox Experiment Classification & Metadata Standards

Panduan standar klasifikasi dan pengisian metadata untuk eksperimen pemodelan analog tektonik (*Sand-Box Analog Modeling*) dalam ekosistem **GRAIN 2.0**. Standar ini dirancang untuk memudahkan pencarian cepat (*fast filtering*), penelusuran asal-usul/maksud eksperimen (*intent traceability*), komparasi struktural, dan integrasi otomatis ke catalog.db serta manifest.json.

---

## 🏛️ Arsitektur 5 Pilar Klasifikasi

Setiap eksperimen sandbox diklasifikasikan ke dalam 5 pilar terpadu:

`mermaid
graph TD
    EXP[Eksperimen Sandbox] --> P1[Pilar 1: Intent & Target Geologi]
    EXP --> P2[Pilar 2: Kinematika & Mesin]
    EXP --> P3[Pilar 3: Material & Stratigrafi]
    EXP --> P4[Pilar 4: Akuisisi Citra & PIV]
    EXP --> P5[Pilar 5: Luaran Analisis & Deliverables]
`

---

## 📋 Daftar Field Metadata yang Harus Diisi

### 🔹 Pilar 1: Intent & Target Geologi
| Field Key | Tipe | Wajib? | Nilai / Opsi Pilihan | Keterangan |
| :--- | :--- | :--- | :--- | :--- |
| intent | string | **YA** | Research • Project | Maksud pelaksanaan eksperimen. |
| project_name | string | **Kondisional** *(Wajib jika intent = Project)* | Teks bebas (Contoh: KUFPEC Kutai Study 2026, BP Berau Deepwater Inversion) | Nama kontrak/klien/studi industri spesifik. |
| esearch_topic | string | Opsional *(Intent = Research)* | Teks bebas (Contoh: Fundamental Salt Diapirism R&D) | Topik atau judul hibah riset akademis. |
| project_basin | string | **YA** *(Auto/Manual)* | Contoh: TALAWANG, MAHAKAM, KUTAI, BARITO | Nama formasi / cekungan geologi target. |
| 	arget_structural_style | string | **YA** | • Fold-and-Thrust Belt (FTB / Thrust Wedge)<br>• Rift Graben / Half-Graben (Normal Faults)<br>• Pull-Apart Basin (Transtensional)<br>• Transpressional Pop-Up / Positive Flower<br>• Inversion Anticline (Positive/Negative Inversion)<br>• Salt/Ductile Tectonics (Diapir / Pillow / Canopy)<br>• Delta Gravity-Driven / Toe-Thrust<br>• Basement-Involved Fault-Propagation<br>• Other / Unspecified | Gaya struktur utama yang disimulasikan. |

---

### 🔹 Pilar 2: Kinematika & Mesin Penggerak
| Field Key | Tipe | Wajib? | Nilai / Opsi Pilihan | Keterangan |
| :--- | :--- | :--- | :--- | :--- |
| 	ectonic_system | string | **YA** | Extensional • Contractional • Strike Slip • Hybrid | Regime tektonik dominan. |
| machine_apparatus | string | **YA** | • IAGI - Dorong<br>• IAGI - Tarik<br>• BP - Dorong<br>• BP - Tarik<br>• BP - Dorong-Tarik<br>• KUFPEC squeeze<br>• KUFPEC base plate<br>• KUFPEC mix | Perangkat rig sandbox dan arah tarikan/dorongan. |
| oundary_detachment_mechanism | string | **YA** | • Rigid Mobile Wall (Piston)<br>• Basal Mylar/Sheet (Conveyor Pull)<br>• Rubber Sheet (Elastic Stretching)<br>• Basal Fault Ramp/Step<br>• Dual Mobile Wall (Symmetric/Asymmetric) | Mekanisme batas kontak dan detachment dasar model. |
| asal_detachment_dip_deg | number | **YA** | Rentang angka -30 s.d. +30 (derajat) | Sudut kemiringan alas (-30° down-dip s.d. +30° up-dip). |
| deformation_stages | string | **YA** | • Single Phase<br>• Multi-Phase Inversion (Ext -> Comp)<br>• Multi-Phase Reactivation (Comp -> Ext)<br>• Transtension/Transpression Sequence | Tahapan deformasi dan reaktivasi multi-fase. |

---

### 🔹 Pilar 3: Material & Stratigrafi Pasir
| Field Key | Tipe | Wajib? | Nilai / Opsi Pilihan | Keterangan |
| :--- | :--- | :--- | :--- | :--- |
| 	otal_sand_thickness_cm | string | **YA** | < 1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, > 10 | Total ketebalan awal pasir/model (cm). |
| materials | array[str] | **YA** *(Multi)* | • Sand (Pasir kuarsa kering)<br>• Gypsum (Plaster rapuh)<br>• Beads (Microbeads / Glass beads)<br>• Silicone/PDMS (Ductile Decollement/Salt Analogue)<br>• Basement Involved (Rigid Pre-cut Block / Fault Step) | Material analog yang digunakan dalam pasir. |
| euse_sand | string | **YA** | Yes • No | Apakah menggunakan pasir ayak daur ulang (Yes) atau pasir baru (No). |
| syn_kinematic_processes | string | **YA** | • None<br>• Incremental Infill (Syn-kinematic Sedimentation)<br>• Continuous Infill<br>• Syn-kinematic Erosion | Sedimentasi/erosi saat motor berjalan. |

---

### 🔹 Pilar 4: Akuisisi Citra & PIV *(Auto-Resolved)*
Field pada pilar ini diekstrak otomatis oleh script [grain_catalog_indexer.py](../grain_catalog_indexer.py):
- **Kamera & Lensa (dari EXIF 1.1 RAW)**: camera_model, lens_model, ocal_length_mm, iso, xposure_time_sec, _number, esolution_raw_px, pixel_scale_mm_per_px.
- **Sudut Pandang Tersedia (dari Taksonomi Folder)**: Map View (1.x), Profile P1 (2.x), Profile P2 (3.x), Slice Map (4a.x), Slice Profile (4b.x), 3D Oblique (5.x).
- **Parameter PIV (dari .npz / .json)**: passes_sequence (contoh 64 -> 32 -> 25 px), inal_iw_size_px, step_overlap_percent, window_shifting, outlier_filter, computed_vector_fields.

---

### 🔹 Pilar 5: Luaran Analisis & Deliverables *(Auto-Detected)*
Daftar produk luaran yang otomatis dideteksi dari isi folder OUTPUT/:
- QPIV Shortening Curve & Pruning Log (OUTPUT/QPIV/)
- .grainraw Binary Container (OUTPUT/GRAINRAW/)
- Single Velmag MP4 Timelapse (OUTPUT/VIDEOS/*velmag*.mp4)
- Dual Split-Screen VMSST MP4 Timelapse (OUTPUT/VIDEOS/*vmsst*.mp4)
- Normalized PIV MP4 Timelapse (OUTPUT/VIDEOS/*normalized*.mp4)
- Serial Slice Comparison Slide (OUTPUT/SLICES/)
- Evolution 5% PowerPoint Report (.pptx) (OUTPUT/REPORTS/*.pptx)

---

## 📁 Berkas Pendukung di Folder Ini

1. **xperiment_classifier_schema.json**: Skema baku JSON Schema Draft 2020-12 untuk validasi integritas field metadata.
2. **METADATA_TEMPLATE.json**: Template kosong siap isi untuk setiap eksperimen baru.
3. **SAMPLE_EXPERIMENT_METADATA.json**: Contoh file metadata lengkap yang telah terisi untuk rujukan.
