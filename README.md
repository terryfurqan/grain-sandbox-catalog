---
title: GRAIN Sandbox Experiment Data Server & Central Catalog
emoji: 🏜️
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# 🏔️ GRAIN Sandbox Experiment Data Server & Central Catalog

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Hugging Face Spaces](https://img.shields.io/badge/🤗%20Hugging%20Face-Spaces-yellow.svg)](https://huggingface.co/spaces)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?style=flat&logo=Python&logoColor=white)](https://www.python.org)
[![Google Drive API](https://img.shields.io/badge/Google%20Drive%20API-v3-4285F4.svg?style=flat&logo=googledrive&logoColor=white)](https://developers.google.com/drive)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> Server Katalog Data & Pengindeks Eksperimen Pemodelan Analog Geologi & Tektonik (*Sandbox Modeling*) dalam ekosistem **GRAIN 2.0**.

---

## 🏛️ Topologi Infrastruktur GRAIN Explorer

- **`D:\999_GRAIN_EXPLORER\0000`**: Pusat Backend Manifest Sentral (`catalog.db`, `manifest.json`, `taxonomy_rules.json`, `audit_report.json`).
- **`D:\999_GRAIN_EXPLORER\0010`**: Vault Eksperimen Terproses (`[yymmdd-hhmmss] - [nama exp]`).
- **`c:\TERR\4. WORK\7. CATALOGUING`**: Engine pemrosesan, indexer, sinkronisasi, dan aturan taksonomi 5 Pilar.

---

## 🚀 Cara Menjalankan Sinkronisasi Katalog

Cukup klik dua kali:
```cmd
run_catalog_sync.bat
```
Atau via terminal:
```bash
python grain_catalog_indexer.py --storage-dir "D:\999_GRAIN_EXPLORER\0010" --manifest-dir "D:\999_GRAIN_EXPLORER\0000"
```

---

## 📄 License
Released under the MIT License for academic and research workflows within the GRAIN 2.0 ecosystem.

