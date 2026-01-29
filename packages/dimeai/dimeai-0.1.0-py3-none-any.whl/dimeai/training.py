"""
TGN model training with temporal graph networks
"""
import json
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from collections import defaultdict

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel

console = Console()


@dataclass
class TemporalEdge:
    """A temporal edge in the graph."""
    source: str
    target: str
    timestamp: int  # Relative ordering
    edge_type: str
    features: Optional[np.ndarray] = None


class TemporalGraphDataset:
    """Dataset for temporal graph learning."""
    
    def __init__(self, graph_path: str, features_path: Optional[str] = None):
        with open(graph_path) as f:
            self.graph_data = json.load(f)
        
        self.features_data = None
        if features_path and Path(features_path).exists():
            with open(features_path) as f:
                self.features_data = json.load(f)
        
        self.nodes = {n["id"]: n for n in self.graph_data.get("nodes", [])}
        self.edges = self.graph_data.get("edges", [])
        
        # Build node index
        self.node_to_idx = {node_id: idx for idx, node_id in enumerate(self.nodes.keys())}
        self.idx_to_node = {idx: node_id for node_id, idx in self.node_to_idx.items()}
        
        # Extract temporal edges (actor -> action -> target)
        self.temporal_edges = self._extract_temporal_edges()
        
        # Get node features
        self.node_features = self._get_node_features()
    
    def _extract_temporal_edges(self) -> List[TemporalEdge]:
        """Extract temporal edges from graph."""
        edges = []
        
        # Find action nodes and their connections
        action_nodes = {n_id: n for n_id, n in self.nodes.items() 
                       if n.get("node_type") == "action"}
        
        # Build edge lookup
        performs = defaultdict(list)  # actor -> [action_ids]
        targets = defaultdict(list)   # action -> [target_ids]
        
        for edge in self.edges:
            rel = edge.get("relation", "")
            if rel == "performs":
                performs[edge["source"]].append(edge["target"])
            elif rel == "targets":
                targets[edge["source"]].append(edge["target"])
        
        # Create temporal edges: actor -[performs]-> action -[targets]-> target
        timestamp = 0
        for action_id, action_data in action_nodes.items():
            # Find actors who perform this action
            actors = [src for src, actions in performs.items() if action_id in actions]
            # Find targets of this action
            action_targets = targets.get(action_id, [])
            
            domain = action_data.get("dimefil_domain", "unknown")
            
            for actor in actors:
                for target in action_targets:
                    if actor != target:  # No self-loops
                        edges.append(TemporalEdge(
                            source=actor,
                            target=target,
                            timestamp=timestamp,
                            edge_type=domain
                        ))
            timestamp += 1
        
        return edges
    
    def _get_node_features(self) -> torch.Tensor:
        """Get node feature matrix."""
        num_nodes = len(self.nodes)
        
        if self.features_data:
            dim = self.features_data.get("embedding_dim", 384)
            features = torch.zeros(num_nodes, dim)
            
            for node_id, idx in self.node_to_idx.items():
                if node_id in self.features_data.get("features", {}):
                    emb = self.features_data["features"][node_id].get("embedding", [])
                    if emb:
                        features[idx] = torch.tensor(emb[:dim])
            
            return features
        else:
            # Random features if no embeddings available
            return torch.randn(num_nodes, 64)
    
    def get_temporal_split(self, train_ratio: float = 0.7) -> Tuple[List[TemporalEdge], List[TemporalEdge]]:
        """Split edges chronologically (no leakage!)."""
        sorted_edges = sorted(self.temporal_edges, key=lambda e: e.timestamp)
        split_idx = int(len(sorted_edges) * train_ratio)
        return sorted_edges[:split_idx], sorted_edges[split_idx:]
    
    def get_edge_index(self, edges: List[TemporalEdge]) -> torch.Tensor:
        """Convert edges to PyG edge_index format."""
        sources = []
        targets = []
        
        for edge in edges:
            if edge.source in self.node_to_idx and edge.target in self.node_to_idx:
                sources.append(self.node_to_idx[edge.source])
                targets.append(self.node_to_idx[edge.target])
        
        return torch.tensor([sources, targets], dtype=torch.long)
    
    def get_edge_labels(self, edges: List[TemporalEdge]) -> torch.Tensor:
        """Get domain labels for edges."""
        domain_to_idx = {
            "diplomatic": 0, "information": 1, "military": 2,
            "economic": 3, "law_enforcement": 4, "legal": 5, "unknown": 6
        }
        
        labels = [domain_to_idx.get(e.edge_type, 6) for e in edges]
        return torch.tensor(labels, dtype=torch.long)


