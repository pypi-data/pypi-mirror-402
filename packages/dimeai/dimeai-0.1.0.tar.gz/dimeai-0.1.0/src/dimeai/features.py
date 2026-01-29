"""
Semantic feature engineering for graph nodes
"""
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

console = Console()

# Try to import sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    SBERT_AVAILABLE = True
except ImportError:
    SBERT_AVAILABLE = False


@dataclass
class NodeFeatures:
    """Features for a graph node."""
    node_id: str
    embedding: np.ndarray
    centrality: float = 0.0
    degree: int = 0
    domain_distribution: Optional[Dict[str, float]] = None


class SemanticFeatureExtractor:
    """Extract semantic features using sentence-transformers."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", verbose: bool = False):
        if not SBERT_AVAILABLE:
            raise ImportError("sentence-transformers not installed. Run: pip install sentence-transformers")
        
        self.verbose = verbose
        if verbose:
            console.print(f"[dim]Loading embedding model: {model_name}[/]")
        
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        
        if verbose:
            console.print(f"[green]Model loaded (dim={self.embedding_dim})[/]")
    
    def embed_text(self, text: str) -> np.ndarray:
        """Get embedding for text."""
        return self.model.encode(text, convert_to_numpy=True)
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Get embeddings for batch of texts."""
        return self.model.encode(texts, convert_to_numpy=True, show_progress_bar=self.verbose)


class GraphFeatureComputer:
    """Compute graph-based features."""
    
    def __init__(self, graph_data: Dict[str, Any]):
        import networkx as nx
        
        self.graph = nx.DiGraph()
        
        # Build graph
        for node in graph_data.get("nodes", []):
            self.graph.add_node(node["id"], **{k: v for k, v in node.items() if k != "id"})
        
        for edge in graph_data.get("edges", []):
            self.graph.add_edge(edge["source"], edge["target"], 
                              **{k: v for k, v in edge.items() if k not in ["source", "target"]})
    
    def compute_centrality(self) -> Dict[str, float]:
        """Compute PageRank centrality for all nodes."""
        import networkx as nx
        try:
            return nx.pagerank(self.graph, alpha=0.85)
        except:
            # Fallback for disconnected graphs
            return {n: 1.0 / len(self.graph) for n in self.graph.nodes()}
    
    def compute_degree(self) -> Dict[str, int]:
        """Compute degree for all nodes."""
        return dict(self.graph.degree())
    
    def get_neighbors(self, node_id: str) -> List[str]:
        """Get neighbors of a node."""
        if node_id not in self.graph:
            return []
        return list(self.graph.predecessors(node_id)) + list(self.graph.successors(node_id))
    
    def compute_adamic_adar(self, node1: str, node2: str) -> float:
        """Compute Adamic-Adar score between two nodes."""
        import networkx as nx
        
        if node1 not in self.graph or node2 not in self.graph:
            return 0.0
        
        # Get common neighbors (treating as undirected)
        neighbors1 = set(self.graph.predecessors(node1)) | set(self.graph.successors(node1))
        neighbors2 = set(self.graph.predecessors(node2)) | set(self.graph.successors(node2))
        common = neighbors1 & neighbors2
        
        score = 0.0
        for neighbor in common:
            degree = self.graph.degree(neighbor)
            if degree > 1:
                score += 1.0 / np.log(degree)
        
        return score
    
    def get_domain_distribution(self, node_id: str) -> Dict[str, float]:
        """Get distribution of DIMEFIL domains for actions connected to this node."""
        if node_id not in self.graph:
            return {}
        
        domains = []
        
        # Check outgoing edges (performs)
        for _, target, data in self.graph.out_edges(node_id, data=True):
            if data.get("relation") == "performs":
                target_data = self.graph.nodes.get(target, {})
                if target_data.get("node_type") == "action":
                    domain = target_data.get("dimefil_domain", "unknown")
                    domains.append(domain)
        
        # Check incoming edges (targets)
        for source, _, data in self.graph.in_edges(node_id, data=True):
            if data.get("relation") == "targets":
                source_data = self.graph.nodes.get(source, {})
                if source_data.get("node_type") == "action":
                    domain = source_data.get("dimefil_domain", "unknown")
                    domains.append(domain)
        
        if not domains:
            return {}
        
        # Compute distribution
        from collections import Counter
        counts = Counter(domains)
        total = sum(counts.values())
        return {k: v / total for k, v in counts.items()}


