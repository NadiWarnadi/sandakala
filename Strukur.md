sandakala-ai/
│
├── domains/                         # Pengetahuan berdasarkan teknologi
│   ├── web/                         # Web development
│   │   ├── backend/
│   │   │   └── laravel/             # Domain spesifik
│   │   │       ├── knowledge/       # Pengetahuan tetap (best practice, prosedur)
│   │   │       │   └── validation.md
│   │   │       ├── errors/          # Error lessons (belajar dari error)
│   │   │       │   └── validation_error.json
│   │   │       └── procedures/      # Prosedur tervalidasi (opsional)
│   │   │           └── deploy.md
│   │   └── frontend/
│   │       └── javascript/          # Bisa diisi nanti
│   └── embedded/                    # Embedded/SoC
│       └── verilog/                 # Domain verilog
│           ├── knowledge/
│           └── errors/
│
├── cache/                           # Dokumentasi hasil fetch dari internet
│   └── laravel_validation_11.html   (bisa di .gitignore jika terlalu besar)
│
├── logs/                            # Log percakapan harian (JSON)
│   └── 2026-04-01.json
│
├── summaries/                       # Ringkasan global per domain
│   ├── web_backend_laravel_summary.md
│   └── embedded_verilog_summary.md
│
├── scripts/                         # Skrip utama
│   ├── orchestrator.py              # Otak utama: tentukan domain, kumpulkan konteks, panggil model
│   ├── intent_classifier.py         # Deteksi apakah perlu dokumentasi eksternal
│   ├── web_fetcher.py               # Ambil dokumentasi dari internet (dengan caching)
│   ├── update_error_memory.py       # Menambah error baru dari chat
│   ├── summarizer.py                # Auto-summarize percakapan panjang
│   └── sync.sh                      # Git pull/push otomatis (opsional)
│
├── config.yaml                      # Konfigurasi model, path, dll
├── README.md                        # Penjelasan proyek
└── requirements.txt
🔍 Penjelasan Setiap Bagian
domains/
Tempat semua pengetahuan terstruktur berdasarkan teknologi.

Setiap sub-folder (misal web/backend/laravel) adalah domain. Di dalamnya:

knowledge/ → file .md berisi best practice, snippet, prosedur tetap.

errors/ → file .json berisi error yang pernah dilaporkan + perbaikan (format baku).

procedures/ → langkah-langkah tervalidasi (opsional).

Keuntungan: pencarian hanya di domain relevan, tidak bercampur.

cache/
Menyimpan dokumentasi yang di-fetch dari internet (misal laravel.com/docs/11/validation.html).

Bisa di-commit jika dokumentasi kecil, atau ditambahkan ke .gitignore agar tidak membesar.

Digunakan oleh web_fetcher.py untuk menghindari fetch berulang.

logs/
Percakapan harian dalam format JSON. Setiap entri: timestamp, domain, user, assistant.

Berguna untuk debugging dan bahan summarization.

summaries/
Ringkasan percakapan per domain, di-update secara berkala oleh summarizer.py.

Saat memulai sesi baru, AI membaca ringkasan ini untuk mengingat konteks global.

scripts/
orchestrator.py: skrip utama yang dijalankan user (python scripts/orchestrator.py "pertanyaan").

Memanggil intent_classifier.py untuk menentukan perlu dokumentasi atau tidak.

Mengumpulkan konteks dari:

domains/.../knowledge/ (pengetahuan tetap)

domains/.../errors/ (error relevan)

cache/ (dokumentasi jika ada)

Membangun prompt dan mengirim ke model (lokal via Ollama atau API).

Menyimpan percakapan ke logs/.

Jika user melaporkan error, memanggil update_error_memory.py untuk menyimpan.

intent_classifier.py: sederhana (rule-based) deteksi apakah pertanyaan membutuhkan dokumentasi eksternal (misal ada kata “dokumentasi”, “versi terbaru”, “cara menggunakan”).

web_fetcher.py: menerima URL atau query, mengambil konten, menyimpan ke cache.

update_error_memory.py: menambahkan error baru ke folder errors/ domain yang sesuai.

summarizer.py: membaca log yang sudah panjang, memanggil model untuk meringkas, simpan ke summaries/.

sync.sh: script untuk git pull/push (bisa dijalankan otomatis setelah setiap interaksi).