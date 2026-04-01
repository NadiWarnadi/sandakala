#!/usr/bin/env python3
"""
Dynamic documentation fetcher that works for any technology.
No need to add per-domain handlers.
"""

import hashlib
import time
import requests
from pathlib import Path
from urllib.parse import quote
import trafilatura
from bs4 import BeautifulSoup

# -------------------------------------------------------------------
# Generic search & extraction helpers
# -------------------------------------------------------------------
def fetch_url_text(url, timeout=10):
    """Fetch URL and extract main text using trafilatura."""
    try:
        response = requests.get(url, timeout=timeout, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            text = trafilatura.extract(response.text, include_comments=False)
            if text:
                return text
            # fallback: BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            for script in soup(["script", "style"]):
                script.decompose()
            return soup.get_text(separator='\n', strip=True)
    except Exception:
        return None

def search_duckduckgo(query, max_results=3):
    """Search DuckDuckGo and return list of result titles+URLs."""
    # Use DuckDuckGo HTML lite version
    url = f"https://lite.duckduckgo.com/lite/?q={quote(query)}"
    try:
        resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(resp.text, 'html.parser')
        results = []
        # Parse the lite results (table rows)
        rows = soup.find_all('tr')
        for row in rows:
            links = row.find_all('a')
            if links:
                href = links[0].get('href')
                title = links[0].get_text(strip=True)
                if href and href.startswith('http') and 'duckduckgo.com' not in href:
                    results.append({'title': title, 'url': href})
                    if len(results) >= max_results:
                        break
        return results
    except Exception:
        return []

def is_official_domain(url, tech_name):
    """Heuristic to check if URL likely belongs to official docs."""
    # Remove protocol and www
    domain = url.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
    tech_lower = tech_name.lower().replace(' ', '')
    # Check if domain contains tech name (e.g., rust-lang.org, svelte.dev, laravel.com)
    if tech_lower in domain:
        return True
    # Also check common patterns: docs.tech.com, tech.io, etc.
    if domain.startswith(tech_lower) or domain.endswith('.' + tech_lower + '.com'):
        return True
    return False

# -------------------------------------------------------------------
# Main dynamic fetcher
# -------------------------------------------------------------------
def fetch_documentation(query, domain, cache_dir):
    """
    Fetch documentation for any technology mentioned in query.
    Returns string of relevant content.
    """
    # Extract technology name from query (simple rule: look for common patterns)
    # For now, we'll use a simple heuristic: if domain contains something like "web/backend/laravel" we already know.
    # But we also want to handle tech not in domain. So we will detect tech name from query.
    tech_name = None
    
    # First, if domain is not 'general', we can use the last part of domain as tech name
    if domain != 'general':
        tech_name = domain.split('/')[-1]
    
    # If not, try to extract from query (e.g., "dokumentasi Rust", "cara menggunakan Svelte")
    if not tech_name:
        # Look for phrases like "dokumentasi X", "X documentation", "cara X"
        import re
        patterns = [
            r'dokumentasi\s+(\w+)',
            r'(\w+)\s+dokumentasi',
            r'documentation\s+for\s+(\w+)',
            r'cara\s+menggunakan\s+(\w+)',
            r'how to use (\w+)'
        ]
        for pat in patterns:
            match = re.search(pat, query.lower())
            if match:
                tech_name = match.group(1)
                break
    
    if not tech_name:
        # Fallback: return empty, no need to fetch
        return ""
    
    # Create cache key based on tech_name and query
    cache_key = hashlib.md5(f"{tech_name}:{query}".encode()).hexdigest()
    cache_file = Path(cache_dir) / f"{cache_key}.txt"
    
    # Check cache with TTL
    if cache_file.exists():
        age = time.time() - cache_file.stat().st_mtime
        if age < 86400:  # 1 day
            return cache_file.read_text()
    
    # Construct search query: "tech_name official documentation"
    search_query = f"{tech_name} official documentation"
    results = search_duckduckgo(search_query, max_results=3)
    
    if not results:
        # Try without "official"
        search_query = f"{tech_name} documentation"
        results = search_duckduckgo(search_query, max_results=3)
    
    # Prioritize official domain results
    official_content = None
    generic_content = None
    
    for res in results:
        url = res['url']
        content = fetch_url_text(url)
        if not content:
            continue
        if is_official_domain(url, tech_name):
            # Found official docs, use it and break
            official_content = content
            break
        else:
            # Save first generic result as fallback
            if not generic_content:
                generic_content = content
    
    final_content = official_content or generic_content
    
    if final_content:
        # Truncate to avoid huge prompts
        if len(final_content) > 10000:
            final_content = final_content[:10000] + "... (truncated)"
        # Save to cache
        cache_file.write_text(final_content)
        return final_content
    else:
        return ""