# 🧭 GRAIN Explorer - Cataloguing Engine & Workspace

Workspace pengembangan sistem katalogisasi sentral dan validasi taksonomi baku (*Flat Direct Taxonomy*) untuk pemodelan analog tektonik geologi (Sandbox Modeling) di bawah ekosistem **GRAIN 2.0**.

---

## 🏛️ Topologi Infrastruktur

- **`D:\999_GRAIN_EXPLORER\0000`**: Pusat Backend Manifest Sentral (`catalog.db`, `manifest.json`, `taxonomy_rules.json`, `audit_report.json`).
- **`D:\999_GRAIN_EXPLORER\0010`**: Vault Eksperimen Terproses (1 folder = 1 eksperimen mandiri).
- **`c:\TERR\4. WORK\7. CATALOGUING`**: Engine pemrosesan, indexer, sinkronisasi, dan aturan taksonomi.

---

## 📋 Berkas Utama Workspace

1. **[`TAXONOMY_RULES.md`](TAXONOMY_RULES.md)**: Aturan baku kode prefiks `0.x` s.d. `5.x`, struktur `OUTPUT/`, dan format penamaan `[PROJECT] - [DDMMYY] (EXP [N])`.
2. **[`CONTEXT.md`](CONTEXT.md)**: Dokumentasi arsitektur sistem dan alur kerja sinkronisasi.
3. **[`grain_catalog_indexer.py`](grain_catalog_indexer.py)**: Skrip Python indexer berkinerja tinggi untuk memindai `0010` dan memperbarui basis data `0000`.
4. **[`run_catalog_sync.bat`](run_catalog_sync.bat)**: Script batch 1-klik untuk eksekusi sinkronisasi secara instan.

---

## 🚀 Cara Menjalankan Sinkronisasi

Cukup klik dua kali:
```cmd
run_catalog_sync.bat
```
Atau via terminal:
```bash
python grain_catalog_indexer.py --storage-dir "D:\999_GRAIN_EXPLORER\0010" --manifest-dir "D:\999_GRAIN_EXPLORER\0000"
```

---

## 🌐 Sinkronisasi Repositori GitHub
- **Remote Repo**: `https://github.com/terryfurqan/grain-sandbox-catalog.git`
