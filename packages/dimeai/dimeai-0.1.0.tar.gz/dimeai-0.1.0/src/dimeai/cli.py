"""
DimeAI CLI - Main entry point
"""
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--quiet', '-q', is_flag=True, help='Suppress non-essential output')
@click.pass_context
def main(ctx, verbose, quiet):
    """DimeAI: DIMEFIL Analyst CLI for geopolitical event analysis."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['quiet'] = quiet


@main.command()
@click.argument('situation')
@click.option('--domains', '-d', multiple=True, 
              type=click.Choice(['diplomatic', 'information', 'military', 'economic', 'financial', 'intelligence', 'law_enforcement']),
              help='DIMEFIL domains to focus on')
@click.option('--max-articles', '-n', default=50, help='Maximum articles to collect')
@click.pass_context
def collect(ctx, situation, domains, max_articles):
    """Collect historical events related to a situation.
    
    Example: dimeai collect "South China Sea tensions 2024"
    """
    from dimeai.collection import collect_articles
    
    if not ctx.obj['quiet']:
        console.print(Panel(f"[bold blue]Collecting articles for:[/] {situation}"))
    
    collect_articles(situation, domains=domains, max_articles=max_articles, verbose=ctx.obj['verbose'])


@main.command()
@click.option('--input-dir', '-i', default='articles', help='Directory with collected articles')
@click.option('--output', '-o', default='extracted_graph.json', help='Output graph file')
@click.option('--model', '-m', default='fastino/gliner2-base-v1', help='GLiNER model to use')
@click.pass_context
def extract(ctx, input_dir, output, model):
    """Extract entities and relationships from collected articles."""
    from dimeai.extraction import run_extraction
    
    if not ctx.obj['quiet']:
        console.print(Panel("[bold blue]Extracting entities with GLiNER 2[/]"))
    
    run_extraction(input_dir, output, model=model, verbose=ctx.obj['verbose'])


@main.command()
@click.option('--graph', '-g', default='extracted_graph.json', help='Input graph file')
@click.option('--output', '-o', default='model.pt', help='Output model file')
@click.option('--epochs', '-e', default=100, help='Training epochs')
@click.option('--train-ratio', default=0.7, help='Train/test split ratio (chronological)')
@click.pass_context
def train(ctx, graph, output, epochs, train_ratio):
    """Train TGN model on extracted graph."""
    from dimeai.training import train_tgn
    
    if not ctx.obj['quiet']:
        console.print(Panel("[bold blue]Training Temporal Graph Network[/]"))
    
    train_tgn(graph, output, epochs=epochs, train_ratio=train_ratio, verbose=ctx.obj['verbose'])


@main.command()
@click.argument('situation')
@click.option('--model', '-m', default='model.pt', help='Trained model file')
@click.option('--graph', '-g', default='extracted_graph.json', help='Graph file')
@click.pass_context
def analyze(ctx, situation, model, graph):
    """Analyze a situation and predict likely events."""
    from dimeai.agent import run_analysis
    
    if not ctx.obj['quiet']:
        console.print(Panel(f"[bold blue]Analyzing:[/] {situation}"))
    
    run_analysis(situation, model_path=model, graph_path=graph, verbose=ctx.obj['verbose'])


@main.command()
@click.option('--model', '-m', default='model.pt', help='Trained model file')
@click.option('--graph', '-g', default='extracted_graph.json', help='Graph file')
@click.pass_context
def simulate(ctx, model, graph):
    """Interactive what-if simulation mode."""
    from dimeai.simulation import run_simulation
    
    if not ctx.obj['quiet']:
        console.print(Panel("[bold blue]What-If Simulation Mode[/]"))
    
    run_simulation(model_path=model, graph_path=graph, verbose=ctx.obj['verbose'])


@main.group()
def config():
    """Manage DimeAI configuration."""
    pass


@config.command('show')
def config_show():
    """Show current configuration."""
    from dimeai.config import load_config
    
    cfg = load_config()
    table = Table(title="DimeAI Configuration")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")
    
    for key, value in cfg.items():
        table.add_row(key, str(value))
    
    console.print(table)


@config.command('set')
@click.argument('key')
@click.argument('value')
def config_set(key, value):
    """Set a configuration value."""
    from dimeai.config import set_config
    
    set_config(key, value)
    console.print(f"[green]Set {key} = {value}[/]")


@main.group()
def features():
    """Compute and inspect node features."""
    pass


@features.command('compute')
@click.option('--graph', '-g', default='extracted_graph.json', help='Input graph file')
@click.option('--output', '-o', default='features.json', help='Output features file')
@click.option('--model', '-m', default='all-MiniLM-L6-v2', help='Embedding model')
@click.pass_context
def features_compute(ctx, graph, output, model):
    """Compute semantic and graph features for all nodes."""
    from dimeai.features import compute_features
    
    compute_features(graph, output, embedding_model=model, verbose=ctx.obj['verbose'])


@features.command('inspect')
@click.argument('node_id')
@click.option('--features-file', '-f', default='features.json', help='Features file')
def features_inspect(node_id, features_file):
    """Inspect features for a specific node."""
    from dimeai.features import inspect_features
    
    inspect_features(features_file, node_id)


@main.command()
@click.option('--graph', '-g', default='extracted_graph.json', help='Graph file')
@click.pass_context
def benchmark(ctx, graph):
    """Run benchmark comparing TGN vs baselines."""
    from dimeai.benchmark import run_benchmark
    
    if not ctx.obj['quiet']:
        console.print(Panel("[bold blue]Running Benchmark[/]"))
    
    run_benchmark(graph, verbose=ctx.obj['verbose'])


@main.command()
@click.option('--graph', '-g', default=None, help='Graph file to load')
@click.option('--model', '-m', default=None, help='Model file to load')
@click.pass_context
def interactive(ctx, graph, model):
    """Start interactive analysis session."""
    from dimeai.interactive import run_interactive
    
    run_interactive(graph_path=graph, model_path=model)


# Dossier commands
@main.group()
def dossier():
    """Manage investigation dossiers."""
    pass


@dossier.command('list')
@click.option('--status', '-s', type=click.Choice(['active', 'archived', 'closed']), help='Filter by status')
def dossier_list(status):
    """List all dossiers."""
    from dimeai.dossier import DossierManager, display_dossier_list
    
    manager = DossierManager()
    dossiers = manager.list_dossiers(status=status)
    display_dossier_list(dossiers, manager)


@dossier.command('create')
@click.argument('name')
@click.option('--description', '-d', default='', help='Dossier description')
@click.option('--tags', '-t', multiple=True, help='Tags for the dossier')
def dossier_create(name, description, tags):
    """Create a new dossier."""
    from dimeai.dossier import DossierManager
    
    manager = DossierManager()
    dossier = manager.create_dossier(name, description, list(tags))
    console.print(f"[green]Created dossier #{dossier.id}: {dossier.name}[/]")


@dossier.command('show')
@click.argument('dossier_id', type=int)
def dossier_show(dossier_id):
    """Show dossier details."""
    from dimeai.dossier import DossierManager, display_dossier_detail
    
    manager = DossierManager()
    dossier = manager.get_dossier(dossier_id)
    
    if not dossier:
        console.print(f"[red]Dossier #{dossier_id} not found[/]")
        return
    
    display_dossier_detail(dossier, manager)


@dossier.command('open')
@click.argument('dossier_id', type=int)
def dossier_open(dossier_id):
    """Open interactive dossier session."""
    from dimeai.dossier_session import run_dossier_session
    
    run_dossier_session(dossier_id)


@dossier.command('collect')
@click.argument('dossier_id', type=int)
@click.argument('query')
@click.option('--max-articles', '-n', default=10, help='Maximum articles to collect')
@click.option('--no-expand', is_flag=True, help='Disable query expansion for grey zone events')
@click.option('--all-sources', is_flag=True, help='Include non-reputable sources')
def dossier_collect(dossier_id, query, max_articles, no_expand, all_sources):
    """Collect more articles for a dossier.
    
    By default, only collects from reputable news sources and think tanks.
    Queries are expanded to find similar grey zone events.
    """
    from dimeai.dossier_session import collect_for_dossier
    
    collect_for_dossier(
        dossier_id, 
        query, 
        max_articles,
        expand_queries=not no_expand,
        reputable_only=not all_sources
    )


@dossier.command('export')
@click.argument('dossier_id', type=int)
@click.option('--output', '-o', default=None, help='Output file (default: dossier_<id>.json)')
def dossier_export(dossier_id, output):
    """Export dossier as graph JSON."""
    from dimeai.dossier import DossierManager
    import json
    
    manager = DossierManager()
    dossier = manager.get_dossier(dossier_id)
    
    if not dossier:
        console.print(f"[red]Dossier #{dossier_id} not found[/]")
        return
    
    graph = manager.export_graph(dossier_id)
    output = output or f"dossier_{dossier_id}.json"
    
    with open(output, 'w') as f:
        json.dump(graph, f, indent=2)
    
    console.print(f"[green]Exported to {output}[/]")
    console.print(f"  Nodes: {len(graph['nodes'])}")
    console.print(f"  Edges: {len(graph['edges'])}")


@dossier.command('note')
@click.argument('dossier_id', type=int)
@click.argument('content')
@click.option('--type', '-t', 'note_type', default='observation',
              type=click.Choice(['observation', 'hypothesis', 'conclusion', 'question']),
              help='Note type')
def dossier_note(dossier_id, content, note_type):
    """Add a note to a dossier."""
    from dimeai.dossier import DossierManager
    
    manager = DossierManager()
    dossier = manager.get_dossier(dossier_id)
    
    if not dossier:
        console.print(f"[red]Dossier #{dossier_id} not found[/]")
        return
    
    note_id = manager.add_note(dossier_id, content, note_type)
    console.print(f"[green]Added {note_type} note #{note_id}[/]")


@dossier.command('delete')
@click.argument('dossier_id', type=int)
@click.option('--force', '-f', is_flag=True, help='Skip confirmation')
def dossier_delete(dossier_id, force):
    """Delete a dossier."""
    from dimeai.dossier import DossierManager
    from rich.prompt import Confirm
    
    manager = DossierManager()
    dossier = manager.get_dossier(dossier_id)
    
    if not dossier:
        console.print(f"[red]Dossier #{dossier_id} not found[/]")
        return
    
    if not force:
        if not Confirm.ask(f"Delete dossier '{dossier.name}' and all its data?"):
            return
    
    manager.delete_dossier(dossier_id)
    console.print(f"[green]Deleted dossier #{dossier_id}[/]")


if __name__ == '__main__':
    main()
