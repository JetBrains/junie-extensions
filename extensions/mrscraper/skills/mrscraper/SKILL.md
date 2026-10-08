---
name: mrscraper
description: |
  Connect, authenticate, route, and troubleshoot MrScraper MCP, and use saved scrapers, stored results, and account tools. For known public URLs, acquire and preserve raw content with mrscraper-fetch first; use mrscraper-scrape only for explicitly requested or clearly beneficial managed extraction, and mrscraper-serp for query-first discovery.
---

# MrScraper MCP

Use this skill for connection and authentication checks, tool selection, shared
response handling, saved reruns, stored results, account status, and
troubleshooting. Load the focused fetch, scrape, or SERP skill for those
workflows.

## Step 1 — Verify or Connect MrScraper MCP

Check whether the current client exposes these seven tools from the MrScraper
MCP provider:

    fetch  scrape  serp  status  rerun  results  result

The client may display server-qualified names. Match the provider and
unqualified tool name; do not assume a fixed namespace.

If the tools are already available, use the existing connection. If they are
missing, ask the user to enable the existing MrScraper connection or configure
the managed Streamable HTTP endpoint:

    https://mcp.mrscraper.com/mcp

A self-managed deployment may expose the same tools over Streamable HTTP or
stdio. Connection setup belongs to the MCP client. After setup or reconnection,
list the available tools and confirm all seven names before claiming the
integration is ready.

## Step 2 — Authenticate

MrScraper MCP authenticates through OAuth 2.1. Authentication belongs to the
MCP connection and is never a tool argument.

When the connection is not authorized, start the MCP client's authorization
flow. Let the client discover the authorization metadata, open the MrScraper
consent page, complete authorization, store the resulting credentials, and
refresh access tokens. The user may need to approve access in a browser, but
must not paste an authorization code, access token, refresh token, API key, or
other credential into the conversation.

Never place credentials in tool arguments, print them, write them into project
artifacts, or manually reproduce the OAuth exchange. Do not configure an
API-key or bearer-token fallback from these skills.

Verify end-to-end access with one small fetch:

    {
      "url": "https://www.scrapethissite.com/pages/simple/"
    }

A successful page response confirms that the connection can authenticate and
reach the web-data service. If it fails, report the error and do not claim
setup is complete.

## Step 3 — Route the Request

| User outcome | MCP tool or skill |
| --- | --- |
| Acquire and preserve raw content from known public URLs for any downstream task | [mrscraper-fetch](../mrscraper-fetch/SKILL.md), preferably first |
| Add managed extraction, repeated records, site mapping, schema guidance, or a reusable scraper | [mrscraper-scrape](../mrscraper-scrape/SKILL.md), normally after or alongside fetch |
| Discover relevant pages from a Google query | [mrscraper-serp](../mrscraper-serp/SKILL.md), then fetch selected pages |
| Reproduce a prior scrape or run an existing AI/manual scraper on new URLs | rerun |
| List or retrieve stored results | results or result |
| Check account usage or domain request outcomes | status |

### Fetch-first principle

For agent-led work, always use fetch for the first exploration of a known public
URL. The raw response preserves complete page context for later questions,
validation, and custom processing. Requesting JSON, a table, or named fields is
not by itself a reason to use scrape; derive those outputs locally from the raw
content when practical.

The general and listing scrape modes send page content through a backend LLM.
Their output is shaped by the extraction prompt and may omit information.
Applying them across many pages also repeats model work that the agent can often
replace with one reusable local extractor.

Prefer this workflow for pages with a shared layout:

1. Fetch representative pages and inspect their raw content.
2. Understand the shared page structure and required fields.
3. Define a stable output schema and reusable local extractor.
4. Fetch the remaining pages, in parallel when safe.
5. Apply the same extractor to every saved response.

For roughly 100 same-layout pages, that means 100 fetches followed by one local
batch extraction instead of 100 separate backend-LLM extractions. This is often
faster, preserves every raw input, and allows fields to be recovered later if
the schema changes.

