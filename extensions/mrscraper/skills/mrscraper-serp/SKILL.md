---
name: mrscraper-serp
description: |
  Discover public pages through web search with MrScraper's webSearch tool. Use when no target URL is known or the user asks to inspect web search results. After discovery, retrieve selected pages with mrscraper-fetch.
---

# Discover Pages with MrScraper MCP Web Search

Use the webSearch tool supplied by the MrScraper MCP server when a task begins
with a search query rather than a known target URL. Use
[mrscraper](../mrscraper/SKILL.md) for connection troubleshooting, account
status, or broader routing.

## Step 1 — Build the Query

Pass the query in url. Include the important entity, attribute, location, or
date:

    {
      "url": "web scraping best practices"
    }

The input can also be a search results URL; its q parameter becomes the query.

## Step 2 — Set the Country and Result Count

Set region to a two-letter country code when results must come from one
country. It defaults to us:

    {
      "url": "running shoes",
      "region": "id"
    }

The search returns 10 results by default. Ask for more, up to 100, only when
the user needs broader coverage:

    {
      "url": "running shoes",
      "region": "id",
      "num_results": 30
    }

### Parameters

| MCP input | Default | Request mapping | Use |
| --- | --- | --- | --- |
| url | required | Body query | Search query, or a search results URL whose q value is used. |
| region | us | Body country | Two-letter result country, such as us or id. |
| num_results | 10 | Body numResults | Number of results, from 10 to 100; fewer may come back. |
| timeout | 600 | MCP upstream deadline | Maximum wait in seconds; not sent in the search body. |

Authentication is handled by the MCP client's OAuth 2.1 connection and is
never a tool input.

## Step 3 — Inspect the Results

The complete response envelope is available in MCP structuredContent and as
formatted JSON text. Prefer structuredContent. Check isError, error, and
status_code before using data. The results are a ranked list in data.data;
each result has rank, title, url, description, and source.

When the user requests a search artifact, save the successful data or full
envelope with local file-writing capability; webSearch has no output-path
input.

## Step 4 — Continue with Relevant URLs

Select only URLs relevant to the user's goal, then load
[mrscraper-fetch](../mrscraper-fetch/SKILL.md) to retrieve and inspect each
selected page before deriving answers, comparisons, or structured output.

Run independent follow-up URLs in parallel when the environment supports safe
parallel execution. Keep the number of pages proportional to the requested
coverage. If the user only requested URL discovery, stop after the search.

## Step 5 — Handle Weak or Missing Results

- Set region when the results come from the wrong country.
- Rewrite noisy queries around the important entity, attribute, and location.
- Raise num_results only after checking the first results.
- Increase timeout when the MCP request deadline is too short.
- Use [mrscraper](../mrscraper/SKILL.md) when the connection or authentication
  fails.

webSearch is for public web search, not for discovering URLs within one
known site.
