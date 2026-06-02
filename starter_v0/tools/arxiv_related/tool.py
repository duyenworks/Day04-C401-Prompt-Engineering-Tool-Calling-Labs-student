from __future__ import annotations

import re
import time
import xml.etree.ElementTree as ET
from typing import Any

import requests

from tools._shared import TIMEOUT, err


ARXIV_API_URL = "https://export.arxiv.org/api/query"
ARXIV_MIN_INTERVAL_SECONDS = 3.0
_last_request_at = 0.0


def _rate_limit() -> None:
    global _last_request_at
    elapsed = time.monotonic() - _last_request_at
    if elapsed < ARXIV_MIN_INTERVAL_SECONDS:
        time.sleep(ARXIV_MIN_INTERVAL_SECONDS - elapsed)
    _last_request_at = time.monotonic()


def _arxiv_id(value: str) -> str:
    match = re.search(r"(\d{4}\.\d{4,5}(?:v\d+)?)", value or "")
    if not match:
        raise ValueError(f"Cannot extract arXiv ID from: {value!r}")
    return match.group(1)


def _entry_text(entry: ET.Element, path: str, ns: dict) -> str:
    node = entry.find(path, ns)
    return (node.text or "").strip() if node is not None and node.text else ""


def find_related_papers(arxiv_url: str = "", max_results: int = 5) -> dict[str, Any]:
    """Given an arXiv paper ID or URL, find related papers in the same category."""
    try:
        arxiv_id = _arxiv_id(arxiv_url)
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
            "arxiv": "http://arxiv.org/schemas/atom",
        }

        # Step 1: fetch the source paper's primary category and title
        _rate_limit()
        resp = requests.get(
            ARXIV_API_URL,
            params={"id_list": arxiv_id},
            headers={"User-Agent": "AI20k-Day04-Research-Agent/1.0"},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
        entries = root.findall(".//atom:entry", ns)
        if not entries:
            raise ValueError(f"arXiv paper not found: {arxiv_id}")

        source = entries[0]
        source_title = _entry_text(source, "./atom:title", ns).replace("\n", " ")
        primary_cat = source.find("./arxiv:primary_category", ns)
        category = primary_cat.get("term") if primary_cat is not None else None

        # Step 2: search by primary category + keywords from title
        keywords = " ".join(
            w for w in re.findall(r"[A-Za-z]{4,}", source_title)
            if w.lower() not in {"with", "from", "this", "that", "using", "based", "toward", "towards", "novel"}
        )[:80]

        search_q = f"cat:{category}" if category else keywords or f"all:{arxiv_id}"
        if keywords and category:
            search_q = f"cat:{category} AND all:{keywords.split()[0]}"

        _rate_limit()
        max_results = max(1, min(int(max_results or 5), 10))
        resp2 = requests.get(
            ARXIV_API_URL,
            params={"search_query": search_q, "max_results": max_results + 1, "sortBy": "submittedDate", "sortOrder": "descending"},
            headers={"User-Agent": "AI20k-Day04-Research-Agent/1.0"},
            timeout=TIMEOUT,
        )
        resp2.raise_for_status()
        root2 = ET.fromstring(resp2.text)

        items: list[dict[str, Any]] = []
        for entry in root2.findall(".//atom:entry", ns):
            eid = _arxiv_id(_entry_text(entry, "./atom:id", ns))
            if eid == arxiv_id:
                continue  # skip the source paper itself
            summary = " ".join(_entry_text(entry, "./atom:summary", ns).replace("\n", " ").split())
            items.append({
                "arxiv_id": eid,
                "title": _entry_text(entry, "./atom:title", ns).replace("\n", " "),
                "summary": summary,
                "authors": [_entry_text(a, "./atom:name", ns) for a in entry.findall("./atom:author", ns)],
                "published": _entry_text(entry, "./atom:published", ns),
                "url": f"https://arxiv.org/abs/{eid}",
                "pdf_url": f"https://arxiv.org/pdf/{eid}.pdf",
                "source": "arxiv.org",
            })
            if len(items) >= max_results:
                break

        return {
            "tool": "arxiv_related",
            "source_arxiv_id": arxiv_id,
            "source_title": source_title,
            "category": category,
            "items": items,
        }
    except Exception as exc:
        return err("arxiv_related", exc)
