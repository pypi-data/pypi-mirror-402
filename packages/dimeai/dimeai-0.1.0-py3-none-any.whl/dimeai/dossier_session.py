"""
Interactive Dossier Session

Allows analysts to:
- Query for more data and add to the dossier
- Extract entities from new articles
- Add notes and observations
- Analyze patterns across the dossier
"""
import json
from typing import Optional, List, Set
from collections import Counter
from urllib.parse import urlparse

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown

from dimeai.dossier import DossierManager, Dossier, display_dossier_detail

console = Console()

# Reputable sources for geopolitical/security news
REPUTABLE_DOMAINS: Set[str] = {
    # Major news agencies
    "reuters.com", "apnews.com", "afp.com",
    # Quality newspapers
    "nytimes.com", "washingtonpost.com", "theguardian.com", "bbc.com", "bbc.co.uk",
    "ft.com", "economist.com", "wsj.com",
    # Asia-focused
    "scmp.com", "straitstimes.com", "japantimes.co.jp", "koreaherald.com",
    "rappler.com", "inquirer.net", "philstar.com", "mb.com.ph",
    "channelnewsasia.com", "bangkokpost.com", "vietnamnews.vn",
    # Security/defense focused
    "defensenews.com", "janes.com", "navalnews.com", "usni.org",
    "breakingdefense.com", "thedefensepost.com",
    # Think tanks and research
    "csis.org", "amti.csis.org", "rand.org", "cfr.org", "brookings.edu",
    "iiss.org", "chathamhouse.org", "lowyinstitute.org",
    "iseas.edu.sg", "rsis.edu.sg",
    # Wire services
    "aljazeera.com", "dw.com", "france24.com", "abc.net.au",
    # Government/official
    "state.gov", "defense.gov", "mofa.go.jp",
}

# Grey zone event query expansions
GREY_ZONE_EXPANSIONS = [
    # Maritime coercion tactics
    "water cannon coast guard",
    "ramming incident maritime",
    "blocking resupply mission",
    "dangerous maneuver vessel",
    "laser incident military",
    # Territorial disputes
    "artificial island construction",
    "reef militarization",
    "exclusive economic zone violation",
    "fishing militia harassment",
    # Similar regional conflicts
    "Senkaku islands incident",
    "Taiwan strait transit",
    "Vietnam fishing boat",
    "Indonesia Natuna islands",
    "Malaysia Luconia shoals",
]


def _is_reputable_source(url: str) -> bool:
    """Check if URL is from a reputable source."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]
        # Check against whitelist
        for reputable in REPUTABLE_DOMAINS:
            if domain == reputable or domain.endswith("." + reputable):
                return True
        return False
    except Exception:
        return False


def _get_domain_name(url: str) -> str:
    """Extract domain name from URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return "unknown"


def expand_grey_zone_queries(base_query: str) -> List[str]:
    """Expand a base query with grey zone event variations."""
    queries = [base_query]
    
    # Add year if not present
    if "202" not in base_query:
        queries.append(f"{base_query} 2024")
        queries.append(f"{base_query} 2023")
    
    # Add related grey zone terms based on query content
    base_lower = base_query.lower()
    
    if "china" in base_lower or "philippines" in base_lower:
        queries.extend([
            f"{base_query} coast guard incident",
            f"{base_query} Second Thomas Shoal",
            f"{base_query} Scarborough Shoal",
        ])
    
    if "south china sea" in base_lower:
        queries.extend([
            f"{base_query} water cannon",
            f"{base_query} ramming",
            f"{base_query} fishing militia",
        ])
    
    return queries[:5]  # Limit to 5 query variations


