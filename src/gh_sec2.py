#!/usr/bin/env python3
"""
GitHub Org + Repo Security Evaluation Checklist -> CSV

Usage:
  export GITHUB_TOKEN=ghp_...  # optional but recommended (repo, read:org, security_events)
  python gh_sec2.py pytorch pytorch  # owner repo
  python gh_sec2.py <owner> <repo> [out.csv]

Outputs:
  security_checklist_<owner>_<repo>.csv (or provided out.csv)
"""

import csv
import os
import re
import sys
import time
import requests
from urllib.parse import quote
from typing import Any, Dict, Iterable, List, Tuple, Optional
import json
from excel_manager import ExcelManager

API_ROOT = "https://api.github.com"
SESSION = requests.Session()
SESSION.headers.update({
    "Accept": "application/vnd.github+json",
    "User-Agent": "gh-security-checklist/2.0"
})
TOKEN = os.getenv("GITHUB_TOKEN")
if TOKEN:
    SESSION.headers.update({"Authorization": f"Bearer {TOKEN}"})


def _req(method: str, url: str, **kwargs) -> requests.Response:
    """HTTP wrapper with minimal rate-limit backoff."""
    for _ in range(3):
        resp = SESSION.request(method, url, timeout=30, **kwargs)
        if resp.status_code == 403 and resp.headers.get("X-RateLimit-Remaining") == "0":
            reset_epoch = int(resp.headers.get("X-RateLimit-Reset", "0") or 0)
            sleep_for = max(0, reset_epoch - int(time.time()) + 1)
            time.sleep(min(sleep_for, 60))
            continue
        return resp
    return resp


def safe_get_json(url: str, params: Optional[Dict[str, Any]] = None) -> Tuple[Any, int, Optional[str]]:
    resp = _req("GET", url, params=params or {})
    try:
        resp.raise_for_status()
        return resp.json(), resp.status_code, None
    except requests.HTTPError as e:
        try:
            j = resp.json()
        except Exception:
            j = {"message": resp.text}
        msg = j.get("message") if isinstance(j, dict) else str(e)
        return None, resp.status_code, msg


