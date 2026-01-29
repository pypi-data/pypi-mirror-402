# MCP List

A small CLI tool that shows which MCP servers are installed and where they come from.

If you have ever wondered:
- "Is this MCP coming from Cursor or my repo?"
- "Why is this MCP available here but not there?"
- "Do I have multiple MCPs with the same name?"

This tool gives you visibility.

## Why this exists

As MCP usage grows, setups get messy:
- MCPs defined in Cursor
- MCPs configured in local repositories
- MCPs installed globally (npm / npx / system)
- Windows + WSL makes this even harder to reason about

There is currently no single place to answer:
> "Which MCP is active, and where is it coming from?"

This CLI is meant to be that answer.

## Install

```bash
pip install mcp-list
```

## Usage

```bash
mcp-list
mcp-list --cursor
mcp-list --repo
mcp-list --global
mcp-list --claude
```

## License

MIT
