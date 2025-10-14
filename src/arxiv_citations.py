#!/usr/bin/env python3
"""
arxiv_citations.py

Given an arXiv reference like "arxiv:2204.05149" (or "2204.05149" / full URL),
fetch the number of citations for that paper.

Strategy:
  1) Try Semantic Scholar Graph API (no key needed): 
     GET https://api.semanticscholar.org/graph/v1/paper/ARXIV:{id}?fields=citationCount
  2) Fallback to OpenAlex Works API:
     GET https://api.openalex.org/works/https://arxiv.org/abs/{id}
     -> read 'cited_by_count'
  3) If OpenAlex can't resolve the arXiv ID, try to resolve a DOI from arXiv API
     then look up the OpenAlex work by DOI:
     - GET http://export.arxiv.org/api/query?id_list={id}
     - find the <arxiv:doi> tag if present
     - GET https://api.openalex.org/works/https://doi.org/{doi}

Notes:
  * Citation counts differ across providers; this script returns the first
    successful provider's count along with which source was used.
  * Requires: Python 3.8+, 'requests' library.

Usage:
  python3 arxiv_citations.py arxiv:2407.21783
  python3 arxiv_citations.py 2204.05149
  python3 arxiv_citations.py https://arxiv.org/abs/2204.05149
  

Output:
  Prints a single line like:
    123 (source=semanticscholar)
  and exits with code 0. On failure, prints an error message to stderr and
  exits with code 1.
"""

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from typing import Optional, Tuple

import requests

UA = "arxiv_citations.py (+https://example.local)"
TIMEOUT = 15

def normalize_arxiv_id(s: str) -> str:
    s = s.strip()
    # Accept prefixes like 'arxiv:' or URLs
    s = re.sub(r'(?i)^arxiv:\s*', '', s)
    m = re.match(r'https?://arxiv\.org/(abs|pdf)/([0-9]{4}\.\d{4,5})(v\d+)?', s, re.I)
    if m:
        return m.group(2)
    # Plain ID like 2204.05149 or 1007.5017 (old format) or with version
    # arXiv IDs can have 4-5 digits after the decimal point
    m = re.match(r'^([0-9]{4}\.\d{4,5})(?:v\d+)?$', s)
    if m:
        return m.group(1)
    raise ValueError(f"Couldn't parse an arXiv ID from: {s}")

def get_from_semanticscholar(arxiv_id: str) -> Optional[int]:
    url = f"https://api.semanticscholar.org/graph/v1/paper/ARXIV:{arxiv_id}"
    params = {"fields": "citationCount"}
    try:
        r = requests.get(url, params=params, headers={"User-Agent": UA}, timeout=TIMEOUT)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict) and "citationCount" in data and isinstance(data["citationCount"], int):
                return data["citationCount"]
    except requests.RequestException:
        pass
    return None

def get_from_openalex_by_arxiv(arxiv_id: str) -> Optional[int]:
    # OpenAlex supports external IDs as path params in many cases.
    url = f"https://api.openalex.org/works/https://arxiv.org/abs/{arxiv_id}"
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict) and isinstance(data.get("cited_by_count"), int):
                return data["cited_by_count"]
    except requests.RequestException:
        pass
    return None

def resolve_doi_from_arxiv(arxiv_id: str) -> Optional[str]:
    # arXiv Atom API; DOI appears in the arxiv namespace when present
    url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)
        if r.status_code == 200 and r.text:
            # Parse XML and look for the arxiv:doi tag
            root = ET.fromstring(r.text)
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            doi_el = root.find('.//arxiv:doi', ns)
            if doi_el is not None and doi_el.text:
                return doi_el.text.strip()
    except requests.RequestException:
        pass
    except ET.ParseError:
        pass
    return None

def get_from_openalex_by_doi(doi: str) -> Optional[int]:
    # Accept raw DOI like 10.1234/abc
    doi = doi.strip()
    if doi.lower().startswith("https://doi.org/"):
        doi_url = doi
    else:
        doi_url = f"https://doi.org/{doi}"
    url = f"https://api.openalex.org/works/{doi_url}"
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict) and isinstance(data.get("cited_by_count"), int):
                return data["cited_by_count"]
    except requests.RequestException:
        pass
    return None

def get_citation_count(arxiv_ref: str) -> Tuple[Optional[int], str]:
    arxiv_id = normalize_arxiv_id(arxiv_ref)
    # Try Semantic Scholar
    count = get_from_semanticscholar(arxiv_id)
    if isinstance(count, int):
        return count, "semanticscholar"
    # Try OpenAlex with arXiv URL
    count = get_from_openalex_by_arxiv(arxiv_id)
    if isinstance(count, int):
        return count, "openalex-arxiv"
    # Try DOI resolution via arXiv API -> OpenAlex by DOI
    doi = resolve_doi_from_arxiv(arxiv_id)
    if doi:
        count = get_from_openalex_by_doi(doi)
        if isinstance(count, int):
            return count, "openalex-doi"
    return None, ""

def main():
    ap = argparse.ArgumentParser(description="Get citation count for an arXiv paper.")
    ap.add_argument("arxiv_ref", help="arXiv reference (e.g., 'arxiv:2204.05149', '2204.05149', or URL)")
    ap.add_argument("--json", action="store_true", help="Print JSON with provider + count instead of plain text.")
    args = ap.parse_args()
    try:
        count, source = get_citation_count(args.arxiv_ref)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    if isinstance(count, int):
        if args.json:
            print(json.dumps({"count": count, "source": source}, ensure_ascii=False))
        else:
            print(f"{count} (source={source})")
        sys.exit(0)
    else:
        print("Could not find a citation count via Semantic Scholar or OpenAlex.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
