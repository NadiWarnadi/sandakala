#!/usr/bin/env python3
"""
Summarize recent conversations for a domain to keep context manageable.
"""

import sys
import json
import yaml
import requests
from pathlib import Path
from datetime import datetime, timedelta

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
CONFIG = yaml.safe_load(CONFIG_PATH.read_text())
MODEL_NAME = CONFIG["model"]["name"]
LOGS_DIR = Path(CONFIG["paths"]["logs"])
SUMMARIES_DIR = Path(CONFIG["paths"]["summaries"])
DOMAIN_BASE = Path(CONFIG["paths"]["domains"])

def load_logs_since(days=7):
    """Load all log entries from the last `days` days."""
    entries = []
    cutoff = datetime.now() - timedelta(days=days)
    for log_file in LOGS_DIR.glob("*.json"):
        # check if file is recent enough
        if datetime.fromtimestamp(log_file.stat().st_mtime) < cutoff:
            continue
        data = json.loads(log_file.read_text())
        entries.extend(data)
    return entries

def group_by_domain(entries):
    """Group entries by domain."""
    grouped = {}
    for entry in entries:
        domain = entry.get("domain", "general")
        grouped.setdefault(domain, []).append(entry)
    return grouped

def summarize_conversation(conversation_text):
    """Call model to summarize a block of conversation."""
    prompt = f"Ringkaskan percakapan berikut dalam beberapa paragraf, fokus pada topik utama, keputusan, dan error yang muncul:\n\n{conversation_text}"
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }
    try:
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()["response"]
    except Exception as e:
        print(f"Summarization failed: {e}")
        return ""

def main():
    entries = load_logs_since(days=3)  # summarize last 3 days
    if not entries:
        print("No recent logs to summarize.")
        return
    
    grouped = group_by_domain(entries)
    
    for domain, convs in grouped.items():
        # Build conversation text
        conv_text = ""
        for conv in convs:
            conv_text += f"User: {conv['user']}\nAssistant: {conv['assistant']}\n\n"
        
        summary = summarize_conversation(conv_text)
        if summary:
            # Save summary to file, overwriting or appending
            summary_file = SUMMARIES_DIR / f"{domain.replace('/', '_')}_summary.md"
            # Optionally prepend with date
            content = f"# Ringkasan {domain} (diperbarui {datetime.now().strftime('%Y-%m-%d')})\n\n{summary}\n\n"
            summary_file.write_text(content)
            print(f"✅ Summary for {domain} saved to {summary_file}")

if __name__ == "__main__":
    main()