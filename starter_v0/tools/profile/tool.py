from __future__ import annotations

import os
from typing import Any

import requests

from tools._shared import TIMEOUT, err


def get_user_profile(screenname: str = "") -> dict[str, Any]:
    """Return public profile info for a Twitter/X account."""
    try:
        key = os.getenv("RAPIDAPI_KEY")
        host = os.getenv("RAPIDAPI_TWITTER_HOST", "twitter-api45.p.rapidapi.com")
        if not key:
            raise RuntimeError("Missing RAPIDAPI_KEY env var")

        response = requests.get(
            f"https://{host}/screenname.php",
            params={"screenname": screenname},
            headers={"x-rapidapi-key": key, "x-rapidapi-host": host},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        raw = response.json()

        profile_url = f"https://x.com/{screenname}"
        name = raw.get("name") or screenname
        bio = (raw.get("desc") or raw.get("description") or "").strip()
        followers = raw.get("sub_count") or raw.get("followers_count") or raw.get("followers")
        following = raw.get("friends_count") or raw.get("following")
        tweet_count = raw.get("statuses_count") or raw.get("tweet_count")
        verified = raw.get("blue_verified") or raw.get("verified") or False
        location = raw.get("location") or ""
        avatar = raw.get("avatar") or ""

        return {
            "tool": "profile",
            "screenname": screenname,
            "items": [{
                "title": f"@{screenname} — {name}",
                "url": profile_url,
                "source": f"@{screenname}",
                "summary": bio or f"X profile of @{screenname}",
                "name": name,
                "bio": bio,
                "location": location,
                "followers": followers,
                "following": following,
                "tweet_count": tweet_count,
                "verified": verified,
                "avatar": avatar,
            }],
        }
    except Exception as exc:
        return err("profile", exc)
