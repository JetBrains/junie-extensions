# mrscraper

Retrieve web pages as HTML, Markdown, or screenshots, search the web, and check
account usage with MrScraper's hosted MCP server.

The included skills keep the retrieved page as the source for summaries and
local extraction, and route query-first tasks through web search before
retrieving the selected pages.

## Contents

- `mcp/.mcp.json`: the hosted MrScraper MCP server,
  `https://mcp.mrscraper.com/mcp` (Streamable HTTP, OAuth 2.1). It exposes
  three tools: `scraperAPI` (a page as HTML, Markdown, a screenshot, or a
  combination), `webSearch` (ranked web search results), and `status` (plan
  and token usage).
- `skills/`: `mrscraper` (connection, routing, account status, and
  troubleshooting), `mrscraper-fetch`, and `mrscraper-serp`.

## Connect

A MrScraper account is required. Sign up at <https://app.mrscraper.com>.

1. Install the extension, then run `/mcp`.
2. `mrscraper` is listed with the status **Authorization required**. Select it,
   choose **Authorize**, sign in to MrScraper in the browser page that opens,
   and approve access.
3. Confirm that the status changes to **Active**.

Try: `Fetch https://www.scrapethissite.com/pages/simple/ and summarize the page.`

## Data handling

Page retrieval and web search contact external websites through MrScraper. The
service receives target URLs, search queries, and request options; results
return to Junie for your task. Use third-party sources only where you have
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
