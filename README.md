# Sandakala - AI Self-Learning dengan Memori Eksternal

Sandakala adalah asisten AI open-source yang dapat belajar dari error, mengambil dokumentasi internet, dan menyimpan memori lintas sesi. Semua data disimpan di GitHub sehingga portabel.

## Instalasi
1. Clone repo ini.
2. Install Python 3.10+ dan `pip install -r requirements.txt`.
3. Install [Ollama](https://ollama.ai) dan pull model (misal `deepseek-coder:6.7b`).
4. Sesuaikan `config.yaml` dengan model dan path.
5. Jalankan: `python scripts/orchestrator.py "pertanyaan Anda"`

## Fitur
- **Domain-based knowledge** – pengetahuan terpisah per teknologi.
- **Auto-learning error** – error yang dilaporkan disimpan dan tidak diulang.
- **Dokumentasi internet** – mengambil dokumentasi resmi sesuai domain.
- **Ringkasan otomatis** – percakapan panjang diringkas.
- **Portabel** – semua data di GitHub, siap dipakai di komputer lain.

## Struktur Folder
Lihat tree di atas.

## Penggunaan
- Tanya: `python scripts/orchestrator.py "Bagaimana cara validasi di Laravel?"`
- Sinkronkan: `./scripts/sync.sh` (opsional)

## Lisensi
MIT