"""
Agent tools for analysis and prediction
"""
import json
import torch
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict, Counter

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


@dataclass
class PredictionResult:
    """Result from event prediction."""
    actor: str
    target: str
    domain: str
    probability: float
    historical_count: int
    reasoning: str


@dataclass
class ActorProfile:
    """Profile of an actor's behavior."""
    actor_id: str
    total_actions: int
    domain_distribution: Dict[str, float]
    top_targets: List[Tuple[str, int]]
    centrality: float


class GraphAnalyzer:
    """Analyze graph for predictions and insights."""
    
    def __init__(self, graph_path: str, model_path: Optional[str] = None):
        with open(graph_path) as f:
            self.graph_data = json.load(f)
        
        self.nodes = {n["id"]: n for n in self.graph_data.get("nodes", [])}
        self.edges = self.graph_data.get("edges", [])
        
        # Build indices
        self._build_indices()
        
        # Load model if available
        self.model = None
        self.model_data = None
        if model_path and Path(model_path).exists():
            self._load_model(model_path)
    
    def _build_indices(self):
        """Build lookup indices for fast queries."""
        self.performs = defaultdict(list)  # actor -> [action_ids]
        self.targets = defaultdict(list)   # action -> [target_ids]
        self.targeted_by = defaultdict(list)  # target -> [action_ids]
        
        for edge in self.edges:
            rel = edge.get("relation", "")
            if rel == "performs":
                self.performs[edge["source"]].append(edge["target"])
            elif rel == "targets":
                self.targets[edge["source"]].append(edge["target"])
                self.targeted_by[edge["target"]].append(edge["source"])
        
        # Actor-to-actor interactions
        self.actor_interactions = defaultdict(lambda: defaultdict(list))
        for actor, actions in self.performs.items():
            for action_id in actions:
                action_data = self.nodes.get(action_id, {})
                domain = action_data.get("dimefil_domain", "unknown")
                for target in self.targets.get(action_id, []):
                    self.actor_interactions[actor][target].append(domain)
        
        # Compute centrality (simple degree-based)
        self.centrality = {}
        for node_id in self.nodes:
            in_degree = sum(1 for e in self.edges if e.get("target") == node_id)
            out_degree = sum(1 for e in self.edges if e.get("source") == node_id)
            self.centrality[node_id] = in_degree + out_degree
        
        max_cent = max(self.centrality.values()) if self.centrality else 1
        self.centrality = {k: v / max_cent for k, v in self.centrality.items()}
    
    def _load_model(self, model_path: str):
        """Load trained model."""
        try:
            from dimeai.training import SimpleTGN
            
            self.model_data = torch.load(model_path)
            self.model = SimpleTGN(
                input_dim=self.model_data["input_dim"],
                hidden_dim=self.model_data["hidden_dim"],
                num_classes=self.model_data["num_classes"]
            )
            self.model.load_state_dict(self.model_data["model_state"])
            self.model.eval()
        except Exception as e:
            console.print(f"[yellow]Could not load model: {e}[/]")
            self.model = None
    
    def get_actor_profile(self, actor_id: str) -> Optional[ActorProfile]:
        """Get profile for an actor."""
        actor_id = actor_id.lower().replace(" ", "_")
        
        if actor_id not in self.nodes:
            # Try fuzzy match
            matches = [n for n in self.nodes if actor_id in n.lower()]
            if matches:
                actor_id = matches[0]
            else:
                return None
        
        # Count actions by domain
        domain_counts = Counter()
        for action_id in self.performs.get(actor_id, []):
            action_data = self.nodes.get(action_id, {})
            domain = action_data.get("dimefil_domain", "unknown")
            domain_counts[domain] += 1
        
        total = sum(domain_counts.values())
        if total == 0:
            return None
        
        domain_dist = {k: v / total for k, v in domain_counts.items()}
        
        # Get top targets
        target_counts = Counter()
        for target, domains in self.actor_interactions.get(actor_id, {}).items():
            target_counts[target] = len(domains)
        
        top_targets = target_counts.most_common(5)
        
        return ActorProfile(
            actor_id=actor_id,
            total_actions=total,
            domain_distribution=domain_dist,
            top_targets=top_targets,
            centrality=self.centrality.get(actor_id, 0.0)
        )
    
    def predict_next_events(
        self, 
        focus_actor: Optional[str] = None,
        focus_domain: Optional[str] = None,
        num_predictions: int = 5
    ) -> List[PredictionResult]:
        """Predict likely next events based on historical patterns."""
        predictions = []
        
        # Score all actor pairs
        scored_pairs = []
        
        actors = [n_id for n_id, n in self.nodes.items() 
                 if n.get("node_type") == "actor" and n.get("actor_type") == "country"]
        
        if focus_actor:
            focus_actor = focus_actor.lower().replace(" ", "_")
            if focus_actor not in actors:
                matches = [a for a in actors if focus_actor in a.lower()]
                if matches:
                    focus_actor = matches[0]
        
        for actor in actors:
            if focus_actor and actor != focus_actor:
                continue
            
            for target in actors:
                if actor == target:
                    continue
                
                # Get historical interactions
                interactions = self.actor_interactions.get(actor, {}).get(target, [])
                
                if not interactions:
                    continue
                
                # Score based on:
                # 1. Historical frequency
                # 2. Recency (more recent = higher weight)
                # 3. Actor centrality
                
                domain_counts = Counter(interactions)
                total = len(interactions)
                
                for domain, count in domain_counts.items():
                    if focus_domain and domain != focus_domain:
                        continue
                    
                    # Probability based on historical frequency
                    prob = count / total
                    
                    # Boost by centrality
                    actor_cent = self.centrality.get(actor, 0.1)
                    target_cent = self.centrality.get(target, 0.1)
                    
                    score = prob * (1 + actor_cent + target_cent)
                    
                    scored_pairs.append({
                        "actor": actor,
                        "target": target,
                        "domain": domain,
                        "score": score,
                        "count": count,
                        "total": total
                    })
        
        # Sort by score
        scored_pairs.sort(key=lambda x: -x["score"])
        
        # Convert to predictions
        for pair in scored_pairs[:num_predictions]:
            reasoning = (
                f"Historical: {pair['count']}/{pair['total']} interactions were {pair['domain']}. "
                f"Actor centrality: {self.centrality.get(pair['actor'], 0):.2f}"
            )
            
            predictions.append(PredictionResult(
                actor=pair["actor"],
                target=pair["target"],
                domain=pair["domain"],
                probability=pair["score"],
                historical_count=pair["count"],
                reasoning=reasoning
            ))
        
        return predictions
    
    def find_similar_situations(self, description: str, top_k: int = 5) -> List[Dict]:
        """Find historical situations similar to description."""
        # Simple keyword matching
        keywords = description.lower().split()
        
        similar = []
        
        for node_id, node in self.nodes.items():
            if node.get("node_type") != "action":
                continue
            
            # Score by keyword overlap
            label = node.get("label", "").lower()
            domain = node.get("dimefil_domain", "").lower()
            patterns = node.get("patterns", "").lower()
            
            text = f"{label} {domain} {patterns}"
            
            score = sum(1 for kw in keywords if kw in text)
            
            if score > 0:
                similar.append({
                    "action_id": node_id,
                    "domain": node.get("dimefil_domain"),
                    "patterns": node.get("patterns"),
                    "score": score
                })
        
        similar.sort(key=lambda x: -x["score"])
        return similar[:top_k]
    
    def get_escalation_risk(self, actor: str, target: str, domain: str) -> Dict[str, Any]:
        """Assess escalation risk for a hypothetical event."""
        actor = actor.lower().replace(" ", "_")
        target = target.lower().replace(" ", "_")
        
        # Historical escalation patterns
        escalation_domains = {"military": 0.7, "law_enforcement": 0.4, "legal": 0.1, 
                            "diplomatic": 0.2, "economic": 0.3, "information": 0.3}
        
        base_risk = escalation_domains.get(domain, 0.3)
        
        # Check historical interactions
        interactions = self.actor_interactions.get(actor, {}).get(target, [])
        
        if interactions:
            # If there's history of military actions, higher risk
            military_ratio = interactions.count("military") / len(interactions)
            base_risk = base_risk * (1 + military_ratio)
        
        # Cap at 1.0
        risk = min(base_risk, 1.0)
        
        risk_level = "LOW" if risk < 0.3 else "MEDIUM" if risk < 0.6 else "HIGH"
        
        return {
            "risk_score": risk,
            "risk_level": risk_level,
            "historical_interactions": len(interactions),
            "reasoning": f"Base risk for {domain}: {escalation_domains.get(domain, 0.3):.0%}, "
                        f"adjusted by historical pattern"
        }