def collect_for_dossier(
    dossier_id: int, 
    query: str, 
    max_articles: int = 10,
    expand_queries: bool = True,
    reputable_only: bool = True
) -> int:
    """Collect articles for a dossier using DuckDuckGo search.
    
    Args:
        dossier_id: Target dossier ID
        query: Search query
        max_articles: Maximum articles to collect
        expand_queries: Whether to expand query for grey zone events
        reputable_only: Only accept articles from reputable sources
    
    Returns number of new articles added.
    """
    import httpx
    from dimeai.dossier import DossierManager
    from dimeai.extraction import classify_dimefil_domain
    
    manager = DossierManager()
    dossier = manager.get_dossier(dossier_id)
    
    if not dossier:
        console.print(f"[red]Dossier #{dossier_id} not found[/]")
        return 0
    
    console.print(f"[cyan]Collecting articles for dossier '{dossier.name}'...[/]")
    
    # Use ddgs for search
    try:
        from ddgs import DDGS
    except ImportError:
        console.print("[red]ddgs not installed. Run: pip install ddgs[/]")
        return 0
    
    # Expand queries if requested
    if expand_queries:
        queries = expand_grey_zone_queries(query)
        console.print(f"[dim]Expanded to {len(queries)} query variations[/]")
    else:
        queries = [query]
    
    added = 0
    skipped_source = 0
    seen_urls = set()
    
    for q in queries:
        if added >= max_articles:
            break
            
        console.print(f"[dim]Query: {q}[/]")
        
        # Search with DuckDuckGo
        try:
            with DDGS() as ddgs:
                # Request more results to account for filtering
                results = list(ddgs.text(q, max_results=max_articles * 2))
        except Exception as e:
            console.print(f"[yellow]Search failed for '{q}': {e}[/]")
            continue
        
        if not results:
            continue
        
        # Fetch each result
        for result in results:
            if added >= max_articles:
                break
                
            url = result.get('href', '') or result.get('link', '')
            title = result.get('title', 'Untitled')
            body = result.get('body', '')
            
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            
            # Check source reputation
            domain = _get_domain_name(url)
            if reputable_only and not _is_reputable_source(url):
                skipped_source += 1
                continue
            
            # Try to fetch full content
            content = None
            fetch_error = None
            
            try:
                with httpx.Client(timeout=15.0, follow_redirects=True) as client:
                    resp = client.get(url, headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                    })
                    if resp.status_code == 200:
                        html = resp.text
                        content = _extract_text_from_html(html)
                    else:
                        fetch_error = f"HTTP {resp.status_code}"
            except httpx.TimeoutException:
                fetch_error = "timeout"
            except httpx.ConnectError:
                fetch_error = "connection failed"
            except Exception as e:
                fetch_error = str(e)[:50]
            
            # Decide what content to use
            if content and len(content) >= 500:
                content_source = "full"
            elif body and len(body) >= 200:
                content = body
                content_source = "snippet"
            else:
                console.print(f"  [red]✗[/] No content: {title[:35]}... ({fetch_error or 'too short'})")
                continue
            
            # Classify domain
            dimefil_domain = classify_dimefil_domain(content)
            
            # Add to dossier
            article_id = manager.add_article(dossier_id, title, url, content, dimefil_domain)
            
            if article_id:
                added += 1
                console.print(f"  [green]✓[/] [{dimefil_domain}] {title[:40]}... ({domain}, {len(content)} chars)")
            else:
                console.print(f"  [yellow]~[/] Duplicate: {title[:30]}...")
    
    console.print(f"\n[green]Added {added} new articles[/]")
    if skipped_source > 0:
        console.print(f"[dim]Skipped {skipped_source} from non-reputable sources[/]")
    
    return added


def _extract_text_from_html(html: str) -> str:
    """Extract readable text from HTML.
    
    Focuses on article content, removing navigation, scripts, etc.
    """
    import re
    
    # Remove script and style elements
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<nav[^>]*>.*?</nav>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<header[^>]*>.*?</header>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<footer[^>]*>.*?</footer>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<aside[^>]*>.*?</aside>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    
    # Try to extract article/main content first
    article_match = re.search(r'<article[^>]*>(.*?)</article>', html, flags=re.DOTALL | re.IGNORECASE)
    main_match = re.search(r'<main[^>]*>(.*?)</main>', html, flags=re.DOTALL | re.IGNORECASE)
    
    if article_match:
        html = article_match.group(1)
    elif main_match:
        html = main_match.group(1)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', html)
    
    # Decode HTML entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    text = text.replace('&apos;', "'")
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text


