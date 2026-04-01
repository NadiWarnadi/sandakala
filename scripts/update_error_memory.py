#!/usr/bin/env python3
"""
Add a new error lesson to the appropriate domain.
Run interactively or pass arguments.
"""

import sys
import json
from pathlib import Path
import yaml
import argparse
from datetime import datetime


CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
CONFIG = yaml.safe_load(CONFIG_PATH.read_text())
DOMAIN_BASE = Path(CONFIG["paths"]["domains"])

def get_domain():
    """Ask user for domain or detect from context."""
    domains = [p.relative_to(DOMAIN_BASE) for p in DOMAIN_BASE.glob("*/*/*") if p.is_dir()]
    print("Available domains:")
    for i, d in enumerate(domains):
        print(f"{i+1}. {d}")
    idx = input("Choose domain number: ")
    try:
        return str(domains[int(idx)-1])
    except:
        return None

def create_error_json(domain):
    """Prompt user for error details and save."""
    error_type = input("Error type (e.g., ReferenceError, ValidationException): ")
    context = input("Context (e.g., validasi form login): ")
    bad_code = input("Salah (code snippet): ")
    fixed_code = input("Perbaikan (code snippet): ")
    lesson = input("Pelajaran (short explanation): ")
    tags = input("Tags (comma separated): ").split(",")
    tags = [t.strip() for t in tags if t.strip()]
    
    error_data = {
        "error_type": error_type,
        "context": context,
        "bad_code": bad_code,
        "fixed_code": fixed_code,
        "lesson": lesson,
        "tags": tags,
        "date": "2026-04-01"  # bisa diisi otomatis
    }
    
    # Generate filename from error type and context
    filename = f"{error_type.lower()}_{context.replace(' ', '_')[:20]}.json"
    error_dir = DOMAIN_BASE / domain / "errors"
    error_dir.mkdir(parents=True, exist_ok=True)
    filepath = error_dir / filename
    filepath.write_text(json.dumps(error_data, indent=2))
    print(f"✅ Error saved to {filepath}")

def main():
    parser = argparse.ArgumentParser(description="Add a new error lesson.")
    parser.add_argument("--domain", help="Domain path (e.g., web/backend/laravel)")
    args = parser.parse_args()
    
    if args.domain:
        domain = args.domain
    else:
        domain = get_domain()
    
    if not domain:
        print("Domain not valid.")
        sys.exit(1)
    
    create_error_json(domain)

def quick_add_error(domain, user_query, assistant_response):
    """
    Menyimpan error secara otomatis berdasarkan percakapan.
    Ekstraksi sederhana: mengambil blok kode pertama sebagai 'bad_code' dan blok kode kedua sebagai 'fixed_code'.
    """
    import re
    # Cari semua blok kode (```...```)
    code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', assistant_response, re.DOTALL)
    if len(code_blocks) >= 2:
        bad_code = code_blocks[0].strip()
        fixed_code = code_blocks[1].strip()
    elif len(code_blocks) == 1:
        # Jika hanya satu blok, gunakan itu sebagai fixed_code, dan bad_code diambil dari user_query
        fixed_code = code_blocks[0].strip()
        # Cari kode yang bermasalah dari user_query (misal: "error di kode: ...")
        bad_match = re.search(r'(?:kode|code)[:\s]+(.*?)(?:\n|$)', user_query, re.IGNORECASE)
        bad_code = bad_match.group(1).strip() if bad_match else "unknown"
    else:
        print("Tidak dapat menemukan kode dalam respons. Simpan manual nanti.")
        return

    # Buat nama file sederhana
    error_type = "auto_error"
    context = user_query[:50]
    filename = f"{error_type}_{context.replace(' ', '_')}.json"
    error_dir = DOMAIN_BASE / domain / "errors"
    error_dir.mkdir(parents=True, exist_ok=True)
    filepath = error_dir / filename

    error_data = {
        "error_type": error_type,
        "context": context,
        "bad_code": bad_code,
        "fixed_code": fixed_code,
        "lesson": "Auto-saved from chat",
        "tags": [],
        "date": datetime.now().strftime("%Y-%m-%d")
    }
    filepath.write_text(json.dumps(error_data, indent=2))
    print(f"✅ Error saved to {filepath}")

if __name__ == "__main__":
    main()