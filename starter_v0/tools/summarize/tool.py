from __future__ import annotations

import re
from typing import Any

from tools._shared import err


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if len(p.strip()) > 30]


def _score(sentence: str, query_terms: set[str]) -> float:
    words = set(re.findall(r"[a-z]+", sentence.lower()))
    overlap = len(words & query_terms)
    length_bonus = min(len(sentence) / 200, 1.0)
    return overlap + length_bonus


def summarize_items(
    items: list[dict[str, Any]] | None = None,
    focus: str = "",
    max_points: int = 5,
    style: str = "bullets",
) -> dict[str, Any]:
    """Extract the most relevant key points from a list of items (from lookup, fetch, paper_text, etc.).

    Performs extractive sentence scoring — no LLM call needed.
    """
    try:
        items = items or []
        if not items:
            return {"tool": "summarize", "focus": focus, "key_points": [], "markdown": "No items to summarize."}

        max_points = max(1, min(int(max_points or 5), 20))
        query_terms = set(re.findall(r"[a-z]+", focus.lower())) if focus else set()

        scored: list[tuple[float, str, str]] = []
        for item in items:
            source = item.get("source") or item.get("url") or ""
            url = item.get("url") or ""
            text = item.get("summary") or item.get("title") or ""
            for sentence in _sentences(text):
                score = _score(sentence, query_terms)
                scored.append((score, sentence, f"[{source}]({url})" if url else source))

        scored.sort(key=lambda x: x[0], reverse=True)

        # Deduplicate: drop sentences that share >60 % words with an already-selected one
        selected: list[tuple[str, str]] = []
        seen_word_sets: list[set[str]] = []
        for _, sentence, src in scored:
            words = set(re.findall(r"[a-z]+", sentence.lower()))
            if any(len(words & seen) / max(len(words), 1) > 0.6 for seen in seen_word_sets):
                continue
            selected.append((sentence, src))
            seen_word_sets.append(words)
            if len(selected) >= max_points:
                break

        key_points = [{"point": s, "source": src} for s, src in selected]

        if style == "numbered":
            lines = [f"{i+1}. {p['point']} — {p['source']}" for i, p in enumerate(key_points)]
        else:
            lines = [f"- {p['point']} — {p['source']}" for p in key_points]

        header = f"**Key points{': ' + focus if focus else ''}**\n\n" if key_points else ""
        markdown = header + "\n".join(lines)

        return {
            "tool": "summarize",
            "focus": focus,
            "style": style,
            "key_points": key_points,
            "markdown": markdown,
            "source_item_count": len(items),
        }
    except Exception as exc:
        return err("summarize", exc)