def extract_for_dossier(dossier_id: int, min_content_length: int = 200) -> int:
    """Extract entities from all articles in a dossier.
    
    Args:
        dossier_id: Target dossier
        min_content_length: Skip articles shorter than this
    
    Returns number of entities extracted.
    """
    from dimeai.dossier import DossierManager
    
    manager = DossierManager()
    articles = manager.get_articles(dossier_id)
    
    if not articles:
        console.print("[yellow]No articles in dossier[/]")
        return 0
    
    # Filter out short articles
    valid_articles = [a for a in articles if len(a.content) >= min_content_length]
    skipped = len(articles) - len(valid_articles)
    
    if skipped > 0:
        console.print(f"[dim]Skipping {skipped} articles with <{min_content_length} chars[/]")
    
    if not valid_articles:
        console.print("[yellow]No articles with sufficient content[/]")
        return 0
    
    console.print(f"[cyan]Extracting entities from {len(valid_articles)} articles...[/]")
    
    try:
        from dimeai.extraction import GLiNERExtractor
        extractor = GLiNERExtractor(verbose=False)
    except ImportError as e:
        console.print(f"[red]GLiNER not available: {e}[/]")
        return 0
    
    total_entities = 0
    total_events = 0
    
    for article in valid_articles:
        result = extractor.extract(article.content)
        entities = result.get("entities", {})
        domain = result.get("dimefil_domain", "unknown")
        patterns = result.get("patterns", [])
        
        # Add entities
        for entity_type, entity_list in entities.items():
            for label in entity_list:
                entity_id = label.lower().replace(" ", "_")
                manager.add_entity(dossier_id, entity_id, entity_type, label)
                total_entities += 1
        
        # Create event if we have actors
        countries = entities.get("country", [])
        if len(countries) >= 2:
            event_id = f"EVT-{article.id:04d}"
            actors = [countries[0].lower().replace(" ", "_")]
            targets = [c.lower().replace(" ", "_") for c in countries[1:]]
            locations = entities.get("disputed_territory", []) + entities.get("sea_region", [])
            dates = entities.get("date", [])
            
            manager.add_event(
                dossier_id, event_id, domain, actors, targets,
                location=locations[0] if locations else None,
                date=dates[0] if dates else None,
                patterns=patterns,
                source_article_id=article.id
            )
            total_events += 1
    
    console.print(f"[green]Extracted {total_entities} entities, {total_events} events[/]")
    return total_entities


def run_dossier_session(dossier_id: int) -> None:
    """Run interactive dossier session."""
    manager = DossierManager()
    dossier = manager.get_dossier(dossier_id)
    
    if not dossier:
        console.print(f"[red]Dossier #{dossier_id} not found[/]")
        return
    
    console.print(Panel.fit(
        f"[bold blue]Dossier: {dossier.name}[/]\n"
        f"{dossier.description or 'No description'}\n\n"
        "Type [green]help[/] for commands",
        border_style="blue"
    ))
    
    while True:
        try:
            cmd = Prompt.ask(f"\n[bold cyan]dossier:{dossier.name}>[/]").strip()
            
            if not cmd:
                continue
            
            parts = cmd.split(maxsplit=1)
            command = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""
            
            if command in ("quit", "exit", "q"):
                break
            
            elif command == "help":
                _show_help()
            
            elif command == "status":
                display_dossier_detail(dossier, manager)
            
            elif command == "collect":
                if not args:
                    console.print("[yellow]Usage: collect <search query>[/]")
                else:
                    collect_for_dossier(dossier_id, args)
            
            elif command == "extract":
                extract_for_dossier(dossier_id)
            
            elif command == "articles":
                _show_articles(manager, dossier_id)
            
            elif command == "entities":
                _show_entities(manager, dossier_id, args if args else None)
            
            elif command == "events":
                _show_events(manager, dossier_id, args if args else None)
            
            elif command == "notes":
                _show_notes(manager, dossier_id)
            
            elif command == "note":
                if not args:
                    console.print("[yellow]Usage: note <your observation>[/]")
                else:
                    note_id = manager.add_note(dossier_id, args, "observation")
                    console.print(f"[green]Added note #{note_id}[/]")
            
            elif command == "hypothesis":
                if not args:
                    console.print("[yellow]Usage: hypothesis <your hypothesis>[/]")
                else:
                    note_id = manager.add_note(dossier_id, args, "hypothesis")
                    console.print(f"[green]Added hypothesis #{note_id}[/]")
            
            elif command == "question":
                if not args:
                    console.print("[yellow]Usage: question <your question>[/]")
                else:
                    note_id = manager.add_note(dossier_id, args, "question")
                    console.print(f"[green]Added question #{note_id}[/]")
            
            elif command == "analyze":
                _analyze_dossier(manager, dossier_id)
            
            elif command == "export":
                output = args if args else f"dossier_{dossier_id}.json"
                graph = manager.export_graph(dossier_id)
                with open(output, 'w') as f:
                    json.dump(graph, f, indent=2)
                console.print(f"[green]Exported to {output}[/]")
            
            else:
                console.print(f"[yellow]Unknown command: {command}. Type 'help' for commands.[/]")
        
        except KeyboardInterrupt:
            console.print("\n[dim]Use 'quit' to exit[/]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/]")
    
    console.print("[dim]Session ended[/]")


def _show_help():
    """Show help for dossier session."""
    help_text = """
## Dossier Commands

| Command | Description |
|---------|-------------|
| `status` | Show dossier statistics |
| `collect <query>` | Search and add articles |
| `extract` | Extract entities from articles |
| `articles` | List collected articles |
| `entities [type]` | List entities (optionally by type) |
| `events [domain]` | List events (optionally by domain) |
| `notes` | Show analyst notes |
| `note <text>` | Add an observation |
| `hypothesis <text>` | Add a hypothesis |
| `question <text>` | Add a question |
| `analyze` | Analyze patterns in dossier |
| `export [file]` | Export as graph JSON |
| `quit` | Exit session |
"""
    console.print(Markdown(help_text))


