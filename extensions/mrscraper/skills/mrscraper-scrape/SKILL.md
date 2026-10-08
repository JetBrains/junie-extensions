---
name: mrscraper-scrape
description: |
  Run MrScraper's general, listing, or map agents for managed structured extraction or bounded URL discovery within a known site. Use when managed output is explicitly requested or justified after source-page inspection; use mrscraper-fetch for initial acquisition of known pages and mrscraper-serp when no starting URL is known.
---

# Extract Structured Data with MrScraper MCP

Do not use scrape for the first exploration of a known page. Start with
[mrscraper-fetch](../mrscraper-fetch/SKILL.md), inspect the complete raw
response, and prefer local analysis or a reusable extractor. Use scrape when
the user explicitly wants MrScraper-managed extraction, or after the agent
understands the website and has defined a stable output schema. Use
[mrscraper](../mrscraper/SKILL.md) for connection troubleshooting, saved runs,
account status, or broader routing.

For general and listing, MrScraper retrieves page HTML and asks a backend LLM to
interpret it according to prompt. This adds model-processing time, can narrow
the result to the requested fields, and repeats model work across many pages.

Before using general or listing, confirm all of the following:

1. The target or representative pages have already been fetched and inspected.
2. The site structure and required output fields are understood.
3. A stable output schema has been defined.
4. Managed extraction still offers a concrete benefit over local code, or the
   user explicitly requested it.

If these conditions are not met, return to fetch. Requiring JSON, a table, or
named fields is not by itself a reason to call scrape. For large same-layout
sets—even roughly 100 pages—safe concurrent fetches plus one reusable local
extractor are often faster and preserve every raw response. The map agent is
separate URL discovery functionality and does not require an extraction schema.

## Step 1 — Choose an Agent

| Agent | Use it for | Required input | Available controls |
| --- | --- | --- | --- |
| general | One detail page or one extraction task | prompt | proxy_country, schema_prompt |
| listing | Repeated records or paginated listings | prompt | proxy_country, max_pages, schema_prompt |
| map | Discovering URLs across a site | URL only | max_depth, max_pages, limit, include_patterns, exclude_patterns |

The default agent is general. For map, omit prompt, schema_prompt, and
proxy_country. For general and listing, omit map-only controls. max_pages is
accepted by listing and map but not general.

agent selects the extraction workflow. mode independently selects the backend
execution tier: Cheap or Super. Omit mode to preserve the backend default, and
select Super only when the extraction requires the stronger mode.

## Step 2 — Define the Extraction

The examples below assume the decision gate above has been satisfied. Write a
prompt from the already-understood page structure and output schema, preserve
source values, and do not ask the model to infer unavailable values.

Detail-page example:

    {
      "url": "https://www.scrapethissite.com/pages/simple/",
      "agent": "general",
      "mode": "Super",
      "prompt": "Extract each country's name, capital, population, and area. Preserve source values and omit unavailable fields."
    }

Repeated-listing example:

    {
      "url": "https://www.scrapethissite.com/pages/forms/?page_num=1",
      "agent": "listing",
      "prompt": "Extract each hockey team's name, year, wins, losses, and win percentage.",
      "max_pages": 5
    }

Site-map example:

    {
      "url": "https://www.scrapethissite.com/",
      "agent": "map",
      "max_depth": 2,
      "max_pages": 50,
      "limit": 1000,
      "include_patterns": "/pages/"
    }

## Step 3 — Add Shape Guidance When Useful

schema_prompt accepts a JSON object, not a file path. If the user supplies a
local JSON Schema file, read and parse it with local file tools, confirm its
root is an object, and pass that object:

    {
      "url": "https://www.scrapethissite.com/pages/simple/",
      "agent": "general",
      "prompt": "Extract every country's name, capital, population, and area.",
      "schema_prompt": {
        "type": "object",
        "properties": {
          "countries": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "name": { "type": "string" },
                "capital": { "type": "string" },
                "population": { "type": "string" },
                "area": { "type": "string" }
              }
            }
          }
        }
      }
    }

The MCP server appends this object to the extraction prompt as best-effort
shape guidance. It does not validate the returned data against the schema.
Validate locally when strict compliance is required.

## Step 4 — Set Parameters

| MCP input | Default | Request mapping | Use |
| --- | --- | --- | --- |
| url | required | Body url | Absolute HTTP or HTTPS starting URL. |
| agent | general | Body agent | Select general, listing, or map. |
| mode | service default | Body mode | Select Cheap or Super execution without changing the agent. |
| prompt | required for general/listing | Body message | Describe the fields or records to extract. |
| proxy_country | omitted | Body proxyCountry | Route general/listing through a country. |
| max_pages | service default | Body maxPages | Bound listing or map pages. |
| max_depth | service default | Body maxDepth | Bound map crawl depth. |
| limit | service default | Body limit | Bound map URL results. |
| include_patterns | omitted | Body includePatterns | Restrict map results to matching URLs. |
| exclude_patterns | omitted | Body excludePatterns | Exclude matching map URLs. |
| schema_prompt | omitted | Appended to message | JSON Schema object for general/listing guidance. |

Authentication is handled by the MCP client's OAuth 2.1 connection. The scrape
tool does not accept a credential or output-path input. Choose the smallest
practical limits and omit optional values when the service default is
appropriate.

## Step 5 — Wait for Completion

General and map usually finish quickly. Listing is synchronous and can take
several minutes even for one page.

Before starting a listing call, tell the user it may take several minutes. Keep
waiting on the original MCP call within the environment's supported tool
timeout. Do not submit a duplicate scrape because the first call is quiet or
still running.

## Step 6 — Use the Output

The complete API envelope is returned in MCP structuredContent and as formatted
JSON text. Prefer structuredContent and check isError, error, and status_code
before trusting the response.

A successful run normally stores its extracted value at:

    structuredContent.data.data.data

The saved scraper UUID is normally at:

    structuredContent.data.data.scraperId

When the user asks for a file, save the extracted value only after the tool
succeeds. Use local file-writing capability and report the path. Preserve the
full envelope separately when the scraper ID, response headers, or diagnostics
also matter.

Post-process only when the user requests filtering, merging, normalization,
CSV, a table, or another deliverable. Extracted fields named token or password
may be legitimate source data and are intentionally preserved.

## Step 7 — Preserve the Reproducible Scraper

Every successful scrape creates a saved AI scraper configuration by default.
Report scraperId when it is available and the extraction may need to run again.

Use the MrScraper rerun tool to apply the saved configuration to the same or
another URL:

    {
      "target": "https://www.scrapethissite.com/pages/forms/?page_num=2",
      "type": "ai",
      "scraper_id": "SCRAPER_UUID"
    }

Prefer rerun over recreating the scrape definition when the user wants a
repeatable extraction. Explain that this reproduces the saved configuration,
not necessarily identical values when the page or model behavior changes.

The rerun tool also handles dashboard-built manual workflows and asynchronous
bulk jobs. Follow the full rerun workflow in
[mrscraper](../mrscraper/SKILL.md), including the required acknowledgment
before any manual rerun.

## Step 8 — Handle Failures

- Check isError, error, and status_code before using or saving output.
- Tighten the prompt when fields are missing or grouped incorrectly.
- Confirm the selected agent accepts every supplied input.
- Validate locally when downstream code requires a strict schema.
- Use [mrscraper-fetch](../mrscraper-fetch/SKILL.md) for page reading.
- Use [mrscraper-serp](../mrscraper-serp/SKILL.md) when discovery must happen
  first.
- Never invent replacement fields or fill missing values with unsupported
  assumptions.
