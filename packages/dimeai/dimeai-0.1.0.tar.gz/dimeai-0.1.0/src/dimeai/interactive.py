"""
Interactive session CLI for DimeAI
"""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
from rich.live import Live
from rich.spinner import Spinner
from typing import Optional, Dict, Any
import json

console = Console()


class InteractiveSession:
    """Interactive DIMEFIL analysis session."""
    
    def __init__(self, graph_path: Optional[str] = None, model_path: Optional[str] = None):
        self.graph_path = graph_path
        self.model_path = model_path
        self.graph_data: Optional[Dict] = None
        self.history: list = []
        
        # Load graph if provided
        if graph_path:
            self._load_graph()
    
    def _load_graph(self) -> None:
        """Load graph data from file."""
        try:
            with open(self.graph_path) as f:
                self.graph_data = json.load(f)
            console.print(f"[green]✓[/] Loaded graph from {self.graph_path}")
        except FileNotFoundError:
            console.print(f"[yellow]![/] Graph file not found: {self.graph_path}")
        except json.JSONDecodeError as e:
            console.print(f"[red]✗[/] Invalid JSON in graph file: {e}")
    
    def _show_help(self) -> None:
        """Display help information."""
        help_text = """
## Commands

| Command | Description |
|---------|-------------|
| `actors` | List all actors in the graph |
| `events [actor]` | Show events, optionally filtered by actor |
| `domains` | Show event distribution by DIMEFIL domain |
| `predict <actor>` | Predict likely next events for an actor |
| `whatif <scenario>` | Analyze a hypothetical scenario |
| `history` | Show analysis history |
| `load <path>` | Load a different graph |
| `status` | Show current session status |
| `help` | Show this help |
| `quit` | Exit the session |
"""
        console.print(Markdown(help_text))
    
    def _show_status(self) -> None:
        """Show current session status."""
        table = Table(title="Session Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Graph", self.graph_path or "Not loaded")
        table.add_row("Model", self.model_path or "Not loaded")
        
        if self.graph_data:
            nodes = self.graph_data.get("nodes", [])
            edges = self.graph_data.get("edges", [])
            actors = [n for n in nodes if n.get("node_type") == "actor"]
            actions = [n for n in nodes if n.get("node_type") == "action"]
            
            table.add_row("Total Nodes", str(len(nodes)))
            table.add_row("Total Edges", str(len(edges)))
            table.add_row("Actors", str(len(actors)))
            table.add_row("Actions", str(len(actions)))
        
        table.add_row("History Items", str(len(self.history)))
        
        console.print(table)
    
    def _list_actors(self) -> None:
        """List all actors in the graph."""
        if not self.graph_data:
            console.print("[yellow]No graph loaded. Use 'load <path>' first.[/]")
            return
        
        nodes = self.graph_data.get("nodes", [])
        actors = [n for n in nodes if n.get("node_type") == "actor"]
        
        if not actors:
            console.print("[yellow]No actors found in graph.[/]")
            return
        
        table = Table(title=f"Actors ({len(actors)})")
        table.add_column("ID", style="cyan")
        table.add_column("Label", style="white")
        table.add_column("Type", style="green")
        table.add_column("Country", style="yellow")
        
        for actor in sorted(actors, key=lambda x: x.get("id", "")):
            table.add_row(
                actor.get("id", ""),
                actor.get("label", ""),
                actor.get("actor_type", ""),
                actor.get("country", "")
            )
        
        console.print(table)
    
    def _show_domains(self) -> None:
        """Show event distribution by DIMEFIL domain."""
        if not self.graph_data:
            console.print("[yellow]No graph loaded. Use 'load <path>' first.[/]")
            return
        
        nodes = self.graph_data.get("nodes", [])
        actions = [n for n in nodes if n.get("node_type") == "action"]
        
        # Count by domain
        domain_counts: Dict[str, int] = {}
        for action in actions:
            domain = action.get("dimefil_domain", "unknown")
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        table = Table(title="Events by DIMEFIL Domain")
        table.add_column("Domain", style="cyan")
        table.add_column("Count", style="green", justify="right")
        table.add_column("Percentage", style="yellow", justify="right")
        
        total = sum(domain_counts.values())
        for domain, count in sorted(domain_counts.items(), key=lambda x: -x[1]):
            pct = (count / total * 100) if total > 0 else 0
            table.add_row(domain, str(count), f"{pct:.1f}%")
        
        console.print(table)
    
    def _show_events(self, actor_filter: Optional[str] = None) -> None:
        """Show events, optionally filtered by actor."""
        if not self.graph_data:
            console.print("[yellow]No graph loaded. Use 'load <path>' first.[/]")
            return
        
        nodes = self.graph_data.get("nodes", [])
        edges = self.graph_data.get("edges", [])
        actions = [n for n in nodes if n.get("node_type") == "action"]
        
        # Build edge lookup
        edge_lookup: Dict[str, list] = {}
        for edge in edges:
            src = edge.get("source", "")
            tgt = edge.get("target", "")
            if src not in edge_lookup:
                edge_lookup[src] = []
            edge_lookup[src].append((tgt, edge.get("relation", "")))
        
        # Filter by actor if specified
        if actor_filter:
            actor_filter = actor_filter.lower()
            filtered_actions = []
            for action in actions:
                action_id = action.get("id", "")
                # Check if actor is connected to this action
                for src, targets in edge_lookup.items():
                    if actor_filter in src.lower():
                        for tgt, rel in targets:
                            if tgt == action_id:
                                filtered_actions.append(action)
                                break
                    for tgt, rel in targets:
                        if tgt == action_id or src == action_id:
                            if actor_filter in tgt.lower():
                                filtered_actions.append(action)
                                break
            actions = list({a["id"]: a for a in filtered_actions}.values())
        
        if not actions:
            console.print("[yellow]No events found.[/]")
            return
        
        table = Table(title=f"Events ({len(actions)})")
        table.add_column("ID", style="cyan", max_width=20)
        table.add_column("Domain", style="green")
        table.add_column("Date", style="yellow")
        table.add_column("Description", style="white", max_width=40)
        
        for action in actions[:50]:  # Limit to 50
            table.add_row(
                action.get("id", "")[:20],
                action.get("dimefil_domain", ""),
                action.get("date", ""),
                action.get("label", "")[:40]
            )
        
        if len(actions) > 50:
            console.print(f"[dim](Showing 50 of {len(actions)} events)[/]")
        
        console.print(table)
    
    def _predict(self, actor: str) -> None:
        """Predict likely next events for an actor."""
        if not self.graph_data:
            console.print("[yellow]No graph loaded. Use 'load <path>' first.[/]")
            return
        
        # Simple heuristic-based prediction (no model needed)
        nodes = self.graph_data.get("nodes", [])
        edges = self.graph_data.get("edges", [])
        
        # Find actor's historical patterns
        actor_lower = actor.lower()
        actor_actions = []
        
        for edge in edges:
            src = edge.get("source", "").lower()
            if actor_lower in src and edge.get("relation") == "performs":
                action_id = edge.get("target", "")
                action_node = next((n for n in nodes if n.get("id") == action_id), None)
                if action_node:
                    actor_actions.append(action_node)
        
        if not actor_actions:
            console.print(f"[yellow]No historical actions found for '{actor}'[/]")
            return
        
        # Count domain frequencies
        domain_counts: Dict[str, int] = {}
        for action in actor_actions:
            domain = action.get("dimefil_domain", "unknown")
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        total = sum(domain_counts.values())
        
        console.print(Panel(f"[bold]Predictions for {actor}[/]"))
        
        table = Table(title="Likely Next Actions (based on historical patterns)")
        table.add_column("Domain", style="cyan")
        table.add_column("Probability", style="green")
        table.add_column("Historical Count", style="yellow")
        
        for domain, count in sorted(domain_counts.items(), key=lambda x: -x[1]):
            prob = count / total
            bar = "█" * int(prob * 20)
            table.add_row(domain, f"{prob:.1%} {bar}", str(count))
        
        console.print(table)
        
        # Add to history
        self.history.append({
            "type": "predict",
            "actor": actor,
            "result": domain_counts
        })
    
    def _whatif(self, scenario: str) -> None:
        """Analyze a hypothetical scenario."""
        console.print(Panel(f"[bold]What-If Analysis[/]\n{scenario}"))
        
        # Parse scenario for keywords
        scenario_lower = scenario.lower()
        
        # Identify likely domain
        domain_keywords = {
            "military": ["military", "exercise", "drill", "navy", "warship", "fighter"],
            "law_enforcement": ["coast guard", "water cannon", "patrol", "intercept", "ram"],
            "diplomatic": ["protest", "talks", "summit", "ambassador", "negotiate"],
            "economic": ["fishing", "trade", "sanction", "tariff", "resource"],
            "legal": ["tribunal", "ruling", "unclos", "arbitration", "court"],
            "information": ["propaganda", "disinformation", "media", "narrative"]
        }
        
        detected_domains = []
        for domain, keywords in domain_keywords.items():
            if any(kw in scenario_lower for kw in keywords):
                detected_domains.append(domain)
        
        if not detected_domains:
            detected_domains = ["diplomatic"]  # Default
        
        console.print(f"\n[cyan]Detected domains:[/] {', '.join(detected_domains)}")
        
        # Simple escalation analysis
        escalation_risk = "LOW"
        if "military" in detected_domains:
            escalation_risk = "HIGH"
        elif "law_enforcement" in detected_domains:
            escalation_risk = "MEDIUM"
        
        risk_color = {"LOW": "green", "MEDIUM": "yellow", "HIGH": "red"}[escalation_risk]
        console.print(f"[{risk_color}]Escalation Risk: {escalation_risk}[/]")
        
        # Suggest countermeasures
        console.print("\n[bold]Suggested Countermeasures:[/]")
        
        countermeasures = {
            "military": ["Diplomatic de-escalation talks", "Third-party mediation", "Confidence-building measures"],
            "law_enforcement": ["Bilateral hotline activation", "Joint patrol protocols", "Incident reporting mechanism"],
            "diplomatic": ["Continue dialogue", "Multilateral engagement (ASEAN)", "Track-2 diplomacy"],
            "economic": ["Trade negotiations", "Resource-sharing agreements", "Joint development zones"],
        }
        
        for domain in detected_domains:
            if domain in countermeasures:
                for cm in countermeasures[domain]:
                    console.print(f"  • {cm}")
        
        # Add to history
        self.history.append({
            "type": "whatif",
            "scenario": scenario,
            "domains": detected_domains,
            "escalation_risk": escalation_risk
        })
    
    def _show_history(self) -> None:
        """Show analysis history."""
        if not self.history:
            console.print("[yellow]No analysis history yet.[/]")
            return
        
        for i, item in enumerate(self.history, 1):
            console.print(f"\n[bold cyan]#{i}[/] {item['type'].upper()}")
            if item["type"] == "predict":
                console.print(f"  Actor: {item['actor']}")
            elif item["type"] == "whatif":
                console.print(f"  Scenario: {item['scenario'][:50]}...")
                console.print(f"  Risk: {item['escalation_risk']}")
    
    def run(self) -> None:
        """Run the interactive session."""
        console.print(Panel.fit(
            "[bold blue]DimeAI Interactive Session[/]\n"
            "Type [green]help[/] for commands, [green]quit[/] to exit",
            border_style="blue"
        ))
        
        self._show_status()
        
        while True:
            try:
                cmd = Prompt.ask("\n[bold cyan]dimeai>[/]").strip()
                
                if not cmd:
                    continue
                
                parts = cmd.split(maxsplit=1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                
                if command in ("quit", "exit", "q"):
                    if Confirm.ask("Exit session?", default=True):
                        console.print("[dim]Goodbye![/]")
                        break
                
                elif command == "help":
                    self._show_help()
                
                elif command == "status":
                    self._show_status()
                
                elif command == "actors":
                    self._list_actors()
                
                elif command == "domains":
                    self._show_domains()
                
                elif command == "events":
                    self._show_events(args if args else None)
                
                elif command == "predict":
                    if not args:
                        console.print("[yellow]Usage: predict <actor>[/]")
                    else:
                        self._predict(args)
                
                elif command == "whatif":
                    if not args:
                        console.print("[yellow]Usage: whatif <scenario description>[/]")
                    else:
                        self._whatif(args)
                
                elif command == "history":
                    self._show_history()
                
                elif command == "load":
                    if not args:
                        console.print("[yellow]Usage: load <graph_path>[/]")
                    else:
                        self.graph_path = args
                        self._load_graph()
                
                else:
                    console.print(f"[yellow]Unknown command: {command}. Type 'help' for commands.[/]")
            
            except KeyboardInterrupt:
                console.print("\n[dim]Use 'quit' to exit[/]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/]")


def run_interactive(graph_path: Optional[str] = None, model_path: Optional[str] = None) -> None:
    """Start interactive session."""
    session = InteractiveSession(graph_path=graph_path, model_path=model_path)
    session.run()
