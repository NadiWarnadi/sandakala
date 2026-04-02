#!/usr/bin/env python3
"""
Sandakala - Main orchestrator.
Usage: python orchestrator.py "your question"
"""

import sys
import json
import yaml
import requests
import subprocess
from update_error_memory import quick_add_error   # import fungsi untuk auto-save error
from pathlib import Path
from datetime import datetime
from intent_classifier import needs_external_docs
from web_fetcher import fetch_documentation

# Load config
CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
CONFIG = yaml.safe_load(CONFIG_PATH.read_text())

MODEL_TYPE = CONFIG["model"]["type"]
MODEL_NAME = CONFIG["model"]["name"]
API_URL = CONFIG["model"].get("api_url")
API_KEY = CONFIG["model"].get("api_key")

DOMAIN_BASE = Path(CONFIG["paths"]["domains"])
LOGS_DIR = Path(CONFIG["paths"]["logs"])
SUMMARIES_DIR = Path(CONFIG["paths"]["summaries"])
CACHE_DIR = Path(CONFIG["paths"]["cache"])

# Ensure directories exist
LOGS_DIR.mkdir(exist_ok=True)
SUMMARIES_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)

def get_clean_tech_name(query, aliases):
    """Minta AI menentukan nama teknologi tunggal dari query untuk folder."""
    prompt = f"""Tentukan SATU nama teknologi/bahasa pemrograman utama dari pertanyaan ini: "{query}".
    Jika ada di daftar alias ini: {list(aliases.keys())}, gunakan nilai petanya.
    Hanya jawab dengan 1 kata (lowercase), contoh: laravel, python, verilog.
    Jika tidak ada teknologi spesifik, jawab 'general'."""
    
    # Panggil fungsi ask_ollama atau ask_api yang sudah ada di orchestrator
    tech = ask_ollama(prompt).strip().lower().replace(".", "")
    return aliases.get(tech, tech)

def detect_domain(query):
    # 1. Load Alias
    alias_path = DOMAIN_BASE / "alias.json"
    aliases = json.loads(alias_path.read_text()) if alias_path.exists() else {}

    # 2. Tanya AI: "Ini teknologi apa?" 
    # (Ini mencegah duplikasi karena AI tahu JS = Javascript)
    tech_name = get_clean_tech_name(query, aliases)
    
    if tech_name == "general":
        return "general"

    # 3. Cari apakah folder tech_name sudah ada di sub-mana pun
    # Contoh: cari 'laravel' di seluruh subfolder domains/
    existing_paths = list(DOMAIN_BASE.glob(f"**/{tech_name}"))
    
    if existing_paths:
        # Jika ketemu, gunakan path yang sudah ada (misal: web/backend/laravel)
        return str(existing_paths[0].relative_to(DOMAIN_BASE))
    
    # 4. Jika BARU, minta AI tentukan kategori foldernya
    cat_prompt = f"Apa kategori parent untuk teknologi '{tech_name}'? Contoh: web/backend, mobile/android, hardware/embedded. Jawab hanya path kategorinya saja."
    category = ask_ollama(cat_prompt).strip().lower().replace(" ", "")
    
    new_domain_path = DOMAIN_BASE / category / tech_name
    
    # Buat foldernya
    (new_domain_path / "knowledge").mkdir(parents=True, exist_ok=True)
    (new_domain_path / "errors").mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Domain baru diciptakan otomatis: {new_domain_path}")
    return str(new_domain_path.relative_to(DOMAIN_BASE))

def load_knowledge(domain):
    """Load all .md files from domain/knowledge/."""
    knowledge_dir = DOMAIN_BASE / domain / "knowledge"
    if not knowledge_dir.exists():
        return ""
    texts = []
    for file in knowledge_dir.glob("*.md"):
        texts.append(f"### {file.stem}\n{file.read_text()}")
    return "\n\n".join(texts)

def load_errors(domain, query):
    """Load error JSON files and return those relevant to query (simple keyword)."""
    error_dir = DOMAIN_BASE / domain / "errors"
    if not error_dir.exists():
        return []
    relevant = []
    for file in error_dir.glob("*.json"):
        try:
            data = json.loads(file.read_text())
            if query.lower() in data.get("context", "").lower() or \
               any(tag.lower() in query.lower() for tag in data.get("tags", [])):
                relevant.append(data)
        except Exception:
            continue
    return relevant

