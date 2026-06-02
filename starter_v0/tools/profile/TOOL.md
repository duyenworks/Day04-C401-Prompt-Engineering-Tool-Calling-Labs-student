# profile

Returns public profile information for a Twitter/X account.

## Args
- `screenname` (str, required) — account handle without `@`

## Returns
`items` list with one entry: `name`, `bio`, `location`, `followers`, `following`, `tweet_count`, `verified`, `avatar`.

## Related tools
- `timeline` — get the user's recent tweets after verifying they exist
- `social_search` — find tweets mentioning the user