Use scrape only when the user explicitly requests managed extraction or when it
still offers a clear benefit after fetch-led exploration. Even then, retain the
fetched source and verify important values against it. The map agent is separate
URL-discovery functionality; use it for bounded site mapping, then fetch the
pages whose content matters.

For discovery-first work, call serp, select relevant URLs, fetch those pages,
and add managed extraction only when a derived structured view is useful.

## Step 4 — Handle Output and Artifacts

API-backed tools return the same response envelope in MCP structuredContent and
in a formatted JSON text block:

    {
      "status_code": 200,
      "data": {},
      "headers": {}
    }

Prefer structuredContent when available. An API failure adds error and sets the
MCP result's isError flag. An input-contract failure is returned as a tool
error. Check those signals before trusting data.

Credentials, cookies, and generated curl credentials are sanitized. Extracted
scraper data is preserved even when it contains fields named token or password
because those fields may be legitimate source values.

MrScraper tools do not accept output paths. When the user requests an artifact,
wait for a successful tool result, select the requested value, and save it with
the environment's local file-writing capability. For scrape, the extracted
value is normally at structuredContent.data.data.data. Keep the full envelope
separately only when run metadata, headers, or diagnostics matter.

Save substantial intermediate artifacts under the current project's
.mrscraper directory unless the user specifies another location. This project
artifact directory is unrelated to MCP connection credentials. Keep artifacts
out of version control unless the user asks to commit them.

## Step 5 — Rerun Saved Scrapers

A successful scrape creates a saved AI scraper configuration. Read its UUID
from structuredContent.data.data.scraperId and use rerun to apply the same
configuration to the same or another URL. Prefer rerun over rebuilding a prompt
when the user wants a repeatable version of an earlier extraction.

The scraperId makes the configuration reusable but does not guarantee
identical extracted values when the source page or model behavior changes.

Choose scraper type and target count independently:

1. Use type=ai for a saved AI scraper created by scrape.
2. Use type=manual for a saved step-based workflow created in the MrScraper
   dashboard. MCP can rerun but cannot create manual workflows.
3. Leave bulk=false for one URL. Set bulk=true for a comma- or
   newline-separated URL list submitted as one asynchronous job.

| Mode | Required ID input | Target | Crawl controls |
| --- | --- | --- | --- |
| Single AI | scraper_id | One URL | Supported |
| Single manual | scraper_id | One URL | Not accepted |
| Bulk AI | bulk=true and id | Comma/newline-separated URLs | Not accepted |
| Bulk manual | bulk=true and id | Comma/newline-separated URLs | Not accepted |

Single AI example:

    {
      "target": "https://www.scrapethissite.com/pages/simple/",
      "type": "ai",
      "scraper_id": "SCRAPER_UUID"
    }

Single AI optionally accepts max_depth, max_pages, limit, include_patterns,
exclude_patterns, proxy_country, max_retry, and timeout. Omit any control that
the user did not request so the saved scraper or backend default remains in
effect; the MCP server does not inject replacement defaults.

Explicit-control example:

    {
      "target": "https://www.scrapethissite.com/pages/forms/?page_num=1",
      "type": "ai",
      "scraper_id": "SCRAPER_UUID",
      "proxy_country": "ID",
      "max_retry": 4,
      "timeout": 120
    }

These controls are rejected by manual and bulk reruns.

Bulk example:

    {
      "target": "https://www.scrapethissite.com/pages/simple/,https://www.scrapethissite.com/pages/forms/?page_num=1",
      "type": "ai",
      "bulk": true,
      "id": "SCRAPER_UUID"
    }

Manual example, after the user accepts the warning below:

    {
      "target": "https://www.scrapethissite.com/pages/simple/",
      "type": "manual",
      "scraper_id": "SCRAPER_UUID",
      "acknowledged": true
    }

Bulk rerun submits one asynchronous backend job. Retain
structuredContent.data.data.bulkResultId and pass it to result as result_id.
Inspect that record until it reaches a terminal state when the user asked to
wait for completion. Do not resubmit the bulk rerun because its result is still
running.

