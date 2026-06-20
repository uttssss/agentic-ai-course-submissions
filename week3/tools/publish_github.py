"""Publish a markdown post to a GitHub Pages repo via the Contents API."""
from __future__ import annotations

import base64
import json

import requests

from ..config.settings import settings


def publish_post(
    content: str,
    filepath: str,
    commit_message: str,
) -> str:
    """Commit content to settings.github_pages_repo at filepath.

    Returns the GitHub Pages URL for the published file.
    Raises RuntimeError if the commit fails.
    """
    repo = settings.github_pages_repo
    if not repo:
        raise RuntimeError("GITHUB_PAGES_REPO is not configured.")
    if not settings.github_token:
        raise RuntimeError("GITHUB_TOKEN is not configured.")

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {settings.github_token}",
    }
    url = f"https://api.github.com/repos/{repo}/contents/{filepath}"

    # Check if file already exists (needed for sha to update)
    sha = None
    check = requests.get(url, headers=headers, timeout=10)
    if check.status_code == 200:
        sha = check.json().get("sha")

    payload: dict = {
        "message": commit_message,
        "content": base64.b64encode(content.encode()).decode(),
    }
    if sha:
        payload["sha"] = sha

    resp = requests.put(url, headers=headers, data=json.dumps(payload), timeout=15)
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"GitHub commit failed ({resp.status_code}): {resp.text}")

    # Derive the rendered GitHub Pages URL for a Jekyll _posts/ file.
    # Filename format: _posts/YYYY-MM-DD-slug.md → /YYYY/MM/DD/slug/
    owner, repo_name = repo.split("/", 1)
    basename = filepath.split("/")[-1].replace(".md", "")
    parts = basename.split("-", 3)  # ["YYYY", "MM", "DD", "slug..."]
    if len(parts) == 4:
        year, month, day, slug = parts
        return f"https://{owner}.github.io/{repo_name}/{year}/{month}/{day}/{slug}/"
    return f"https://github.com/{owner}/{repo_name}/blob/main/{filepath}"
