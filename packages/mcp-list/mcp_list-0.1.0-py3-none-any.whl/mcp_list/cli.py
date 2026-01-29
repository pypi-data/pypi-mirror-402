import json
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

app = typer.Typer(add_completion=False)
console = Console()


def find_cursor_config() -> Optional[Path]:
    """Find Cursor MCP configuration file."""
    if os.name == "nt":  # Windows
        appdata = os.getenv("APPDATA")
        if appdata:
            # Common Cursor config locations on Windows
            possible_paths = [
                Path(appdata) / "Cursor" / "User" / "settings.json",
                Path(appdata) / "Cursor" / "User" / "globalStorage" / "mcp.json",
                Path(os.getenv("LOCALAPPDATA", "")) / "Cursor" / "User" / "settings.json",
            ]
            for path in possible_paths:
                if path.exists():
                    return path
    else:  # macOS/Linux
        home = Path.home()
        possible_paths = [
            home / ".config" / "Cursor" / "User" / "settings.json",
            home / ".config" / "Cursor" / "User" / "globalStorage" / "mcp.json",
            home / "Library" / "Application Support" / "Cursor" / "User" / "settings.json",
        ]
        for path in possible_paths:
            if path.exists():
                return path
    return None


def parse_cursor_config(config_path: Path) -> List[Dict]:
    """Parse Cursor configuration and extract MCP servers."""
    mcps = []
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # Cursor stores MCPs in different possible locations
        mcp_configs = []

        # Check for mcp.servers in settings.json
        if "mcp" in config and "servers" in config["mcp"]:
            mcp_configs = config["mcp"]["servers"]
        elif "mcpServers" in config:
            mcp_configs = config["mcpServers"]

        for name, server_config in mcp_configs.items():
            mcps.append(
                {
                    "name": name,
                    "source": "Cursor",
                    "source_path": str(config_path),
                    "config": server_config,
                }
            )
    except Exception:
        pass
    return mcps


def find_claude_md_files(start_path: Optional[Path] = None) -> List[Path]:
    """Find all claude.md/CLAUDE.md files in the project/repo."""
    if start_path is None:
        start_path = Path.cwd()

    claude_files: List[Path] = []

    # Search current directory and parent directories up to repo root
    current = start_path.resolve()
    max_depth = 10  # Prevent infinite loops
    filename_candidates = {"claude.md", "CLAUDE.md"}

    for _ in range(max_depth):
        for name in filename_candidates:
            claude_path = current / name
            if claude_path.exists():
                claude_files.append(claude_path)

        # Check for .cursorrules or .cursor directory
        if (current / ".git").exists() or (current / ".cursor").exists():
            # We're at repo root, also check subdirectories
            for md_file in current.rglob("claude.md"):
                if md_file not in claude_files:
                    claude_files.append(md_file)
            for md_file in current.rglob("CLAUDE.md"):
                if md_file not in claude_files:
                    claude_files.append(md_file)
            break

        parent = current.parent
        if parent == current:  # Reached filesystem root
            break
        current = parent

    return claude_files


def parse_claude_md(md_path: Path) -> List[Dict]:
    """Parse claude.md file and extract MCP configurations."""
    mcps = []
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Try to find JSON code blocks with MCP config
        json_blocks = re.findall(r"```json\s*\n(.*?)\n```", content, re.DOTALL)
        for block in json_blocks:
            try:
                config = json.loads(block)
                if "mcp" in config or "mcpServers" in config:
                    servers = config.get("mcp", {}).get("servers", {}) or config.get(
                        "mcpServers", {}
                    )
                    for name, server_config in servers.items():
                        mcps.append(
                            {
                                "name": name,
                                "source": "claude.md",
                                "source_path": str(md_path),
                                "config": server_config,
                            }
                        )
            except Exception:
                pass

        # Also look for MCP server mentions in text
        mcp_patterns = [
            r"mcp[_-]?server[s]?[:\s]+([^\n]+)",
            r"@mcp[_-]?([^\s\n]+)",
        ]
        for pattern in mcp_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if match.strip():
                    mcps.append(
                        {
                            "name": match.strip(),
                            "source": "claude.md",
                            "source_path": str(md_path),
                            "config": {},
                        }
                    )
    except Exception:
        pass
    return mcps


def find_global_mcps() -> List[Dict]:
    """Find globally installed MCP servers."""
    mcps = []

    # Check npm global packages
    try:
        result = subprocess.run(
            ["npm", "list", "-g", "--depth=0", "--json"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            npm_packages = json.loads(result.stdout)
            dependencies = npm_packages.get("dependencies", {})
            for pkg_name in dependencies.keys():
                if "mcp" in pkg_name.lower():
                    mcps.append(
                        {
                            "name": pkg_name,
                            "source": "npm (global)",
                            "source_path": "npm global packages",
                            "config": {},
                        }
                    )
    except Exception:
        pass

    return mcps


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    cursor: bool = typer.Option(False, "--cursor", help="Show only Cursor MCPs"),
    repo: bool = typer.Option(False, "--repo", help="Show only repo/project MCPs"),
    global_mcps: bool = typer.Option(False, "--global", help="Show only global MCPs"),
    claude: bool = typer.Option(False, "--claude", help="Show only claude.md MCPs"),
) -> None:
    """
    List all MCP servers and their sources (Cursor, claude.md, global).
    """
    if ctx.invoked_subcommand is not None:
        return

    all_mcps: List[Dict] = []

    # Determine which sources to check based on flags
    check_cursor = cursor or (not repo and not global_mcps and not claude)
    check_claude = claude or repo or (not cursor and not global_mcps)
    check_global = global_mcps or (not cursor and not repo and not claude)

    # Check Cursor configs
    if check_cursor:
        cursor_config = find_cursor_config()
        if cursor_config:
            cursor_mcps = parse_cursor_config(cursor_config)
            all_mcps.extend(cursor_mcps)
        elif cursor:
            rprint("[yellow]No Cursor configuration found[/yellow]")

    # Check claude.md files
    if check_claude:
        claude_files = find_claude_md_files()
        if claude_files:
            for md_file in claude_files:
                md_mcps = parse_claude_md(md_file)
                all_mcps.extend(md_mcps)
        elif claude or repo:
            rprint("[yellow]No claude.md files found[/yellow]")

    # Check global MCPs
    if check_global:
        global_mcp_list = find_global_mcps()
        all_mcps.extend(global_mcp_list)

    # Filter based on flags
    if cursor:
        all_mcps = [mcp for mcp in all_mcps if mcp["source"] == "Cursor"]
    elif claude or repo:
        all_mcps = [mcp for mcp in all_mcps if mcp["source"] == "claude.md"]
    elif global_mcps:
        all_mcps = [
            mcp for mcp in all_mcps if "global" in mcp["source"].lower()
        ]

    # Display results
    if not all_mcps:
        rprint("[yellow]No MCP servers found.[/yellow]")
        return

    table = Table(title="MCP Servers", show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Source", style="green")
    table.add_column("Location", style="yellow")

    for mcp in all_mcps:
        table.add_row(mcp["name"], mcp["source"], mcp["source_path"])

    console.print(table)

    # Summary
    sources: Dict[str, int] = {}
    for mcp in all_mcps:
        source = mcp["source"]
        sources[source] = sources.get(source, 0) + 1

    rprint(f"\n[bold]Summary:[/bold] {len(all_mcps)} MCP server(s) found")
    for source, count in sources.items():
        rprint(f"  - {source}: {count}")


if __name__ == "__main__":
    app()
