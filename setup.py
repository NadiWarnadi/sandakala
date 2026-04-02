#!/usr/bin/env python3
import os
import sys
import subprocess
import yaml
import json
from pathlib import Path

def run_command(command):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + command)
    except Exception as e:
        print(f"❌ Gagal menginstal: {command}. Error: {e}")

def setup():
    print("🚀 --- SANDAKALA AI SETUP --- 🚀\n")

    # 1. Instalasi Requirements
    if os.path.exists("requirements.txt"):
        print("📦 Menginstal library Python...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    else:
        print("⚠️ requirements.txt tidak ditemukan, menginstal library dasar...")
        run_command(["requests", "pyyaml", "beautifulsoup4", "trafilatura"])

    # 2. Pembuatan Folder
    print("\n📁 Menyiapkan struktur folder...")
    folders = ["domains", "cache", "logs", "summaries", "scripts"]
    for f in folders:
        Path(f).mkdir(exist_ok=True)
        print(f"   ✅ Folder '{f}' siap.")

    # 3. Konfigurasi Interaktif
    print("\n⚙️ --- Konfigurasi config.yaml ---")
    config_path = Path("config.yaml")
    
    # Load existing if exists
    current_cfg = {}
    if config_path.exists():
        with open(config_path, 'r') as f:
            current_cfg = yaml.safe_load(f) or {}

    m_type = input(f"Tipe model (ollama/api) [{current_cfg.get('model',{}).get('type','ollama')}]: ") or "ollama"
    m_name = input(f"Nama model [{current_cfg.get('model',{}).get('name','deepseek-coder:6.7b')}]: ") or "deepseek-coder:6.7b"
    
    api_url = current_cfg.get('model',{}).get('api_url')
    if m_type == "ollama":
        api_url = "http://localhost:11434/api/generate"
    elif m_type == "api":
        api_url = input(f"Masukkan API URL: ")
    
    api_key = None
    if m_type == "api":
        api_key = input("Masukkan API Key: ")

    new_config = {
        "model": {
            "type": m_type,
            "name": m_name,
            "api_url": api_url,
            "api_key": api_key
        },
        "paths": {
            "domains": "domains",
            "cache": "cache",
            "logs": "logs",
            "summaries": "summaries"
        },
        "internet": {
            "enabled": True,
            "default_timeout": 10,
            "cache_ttl": 86400
        }
    }

    with open(config_path, 'w') as f:
        yaml.dump(new_config, f, default_flow_style=False)
    print(f"✅ config.yaml berhasil diperbarui.")

    # 4. Cek Koneksi Ollama
    if m_type == "ollama":
        print("\n🔍 Mengecek koneksi ke Ollama...")
        import requests
        try:
            # Cek status Ollama
            resp = requests.get("http://localhost:11434/api/tags", timeout=5)
            if resp.status_code == 200:
                models = [m['name'] for m in resp.json().get('models', [])]
                print(f"   ✅ Ollama Aktif!")
                if m_name in models:
                    print(f"   ✅ Model '{m_name}' ditemukan.")
                else:
                    print(f"   ⚠️ Model '{m_name}' belum di-download. Jalankan 'ollama pull {m_name}' nanti.")
            else:
                print("   ❌ Ollama merespon tapi ada masalah.")
        except:
            print("   ❌ Gagal terhubung ke Ollama. Pastikan 'ollama serve' sudah jalan.")

    # 5. Buat Alias Awal
    alias_file = Path("domains/alias.json")
    if not alias_file.exists():
        with open(alias_file, 'w') as f:
            json.dump({"js": "javascript", "py": "python", "ts": "typescript"}, f)
        print("\n🔗 File alias.json dibuat di folder domains.")

    print("\n🎉 SETUP SELESAI!")
    print("Gunakan './sandakala.sh \"pertanyaan\"' untuk mulai.")

if __name__ == "__main__":
    setup()