def compute_features(
    graph_path: str,
    output_path: str,
    embedding_model: str = "all-MiniLM-L6-v2",
    verbose: bool = False
) -> None:
    """Compute semantic and graph features for all nodes.
    
    Args:
        graph_path: Path to extracted graph JSON
        output_path: Path to save features
        embedding_model: Sentence transformer model name
        verbose: Enable verbose output
    """
    # Load graph
    graph_file = Path(graph_path)
    if not graph_file.exists():
        console.print(f"[red]Graph file not found: {graph_path}[/]")
        return
    
    with open(graph_file) as f:
        graph_data = json.load(f)
    
    nodes = graph_data.get("nodes", [])
    console.print(f"Loaded graph with [cyan]{len(nodes)}[/] nodes")
    
    # Initialize feature extractors
    try:
        semantic = SemanticFeatureExtractor(model_name=embedding_model, verbose=verbose)
    except ImportError as e:
        console.print(f"[red]{e}[/]")
        return
    
    graph_features = GraphFeatureComputer(graph_data)
    
    # Compute graph-level features
    console.print("[dim]Computing graph features...[/]")
    centrality = graph_features.compute_centrality()
    degrees = graph_features.compute_degree()
    
    # Compute embeddings for each node
    features = {}
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Computing embeddings...", total=len(nodes))
        
        for node in nodes:
            node_id = node["id"]
            node_type = node.get("node_type", "unknown")
            label = node.get("label", node_id)
            
            # Create text representation for embedding
            if node_type == "actor":
                text = f"{label} ({node.get('actor_type', 'entity')})"
            elif node_type == "action":
                domain = node.get("dimefil_domain", "unknown")
                patterns = node.get("patterns", "")
                text = f"{domain} action: {patterns}" if patterns else f"{domain} action"
            elif node_type == "location":
                text = f"Location: {label}"
            elif node_type == "temporal":
                text = f"Date: {label}"
            else:
                text = label
            
            # Compute embedding
            embedding = semantic.embed_text(text)
            
            # Get domain distribution for actors
            domain_dist = None
            if node_type == "actor":
                domain_dist = graph_features.get_domain_distribution(node_id)
            
            features[node_id] = {
                "embedding": embedding.tolist(),
                "centrality": centrality.get(node_id, 0.0),
                "degree": degrees.get(node_id, 0),
                "node_type": node_type,
                "domain_distribution": domain_dist
            }
            
            progress.update(task, advance=1)
    
    # Save features
    output_file = Path(output_path)
    with open(output_file, 'w') as f:
        json.dump({
            "embedding_model": embedding_model,
            "embedding_dim": semantic.embedding_dim,
            "num_nodes": len(features),
            "features": features
        }, f)
    
    # Show stats
    table = Table(title="Feature Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="green")
    
    table.add_row("Nodes with features", str(len(features)))
    table.add_row("Embedding dimension", str(semantic.embedding_dim))
    table.add_row("Avg centrality", f"{np.mean(list(centrality.values())):.4f}")
    table.add_row("Avg degree", f"{np.mean(list(degrees.values())):.1f}")
    
    # Count by node type
    type_counts = {}
    for node_id, feat in features.items():
        nt = feat.get("node_type", "unknown")
        type_counts[nt] = type_counts.get(nt, 0) + 1
    
    table.add_row("", "")
    for nt, count in sorted(type_counts.items()):
        table.add_row(f"  {nt}", str(count))
    
    console.print(table)
    console.print(f"\n[green]Features saved to:[/] {output_path}")


def inspect_features(features_path: str, node_id: str) -> None:
    """Inspect features for a specific node."""
    features_file = Path(features_path)
    if not features_file.exists():
        console.print(f"[red]Features file not found: {features_path}[/]")
        return
    
    with open(features_file) as f:
        data = json.load(f)
    
    features = data.get("features", {})
    
    if node_id not in features:
        console.print(f"[yellow]Node not found: {node_id}[/]")
        # Show similar nodes
        similar = [n for n in features.keys() if node_id.lower() in n.lower()][:5]
        if similar:
            console.print(f"[dim]Similar nodes: {similar}[/]")
        return
    
    feat = features[node_id]
    
    table = Table(title=f"Features for: {node_id}")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Node type", feat.get("node_type", "unknown"))
    table.add_row("Centrality", f"{feat.get('centrality', 0):.4f}")
    table.add_row("Degree", str(feat.get("degree", 0)))
    
    embedding = feat.get("embedding", [])
    table.add_row("Embedding dim", str(len(embedding)))
    table.add_row("Embedding (first 5)", str(embedding[:5]))
    
    domain_dist = feat.get("domain_distribution")
    if domain_dist:
        table.add_row("", "")
        table.add_row("[bold]Domain Distribution[/]", "")
        for domain, prob in sorted(domain_dist.items(), key=lambda x: -x[1]):
            table.add_row(f"  {domain}", f"{prob:.1%}")
    
    console.print(table)
