---
name: mrscraper
description: |
  Connect, authenticate, route, and troubleshoot MrScraper MCP, and check account usage with the status tool. For known public URLs, retrieve and preserve page content with mrscraper-fetch first; use mrscraper-serp for query-first discovery through web search.
---

# MrScraper MCP

Use this skill for connection and authentication checks, tool selection, shared
response handling, account status, and troubleshooting. Load the focused fetch
or SERP skill for page retrieval and web search.

## Step 1 — Verify or Connect MrScraper MCP

Check whether the current client exposes these three tools from the MrScraper
MCP provider:

    scraperAPI  webSearch  status

The client may display server-qualified names. Match the provider and
unqualified tool name; do not assume a fixed namespace.

If the tools are already available, use the existing connection. If they are
missing, ask the user to enable the existing MrScraper connection or configure
the managed Streamable HTTP endpoint:

    https://mcp.mrscraper.com/mcp

A self-managed deployment may expose the same tools over Streamable HTTP or
stdio. Connection setup belongs to the MCP client. After setup or reconnection,
list the available tools and confirm all three names before claiming the
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

The connection uses three scopes: scrape:write for scraperAPI, scrape:read for
webSearch, and account:read for status. A tool called without its scope returns
403 insufficient_scope; reauthorize the connection so the client requests it.

Verify end-to-end access with status, which reads the account without
retrieving a page:

    {}

A successful account summary confirms that the connection can authenticate and
reach MrScraper. If it fails, report the error and do not claim setup is
complete.

## Step 3 — Route the Request

| User outcome | MCP tool or skill |
| --- | --- |
| Retrieve and preserve a known public page as HTML, Markdown, or a screenshot | [mrscraper-fetch](../mrscraper-fetch/SKILL.md) with scraperAPI |
| Discover relevant pages from a web search query | [mrscraper-serp](../mrscraper-serp/SKILL.md) with webSearch, then retrieve selected pages |
| Check the plan, token usage, or remaining tokens | status |

### Retrieve first, extract locally

scraperAPI returns raw page content. Produce summaries, tables, JSON, and other
structured output from that content with local analysis or extraction logic.
The raw response preserves complete page context for later questions,
validation, and changes to the requested schema.

Prefer this workflow for pages with a shared layout:

1. Retrieve representative pages and inspect their content.
2. Understand the shared page structure and required fields.
3. Define a stable output schema and reusable local extractor.
4. Retrieve the remaining pages, in parallel when safe.
5. Apply the same extractor to every saved response.

Request Markdown when readable text is enough and HTML when an extractor needs
the page structure.

For discovery-first work, call webSearch, select relevant URLs, and retrieve
the pages whose content will inform the answer.

MrScraper MCP does not create AI scrapers, rerun saved scrapers, or list stored
results. Point the user to the MrScraper dashboard at https://app.mrscraper.com
for those.

## Step 4 — Handle Output and Artifacts

scraperAPI and webSearch return the same response envelope in MCP
structuredContent and in a formatted JSON text block:

    {
      "status_code": 200,
      "data": {},
      "headers": {}
    }

Prefer structuredContent when available. An API failure adds error and sets the
MCP result's isError flag. An input-contract failure is returned as a tool
error. Check those signals before trusting data. Credential-bearing headers and
credential metadata are removed from responses.

MrScraper tools do not accept output paths. When the user requests an artifact,
wait for a successful tool result, select the requested value, and save it with
the environment's local file-writing capability. A screenshot is a base64 JPEG
in data.screenshot; decode it before saving an image.

Save substantial intermediate artifacts under the current project's
.mrscraper directory unless the user specifies another location. This project
artifact directory is unrelated to MCP connection credentials. Keep artifacts
out of version control unless the user asks to commit them.

## Step 5 — Review Account Usage

Call status with an empty object:

    {}

The result summarizes the subscription status, token limit, token usage,
remaining tokens, usage percentage, rate limit, auto-renewal, renewal date,
and the account's name, email, and verification state:

    {
      "kind": "mrscraper-cli-status-summary",
      "status_code": 200,
      "data": {
        "account": {
          "subscription_status": "active",
          "token_usage": 250,
          "token_limit": 1000,
          "token_remaining": 750,
          "usage_percent": 25
        }
      }
    }

Check remaining tokens before a large batch of page retrievals. status reports
account usage, not the progress of a request.

## Step 6 — Troubleshoot

- Missing tools: enable or reconnect the MrScraper MCP connection, then confirm
  scraperAPI, webSearch, and status are exposed.
- Unauthorized or expired authorization: reauthorize the OAuth 2.1 connection
  through the MCP client.
- 403 insufficient_scope: reauthorize so the client requests the missing scope.
- Input-contract error: inspect the tool schema and omit inputs that do not
  apply. The previous fetch, scrape, serp, rerun, results, and result tools were
  replaced by scraperAPI, webSearch, and status.
- Page incomplete or missing dynamic content: load mrscraper-fetch and revise
  page-loading inputs deliberately.
- Search results weak: load mrscraper-serp and refine the query, country, or
  number of results.

## Limits

Use another tool for:

- Clicking controls, completing forms, or authenticated browser sessions.
- Parsing local PDFs, documents, spreadsheets, or other files.
- Recurring monitoring, notifications, or scheduling.

Explain the boundary and continue with any supported portion of the task.
