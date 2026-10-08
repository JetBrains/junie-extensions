# mrscraper

Web scraping, structured data extraction, and Google search for AI assistants.

Connect your agent to MrScraper for raw page fetching, managed structured
extraction, Google discovery, and reusable saved scraper workflows. The
included skills preserve source responses with a fetch-first workflow before
adding backend extraction when it is explicitly requested or clearly useful.

## Contents

- `mcp/.mcp.json`: the hosted MrScraper MCP server,
  `https://mcp.mrscraper.com/mcp` (Streamable HTTP, OAuth 2.1). It exposes
  seven tools: `fetch`, `scrape`, `serp`, `rerun`, `results`, `result`, and
  `status`.
- `skills/`: `mrscraper` (connection, routing, saved runs, results, account),
  `mrscraper-fetch`, `mrscraper-scrape`, and `mrscraper-serp`.

## Connect

A MrScraper account is required. Sign up at <https://app.mrscraper.com>.

1. Install the extension, then run `/mcp`.
2. `mrscraper` is listed with the status **Authorization required**. Select it,
   choose **Authorize**, sign in to MrScraper in the browser page that opens,
   and approve access.
3. Confirm that the status changes to **Active**.

Try: `Fetch https://www.scrapethissite.com/pages/simple/ and summarize the page.`

## Data handling

Fetching, extraction, search, and reruns contact external websites through
MrScraper. The service receives target URLs and tool inputs, including
extraction instructions; results return to Junie for your task. Managed general
and listing extraction sends page content and the extraction prompt to a
backend language model and saves a reusable scraper configuration; reruns
create new stored results. Use third-party sources only where you have
authorization and comply with their terms. The extension contains no
credentials.

## Links

- Documentation: <https://docs.mrscraper.com/docs/getting-started/mcp-server>
- Support: <https://mrscraper.com/support> · support@mrscraper.com
- Privacy policy: <https://mrscraper.com/privacy-policy>
- Acceptable use policy: <https://mrscraper.com/acceptable-use-policy>
- Terms of use: <https://mrscraper.com/terms-of-use>

## License

MIT. See [LICENSE](LICENSE). The skills are maintained in
<https://github.com/mrscraper-com/mrscraper-claude-plugin>
(`plugins/mrscraper/skills`).
