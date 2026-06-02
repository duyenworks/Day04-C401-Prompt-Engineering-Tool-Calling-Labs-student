# trending

Returns trending topics on X/Twitter for a country or worldwide.

## Args
- `country` (str, default `"worldwide"`) — country name in English, e.g. `"Vietnam"`, `"United States"`, `"worldwide"`
- `limit` (int, default `10`) — number of trends to return

## Returns
`items` list with `title`, `url` (search link), `tweet_volume`.

## Related tools
- `social_search` — search tweets about a trending topic
- `timeline` — get a specific account's recent posts