def load_summary(domain):
    """Load summary for domain if exists."""
    summary_file = SUMMARIES_DIR / f"{domain.replace('/', '_')}_summary.md"
    if summary_file.exists():
        return summary_file.read_text()
    return ""

def build_prompt(query, domain, context):
    """Construct full prompt for the model."""
    system_parts = [
        f"Anda adalah asisten AI bernama Sandakala, ahli dalam domain {domain}.",
        "Gunakan pengetahuan berikut untuk menjawab pertanyaan dengan akurat dan memberikan kode jika diperlukan."
    ]
    
    summary = load_summary(domain)
    if summary:
        system_parts.append(f"\n## Ringkasan Riset Sebelumnya\n{summary}")
    
    knowledge = load_knowledge(domain)
    if knowledge:
        system_parts.append(f"\n## Pengetahuan Tetap\n{knowledge}")
    
    errors = load_errors(domain, query)
    if errors:
        error_text = "\n## Error yang Pernah Terjadi (Jangan Diulang)\n"
        for err in errors:
            error_text += f"- **{err.get('error_type', 'Error')}** dalam {err.get('context', '')}\n"
            error_text += f"  ❌ Salah: `{err.get('bad_code', '')}`\n"
            error_text += f"  ✅ Perbaikan: `{err.get('fixed_code', '')}`\n"
            error_text += f"  📘 Pelajaran: {err.get('lesson', '')}\n\n"
        system_parts.append(error_text)
    
    if context:
        system_parts.append(f"\n## Dokumentasi Eksternal (diambil dari internet)\n{context}")
    
    system_prompt = "\n".join(system_parts)
    return f"{system_prompt}\n\n## Pertanyaan\n{query}\n\nJawab dengan jelas dan berikan kode jika diperlukan."

# POIN B: Perbaikan Indentasi fungsi (harus di paling kiri)
def auto_save_error_if_reported(user_query, assistant_response, domain):
    """Jika user melaporkan error dan AI memberikan kode perbaikan, simpan otomatis."""
    if "error" in user_query.lower() or "gagal" in user_query.lower() or "tidak berjalan" in user_query.lower():
        if "```" in assistant_response:
            print("\n💡 Terdeteksi laporan error. Apakah ingin menyimpannya sebagai pelajaran? (y/n)")
            choice = input().strip().lower()
            if choice == 'y':
                quick_add_error(domain, user_query, assistant_response)
                print("✅ Error lesson saved.")

def ask_ollama(prompt):
    url = "http://localhost:11434/api/generate"
    payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False}
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    return resp.json()["response"]

def ask_api(prompt):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {"model": MODEL_NAME, "messages": [{"role": "user", "content": prompt}]}
    resp = requests.post(API_URL, json=payload, headers=headers)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

def save_log(query, response, domain, external_used=False):
    log_file = LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.json"
    entry = {
        "timestamp": datetime.now().isoformat(),
        "domain": domain,
        "user": query,
        "assistant": response,
        "external_docs_used": external_used
    }
    if log_file.exists():
        data = json.loads(log_file.read_text())
    else:
        data = []
    data.append(entry)
    log_file.write_text(json.dumps(data, indent=2))

def main():
    if len(sys.argv) < 2:
        print("Usage: python orchestrator.py \"your question\"")
        sys.exit(1)
    query = sys.argv[1]
    
    domain = detect_domain(query)
    print(f"🔍 Domain detected: {domain}")
    
    external_context = ""
    if needs_external_docs(query):
        print("🌐 Fetching external documentation...")
        external_context = fetch_documentation(query, domain, CACHE_DIR)
    else:
        external_context = "" # Perbaikan indentasi di sini

    prompt = build_prompt(query, domain, external_context)
    
    print("🤖 Asking model...")
    try:
        if MODEL_TYPE == "ollama":
            response = ask_ollama(prompt)
        elif MODEL_TYPE == "api":
            response = ask_api(prompt)
        else:
            raise ValueError(f"Unknown model type: {MODEL_TYPE}")
    except Exception as e:
        print(f"❌ Model error: {e}")
        sys.exit(1)
    
    print("\n" + "="*50)
    print("ANSWER:")
    print("="*50)
    print(response)
    
    save_log(query, response, domain, external_context != "")
    
   
    auto_save_error_if_reported(query, response, domain)

if __name__ == "__main__":
    main()