Before the first rerun call with type=manual in a conversation, show the
following warning exactly once and wait for the user's acknowledgment. Do not
call the tool until the user accepts it, and do not repeat the warning on later
manual reruns in the same conversation. After the user accepts, pass
acknowledged=true on every manual rerun in that conversation; rerun refuses a
manual rerun without it and returns this warning instead.

> ### Compliance & Legal Risk
>
> WARNING
>
> **Scraping login-protected pages carries serious legal and compliance
> risks.** Many websites explicitly prohibit automated access in their Terms
> of Service, and bypassing authentication to scrape content may expose you to
> legal action including lawsuits, account termination, and financial
> penalties. By proceeding on scraping login-protected pages, you confirm that
> you have read and understood the target website's Terms of Service, and you
> **fully accept all legal, financial, and ethical responsibility** for your
> actions.

## Step 6 — Inspect Stored Results

Use results when the exact result UUID is unknown:

    {
      "sort_field": "updatedAt",
      "sort_order": "desc",
      "page_size": 20,
      "page": 1
    }

Apply exact backend filters when the user knows identifying result fields:

    {
      "scraper_id": "SCRAPER_UUID",
      "status": "Finished",
      "type": "Rerun-AI",
      "url": "https://www.scrapethissite.com/pages/simple/"
    }

| Input | Default | Use |
| --- | --- | --- |
| sort_field | updatedAt | Stored-result sort key. |
| sort_order | desc | Sort direction: asc or desc. |
| page_size | 10 | Positive number of records per page. |
| page | 1 | One-based page number. |
| search | omitted | Free-text result filter. |
| date_range_column | omitted | Date column used by start_at and end_at. |
| start_at | omitted | Inclusive ISO 8601 range start. |
| end_at | omitted | Inclusive ISO 8601 range end. |
| scraper_id | omitted | Exact saved scraper UUID filter. |
| status | omitted | Exact Draft, Finished, Running, Failed, or Cancelled filter. |
| type | omitted | Exact result type filter, such as AI or Rerun-AI. |
| url | omitted | Exact stored target URL filter. |

Use result when the UUID is known:

    {
      "result_id": "RESULT_UUID",
      "include_html": false
    }

A result_id may also be the bulkResultId returned by an asynchronous rerun.
include_html defaults to true. Set it to false for a smaller response while
polling status or when extracted data is sufficient.

## Step 7 — Review Account Usage

Call status with an empty object for subscription and token usage:

    {}

Add domain request outcomes and a time range only when needed:

    {
      "domain": "www.scrapethissite.com",
      "from": "7d",
      "to": "now"
    }

| Input | Default | Use |
| --- | --- | --- |
| domain | omitted | Add request outcomes for a normalized hostname. |
| from | 24h | ISO start or relative duration such as 30m, 24h, or 7d. |
| to | now | ISO end, now, or a relative duration. |
| action | omitted | Exact request-action filter, used only with domain. |
| api_token_name | omitted | API-token-name filter, used only with domain. |

Domain outcomes describe MrScraper requests. They are not traffic, audience,
SEO, or market analytics. status reports account and request health, not
scrape-job progress; use result for a known asynchronous result ID.

## Step 8 — Troubleshoot

- Missing tools: enable or reconnect the MrScraper MCP connection, then confirm
  all seven tools are exposed.
- Unauthorized or expired authorization: reauthorize the OAuth 2.1 connection
  through the MCP client.
- Input-contract error: inspect the tool schema and omit inputs that do not
  apply to the selected mode.
- Page incomplete or missing dynamic content: load mrscraper-fetch and revise
  page-loading inputs deliberately.
- Extraction incomplete: load mrscraper-scrape and improve the prompt, agent,
  or limits.
- Search results weak: load mrscraper-serp and refine the query, locale, or
  page.

## Limits

Use another tool for:

- Clicking controls, completing forms, or authenticated browser sessions.
- Parsing local PDFs, documents, spreadsheets, or other files.
- Recurring monitoring, notifications, or scheduling.

Explain the boundary and continue with any supported portion of the task.
