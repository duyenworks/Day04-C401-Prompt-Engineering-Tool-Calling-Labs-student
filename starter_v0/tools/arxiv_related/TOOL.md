# arxiv_related

Given an arXiv paper ID or URL, find related recent papers in the same category.

## Args
- `arxiv_url` (str, required) — arXiv ID (`2401.12345`) or full URL
- `max_results` (int, default `5`) — number of related papers to return

## Returns
`items` list of related papers with `arxiv_id`, `title`, `summary`, `authors`, `url`, `pdf_url`.
Also returns `source_title` and `category` of the input paper.

## Related tools
- `papers` — search arXiv by keyword first
- `paper_text` — read the full text of a specific paper
- `summarize` — condense key points from multiple papers
