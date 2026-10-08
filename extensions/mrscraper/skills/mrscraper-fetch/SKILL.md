---
name: mrscraper-fetch
description: |
  Retrieve raw HTML from a known public URL with MrScraper. Use for reading, inspecting, summarizing, archiving, or analyzing a page, and as the default content-acquisition step before agent-led or local extraction. Supports browser rendering, real-device Super Mode, and page-load controls; use mrscraper-serp when no target URL is known.
---

# Fetch Page Content with MrScraper MCP

Use the fetch tool supplied by the MrScraper MCP server for the first exploration
whenever the user already has a public URL. Keep using the raw response for
summarization, comparison, transformation, and structured output instead of
handing the page to another LLM by default. Use
[mrscraper](../mrscraper/SKILL.md) for connection and authentication checks,
saved runs, account status, or broader routing.

## Page Retrieval Context

fetch calls MrScraper's
[page-fetching service](https://docs.mrscraper.com/docs/features/unblocker) once.
Browser rendering executes page JavaScript, locale routing selects a
geo-specific country, selector waits allow delayed content to appear, and
homepage navigation establishes a normal navigation path before loading the
target. Super Mode selects real-device routing independently of browser
rendering.

Use fetch only for content the user is authorized to access and in accordance
with the site's requirements. Page-loading controls can help render a site that
does not work with a basic request.

Start with the URL alone and add only the controls the target needs. Plan-token
usage is based on runtime and bandwidth: one token per 30 seconds and one token
per 0.2 MB, rounded up per component. Resource blocking can reduce bandwidth
for text-focused pages. Retries stop when the request succeeds, max_retries is
reached, or the running token total reaches token_cap. The initial request
always runs even when it exceeds that cap. See the
[Token Plan](https://docs.mrscraper.com/docs/getting-started/api-token) for the
maintained calculation.

## Step 1 — Define the Outcome

Confirm the target URL and what the user wants:

- Preserve a raw source before extraction, transformation, or comparison.
- Read, summarize, cite, or inspect the page.
- Check whether specific text appears.
- Archive the response.
- Produce fields, JSON, tables, or other structured output with local logic.
- Verify or supplement a managed scrape or saved result.
- Load JavaScript-rendered or geo-sensitive content.

Do not call scrape merely because the requested output is structured. Fetch the
page, understand its layout, and transform the saved raw content locally. Use
[mrscraper-scrape](../mrscraper-scrape/SKILL.md) only when the user explicitly
requests managed extraction, or after fetch-led exploration has produced a
stable output schema and managed extraction still offers a concrete benefit.
Use [mrscraper-serp](../mrscraper-serp/SKILL.md) when discovery must happen
first.

### Prefer reusable local extraction

When many pages share a layout:

1. Fetch representative pages and inspect their raw content.
2. Define one local extraction schema and implementation.
3. Fetch the remaining pages, in parallel when safe and proportional.
4. Apply the same local extractor to every saved response.

For roughly 100 same-layout pages, concurrent fetches followed by one local
batch extraction are often faster than 100 separate backend-LLM extractions.
This also preserves every raw input for later recovery or schema changes.

## Step 2 — Run the Fetch

The client may namespace the tool name; select fetch from the MrScraper MCP
provider. Start with one call containing only the required URL:

    {
      "url": "https://www.scrapethissite.com/pages/simple/"
    }

The result is available in MCP structuredContent and as formatted JSON text:

    {
      "status_code": 200,
      "data": "<html>...</html>",
      "headers": {
        "content-type": "text/html"
      }
    }

Prefer structuredContent. Check isError, error, and status_code before using
data. Non-JSON page bodies are preserved exactly.

## Step 3 — Choose Page-Loading Options

browser_rendering and super_mode are independent axes. All four combinations
can return different content or failures for the same URL:

| browser_rendering | super_mode | Loading path |
| --- | --- | --- |
| false | false | Standard routing with the non-browser loader. |
| true | false | Standard routing with browser loading and JavaScript. |
| false | true | Real-device routing with the non-browser loader. |
| true | true | Real-device routing with browser loading and JavaScript. |

Use browser rendering when the page depends on JavaScript:

    {
      "url": "https://www.scrapethissite.com/pages/ajax-javascript/#2015",
      "browser_rendering": true
    }

Use Super Mode with the non-browser loader when routing may be the problem but
browser loading is unnecessary or returns a worse response:

    {
      "url": "https://www.scrapethissite.com/pages/simple/",
      "super_mode": true
    }

Use both controls for real-device browser loading:

    {
      "url": "https://www.scrapethissite.com/pages/ajax-javascript/#2015",
      "browser_rendering": true,
      "super_mode": true
    }

Browser rendering is not a strictly stronger mode. Some sites fail or return
worse content with browser_rendering=true but load successfully when it is
false. Super Mode does not enable browser rendering.

Wait for delayed content with a CSS selector:

    {
      "url": "https://www.scrapethissite.com/pages/ajax-javascript/#2015",
      "browser_rendering": true,
      "wait_for_selector": ".film"
    }

Use geographic routing or homepage navigation when the target requires it:

    {
      "url": "https://www.scrapethissite.com/pages/simple/",
      "browser_rendering": true,
      "geo_code": "ID",
      "home_page": true
    }

Use geographic routing for geo-specific content.

Bound resource use for a browser-rendered page:

    {
      "url": "https://www.scrapethissite.com/pages/ajax-javascript/#2015",
      "browser_rendering": true,
      "block_resources": true,
      "max_retries": 3,
      "token_cap": 10000,
      "timeout": 60
    }

### Parameters

| MCP input | Default | Request mapping | Use |
| --- | --- | --- | --- |
| url | required | Query url | Absolute HTTP or HTTPS target URL. |
| browser_rendering | false | Query browserRendering | Execute page JavaScript. |
| super_mode | false | Query super | Select real-device routing independently of browser rendering. |
| geo_code | omitted | Query geoCode | Route through an ISO 3166-1 alpha-2 country. |
| wait_for_selector | omitted | Query waitForSelector | Wait for a CSS selector; requires browser_rendering=true. |
| home_page | false | Query homePage | Visit the site root before the target page. |
| block_resources | false | Query blockResources | Block nonessential resources during loading. |
| max_retries | 3 | Query maxRetries | Maximum retries after failure; zero disables retries. |
| token_cap | omitted | Query tokenCap | Retry token budget; the initial request still runs. |
| timeout | 30 | Query timeout | Page-load timeout in seconds; transport receives another 30 seconds. |

Authentication is handled by the MCP client's OAuth 2.1 connection and is
never a tool input.

## Step 4 — Inspect and Retry Deliberately

Start with both controls false unless the task already establishes a
requirement. If the response fails, is blocked, incomplete, or missing dynamic
content:

1. Inspect the initial response.
2. Change one axis at a time: browser_rendering for JavaScript, or super_mode
   when routing may be the problem.
3. If browser loading fails or returns worse content, retry the same super_mode
   value with browser_rendering=false.
4. Try the remaining untested combinations when the response is still unusable.
5. Add wait_for_selector, geo_code, or home_page only when evidence shows that
   the target requires it.
6. Stop after a usable response unless the user requests a comparison.

Do not repeat an identical combination. Treat wait_for_selector as a CSS
selector, not a duration. Browser rendering loads a page; it does not click
controls, submit forms, or provide an authenticated interactive browser
session.

## Step 5 — Deliver the Result

Answer the user's request from data. Keep the full envelope when headers or
diagnostics matter. When the user requests an archive, save the successful
response or its data value with the environment's local file-writing
capability; fetch itself has no output-path input.

Keep fetched content as the source of truth for later steps. Build summaries,
tables, JSON transformations, and extraction scripts from that raw content. If
fetch fails and another MrScraper workflow can still complete the task, disclose
that the raw response was not preserved and do not present the narrower result
as exhaustive source content.
