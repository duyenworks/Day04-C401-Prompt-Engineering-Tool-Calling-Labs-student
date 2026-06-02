# summarize

Extracts and ranks the most relevant sentences from a list of items (from `lookup`, `fetch`, `papers`, `paper_text`, etc.) using keyword overlap scoring. No LLM call — fast and deterministic.

## Args
- `items` (list, required) — array of items from another tool's result
- `focus` (str, default `""`) — optional topic/angle to score sentences toward
- `max_points` (int, default `5`) — number of key points to extract
- `style` (str, default `"bullets"`) — `"bullets"` or `"numbered"`

## Returns
`key_points` list of `{point, source}` dicts, plus `markdown` ready for display.

## Related tools
- `lookup` — web search results to summarize
- `fetch` — page content to summarize
- `papers` / `paper_text` — academic paper content to summarize
- `format` — if you want a fully structured digest instead
