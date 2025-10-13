#!/usr/bin/env python3
"""
GitHub Security Evaluation Checklist -> CSV

Usage:
  python gh_sec.py pytorch pytorch
  export GITHUB_TOKEN=ghp_...  # (optional but recommended)
"""

import csv
import os
import re
import time
import sys
import requests
from urllib.parse import quote

API_ROOT = "https://api.github.com"
SESSION = requests.Session()
SESSION.headers.update({
    "Accept": "application/vnd.github+json",
    "User-Agent": "gh-security-checklist/1.0"
})
TOKEN = os.getenv("GITHUB_TOKEN")
if TOKEN:
    SESSION.headers.update({"Authorization": f"Bearer {TOKEN}"})

def _req(method, url, **kwargs):
    """Wrapper with simple rate-limit handling and error capture."""
    for attempt in range(3):
        resp = SESSION.request(method, url, timeout=30, **kwargs)
        # Rate limit?
        if resp.status_code == 403 and resp.headers.get("X-RateLimit-Remaining") == "0":
            reset = int(resp.headers.get("X-RateLimit-Reset", "0"))
            sleep_for = max(0, reset - int(time.time()) + 1)
            time.sleep(min(sleep_for, 60))
            continue
        return resp
    return resp  # last response

def safe_get_json(url, params=None):
    r = _req("GET", url, params=params or {})
    try:
        r.raise_for_status()
        return r.json(), r.status_code, None
    except requests.HTTPError as e:
        try:
            j = r.json()
        except Exception:
            j = {"message": r.text}
        return None, r.status_code, j.get("message") if isinstance(j, dict) else str(e)

def find_file_presence(owner, repo, paths):
    """Return (found_path, url or None)."""
    for p in paths:
        j, code, err = safe_get_json(f"{API_ROOT}/repos/{owner}/{repo}/contents/{quote(p)}")
        if j and isinstance(j, dict) and j.get("type") in ("file", "symlink"):
            return p, j.get("html_url")
    return None, None

