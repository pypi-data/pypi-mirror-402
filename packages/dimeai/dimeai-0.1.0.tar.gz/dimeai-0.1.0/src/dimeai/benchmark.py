"""
Benchmark TGN vs baselines
"""
import json
import torch
import numpy as np
from pathlib import Path
from typing import Dict, Any, List
from collections import Counter

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def run_benchmark(graph_path: str, verbose: bool = False) -> Dict[str, Any]:
    """Run benchmark comparing TGN to baselines.
    
    Args:
        graph_path: Path to graph data
        verbose: Enable verbose output
        
    Returns:
        Benchmark results
    """
    from dimeai.training import TemporalGraphDataset, SimpleTGN
    
    console.print(f"Loading graph from [cyan]{graph_path}[/]")
    
    # Load dataset
    dataset = TemporalGraphDataset(graph_path)
    
    console.print(f"  Nodes: {len(dataset.nodes)}")
    console.print(f"  Temporal edges: {len(dataset.temporal_edges)}")
    
    if len(dataset.temporal_edges) < 20:
        console.print("[red]Not enough data for benchmark[/]")
        return {"error": "Insufficient data"}
    
    # Run multiple train/test splits
    results = {
        "random": [],
        "majority": [],
        "tgn": []
    }
    
    splits = [0.5, 0.6, 0.7, 0.8]
    
    for split in splits:
        console.print(f"\n[cyan]Testing split: {split:.0%} train[/]")
        
        train_edges, test_edges = dataset.get_temporal_split(split)
        
        if len(test_edges) < 10:
            console.print(f"  [yellow]Skipping - too few test edges ({len(test_edges)})[/]")
            continue
        
        train_edge_index = dataset.get_edge_index(train_edges)
        test_edge_index = dataset.get_edge_index(test_edges)
        train_labels = dataset.get_edge_labels(train_edges)
        test_labels = dataset.get_edge_labels(test_edges)
        
        x = dataset.node_features
        num_classes = 7
        
        # Random baseline
        random_preds = torch.randint(0, num_classes, (len(test_labels),))
        random_acc = (random_preds == test_labels).float().mean().item()
        results["random"].append(random_acc)
        
        # Majority baseline
        majority_class = train_labels.mode().values.item()
        majority_preds = torch.full_like(test_labels, majority_class)
        majority_acc = (majority_preds == test_labels).float().mean().item()
        results["majority"].append(majority_acc)
        
        # Train TGN
        class_counts = torch.bincount(train_labels, minlength=num_classes)
        class_weights = 1.0 / (class_counts.float() + 1)
        class_weights = class_weights / class_weights.sum() * num_classes
        
        model = SimpleTGN(input_dim=x.shape[1], hidden_dim=128, num_classes=num_classes)
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-5)
        criterion = torch.nn.CrossEntropyLoss(weight=class_weights)
        
        # Quick training
        model.train()
        for epoch in range(50):
            optimizer.zero_grad()
            out = model(x, train_edge_index)
            loss = criterion(out, train_labels)
            loss.backward()
            optimizer.step()
        
        # Evaluate
        model.eval()
        with torch.no_grad():
            test_out = model(x, test_edge_index)
            test_pred = test_out.argmax(dim=1)
            tgn_acc = (test_pred == test_labels).float().mean().item()
        
        results["tgn"].append(tgn_acc)
        
        if verbose:
            console.print(f"  Random: {random_acc:.1%}, Majority: {majority_acc:.1%}, TGN: {tgn_acc:.1%}")
    
    # Summary
    console.print(Panel("[bold]Benchmark Results[/]"))
    
    table = Table(title="Model Performance Across Splits")
    table.add_column("Model", style="cyan")
    table.add_column("Mean Accuracy", justify="right", style="green")
    table.add_column("Std Dev", justify="right")
    table.add_column("Min", justify="right")
    table.add_column("Max", justify="right")
    
    for model_name, accs in results.items():
        if accs:
            mean_acc = np.mean(accs)
            std_acc = np.std(accs)
            min_acc = np.min(accs)
            max_acc = np.max(accs)
            
            table.add_row(
                model_name.upper(),
                f"{mean_acc:.1%}",
                f"{std_acc:.1%}",
                f"{min_acc:.1%}",
                f"{max_acc:.1%}"
            )
    
    console.print(table)
    
    # Statistical comparison
    if results["tgn"] and results["random"]:
        tgn_mean = np.mean(results["tgn"])
        random_mean = np.mean(results["random"])
        improvement = tgn_mean - random_mean
        
        if improvement > 0.05:
            console.print(f"\n[green]✓ TGN beats random by {improvement:.1%}[/]")
        else:
            console.print(f"\n[yellow]⚠ TGN improvement over random: {improvement:.1%}[/]")
    
    return {
        "splits": splits[:len(results["tgn"])],
        "random": results["random"],
        "majority": results["majority"],
        "tgn": results["tgn"],
        "tgn_mean": np.mean(results["tgn"]) if results["tgn"] else 0,
        "random_mean": np.mean(results["random"]) if results["random"] else 0
    }


def test_temporal_leakage(graph_path: str) -> bool:
    """Test that there's no temporal leakage in the split.
    
    Returns True if no leakage detected.
    """
    from dimeai.training import TemporalGraphDataset
    
    dataset = TemporalGraphDataset(graph_path)
    train_edges, test_edges = dataset.get_temporal_split(0.7)
    
    # Check that all train timestamps < all test timestamps
    if not train_edges or not test_edges:
        return True
    
    max_train_ts = max(e.timestamp for e in train_edges)
    min_test_ts = min(e.timestamp for e in test_edges)
    
    no_leakage = max_train_ts < min_test_ts
    
    if no_leakage:
        console.print("[green]✓ No temporal leakage detected[/]")
    else:
        console.print("[red]✗ Temporal leakage detected![/]")
    
    return no_leakage


def test_class_distribution(graph_path: str) -> Dict[str, int]:
    """Analyze class distribution in the dataset."""
    from dimeai.training import TemporalGraphDataset
    
    dataset = TemporalGraphDataset(graph_path)
    
    domain_counts = Counter()
    for edge in dataset.temporal_edges:
        domain_counts[edge.edge_type] += 1
    
    console.print("\n[bold]Class Distribution:[/]")
    table = Table()
    table.add_column("Domain", style="cyan")
    table.add_column("Count", justify="right", style="green")
    table.add_column("Percentage", justify="right")
    
    total = sum(domain_counts.values())
    for domain, count in domain_counts.most_common():
        table.add_row(domain, str(count), f"{count/total:.1%}")
    
    console.print(table)
    
    return dict(domain_counts)
