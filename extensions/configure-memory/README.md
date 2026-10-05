# Configure Memory

Bring saved project decisions, preferences, and goals into Junie so you can continue a task without repeating its background.

## What it does

Configure keeps the context you choose to save across your AI tools. This extension gives Junie a connection to that profile and a skill for finding the details relevant to the current task.

For example, ask Junie to use your saved project decisions when planning a feature, recall your coding preferences before editing, or save a decision you have just made. Saving requires a user request. The skill treats retrieved memories as reference data and uses the tool's actual result to report what was saved.

## Connection

The extension connects to `https://mcp.configure.dev/` over Streamable HTTP. A Configure account and OAuth sign-in are required to access profile data. No API key, local server, or embedded credential is needed.

If Junie shows **Authorization required**, open `/mcp`, select Configure, and complete the sign-in flow. Review the requested permissions before authorizing access. You can manage your saved context and app permissions in Configure.

Tools for separately connected apps may also be available. The skill uses them only when relevant to the current request and within granted permissions.

## Examples

- Use my saved Configure project decisions to help plan this feature.
- What coding preferences have I saved in Configure?
- Save this decision in Configure: the project uses PostgreSQL.

## Links

- [Configure](https://configure.dev)
- [Connection documentation](https://docs.configure.dev/mcp/overview)
- [Privacy policy](https://configure.dev/privacy.html)
- [Terms](https://configure.dev/terms.html)