def run_analysis(
    situation: str,
    model_path: str,
    graph_path: str,
    verbose: bool = False
) -> None:
    """Run analysis on a situation using trained model.
    
    Args:
        situation: Description of situation to analyze
        model_path: Path to trained model
        graph_path: Path to graph data
        verbose: Enable verbose output
    """
    console.print(Panel(f"[bold]Analyzing:[/] {situation}"))
    
    # Initialize analyzer
    analyzer = GraphAnalyzer(graph_path, model_path)
    
    # Find similar historical situations
    console.print("\n[bold cyan]Similar Historical Situations:[/]")
    similar = analyzer.find_similar_situations(situation)
    
    if similar:
        table = Table()
        table.add_column("Domain", style="cyan")
        table.add_column("Patterns", style="green")
        table.add_column("Relevance", justify="right")
        
        for s in similar:
            table.add_row(
                s["domain"],
                s["patterns"][:30] if s["patterns"] else "-",
                str(s["score"])
            )
        console.print(table)
    else:
        console.print("[yellow]No similar situations found[/]")
    
    # Predict likely next events
    console.print("\n[bold cyan]Predicted Next Events:[/]")
    predictions = analyzer.predict_next_events(num_predictions=5)
    
    if predictions:
        table = Table()
        table.add_column("Actor", style="cyan")
        table.add_column("Target", style="yellow")
        table.add_column("Domain", style="green")
        table.add_column("Probability", justify="right")
        
        for p in predictions:
            table.add_row(
                p.actor,
                p.target,
                p.domain,
                f"{p.probability:.2f}"
            )
        console.print(table)
    else:
        console.print("[yellow]No predictions available[/]")
    
    # Extract actors from situation for risk assessment
    keywords = situation.lower().split()
    actors = ["china", "philippines", "vietnam", "taiwan", "us"]
    mentioned = [a for a in actors if a in keywords]
    
    if len(mentioned) >= 2:
        console.print("\n[bold cyan]Escalation Risk Assessment:[/]")
        risk = analyzer.get_escalation_risk(mentioned[0], mentioned[1], "law_enforcement")
        
        risk_color = {"LOW": "green", "MEDIUM": "yellow", "HIGH": "red"}[risk["risk_level"]]
        console.print(f"[{risk_color}]Risk Level: {risk['risk_level']} ({risk['risk_score']:.0%})[/]")
        console.print(f"[dim]{risk['reasoning']}[/]")
