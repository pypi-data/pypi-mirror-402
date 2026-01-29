"""
Article collection via web scraping using DingoCrawl
"""
import os
import json
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Set, Optional
from dataclasses import dataclass

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel

console = Console()

# Try to import dingocrawl
try:
    from dingocrawl.search import search_web_full
    from dingocrawl.crawler import fetch_page, html_to_markdown
    DINGOCRAWL_AVAILABLE = True
except ImportError:
    DINGOCRAWL_AVAILABLE = False


@dataclass
class DIMEFILDomain:
    """Configuration for a DIMEFIL domain."""
    name: str
    seed_queries: List[str]


# DIMEFIL domain configurations with seed queries
DIMEFIL_DOMAINS = {
    'diplomatic': DIMEFILDomain(
        name='diplomatic',
        seed_queries=[
            'South China Sea diplomatic protest Philippines China 2024',
            'ASEAN China code of conduct South China Sea negotiations',
            'Philippines China bilateral talks maritime dispute',
        ],
    ),
    'information': DIMEFILDomain(
        name='information',
        seed_queries=[
            'China South China Sea propaganda disinformation campaign',
            'Philippines China information warfare maritime claims',
            'South China Sea cognitive warfare narrative control',
        ],
    ),
    'military': DIMEFILDomain(
        name='military',
        seed_queries=[
            'PLA Navy South China Sea patrol military exercise 2024',
            'China military drill Taiwan Strait warships aircraft',
            'US Philippines Balikatan joint military exercise',
        ],
    ),
    'economic': DIMEFILDomain(
        name='economic',
        seed_queries=[
            'South China Sea fishing dispute China Philippines fishermen',
            'IUU illegal fishing Chinese fleet South China Sea',
            'Scarborough Shoal fishing rights Filipino fishermen',
        ],
    ),
    'law_enforcement': DIMEFILDomain(
        name='law_enforcement',
        seed_queries=[
            'China coast guard water cannon Philippines vessel 2024',
            'Second Thomas Shoal resupply mission China coast guard',
            'Scarborough Shoal coast guard harassment Philippines',
        ],
    ),
    'legal': DIMEFILDomain(
        name='legal',
        seed_queries=[
            'South China Sea arbitration ruling Philippines China UNCLOS',
            'nine dash line international law tribunal ruling',
            'UNCLOS exclusive economic zone South China Sea',
        ],
    ),
}


