
    #!/usr/bin/env python3
"""
Intent classifier to decide if we need to fetch external documentation.
"""

def needs_external_docs(query):
    """Return True if query likely requires fresh documentation."""
    q = query.lower()
    # Keywords indicating need for documentation
    doc_keywords = [
        "dokumentasi", "docs", "how to use", "cara menggunakan",
        "fungsi baru", "latest version", "versi terbaru", "api reference",
        "parameter", "syntax", "contoh penggunaan", "tutorial",
        "dokumentasi resmi", "official docs"
    ]
    for kw in doc_keywords:
        if kw in q:
            return True
    # If query length is long (more than 5 words) and contains a potential tech name, assume needs docs
    # Simple: if query has more than 5 words and contains common tech words (optional)
    # But to avoid false positives, we keep it simple: just keywords for now.
    return False