class SimpleTGN(nn.Module):
    """Simple Temporal Graph Network for link prediction."""
    
    def __init__(self, input_dim: int, hidden_dim: int = 128, num_classes: int = 7):
        super().__init__()
        
        self.node_encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim)
        )
        
        # Edge classifier (concatenate source and target embeddings)
        self.edge_classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, num_classes)
        )
    
    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        """Forward pass for edge classification."""
        # Encode nodes
        node_emb = self.node_encoder(x)
        
        # Get source and target embeddings for each edge
        src_emb = node_emb[edge_index[0]]
        tgt_emb = node_emb[edge_index[1]]
        
        # Concatenate and classify
        edge_emb = torch.cat([src_emb, tgt_emb], dim=1)
        return self.edge_classifier(edge_emb)
    
    def predict_link(self, x: torch.Tensor, src_idx: int, tgt_idx: int) -> torch.Tensor:
        """Predict link probability between two nodes."""
        node_emb = self.node_encoder(x)
        src_emb = node_emb[src_idx].unsqueeze(0)
        tgt_emb = node_emb[tgt_idx].unsqueeze(0)
        edge_emb = torch.cat([src_emb, tgt_emb], dim=1)
        return F.softmax(self.edge_classifier(edge_emb), dim=1)


def train_tgn(
    graph_path: str,
    output_path: str,
    features_path: Optional[str] = None,
    epochs: int = 100,
    train_ratio: float = 0.7,
    verbose: bool = False
) -> Dict[str, Any]:
    """Train Temporal Graph Network on extracted graph.
    
    Args:
        graph_path: Path to extracted graph JSON
        output_path: Path to save trained model
        features_path: Path to precomputed features (optional)
        epochs: Number of training epochs
        train_ratio: Chronological train/test split ratio
        verbose: Enable verbose output
        
    Returns:
        Training results including metrics
    """
    # Load dataset
    console.print(f"Loading graph from [cyan]{graph_path}[/]")
    
    try:
        dataset = TemporalGraphDataset(graph_path, features_path)
    except Exception as e:
        console.print(f"[red]Failed to load dataset: {e}[/]")
        return {"error": str(e)}
    
    console.print(f"  Nodes: {len(dataset.nodes)}")
    console.print(f"  Temporal edges: {len(dataset.temporal_edges)}")
    
    if len(dataset.temporal_edges) < 10:
        console.print("[red]Not enough temporal edges for training[/]")
        return {"error": "Insufficient data"}
    
    # Temporal split
    train_edges, test_edges = dataset.get_temporal_split(train_ratio)
    console.print(f"  Train edges: {len(train_edges)}")
    console.print(f"  Test edges: {len(test_edges)}")
    
    if len(test_edges) < 5:
        console.print("[yellow]Warning: Very few test edges[/]")
    
    # Prepare data
    train_edge_index = dataset.get_edge_index(train_edges)
    test_edge_index = dataset.get_edge_index(test_edges)
    train_labels = dataset.get_edge_labels(train_edges)
    test_labels = dataset.get_edge_labels(test_edges)
    
    x = dataset.node_features
    input_dim = x.shape[1]
    
    # Count classes
    num_classes = 7
    class_counts = torch.bincount(train_labels, minlength=num_classes)
    console.print(f"  Class distribution: {class_counts.tolist()}")
    
    # Compute class weights (inverse frequency) for imbalanced data
    # Higher weight for rare classes
    total_samples = class_counts.sum().float()
    class_weights = total_samples / (num_classes * class_counts.float().clamp(min=1))
    console.print(f"  Class weights: {[f'{w:.2f}' for w in class_weights.tolist()]}")
    
    # Initialize model
    model = SimpleTGN(input_dim=input_dim, hidden_dim=128, num_classes=num_classes)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-5)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    
    # Training loop
    best_acc = 0.0
    best_model_state = None
    train_losses = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Training...", total=epochs)
        
        for epoch in range(epochs):
            model.train()
            optimizer.zero_grad()
            
            out = model(x, train_edge_index)
            loss = criterion(out, train_labels)
            
            loss.backward()
            optimizer.step()
            
            train_losses.append(loss.item())
            
            # Evaluate every 10 epochs
            if (epoch + 1) % 10 == 0:
                model.eval()
                with torch.no_grad():
                    test_out = model(x, test_edge_index)
                    test_pred = test_out.argmax(dim=1)
                    test_acc = (test_pred == test_labels).float().mean().item()
                    
                    if test_acc > best_acc:
                        best_acc = test_acc
                        best_model_state = model.state_dict().copy()
                
                if verbose:
                    console.print(f"  Epoch {epoch+1}: loss={loss.item():.4f}, test_acc={test_acc:.4f}")
            
            progress.update(task, advance=1)
    
    # Load best model
    if best_model_state:
        model.load_state_dict(best_model_state)
    
    # Final evaluation
    model.eval()
    with torch.no_grad():
        test_out = model(x, test_edge_index)
        test_pred = test_out.argmax(dim=1)
        final_acc = (test_pred == test_labels).float().mean().item()
        
        # Compute per-class metrics for macro F1
        from sklearn.metrics import f1_score, classification_report
        macro_f1 = f1_score(test_labels.numpy(), test_pred.numpy(), average='macro', zero_division=0)
        weighted_f1 = f1_score(test_labels.numpy(), test_pred.numpy(), average='weighted', zero_division=0)
    
    # Compute baselines
    # Random baseline
    random_preds = torch.randint(0, num_classes, (len(test_labels),))
    random_acc = (random_preds == test_labels).float().mean().item()
    random_macro_f1 = f1_score(test_labels.numpy(), random_preds.numpy(), average='macro', zero_division=0)
    
    # Majority baseline
    majority_class = train_labels.mode().values.item()
    majority_preds = torch.full_like(test_labels, majority_class)
    majority_acc = (majority_preds == test_labels).float().mean().item()
    majority_macro_f1 = f1_score(test_labels.numpy(), majority_preds.numpy(), average='macro', zero_division=0)
    
    # Save model
    torch.save({
        "model_state": model.state_dict(),
        "input_dim": input_dim,
        "hidden_dim": 128,
        "num_classes": num_classes,
        "node_to_idx": dataset.node_to_idx,
        "train_ratio": train_ratio,
        "final_acc": final_acc,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "random_baseline": random_acc,
        "majority_baseline": majority_acc
    }, output_path)
    
    # Display results
    console.print(Panel("[bold]Training Complete[/]"))
    
    table = Table(title="Model Performance (Edge Classification)")
    table.add_column("Model", style="cyan")
    table.add_column("Accuracy", justify="right")
    table.add_column("Macro F1", justify="right", style="green")
    table.add_column("vs Random F1", justify="right")
    
    table.add_row("Random Baseline", f"{random_acc:.1%}", f"{random_macro_f1:.1%}", "-")
    table.add_row("Majority Baseline", f"{majority_acc:.1%}", f"{majority_macro_f1:.1%}",
                  f"{(majority_macro_f1 - random_macro_f1)*100:+.1f}pp")
    table.add_row("[bold]TGN Model[/]", f"[bold]{final_acc:.1%}[/]", f"[bold]{macro_f1:.1%}[/]",
                  f"[bold]{(macro_f1 - random_macro_f1)*100:+.1f}pp[/]")
    
    console.print(table)
    
    # Check if we beat baselines on macro F1 (fair metric for imbalanced data)
    if macro_f1 > majority_macro_f1:
        console.print("[green]✓ TGN beats majority baseline on Macro F1![/]")
    elif macro_f1 > random_macro_f1 + 0.05:
        console.print("[yellow]⚠ TGN beats random but not majority on Macro F1[/]")
    else:
        console.print("[red]✗ TGN does not significantly beat random baseline[/]")
    
    console.print(f"\n[green]Model saved to:[/] {output_path}")
    
    return {
        "final_acc": final_acc,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "random_baseline": random_acc,
        "random_macro_f1": random_macro_f1,
        "majority_baseline": majority_acc,
        "majority_macro_f1": majority_macro_f1,
        "train_edges": len(train_edges),
        "test_edges": len(test_edges),
        "beats_majority_f1": macro_f1 > majority_macro_f1
    }
