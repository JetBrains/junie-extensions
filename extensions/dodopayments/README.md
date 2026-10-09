# dodopayments

Official Dodo Payments extension: integration skills plus the Dodo Payments API and documentation MCP servers.

Source of truth: [dodopayments/dodo-agent-plugin](https://github.com/dodopayments/dodo-agent-plugin) (`providers/junie/`, generated). MIT.

## Features
- Skills for checkout, subscriptions, mobile checkout, webhooks, framework adapters, usage- and credit-based billing, license keys, product catalog, discounts, localized pricing, customers, refunds and disputes, BillingSDK, Better Auth, best practices, testing/go-live, and MCP server usage. Long sections live in each skill's `references/` folder.
- `dodopayments-api` MCP server (`https://mcp.dodopayments.com/mcp`): live Dodo Payments API. Run `/mcp` and authorize on first use (browser OAuth, no API key).
- `dodo-knowledge` MCP server (`https://knowledge.dodopayments.com/mcp`): documentation search, no auth.

## Installation
Add this extension to Junie via your configuration settings.
