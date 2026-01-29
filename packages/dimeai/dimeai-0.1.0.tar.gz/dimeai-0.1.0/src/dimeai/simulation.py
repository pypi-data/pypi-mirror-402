"""
What-if simulation mode for countermeasure analysis
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from collections import Counter

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown

console = Console()


@dataclass
class Scenario:
    """A hypothetical scenario."""
    name: str
    actor: str
    action_domain: str
    target: str
    description: str


@dataclass
class SimulationResult:
    """Result of simulating a scenario."""
    scenario: Scenario
    likely_responses: List[Dict[str, Any]]
    escalation_risk: str
    historical_precedents: int
    recommended_countermeasures: List[str]


class WhatIfSimulator:
    """Simulate what-if scenarios based on historical patterns."""
    
    DOMAIN_ESCALATION = {
        "military": 0.8,
        "law_enforcement": 0.5,
        "legal": 0.2,
        "diplomatic": 0.3,
        "economic": 0.4,
        "information": 0.4
    }
    
    COUNTERMEASURES = {
        "military": [
            "Diplomatic de-escalation talks",
            "Third-party mediation (ASEAN)",
            "Confidence-building measures",
            "Military-to-military hotline activation"
        ],
        "law_enforcement": [
            "Bilateral coast guard protocols",
            "Joint patrol agreements",
            "Incident reporting mechanism",
            "Maritime communication channels"
        ],
        "legal": [
            "International arbitration",
            "UNCLOS dispute resolution",
            "Diplomatic note verbale",
            "Multilateral legal framework"
        ],
        "diplomatic": [
            "Continue bilateral dialogue",
            "Track-2 diplomacy",
            "ASEAN engagement",
            "Summit-level talks"
        ],
        "economic": [
            "Trade negotiations",
            "Resource-sharing agreements",
            "Joint development zones",
            "Fishing rights protocols"
        ],
        "information": [
            "Counter-narrative campaigns",
            "Fact-checking initiatives",
            "Media transparency",
            "Public diplomacy"
        ]
    }
    
    def __init__(self, graph_path: str):
        with open(graph_path) as f:
            self.graph_data = json.load(f)
        
        self.nodes = {n["id"]: n for n in self.graph_data.get("nodes", [])}
        self.edges = self.graph_data.get("edges", [])
        
        # Build action-reaction patterns
        self._build_patterns()
    
    def _build_patterns(self):
        """Build action-reaction patterns from historical data."""
        from collections import defaultdict
        
        self.performs = defaultdict(list)
        self.targets = defaultdict(list)
        
        for edge in self.edges:
            rel = edge.get("relation", "")
            if rel == "performs":
                self.performs[edge["source"]].append(edge["target"])
            elif rel == "targets":
                self.targets[edge["source"]].append(edge["target"])
        
        # Build response patterns: after domain X, what domain Y follows?
        self.response_patterns = defaultdict(lambda: defaultdict(int))
        
        # Get actions sorted by some ordering (using action ID as proxy for time)
        actions = [(n_id, n) for n_id, n in self.nodes.items() 
                  if n.get("node_type") == "action"]
        actions.sort(key=lambda x: x[0])
        
        # Look at consecutive actions involving same actors
        for i in range(len(actions) - 1):
            curr_id, curr = actions[i]
            next_id, next_action = actions[i + 1]
            
            curr_domain = curr.get("dimefil_domain", "unknown")
            next_domain = next_action.get("dimefil_domain", "unknown")
            
            # Find actors involved
            curr_actors = set()
            for actor, action_ids in self.performs.items():
                if curr_id in action_ids:
                    curr_actors.add(actor)
            
            next_actors = set()
            for actor, action_ids in self.performs.items():
                if next_id in action_ids:
                    next_actors.add(actor)
            
            # If there's actor overlap, record the pattern
            if curr_actors & next_actors:
                self.response_patterns[curr_domain][next_domain] += 1
    
    def simulate(self, scenario: Scenario) -> SimulationResult:
        """Simulate a scenario and predict outcomes."""
        domain = scenario.action_domain.lower()
        
        # Get likely responses based on historical patterns
        responses = []
        pattern = self.response_patterns.get(domain, {})
        total = sum(pattern.values())
        
        if total > 0:
            for resp_domain, count in sorted(pattern.items(), key=lambda x: -x[1]):
                prob = count / total
                responses.append({
                    "domain": resp_domain,
                    "probability": prob,
                    "historical_count": count
                })
        else:
            # Default responses if no pattern data
            responses = [
                {"domain": "diplomatic", "probability": 0.4, "historical_count": 0},
                {"domain": "law_enforcement", "probability": 0.3, "historical_count": 0},
                {"domain": "legal", "probability": 0.2, "historical_count": 0}
            ]
        
        # Calculate escalation risk
        base_risk = self.DOMAIN_ESCALATION.get(domain, 0.3)
        
        # Adjust based on likely responses
        if responses:
            top_response = responses[0]["domain"]
            response_risk = self.DOMAIN_ESCALATION.get(top_response, 0.3)
            risk = (base_risk + response_risk) / 2
        else:
            risk = base_risk
        
        risk_level = "LOW" if risk < 0.35 else "MEDIUM" if risk < 0.6 else "HIGH"
        
        # Get countermeasures
        countermeasures = self.COUNTERMEASURES.get(domain, [])
        
        # Count historical precedents
        precedents = sum(1 for n in self.nodes.values() 
                        if n.get("dimefil_domain") == domain)
        
        return SimulationResult(
            scenario=scenario,
            likely_responses=responses[:5],
            escalation_risk=risk_level,
            historical_precedents=precedents,
            recommended_countermeasures=countermeasures
        )
    
    def compare_scenarios(self, scenarios: List[Scenario]) -> List[SimulationResult]:
        """Compare multiple scenarios."""
        return [self.simulate(s) for s in scenarios]


def run_simulation(
    model_path: str,
    graph_path: str,
    verbose: bool = False
) -> None:
    """Run interactive what-if simulation.
    
    Args:
        model_path: Path to trained model
        graph_path: Path to graph data
        verbose: Enable verbose output
    """
    console.print(Panel.fit(
        "[bold blue]What-If Simulation Mode[/]\n"
        "Define scenarios and analyze potential outcomes",
        border_style="blue"
    ))
    
    simulator = WhatIfSimulator(graph_path)
    scenarios = []
    
    while True:
        console.print("\n[bold cyan]Options:[/]")
        console.print("  1. Add scenario")
        console.print("  2. Simulate all scenarios")
        console.print("  3. Compare scenarios")
        console.print("  4. Clear scenarios")
        console.print("  5. Exit")
        
        choice = Prompt.ask("Select", choices=["1", "2", "3", "4", "5"], default="1")
        
        if choice == "1":
            # Add scenario
            name = Prompt.ask("Scenario name")
            actor = Prompt.ask("Actor (e.g., China, Philippines)")
            domain = Prompt.ask(
                "Action domain",
                choices=["military", "law_enforcement", "legal", "diplomatic", "economic", "information"],
                default="law_enforcement"
            )
            target = Prompt.ask("Target (e.g., Philippines, Vietnam)")
            description = Prompt.ask("Description")
            
            scenario = Scenario(
                name=name,
                actor=actor.lower(),
                action_domain=domain,
                target=target.lower(),
                description=description
            )
            scenarios.append(scenario)
            console.print(f"[green]Added scenario: {name}[/]")
        
        elif choice == "2":
            # Simulate all
            if not scenarios:
                console.print("[yellow]No scenarios defined[/]")
                continue
            
            for scenario in scenarios:
                result = simulator.simulate(scenario)
                _display_result(result)
        
        elif choice == "3":
            # Compare
            if len(scenarios) < 2:
                console.print("[yellow]Need at least 2 scenarios to compare[/]")
                continue
            
            results = simulator.compare_scenarios(scenarios)
            _display_comparison(results)
        
        elif choice == "4":
            scenarios = []
            console.print("[green]Scenarios cleared[/]")
        
        elif choice == "5":
            break
    
    console.print("[dim]Simulation ended[/]")


def _display_result(result: SimulationResult):
    """Display simulation result."""
    console.print(Panel(f"[bold]{result.scenario.name}[/]"))
    
    console.print(f"[cyan]Actor:[/] {result.scenario.actor}")
    console.print(f"[cyan]Action:[/] {result.scenario.action_domain}")
    console.print(f"[cyan]Target:[/] {result.scenario.target}")
    console.print(f"[cyan]Description:[/] {result.scenario.description}")
    
    # Escalation risk
    risk_color = {"LOW": "green", "MEDIUM": "yellow", "HIGH": "red"}[result.escalation_risk]
    console.print(f"\n[{risk_color}]Escalation Risk: {result.escalation_risk}[/]")
    console.print(f"[dim]Historical precedents: {result.historical_precedents}[/]")
    
    # Likely responses
    console.print("\n[bold]Likely Responses:[/]")
    table = Table()
    table.add_column("Domain", style="cyan")
    table.add_column("Probability", justify="right")
    table.add_column("Historical", justify="right")
    
    for resp in result.likely_responses[:3]:
        table.add_row(
            resp["domain"],
            f"{resp['probability']:.0%}",
            str(resp["historical_count"])
        )
    console.print(table)
    
    # Countermeasures
    console.print("\n[bold]Recommended Countermeasures:[/]")
    for cm in result.recommended_countermeasures[:3]:
        console.print(f"  • {cm}")


def _display_comparison(results: List[SimulationResult]):
    """Display comparison of multiple scenarios."""
    console.print(Panel("[bold]Scenario Comparison[/]"))
    
    table = Table()
    table.add_column("Scenario", style="cyan")
    table.add_column("Domain", style="green")
    table.add_column("Risk", justify="center")
    table.add_column("Top Response")
    table.add_column("Precedents", justify="right")
    
    for result in results:
        risk_color = {"LOW": "green", "MEDIUM": "yellow", "HIGH": "red"}[result.escalation_risk]
        top_resp = result.likely_responses[0]["domain"] if result.likely_responses else "-"
        
        table.add_row(
            result.scenario.name,
            result.scenario.action_domain,
            f"[{risk_color}]{result.escalation_risk}[/]",
            top_resp,
            str(result.historical_precedents)
        )
    
    console.print(table)
    
    # Recommendation
    lowest_risk = min(results, key=lambda r: {"LOW": 0, "MEDIUM": 1, "HIGH": 2}[r.escalation_risk])
    console.print(f"\n[green]Lowest risk scenario:[/] {lowest_risk.scenario.name}")
