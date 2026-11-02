---
name: mrscraper-fetch
description: |
  Retrieve a known public URL with MrScraper's scraperAPI tool as HTML, Markdown, a screenshot, or a combination. Use for reading, summarizing, archiving, or analyzing a page and before local extraction; supports automatic browser fallback, real-device routing, proxies, and retries. Use mrscraper-serp when no URL is known.
---

# Retrieve Page Content with MrScraper MCP

Use the scraperAPI tool supplied by the MrScraper MCP server whenever the user
already has a public URL. Keep using the retrieved content for summarization,
comparison, transformation, and structured output. Use
[mrscraper](../mrscraper/SKILL.md) for connection and authentication checks,
account status, or broader routing, and
[mrscraper-serp](../mrscraper-serp/SKILL.md) when discovery must happen first.

## Page Retrieval Context

scraperAPI calls MrScraper's
[page-fetching service](https://docs.mrscraper.com/docs/features/unblocker) once.
Browser rendering executes page JavaScript, geographic routing selects the
proxy country, selector waits let delayed content appear, and homepage
navigation visits the site root before the target. Real-device routing (super)
is independent of browser rendering.

Use scraperAPI only for content the user is authorized to access and in
accordance with the site's requirements.

Start with the URL alone and add only the controls the target needs. Plan-token
usage is based on runtime and bandwidth: one token per 30 seconds and one token
per 0.25 MB, rounded up per component. Resource blocking can reduce bandwidth
for text-focused pages. Retries stop when the request succeeds, max_retries is
reached, or the running token total reaches token_cap. The initial request
always runs even when it exceeds that cap. See the
[Token Plan](https://docs.mrscraper.com/docs/getting-started/api-token) for the
maintained calculation.

## Step 1 — Define the Outcome

Confirm the target URL and what the user wants:

- Read, summarize, cite, or inspect the page.
- Check whether specific text appears.
- Archive the page or capture a screenshot.
- Produce fields, JSON, tables, or other structured output with local logic.
- Load JavaScript-rendered or geo-sensitive content.

When many pages share a layout, retrieve representative pages, define one local
extractor, retrieve the remaining pages in parallel when safe and proportional,
and apply the same extractor to every saved response.

## Step 2 — Retrieve the Page

The client may namespace the tool name; select scraperAPI from the MrScraper
MCP provider. Start with one call containing only the required URL, which
requests HTML:

    {
      "url": "https://www.scrapethissite.com/pages/simple/"
    }

Request Markdown instead of HTML for readable text:

    {
      "url": "https://www.scrapethissite.com/pages/simple/",
      "html": false,
      "markdown": true
    }

The result is available in MCP structuredContent and as formatted JSON text.
The requested representations are in data:

    {
      "status_code": 200,
      "data": {
        "html": "<!DOCTYPE html>...",
        "markdown": null,
        "screenshot": null,
        "token_usage": 3,
        "runtime": 18.02,
        "retry_count": 0,
        "error": null
      },
      "headers": {
        "x-status-code": "200"
      }
    }

Prefer structuredContent. Check isError, error, status_code, and
headers["x-status-code"] (the target page's status) before using data.

A screenshot is a base64 JPEG that can be large. Request it only when the user
needs an image, and save it to a file rather than reading it into the
conversation:

    {
      "url": "https://www.scrapethissite.com/pages/simple/",
      "html": false,
      "screenshot": true
    }

## Step 3 — Choose Page-Loading Options

Omit browser_rendering to let the service choose: it falls back to a browser
automatically when needed. true forces a browser and false disables it.
screenshot=true always uses a browser.

Use real-device routing when routing may be the problem:

    {
      "url": "https://www.scrapethissite.com/pages/simple/",
      "super": true
    }

Wait for delayed content with a CSS selector:

    {
      "url": "https://www.scrapethissite.com/pages/ajax-javascript/#2015",
      "browser_rendering": true,
      "wait_for_selector": ".film"
    }

Use geographic routing or homepage navigation when the target requires it:

    {
      "url": "https://www.scrapethissite.com/pages/simple/",
      "geo_code": "ID",
      "home_page": true
    }

Bound resource use:

    {
      "url": "https://www.scrapethissite.com/pages/ajax-javascript/#2015",
      "block_resources": true,
      "max_retries": 1,
      "token_cap": 10,
      "timeout": 60
    }

### Parameters

| MCP input | Default | Request mapping | Use |
| --- | --- | --- | --- |
| url | required | Body url | Absolute HTTP or HTTPS target URL. |
| html | true | Query html | Request HTML content. |
| markdown | false | Query markdown | Request Markdown content. |
| screenshot | false | Query screenshot | Capture a base64 JPEG; forces browser rendering. |
| browser_rendering | automatic | Query browserRendering | true forces and false disables browser rendering. |
| super | false | Query super | Real-device routing, independent of browser rendering. |
| geo_code | US | Query geoCode | Proxy country, such as US, ID, or SG. |
| proxy_country | omitted | Query proxyCountry | Compatibility country option. |
| use_proxy | true | Query useProxy | Set false to skip the service's configured proxy. |
| proxy | omitted | Query proxy | Custom proxy as username:password@host:port. |
| wait_for_selector | omitted | Query waitForSelector | CSS selector to wait for. |
| home_page | false | Query warmStart | Visit the site root before the target page. |
| block_resources | false | Query blockResources | Block images, CSS, and fonts. |
| bypass_proxy | false | Query bypassProxy | Enable the proxy-bypass behavior. |
| cookie_jar | omitted | Query cookieJar | Cookie configuration string. |
| headers | omitted | Query headers | Target page request headers as an object or JSON string. |
| max_retries | 3 | Body maxRetries | Maximum retries; zero disables retries. |
| token_cap | omitted | Body tokenCap | Running token total that stops further retries. |
| timeout | 120 | Query timeout | Page timeout from 1 to 300 seconds. |
| stream | omitted | Query stream | Ask the API to stream; the response is still returned once. |
| discard_token_secret | empty | Header x-discard-token-secret | Optional upstream header. |

Authentication is handled by the MCP client's OAuth 2.1 connection and is
never a tool input.

## Step 4 — Inspect and Retry Deliberately

Start with the URL alone unless the task already establishes a requirement. If
the response fails, is blocked, incomplete, or missing dynamic content:

1. Inspect status_code, data.error, headers["x-status-code"], and the content.
2. Change one axis at a time: force or disable browser_rendering, or set super
   when routing may be the problem.
3. Add wait_for_selector, geo_code, or home_page only when evidence shows that
   the target requires it.
4. Stop after a usable response unless the user requests a comparison.

Do not repeat an identical request. Treat wait_for_selector as a CSS selector,
not a duration. Browser rendering loads a page; it does not click controls,
submit forms, or provide an authenticated interactive browser session.

## Step 5 — Deliver the Result

Answer the user's request from data. Keep the full envelope when headers or
diagnostics matter. When the user requests an archive, save the successful
response or the requested field with the environment's local file-writing
capability; scraperAPI itself has no output-path input.

Keep retrieved content as the source of truth for later steps. Build
summaries, tables, JSON transformations, and extraction scripts from it, and
retrieve the page again when a follow-up needs details that an earlier
transformation did not preserve.
