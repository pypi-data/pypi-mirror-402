import click
import json
import requests
import sys
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

from . import store
from .collectors import get_collector
from .exporters import export_as

console = Console()

@click.group()
@click.version_option(version="1.0.0")
def main():
    """Universal LLM context portability - take your AI conversations anywhere."""
    pass

@main.command(name='import')
@click.argument('source')
@click.argument('path', required=False)
def import_(source: str, path: str = None):
    """Import conversations from a platform."""
    try:
        collector = get_collector(source)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description=f"Importing from {source}...", total=None)
            conversations = collector.collect(path)
            
            if not conversations:
                rprint("[yellow]No conversations found.[/yellow]")
                return
            
            store.save_conversations(conversations)
            rprint(f"[green]✓ Imported {len(conversations)} conversations from {source}[/green]")
            
    except Exception as e:
        rprint(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)

@main.command()
@click.option('-s', '--source', help='Filter by source platform')
@click.option('--selected', is_flag=True, help='Show only selected conversations')
def list(source: str = None, selected: bool = False):
    """List all imported conversations."""
    conversations = store.get_conversations(source=source, selected=selected)
    
    if not conversations:
        rprint("[yellow]No conversations found. Run `omni import` first.[/yellow]")
        return

    table = Table(title="OmniContext Conversations", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim", width=34)
    table.add_column("Date")
    table.add_column("Source")
    table.add_column("Messages", justify="right")
    table.add_column("Title")

    for conv in conversations:
        date = conv.createdAt.split('T')[0]
        title = (conv.title[:40] + '...') if len(conv.title) > 40 else conv.title
        table.add_row(
            conv.id[:32],
            date,
            conv.source,
            str(len(conv.messages)),
            title
        )

    console.print(table)
    stats = store.get_stats()
    rprint(f"\n[dim]Total: {stats['total']} | Selected: {stats['selected']}[/dim]\n")

@main.command()
@click.argument('query')
@click.option('-n', '--limit', default=10, help='Max results to show')
@click.option('--source', help='Filter by source platform')
def search(query: str, limit: int, source: str = None):
    """Search conversations by keyword."""
    conversations = store.get_conversations(source=source)
    query_lower = query.lower()
    
    matches = []
    for conv in conversations:
        matched_messages = []
        title_match = query_lower in conv.title.lower()
        
        for i, msg in enumerate(conv.messages):
            if query_lower in msg.content.lower():
                matched_messages.append({"role": msg.role, "content": msg.content, "index": i})
        
        if title_match or matched_messages:
            matches.append({"conv": conv, "matched_messages": matched_messages})
            
    if not matches:
        rprint(f"[yellow]No results for \"{query}\"[/yellow]")
        return

    rprint(f"\n[blue]Found {len(matches)} conversations matching \"{query}\"[/blue]\n")
    
    for match in matches[:limit]:
        conv = match["conv"]
        rprint(f"[bold]{conv.title}[/bold]")
        rprint(f"[dim]ID: {conv.id} | Source: {conv.source} | {conv.createdAt.split('T')[0]}[/dim]")
        
        for msg in match["matched_messages"][:2]:
            snippet = get_snippet(msg["content"], query, 80)
            role_icon = "👤" if msg["role"] == "user" else "🤖"
            rprint(f"  [dim]{role_icon} ...{snippet}...[/dim]")
        
        if len(match["matched_messages"]) > 2:
            rprint(f"  [dim]... and {len(match['matched_messages']) - 2} more matches[/dim]")
        rprint("")

    if len(matches) > limit:
        rprint(f"[dim]Showing {limit} of {len(matches)} results. Use --limit to see more.[/dim]\n")

def get_snippet(content: str, query: str, length: int) -> str:
    lower = content.lower()
    index = lower.find(query.lower())
    if index == -1: return content[:length].replace('\n', ' ')
    
    start = max(0, index - length // 2)
    end = min(len(content), index + len(query) + length // 2)
    return content[start:end].replace('\n', ' ')

@main.command()
@click.argument('ids', nargs=-1)
@click.option('-a', '--all', 'all_', is_flag=True, help='Select all conversations')
@click.option('-s', '--search', 'query', help='Select by keyword search')
@click.option('--after', help='Select conversations after date (YYYY-MM-DD)')
@click.option('--source', help='Select by source platform')
@click.option('--clear', is_flag=True, help='Clear current selection')
def select(ids: list, all_: bool, query: str, after: str, source: str, clear: bool):
    """Select conversations for export."""
    if clear:
        store.clear_selection()
        rprint("[green]✓ Selection cleared[/green]")
        return
        
    if all_:
        store.select_all()
        stats = store.get_stats()
        rprint(f"[green]✓ Selected all {stats['total']} conversations[/green]")
        return
        
    conversations = store.get_conversations(source=source)
    
    if after:
        after_date = datetime.strptime(after, "%Y-%m-%d")
        conversations = [c for c in conversations if datetime.fromisoformat(c.createdAt.replace('Z', '+00:00')).replace(tzinfo=None) >= after_date]
        
    if query:
        query_lower = query.lower()
        conversations = [c for c in conversations if query_lower in c.title.lower() or any(query_lower in m.content.lower() for m in c.messages)]
        
    if ids:
        conversations = [c for c in conversations if any(id_ in c.id for id_ in ids)]
        
    ids_to_select = [c.id for c in conversations]
    store.select_conversations(ids_to_select)
    rprint(f"[green]✓ Selected {len(ids_to_select)} conversations[/green]")

@main.command()
@click.argument('format')
@click.option('-t', '--max-tokens', type=int, help='Maximum tokens (for prompt format)')
@click.option('-o', '--output', help='Write output to file instead of stdout')
def export(format: str, max_tokens: int, output: str):
    """Export selected conversations."""
    conversations = store.get_selected_conversations()
    
    if not conversations:
        rprint("[yellow]No conversations selected. Run `omni select` first.[/yellow]")
        sys.exit(1)
        
    memories = [] # Could pull from store if implemented
    
    content = export_as(format, conversations, memories, {"max_tokens": max_tokens})
    
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(content)
        rprint(f"[green]✓ Exported to {output}[/green]")
    else:
        print(content)

@main.command()
@click.argument('question')
@click.option('-t', '--max-tokens', default=1000, help='Maximum output tokens')
@click.option('-p', '--provider', help='Override configured provider')
def ask(question: str, max_tokens: int, provider: str):
    """Ask a question about selected conversations (requires API key)."""
    config = store.get_config()
    target_provider = provider or config.get("provider")
    api_key = config.get("apiKey")
    
    if not api_key:
        rprint("[red]API key not configured. Run: omni config set api-key <YOUR_KEY>[/red]")
        sys.exit(1)
        
    if not target_provider:
        rprint("[red]Provider not configured. Run: omni config set provider openai[/red]")
        sys.exit(1)
        
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Preparing context...", total=None)
        
        conversations = store.get_selected_conversations()
        if not conversations:
            rprint("[yellow]No conversations selected. Run `omni select` first.[/yellow]")
            sys.exit(1)
            
        context = export_as('prompt', conversations, [], {"max_tokens": 100000})
        
        prompt = f"Use the following conversation history as context to answer the user's question.\n\n--- CONTEXT ---\n{context}\n\n--- QUESTION ---\n{question}\n\nAnswer:"
        
        progress.add_task(description=f"Querying {target_provider}...", total=None)
        
        try:
            if target_provider == 'openai':
                result = call_openai(api_key, prompt, config.get("model", "gpt-4o"), max_tokens)
            elif target_provider == 'anthropic':
                result = call_anthropic(api_key, prompt, config.get("model", "claude-3-sonnet-20240229"), max_tokens)
            else:
                rprint(f"[red]Unsupported provider: {target_provider}[/red]")
                sys.exit(1)
                
            rprint("\n[bold]🤖 Answer:[/bold]\n")
            print(result)
            print("")
            
        except Exception as e:
            rprint(f"[red]Error: {str(e)}[/red]")
            sys.exit(1)

@main.command()
@click.argument('action', required=False)
@click.argument('key', required=False)
@click.argument('value', required=False)
def config(action: str = None, key: str = None, value: str = None):
    """Manage configuration."""
    if not action:
        cfg = store.get_config()
        rprint("\n[blue]Current configuration:[/blue]\n")
        rprint(f"  api-key:  {'[green][SET][/green]' if cfg.get('apiKey') else '[dim][NOT SET][/dim]'}")
        rprint(f"  provider: {cfg.get('provider', '[dim](not set)[/dim]')}")
        rprint(f"  model:    {cfg.get('model', '[dim](not set)[/dim]')}")
        rprint("")
        return

    if action == 'set' and key and value:
        key_map = {
            'api-key': 'apiKey',
            'apikey': 'apiKey',
            'provider': 'provider',
            'model': 'model'
        }
        db_key = key_map.get(key.lower())
        if not db_key:
            rprint(f"[red]Unknown config key: {key}[/red]")
            sys.exit(1)
            
        store.set_config(db_key, value)
        rprint(f"[green]✓ Set {key} = {'[hidden]' if key == 'api-key' else value}[/green]")
        return
        
    rprint("[red]Usage: omni config set <key> <value>[/red]")
    sys.exit(1)

def call_openai(api_key: str, prompt: str, model: str, max_tokens: int) -> str:
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens
        }
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

def call_anthropic(api_key: str, prompt: str, model: str, max_tokens: int) -> str:
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens
        }
    )
    response.raise_for_status()
    return response.json()["content"][0]["text"]

if __name__ == "__main__":
    main()
