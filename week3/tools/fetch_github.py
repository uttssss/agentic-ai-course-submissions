"""Fetch content from a GitHub repository via the Contents API."""
from __future__ import annotations

import base64

import requests

from ..config.settings import settings


def fetch_github_readme(repo: str) -> str:
    """Return the decoded README text for owner/repo, or '' on failure."""
    headers = {"Accept": "application/vnd.github+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    for filename in ("README.md", "readme.md", "README.rst", "README"):
        url = f"https://api.github.com/repos/{repo}/contents/{filename}"
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("encoding") == "base64":
                return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
    return ""


def fetch_github_file(repo: str, path: str) -> str:
    """Return decoded text of a specific file in owner/repo."""
    headers = {"Accept": "application/vnd.github+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if data.get("encoding") == "base64":
        return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
    return data.get("content", "")