def analyze_actions_pinning(workflows, owner, repo):
    """
    Heuristic: look for 'uses: owner/action@ref'.
    If ref looks like a full SHA (40-hex), count as pinned; if tag/branch, unpinned.
    """
    pinned, unpinned = 0, 0
    sha40 = re.compile(r"^[0-9a-f]{40}$")
    for wf in workflows:
        # Fetch workflow file content
        j, code, err = safe_get_json(wf["url"])
        if not j or "path" not in j:
            continue
        # Download raw content
        # Preferred raw content endpoint:
        raw_resp = _req("GET", f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{j['path']}")
        if raw_resp.status_code != 200:
            # Try download_url as fallback
            dl = j.get("download_url")
            if not dl:
                continue
            raw_resp = _req("GET", dl)
            if raw_resp.status_code != 200:
                continue
        text = raw_resp.text or ""
        # Grep lines with 'uses:'
        for line in text.splitlines():
            m = re.search(r"uses:\s*([\w\-/\.]+)@([^\s#]+)", line.strip())
            if m:
                ref = m.group(2).strip()
                if sha40.match(ref):
                    pinned += 1
                else:
                    unpinned += 1
    return pinned, unpinned

def risk(flag, when_true="Low", when_false="High", unknown="Unknown"):
    if flag is True:
        return when_true
    if flag is False:
        return when_false
    return unknown

def generate_security_checklist(owner, repo, out_csv=None):
    out_csv = out_csv or f"security_checklist_{owner}_{repo}.csv"
    rows = []

    def add(category, insight, endpoint, value, notes="", risk_level="Unknown"):
        rows.append({
            "Category": category,
            "Insight": insight,
            "API Endpoint": endpoint,
            "Value": value,
            "Risk": risk_level,
            "Notes": notes
        })

    # 1) Repository metadata
    repo_json, code, err = safe_get_json(f"{API_ROOT}/repos/{owner}/{repo}")
    if not repo_json:
        raise SystemExit(f"Failed to fetch repo: {code} {err}")

    visibility = "private" if repo_json.get("private") else "public"
    archived = bool(repo_json.get("archived"))
    default_branch = repo_json.get("default_branch", "main")
    topics = ", ".join(repo_json.get("topics", []))

    add("Repository Metadata", "Visibility", f"/repos/{owner}/{repo}",
        visibility, risk_level="Informational")
    add("Repository Metadata", "Archived", f"/repos/{owner}/{repo}",
        str(archived), risk_level=risk(archived, when_true="Low", when_false="Informational"))
    add("Repository Metadata", "Default branch", f"/repos/{owner}/{repo}",
        default_branch, risk_level="Informational")
    add("Repository Metadata", "Topics", f"/repos/{owner}/{repo}",
        topics or "None", risk_level="Informational")

    # 2) Branch protection (default branch)
    prot_json, code, err = safe_get_json(f"{API_ROOT}/repos/{owner}/{repo}/branches/{quote(default_branch)}/protection")
    if prot_json:
        # Required reviews / status checks
        pr_reviews = prot_json.get("required_pull_request_reviews") or {}
        status_checks = prot_json.get("required_status_checks") or {}
        allow_force_pushes = prot_json.get("allow_force_pushes", {}).get("enabled")
        allow_deletions = prot_json.get("allow_deletions", {}).get("enabled")

        add("Branch Protection", "Required PR reviews",
            f"/repos/{owner}/{repo}/branches/{default_branch}/protection",
            "enabled" if pr_reviews else "disabled",
            risk_level=risk(bool(pr_reviews), when_true="Low", when_false="High"))

        add("Branch Protection", "Required status checks",
            f"/repos/{owner}/{repo}/branches/{default_branch}/protection",
            "enabled" if status_checks else "disabled",
            risk_level=risk(bool(status_checks), when_true="Low", when_false="Medium"))

        add("Branch Protection", "Force pushes allowed?",
            f"/repos/{owner}/{repo}/branches/{default_branch}/protection",
            str(bool(allow_force_pushes)),
            risk_level=risk(allow_force_pushes is False, when_true="Low", when_false="High"))

        add("Branch Protection", "Allow branch deletions?",
            f"/repos/{owner}/{repo}/branches/{default_branch}/protection",
            str(bool(allow_deletions)),
            risk_level=risk(allow_deletions is False, when_true="Low", when_false="Medium"))
    else:
        add("Branch Protection", "Protection (default branch)",
            f"/repos/{owner}/{repo}/branches/{default_branch}/protection",
            "unavailable", notes=f"{code}: {err}",
            risk_level="High")  # assume high risk if unknown (often disabled or no access)

    # 3) Security policy & governance files
    sec_path, sec_url = find_file_presence(owner, repo, ["SECURITY.md", ".github/SECURITY.md", "docs/SECURITY.md"])
    add("Security Policy", "SECURITY.md present",
        "/repos/{owner}/{repo}/contents/SECURITY.md",
        "yes" if sec_path else "no",
        notes=sec_url or "",
        risk_level=risk(bool(sec_path), when_true="Low", when_false="Medium"))

    co_path, co_url = find_file_presence(owner, repo, [".github/CODEOWNERS", "CODEOWNERS", "docs/CODEOWNERS"])
    add("Governance", "CODEOWNERS present",
        "/repos/{owner}/{repo}/contents/CODEOWNERS",
        "yes" if co_path else "no",
        notes=co_url or "",
        risk_level=risk(bool(co_path), when_true="Low", when_false="Medium"))

    lic_json, code, err = safe_get_json(f"{API_ROOT}/repos/{owner}/{repo}/license")
    if lic_json and lic_json.get("license"):
        add("Legal", "License",
            f"/repos/{owner}/{repo}/license",
            lic_json["license"].get("spdx_id") or lic_json["license"].get("key") or "custom",
            notes=lic_json.get("html_url", ""),
            risk_level="Informational")
    else:
        add("Legal", "License",
            f"/repos/{owner}/{repo}/license",
            "unavailable", notes=f"{code}: {err or 'no license detected'}",
            risk_level="Medium")

    # 4) Actions workflows + pinning heuristic
    wfs, code, err = safe_get_json(f"{API_ROOT}/repos/{owner}/{repo}/actions/workflows")
    if wfs and isinstance(wfs.get("workflows"), list):
        workflows = wfs["workflows"]
        add("Automation", "Workflow count", f"/repos/{owner}/{repo}/actions/workflows",
            str(len(workflows)), risk_level="Informational")

        pinned, unpinned = analyze_actions_pinning(workflows, owner, repo)
        add("Automation", "External actions pinned to commit SHA",
            "(raw file scan of workflows)", str(pinned),
            risk_level=risk(pinned > 0 and unpinned == 0, when_true="Low", when_false="Medium"))
        add("Automation", "External actions NOT pinned (tag/branch)",
            "(raw file scan of workflows)", str(unpinned),
            risk_level=risk(unpinned == 0, when_true="Low", when_false="Medium-High"))
    else:
        add("Automation", "Workflows list",
            f"/repos/{owner}/{repo}/actions/workflows",
            "unavailable", notes=f"{code}: {err}", risk_level="Unknown")

    # 5) Environments (protected deployments)
    envs, code, err = safe_get_json(f"{API_ROOT}/repos/{owner}/{repo}/environments")
    if envs and isinstance(envs.get("environments"), list):
        env_names = [e.get("name") for e in envs["environments"]]
        add("Deployments", "Protected environments",
            f"/repos/{owner}/{repo}/environments",
            ", ".join(env_names) if env_names else "none",
            risk_level=risk(bool(env_names), when_true="Low", when_false="Informational"))
    else:
        add("Deployments", "Protected environments",
            f"/repos/{owner}/{repo}/environments",
            "unavailable", notes=f"{code}: {err}", risk_level="Unknown")

    # 6) Dependency/SBOM (may require permissions; works for many public repos)
    sbom, code, err = safe_get_json(f"{API_ROOT}/repos/{owner}/{repo}/dependency-graph/sbom")
    if sbom and isinstance(sbom, dict):
        dep_count = len(sbom.get("sbom", {}).get("packages", []))
        add("Dependencies", "SBOM packages",
            f"/repos/{owner}/{repo}/dependency-graph/sbom",
            str(dep_count), risk_level="Informational")
    else:
        add("Dependencies", "SBOM packages",
            f"/repos/{owner}/{repo}/dependency-graph/sbom",
            "unavailable", notes=f"{code}: {err}", risk_level="Unknown")

    # 7) Code scanning alerts (public visibility varies by repo)
    alerts, code, err = safe_get_json(f"{API_ROOT}/repos/{owner}/{repo}/code-scanning/alerts?per_page=100")
    if isinstance(alerts, list):
        add("Scanning", "Code scanning alerts (count)",
            f"/repos/{owner}/{repo}/code-scanning/alerts",
            str(len(alerts)),
            risk_level=risk(len(alerts) == 0, when_true="Low", when_false="Medium"))
    else:
        add("Scanning", "Code scanning alerts",
            f"/repos/{owner}/{repo}/code-scanning/alerts",
            "unavailable", notes=f"{code}: {err}", risk_level="Unknown")

    # 8) Secret scanning alerts (usually requires org/repo permissions)
    secrets, code, err = safe_get_json(f"{API_ROOT}/repos/{owner}/{repo}/secret-scanning/alerts?per_page=100")
    if isinstance(secrets, list):
        add("Scanning", "Secret scanning alerts (count)",
            f"/repos/{owner}/{repo}/secret-scanning/alerts",
            str(len(secrets)),
            risk_level=risk(len(secrets) == 0, when_true="Low", when_false="High"))
    else:
        add("Scanning", "Secret scanning alerts",
            f"/repos/{owner}/{repo}/secret-scanning/alerts",
            "unavailable", notes=f"{code}: {err}", risk_level="Unknown")

    # 9) Dependabot alerts (often requires security_events scope)
    deps, code, err = safe_get_json(f"{API_ROOT}/repos/{owner}/{repo}/dependabot/alerts?per_page=100")
    if isinstance(deps, list):
        add("Dependencies", "Dependabot alerts (count)",
            f"/repos/{owner}/{repo}/dependabot/alerts",
            str(len(deps)),
            risk_level=risk(len(deps) == 0, when_true="Low", when_false="Medium-High"))
    else:
        add("Dependencies", "Dependabot alerts",
            f"/repos/{owner}/{repo}/dependabot/alerts",
            "unavailable", notes=f"{code}: {err}", risk_level="Unknown")

    # 10) Commit verification (sample recent commit on default branch)
    commits, code, err = safe_get_json(f"{API_ROOT}/repos/{owner}/{repo}/commits?sha={quote(default_branch)}&per_page=1")
    if isinstance(commits, list) and commits:
        v = commits[0].get("commit", {}).get("verification") or commits[0].get("verification")
        verified = v.get("verified") if isinstance(v, dict) else commits[0].get("verification", {}).get("verified")
        add("Commits", "Latest commit verified",
            f"/repos/{owner}/{repo}/commits",
            str(bool(verified)),
            risk_level=risk(bool(verified), when_true="Low", when_false="Medium"))
    else:
        add("Commits", "Latest commit verified",
            f"/repos/{owner}/{repo}/commits",
            "unavailable", notes=f"{code}: {err}", risk_level="Unknown")

    # 11) Collaborator/permission surface (only returns with access; otherwise unavailable)
    collabs, code, err = safe_get_json(f"{API_ROOT}/repos/{owner}/{repo}/collaborators?per_page=1")
    if isinstance(collabs, list):
        add("Access Control", "Collaborators endpoint",
            f"/repos/{owner}/{repo}/collaborators",
            "accessible", risk_level="Informational")
    else:
        add("Access Control", "Collaborators endpoint",
            f"/repos/{owner}/{repo}/collaborators",
            "unavailable", notes=f"{code}: {err}", risk_level="Unknown")

    # Write CSV
    fieldnames = ["Category", "Insight", "API Endpoint", "Value", "Risk", "Notes"]
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    return out_csv


def _parse_owner_repo_args(argv):
    """Accept either 'owner repo' or 'owner/repo' and optional output path.

    Returns (owner, repo, out_csv or None).
    """
    owner = None
    repo = None
    out_csv = None

    # argv[0] is script name
    if len(argv) >= 2:
        arg1 = argv[1].strip()
        if "/" in arg1:
            parts = arg1.split("/", 1)
            owner, repo = parts[0].strip(), parts[1].strip()
            if len(argv) >= 3:
                out_csv = argv[2].strip() or None
        else:
            if len(argv) >= 3:
                owner, repo = arg1, argv[2].strip()
                if len(argv) >= 4:
                    out_csv = argv[3].strip() or None
    return owner, repo, out_csv


if __name__ == "__main__":
    # Usage examples:
    #   python gh_sec.py pytorch/pytorch [output.csv]
    #   python gh_sec.py pytorch pytorch [output.csv]
    owner, repo, out_csv = _parse_owner_repo_args(sys.argv)
    if not owner or not repo:
        sys.exit("Usage: gh_sec.py <owner/repo | owner repo> [output.csv]")

    try:
        path = generate_security_checklist(owner, repo, out_csv=out_csv)
        print(f"Wrote security checklist to {path}")
    except SystemExit:
        raise
    except Exception as e:
        sys.exit(f"Failed generating security checklist: {e}")