class ArticleCollector:
    """Collects DIMEFIL-relevant articles using dingocrawl."""
    
    def __init__(self, output_dir: str = 'articles', verbose: bool = False):
        if not DINGOCRAWL_AVAILABLE:
            raise ImportError(
                "dingocrawl not installed. Install with: pip install dingocrawl"
            )
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
        self.existing_hashes = self._load_existing_hashes()
    
    def _load_existing_hashes(self) -> Set[str]:
        """Load content hashes of existing articles for deduplication."""
        hashes = set()
        
        for filepath in self.output_dir.glob('*.txt'):
            content = filepath.read_text(encoding='utf-8')
            lines = content.split('\n')
            body_start = 0
            for i, line in enumerate(lines):
                if line.startswith('Content Length:'):
                    body_start = i + 2
                    break
            body = '\n'.join(lines[body_start:])
            content_hash = hashlib.md5(body.encode()).hexdigest()
            hashes.add(content_hash)
        
        return hashes
    
    def _is_duplicate(self, content: str) -> bool:
        """Check if content is a duplicate."""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        return content_hash in self.existing_hashes
    
    def _add_hash(self, content: str):
        """Add content hash to existing hashes."""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        self.existing_hashes.add(content_hash)
    
    def _generate_filename(self, domain: str, title: str) -> str:
        """Generate a unique filename for an article."""
        clean_title = title.lower()
        clean_title = ''.join(c if c.isalnum() or c == ' ' else '_' for c in clean_title)
        clean_title = '_'.join(clean_title.split())[:50]
        title_hash = hashlib.md5(title.encode()).hexdigest()[:8]
        return f"{domain}_{clean_title}_{title_hash}.txt"
    
    def _is_valid_content(self, content: str) -> tuple[bool, str]:
        """Validate content quality."""
        if len(content) < 200:
            return False, f"Too short ({len(content)} chars)"
        
        # Check printable ratio
        printable_ratio = sum(1 for c in content[:1000] if c.isprintable() or c in '\n\t') / min(len(content), 1000)
        if printable_ratio < 0.8:
            return False, f"Binary/garbled ({printable_ratio:.0%} printable)"
        
        # Check for English keywords
        keywords = ['the', 'and', 'china', 'philippines', 'sea', 'coast', 'guard', 'south']
        word_count = sum(1 for w in keywords if w in content.lower())
        if word_count < 2:
            return False, f"Lacks keywords ({word_count} found)"
        
        return True, "OK"
    
    def collect_for_domain(
        self, 
        domain: DIMEFILDomain, 
        max_articles: int = 20,
        progress: Optional[Progress] = None,
        task_id: Optional[int] = None
    ) -> List[Dict]:
        """Collect articles for a single DIMEFIL domain."""
        collected = []
        seen_urls = set()
        bad_domains = ['zhihu.com', 'baidu.com', 'google.com/support']
        
        for query in domain.seed_queries:
            if len(collected) >= max_articles:
                break
            
            if self.verbose:
                console.print(f"  [dim]Searching: {query[:50]}...[/]")
            
            try:
                results = search_web_full(query, max_results=10, region='us-en')
            except Exception as e:
                if self.verbose:
                    console.print(f"  [red]Search failed: {e}[/]")
                continue
            
            for result in results:
                if len(collected) >= max_articles:
                    break
                
                url = result.get('href', '')
                title = result.get('title', '')
                
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                
                if any(bd in url for bd in bad_domains):
                    continue
                
                try:
                    html = fetch_page(url)
                    if not html:
                        continue
                    
                    markdown = html_to_markdown(html)
                    
                    valid, reason = self._is_valid_content(markdown)
                    if not valid:
                        if self.verbose:
                            console.print(f"  [yellow]Skip: {reason}[/]")
                        continue
                    
                    if self._is_duplicate(markdown):
                        if self.verbose:
                            console.print(f"  [yellow]Skip: Duplicate[/]")
                        continue
                    
                    # Save article
                    filename = self._generate_filename(domain.name, title)
                    filepath = self.output_dir / filename
                    
                    article_content = f"""Title: {title}
URL: {url}
Domain: {domain.name}
Query: {query}
Content Length: {len(markdown)}

{markdown}
"""
                    filepath.write_text(article_content, encoding='utf-8')
                    self._add_hash(markdown)
                    
                    collected.append({
                        'filename': filename,
                        'title': title,
                        'url': url,
                        'domain': domain.name,
                        'length': len(markdown)
                    })
                    
                    if progress and task_id is not None:
                        progress.update(task_id, advance=1)
                    
                    if self.verbose:
                        console.print(f"  [green]✓[/] {title[:50]}...")
                    
                    time.sleep(1)  # Rate limiting
                    
                except Exception as e:
                    if self.verbose:
                        console.print(f"  [red]Error: {e}[/]")
                    continue
        
        return collected
    
    def collect(
        self,
        situation: str,
        domains: Optional[List[str]] = None,
        max_articles: int = 50
    ) -> Dict[str, List[Dict]]:
        """Collect articles related to a situation.
        
        Args:
            situation: Description of the geopolitical situation (used to augment queries)
            domains: DIMEFIL domains to focus on (default: all)
            max_articles: Maximum total articles to collect
        """
        if domains:
            target_domains = {k: v for k, v in DIMEFIL_DOMAINS.items() if k in domains}
        else:
            target_domains = DIMEFIL_DOMAINS
        
        if not target_domains:
            console.print("[red]No valid domains specified[/]")
            return {}
        
        # Calculate per-domain limit
        per_domain = max(5, max_articles // len(target_domains))
        
        all_collected = {}
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            
            for domain_name, domain_config in target_domains.items():
                task = progress.add_task(f"[cyan]{domain_name}[/]", total=per_domain)
                
                # Augment queries with situation context
                augmented = DIMEFILDomain(
                    name=domain_config.name,
                    seed_queries=[f"{situation} {q}" for q in domain_config.seed_queries[:2]] + 
                                 domain_config.seed_queries
                )
                
                collected = self.collect_for_domain(
                    augmented, 
                    max_articles=per_domain,
                    progress=progress,
                    task_id=task
                )
                all_collected[domain_name] = collected
                progress.update(task, completed=per_domain)
        
        # Show summary
        self._show_summary(all_collected)
        
        return all_collected
    
    def _show_summary(self, collected: Dict[str, List[Dict]]):
        """Display collection summary."""
        table = Table(title="Collection Summary")
        table.add_column("Domain", style="cyan")
        table.add_column("Articles", justify="right", style="green")
        table.add_column("Total Size", justify="right")
        
        total_articles = 0
        total_size = 0
        
        for domain, articles in collected.items():
            count = len(articles)
            size = sum(a.get('length', 0) for a in articles)
            total_articles += count
            total_size += size
            table.add_row(domain, str(count), f"{size:,} chars")
        
        table.add_row("", "", "", style="dim")
        table.add_row("[bold]Total[/]", f"[bold]{total_articles}[/]", f"[bold]{total_size:,} chars[/]")
        
        console.print(table)
        console.print(f"\n[dim]Existing articles: {len(self.existing_hashes)}[/]")


def collect_articles(
    situation: str,
    domains: Optional[List[str]] = None,
    max_articles: int = 50,
    output_dir: str = 'articles',
    verbose: bool = False
) -> List[str]:
    """Collect articles related to a situation.
    
    Args:
        situation: Description of the geopolitical situation
        domains: DIMEFIL domains to focus on
        max_articles: Maximum number of articles to collect
        output_dir: Directory to save articles
        verbose: Enable verbose output
        
    Returns:
        List of collected article paths
    """
    try:
        collector = ArticleCollector(output_dir=output_dir, verbose=verbose)
    except ImportError as e:
        console.print(f"[red]{e}[/]")
        console.print("\n[yellow]To install dingocrawl:[/]")
        console.print("  pip install dingocrawl")
        return []
    
    collected = collector.collect(situation, domains=domains, max_articles=max_articles)
    
    # Return list of file paths
    paths = []
    for articles in collected.values():
        for article in articles:
            paths.append(str(Path(output_dir) / article['filename']))
    
    return paths