def _parse_owner_repo_args(argv: List[str]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Accept either 'owner repo' or 'owner/repo' and optional output path."""
    owner = None
    repo = None
    out_csv = None

    if len(argv) >= 2:
        arg1 = argv[1].strip()
        if "/" in arg1:
            owner, repo = (p.strip() for p in arg1.split("/", 1))
            if len(argv) >= 3:
                out_csv = argv[2].strip() or None
        else:
            if len(argv) >= 3:
                owner = arg1
                repo = argv[2].strip()
                if len(argv) >= 4:
                    out_csv = argv[3].strip() or None
    return owner, repo, out_csv


def _flatten(prefix: str, obj: Any) -> Iterable[Tuple[str, str]]:
    """Flatten nested dict/list into dot/bracket path keys to string values."""
    def _to_str(val: Any) -> str:
        if val is None or isinstance(val, (str, int, float, bool)):
            return str(val)
        return json.dumps(val, ensure_ascii=False)

    if isinstance(obj, dict):
        for k, v in obj.items():
            new_prefix = f"{prefix}.{k}" if prefix else str(k)
            yield from _flatten(new_prefix, v)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            new_prefix = f"{prefix}[{i}]" if prefix else f"[{i}]"
            yield from _flatten(new_prefix, v)
    else:
        yield prefix, _to_str(obj)


def _owner_resource(owner_login: str, owner_type_hint: Optional[str]) -> Tuple[str, Optional[Dict[str, Any]], int, Optional[str]]:
    """Resolve owner to /orgs/{owner} or /users/{owner}."""
    if owner_type_hint and owner_type_hint.lower() == "organization":
        url = f"{API_ROOT}/orgs/{owner_login}"
        return url, *safe_get_json(url)
    # try org first, then user
    org_url = f"{API_ROOT}/orgs/{owner_login}"
    j, code, err = safe_get_json(org_url)
    if j:
        return org_url, j, code, err
    user_url = f"{API_ROOT}/users/{owner_login}"
    j2, code2, err2 = safe_get_json(user_url)
    return user_url, j2, code2, err2


def collect(owner: str, repo: str) -> List[Dict[str, str]]:
    """Collect repo and owner/org data as rows for CSV with Scope/Key/Value."""
    rows: List[Dict[str, str]] = []

    def add(scope: str, key: str, value: str):
        rows.append({"Scope": scope, "Key": key, "Value": value})

    # Repo core
    repo_url = f"{API_ROOT}/repos/{owner}/{repo}"
    repo_json, code, err = safe_get_json(repo_url)
    if not repo_json:
        raise SystemExit(f"Failed to fetch repo: {code} {err}")

    for k, v in _flatten("repo", repo_json):
        add("Repository", k, v)

    owner_login = (repo_json.get("owner") or {}).get("login") or owner
    owner_type = (repo_json.get("owner") or {}).get("type")

    # Owner/org core
    _, owner_json, code2, err2 = _owner_resource(owner_login, owner_type)
    if owner_json:
        for k, v in _flatten("owner", owner_json):
            add("Owner/Org", k, v)
        # MFA enforcement (when token has org visibility). GitHub exposes
        # 'two_factor_requirement_enabled' on org objects for org owners.
        if isinstance(owner_json, dict) and owner_json.get("type") == "Organization":
            if "two_factor_requirement_enabled" in owner_json:
                add("Owner/Org", "security.two_factor_requirement_enabled",
                    str(bool(owner_json.get("two_factor_requirement_enabled"))))
            else:
                add("Owner/Org", "security.two_factor_requirement_enabled",
                    "unavailable - missing field (insufficient permissions?)")
    else:
        add("Owner/Org", "owner.fetch_error", f"{code2} {err2}")

    # Additional lightweight endpoints (non-fatal)
    topics_url = f"{API_ROOT}/repos/{owner}/{repo}/topics"
    topics_json, _, _ = safe_get_json(topics_url)
    if isinstance(topics_json, dict):
        add("Repository", "topics", ", ".join(topics_json.get("names", [])))

    langs_url = f"{API_ROOT}/repos/{owner}/{repo}/languages"
    langs_json, _, _ = safe_get_json(langs_url)
    if isinstance(langs_json, dict):
        add("Repository", "languages", ", ".join(sorted(langs_json.keys())))

    # Org members without 2FA (endpoint requires org owner + read:org; best-effort)
    if owner_json and isinstance(owner_json, dict) and owner_json.get("type") == "Organization":
        twofa_url = f"{API_ROOT}/orgs/{owner_login}/members"
        # Legacy filter used by GitHub API v3: filter=2fa_disabled
        members_2fa_json, code3, err3 = safe_get_json(twofa_url + "?filter=2fa_disabled")
        if isinstance(members_2fa_json, list):
            add("Owner/Org", "security.members_without_2fa_count", str(len(members_2fa_json)))
        else:
            add("Owner/Org", "security.members_without_2fa_count", f"unavailable - {code3} {err3}")

    return rows


def write_csv(rows: List[Dict[str, str]], path: str) -> str:
    fieldnames = ["Scope", "Key", "Value"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return path


def query_github_security_to_excel(owner: str, repo: str, excel_manager, model_name: str) -> None:
    """
    Query GitHub repository security information and export to Excel tab.
    
    Args:
        owner: GitHub repository owner
        repo: GitHub repository name
        excel_manager: ExcelManager instance
        model_name: Model name for tab naming
        
    Returns:
        None
    """
    rows = collect(owner, repo)
    
    # Create tab name
    tab_name = f"{model_name}_github_security"
    
    # Use Excel manager to create the tab
    excel_manager.create_tab_from_csv_data(tab_name, rows)
    print(f"GitHub security data written: {len(rows)} rows to Excel tab '{tab_name}'")

def query_github_security(owner: str, repo: str, output_dir: str = "../model_scores") -> str:
    """
    Query GitHub repository security information and export to CSV.
    
    DEPRECATED: Use query_github_security_to_excel instead.
    
    Args:
        owner: GitHub repository owner
        repo: GitHub repository name
        output_dir: Directory to save the CSV file
        
    Returns:
        Path to the created CSV file
    """
    rows = collect(owner, repo)
    out_csv = f"{output_dir}/security_checklist_{owner}_{repo}.csv"
    path = write_csv(rows, out_csv)
    print(f"GitHub security data written: {len(rows)} rows to {path}")
    return path


def main():
    owner, repo, out_csv = _parse_owner_repo_args(sys.argv)
    if not owner or not repo:
        sys.exit("Usage: gh_sec2.py <owner/repo | owner repo> [output.csv]")

    out_csv = out_csv or f"../model_scores/security_checklist_{owner}_{repo}.csv"

    rows = collect(owner, repo)
    path = write_csv(rows, out_csv)
    print(f"Wrote {len(rows)} rows to {path}")


if __name__ == "__main__":
    main()
