from __future__ import annotations

import os
from typing import Any

import requests

from tools._shared import TIMEOUT, err


def get_trending_topics(country: str = "worldwide", limit: int = 10) -> dict[str, Any]:
    """Return trending topics on X/Twitter for a given country."""
    try:
        key = os.getenv("RAPIDAPI_KEY")
        host = os.getenv("RAPIDAPI_TWITTER_HOST", "twitter-api45.p.rapidapi.com")
        if not key:
            raise RuntimeError("Missing RAPIDAPI_KEY env var")

        response = requests.get(
            f"https://{host}/trends.php",
            params={"country": country},
            headers={"x-rapidapi-key": key, "x-rapidapi-host": host},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        raw_trends = data.get("trends") or data.get("data") or []
        items: list[dict[str, Any]] = []
        for trend in raw_trends[: max(1, int(limit or 10))]:
            name = trend.get("name") or trend.get("trend") or trend.get("query") or ""
            tweet_volume = trend.get("tweet_volume") or trend.get("tweetVolume") or trend.get("count")
            items.append({
                "title": name,
                "summary": name,
                "url": f"https://x.com/search?q={requests.utils.quote(name)}&f=live",
                "source": "x.com/trends",
                "tweet_volume": tweet_volume,
            })

        return {
            "tool": "trending",
            "country": country,
            "items": items,
        }
    except Exception as exc:
        return err("trending", exc)
