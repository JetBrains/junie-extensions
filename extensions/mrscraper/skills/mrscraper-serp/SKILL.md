---
name: mrscraper-serp
description: |
  Discover public pages through Google with MrScraper using a search query or Google search URL. Use when no target URL is known or the user asks to inspect Google results. After discovery, preserve selected pages with mrscraper-fetch before adding managed extraction through mrscraper-scrape.
---

# Discover Pages with MrScraper MCP SERP

Use the serp tool supplied by the MrScraper MCP server when a task begins with
a search query rather than a known target URL. Use
[mrscraper](../mrscraper/SKILL.md) for connection troubleshooting, saved runs,
account status, or broader routing.

## Step 1 — Build the Query

Include the important entity, attribute, location, or date in query_or_url:

    {
      "query_or_url": "web scraping best practices"
    }

The input can also be a complete Google search URL:

    {
      "query_or_url": "https://www.google.com/search?q=web+scraping&gl=us&hl=en&start=20"
    }

For a Google URL, the tool reads q, gl, hl, and start. Explicit region,
language, and page inputs take precedence.

## Step 2 — Set Locale and Pagination

Set both country and language when results must match a locale:

    {
      "query_or_url": "running shoes",
      "region": "id",
      "language": "id",
      "page": 2
    }

Start with the first page unless the user requests broader coverage. Inspect
the current page before requesting another.

## Step 3 — Choose the Output

Parsed JSON is the default and is suitable for selecting titles, URLs, and
snippets:

    {
      "query_or_url": "iphone 17",
      "format": "json"
    }

Request result-page HTML when the page itself is needed:

    {
      "query_or_url": "iphone 17",
      "format": "html"
    }

Use JavaScript rendering for dynamic result features such as AI Overview:

    {
      "query_or_url": "what is web scraping",
      "render_js": true
    }

### Parameters

| MCP input | Default | Request mapping | Use |
| --- | --- | --- | --- |
| query_or_url | required | Body query | Search query or complete Google search URL. |
| region | URL value or omitted | Body region | Google result country, such as us or id. |
| language | URL value or omitted | Body language | Google result language, such as en or id. |
| page | URL value or omitted | Body page | Positive, one-based results page. |
| format | json | Body format | Return parsed JSON or result-page HTML. |
| render_js | false | Body renderJs | Wait for JavaScript-rendered result features. |
| raw | false | Body format=html | Deprecated compatibility alias; prefer format=html. |
| client_timeout | 120 | MCP upstream deadline | Maximum wait in seconds; not sent in the SERP body. |

Authentication is handled by the MCP client's OAuth 2.1 connection and is
never a tool input.

## Step 4 — Inspect the Results

The complete response envelope is available in MCP structuredContent and as
formatted JSON text. Prefer structuredContent. Check isError, error, and
status_code before using data.

For format=json, inspect data for the available titles, URLs, snippets, and
other result fields. For format=html, data contains result-page HTML.

When the user requests a search artifact, save the successful data or full
envelope with local file-writing capability; serp has no output-path input.

## Step 5 — Continue with Relevant URLs

Select only URLs relevant to the user's goal, then:

- Load [mrscraper-fetch](../mrscraper-fetch/SKILL.md) to preserve and inspect
  each selected page before deriving answers, comparisons, or structured output.
- Add [mrscraper-scrape](../mrscraper-scrape/SKILL.md) only when the user
  explicitly requests managed extraction or it still offers a clear benefit
  after the page structure and output schema are understood.

Run independent follow-up URLs in parallel when the environment supports safe
parallel execution. Keep the number of pages proportional to the requested
coverage.

## Step 6 — Handle Weak or Missing Results

- Set both region and language when the locale is wrong.
- Rewrite noisy queries around the important entity, attribute, and location.
- Request another result page only after checking the current page.
- Retry once with render_js=true when a dynamic result feature is required.
- Increase client_timeout when the MCP request deadline is too short.
- Use [mrscraper](../mrscraper/SKILL.md) when the connection or authentication
  fails.

SERP is for public Google discovery. Use the map agent in
[mrscraper-scrape](../mrscraper-scrape/SKILL.md) to discover URLs within one
known site.