def _show_articles(manager: DossierManager, dossier_id: int):
    """Show articles in dossier."""
    articles = manager.get_articles(dossier_id)
    
    if not articles:
        console.print("[yellow]No articles[/]")
        return
    
    table = Table(title=f"Articles ({len(articles)})")
    table.add_column("ID", style="cyan", justify="right")
    table.add_column("Title", style="white", max_width=40)
    table.add_column("Domain", style="green")
    table.add_column("Collected", style="dim")
    
    for article in articles[:20]:
        table.add_row(
            str(article.id),
            article.title[:40] if article.title else "-",
            article.domain,
            article.collected_at[:10]
        )
    
    if len(articles) > 20:
        console.print(f"[dim](Showing 20 of {len(articles)})[/]")
    
    console.print(table)


def _show_entities(manager: DossierManager, dossier_id: int, entity_type: str = None):
    """Show entities in dossier."""
    entities = manager.get_entities(dossier_id, entity_type)
    
    if not entities:
        console.print("[yellow]No entities[/]")
        return
    
    table = Table(title=f"Entities ({len(entities)})")
    table.add_column("ID", style="cyan")
    table.add_column("Label", style="white")
    table.add_column("Type", style="green")
    
    for entity in entities[:30]:
        table.add_row(entity.entity_id, entity.label, entity.entity_type)
    
    if len(entities) > 30:
        console.print(f"[dim](Showing 30 of {len(entities)})[/]")
    
    console.print(table)


def _show_events(manager: DossierManager, dossier_id: int, domain: str = None):
    """Show events in dossier."""
    events = manager.get_events(dossier_id, domain)
    
    if not events:
        console.print("[yellow]No events[/]")
        return
    
    table = Table(title=f"Events ({len(events)})")
    table.add_column("ID", style="cyan")
    table.add_column("Domain", style="green")
    table.add_column("Actors", style="yellow")
    table.add_column("Targets", style="red")
    table.add_column("Date", style="dim")
    
    for event in events[:20]:
        table.add_row(
            event.event_id,
            event.domain,
            ", ".join(event.actors[:2]),
            ", ".join(event.targets[:2]),
            event.date or "-"
        )
    
    if len(events) > 20:
        console.print(f"[dim](Showing 20 of {len(events)})[/]")
    
    console.print(table)


def _show_notes(manager: DossierManager, dossier_id: int):
    """Show notes in dossier."""
    notes = manager.get_notes(dossier_id)
    
    if not notes:
        console.print("[yellow]No notes[/]")
        return
    
    for note in notes:
        type_color = {
            "observation": "blue",
            "hypothesis": "yellow", 
            "conclusion": "green",
            "question": "cyan"
        }.get(note.note_type, "white")
        
        console.print(Panel(
            note.content,
            title=f"[{type_color}]{note.note_type.upper()}[/] #{note.id}",
            subtitle=note.created_at[:16]
        ))


def _analyze_dossier(manager: DossierManager, dossier_id: int):
    """Analyze patterns in dossier."""
    events = manager.get_events(dossier_id)
    entities = manager.get_entities(dossier_id)
    
    if not events:
        console.print("[yellow]No events to analyze[/]")
        return
    
    console.print(Panel("[bold]Dossier Analysis[/]"))
    
    # Domain distribution
    domain_counts = Counter(e.domain for e in events)
    console.print("\n[bold cyan]Event Distribution by Domain:[/]")
    for domain, count in domain_counts.most_common():
        pct = count / len(events) * 100
        bar = "█" * int(pct / 5)
        console.print(f"  {domain}: {count} ({pct:.0f}%) {bar}")
    
    # Most active actors
    actor_counts = Counter()
    for event in events:
        for actor in event.actors:
            actor_counts[actor] += 1
    
    console.print("\n[bold cyan]Most Active Actors:[/]")
    for actor, count in actor_counts.most_common(5):
        console.print(f"  {actor}: {count} events")
    
    # Most targeted
    target_counts = Counter()
    for event in events:
        for target in event.targets:
            target_counts[target] += 1
    
    console.print("\n[bold cyan]Most Targeted:[/]")
    for target, count in target_counts.most_common(5):
        console.print(f"  {target}: {count} times")
    
    # Pattern frequency
    pattern_counts = Counter()
    for event in events:
        for pattern in event.patterns:
            pattern_counts[pattern] += 1
    
    if pattern_counts:
        console.print("\n[bold cyan]Strategic Patterns:[/]")
        for pattern, count in pattern_counts.most_common():
            console.print(f"  {pattern}: {count}")
