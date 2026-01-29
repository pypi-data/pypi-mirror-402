"""
Entity and relationship extraction using GLiNER 2
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

console = Console()

# Try to import GLiNER2
try:
    from gliner2 import GLiNER2
    GLINER2_AVAILABLE = True
except ImportError:
    GLINER2_AVAILABLE = False


def classify_dimefil_domain(text: str) -> str:
    """Classify text into DIMEFIL domain.
    
    Standalone function for use without loading GLiNER model.
    """
    text_lower = text.lower()
    
    scores = {
        "military": 0, "law_enforcement": 0, "legal": 0,
        "economic": 0, "information": 0, "diplomatic": 0
    }
    
    # Military
    for kw in ["military exercise", "naval drill", "bomber", "fighter jet", "warship", "missile", "blockade"]:
        if kw in text_lower:
            scores["military"] += 3
    for kw in ["exercise", "drill", "navy", "troops", "carrier"]:
        if kw in text_lower:
            scores["military"] += 1
    
    # Law Enforcement
    for kw in ["water cannon", "coast guard fired", "rammed", "collision", "expelled", "seized"]:
        if kw in text_lower:
            scores["law_enforcement"] += 3
    for kw in ["coast guard", "patrol", "enforcement", "intercept"]:
        if kw in text_lower:
            scores["law_enforcement"] += 1
    
    # Legal
    for kw in ["tribunal ruling", "arbitration", "unclos", "international court"]:
        if kw in text_lower:
            scores["legal"] += 3
    for kw in ["tribunal", "ruling", "legal", "jurisdiction"]:
        if kw in text_lower:
            scores["legal"] += 1
    
    # Economic
    for kw in ["fishing fleet", "illegal fishing", "fishing rights", "oil drilling"]:
        if kw in text_lower:
            scores["economic"] += 3
    for kw in ["fishing", "trade", "economic", "sanction"]:
        if kw in text_lower:
            scores["economic"] += 1
    
    # Information
    for kw in ["disinformation", "propaganda campaign", "information warfare"]:
        if kw in text_lower:
            scores["information"] += 3
    for kw in ["propaganda", "narrative", "misinformation"]:
        if kw in text_lower:
            scores["information"] += 1
    
    # Diplomatic
    for kw in ["diplomatic protest", "bilateral talks", "code of conduct"]:
        if kw in text_lower:
            scores["diplomatic"] += 2
    for kw in ["diplomat", "ambassador", "talks", "summit"]:
        if kw in text_lower:
            scores["diplomatic"] += 0.5
    
    max_score = max(scores.values())
    if max_score == 0:
        return "diplomatic"
    
    for domain, score in scores.items():
        if score == max_score:
            return domain
    return "diplomatic"


@dataclass
class ExtractionResult:
    """Result from entity extraction."""
    entities: Dict[str, List[str]]
    dimefil_domain: str
    patterns: List[str]
    source_file: str


class GLiNERExtractor:
    """GLiNER2-based entity and relationship extractor."""
    
    ENTITY_LABELS = [
        "country",
        "government_body",
        "spokesperson",
        "military_unit",
        "coast_guard",
        "disputed_territory",
        "sea_region",
        "city",
        "date",
        "military_asset"
    ]
    
    def __init__(self, model_id: str = "fastino/gliner2-base-v1", verbose: bool = False):
        if not GLINER2_AVAILABLE:
            raise ImportError("gliner2 not installed. Run: pip install gliner2")
        
        self.verbose = verbose
        if verbose:
            console.print(f"[dim]Loading GLiNER2 model: {model_id}[/]")
        
        self.model = GLiNER2.from_pretrained(model_id)
        
        if verbose:
            console.print("[green]Model loaded[/]")
    
    def _chunk_text(self, text: str, max_chars: int = 2000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks."""
        if len(text) <= max_chars:
            return [text]
        
        chunks = []
        start = 0
        while start < len(text):
            end = start + max_chars
            if end < len(text):
                last_period = text.rfind('. ', max(end - 200, start), end)
                if last_period > start:
                    end = last_period + 1
            chunks.append(text[start:end])
            start = end - overlap if end < len(text) else end
        
        return chunks
    
    def _is_valid_entity(self, text: str) -> bool:
        """Check if entity text is valid."""
        if not text or not isinstance(text, str):
            return False
        text = text.strip()
        if any(x in text.lower() for x in ['http', 'www.', '.com', '.org', '.html']):
            return False
        if text.count('-') >= 3 and len(text) > 25:
            return False
        if len(text) < 2:
            return False
        return True
    
    def _classify_dimefil(self, text: str) -> str:
        """Classify text into DIMEFIL domain."""
        text_lower = text.lower()
        
        scores = {
            "military": 0, "law_enforcement": 0, "legal": 0,
            "economic": 0, "information": 0, "diplomatic": 0
        }
        
        # Military
        for kw in ["military exercise", "naval drill", "bomber", "fighter jet", "warship", "missile", "blockade"]:
            if kw in text_lower:
                scores["military"] += 3
        for kw in ["exercise", "drill", "navy", "troops", "carrier"]:
            if kw in text_lower:
                scores["military"] += 1
        
        # Law Enforcement
        for kw in ["water cannon", "coast guard fired", "rammed", "collision", "expelled", "seized"]:
            if kw in text_lower:
                scores["law_enforcement"] += 3
        for kw in ["coast guard", "patrol", "enforcement", "intercept"]:
            if kw in text_lower:
                scores["law_enforcement"] += 1
        
        # Legal
        for kw in ["tribunal ruling", "arbitration", "unclos", "international court"]:
            if kw in text_lower:
                scores["legal"] += 3
        for kw in ["tribunal", "ruling", "legal", "jurisdiction"]:
            if kw in text_lower:
                scores["legal"] += 1
        
        # Economic
        for kw in ["fishing fleet", "illegal fishing", "fishing rights", "oil drilling"]:
            if kw in text_lower:
                scores["economic"] += 3
        for kw in ["fishing", "trade", "economic", "sanction"]:
            if kw in text_lower:
                scores["economic"] += 1
        
        # Information
        for kw in ["disinformation", "propaganda campaign", "information warfare"]:
            if kw in text_lower:
                scores["information"] += 3
        for kw in ["propaganda", "narrative", "misinformation"]:
            if kw in text_lower:
                scores["information"] += 1
        
        # Diplomatic
        for kw in ["diplomatic protest", "bilateral talks", "code of conduct"]:
            if kw in text_lower:
                scores["diplomatic"] += 2
        for kw in ["diplomat", "ambassador", "talks", "summit"]:
            if kw in text_lower:
                scores["diplomatic"] += 0.5
        
        max_score = max(scores.values())
        if max_score == 0:
            return "diplomatic"
        
        for domain, score in scores.items():
            if score == max_score:
                return domain
        return "diplomatic"
    
    def _detect_patterns(self, text: str) -> List[str]:
        """Detect strategic patterns in text."""
        text_lower = text.lower()
        patterns = []
        
        pattern_keywords = {
            "fait_accompli": ["seized control", "occupied", "built artificial", "established presence"],
            "grey_zone_coercion": ["water cannon", "dangerous maneuver", "rammed", "blocked passage"],
            "escalation": ["in retaliation", "escalated tensions", "military response"],
            "deterrence_signaling": ["military drill", "naval exercise", "show of force"],
            "coalition_balancing": ["trilateral", "quadrilateral", "allied forces", "joint patrol"],
            "legal_warfare": ["tribunal ruled", "arbitration ruling", "unclos violation"]
        }
        
        for pattern, keywords in pattern_keywords.items():
            if any(kw in text_lower for kw in keywords):
                patterns.append(pattern)
        
        return patterns
    
    def extract(self, text: str, threshold: float = 0.3) -> Dict[str, Any]:
        """Extract entities from text using GLiNER2."""
        chunks = self._chunk_text(text, max_chars=2000, overlap=200)
        
        all_entities: Dict[str, set] = {label: set() for label in self.ENTITY_LABELS}
        
        for chunk in chunks:
            try:
                result = self.model.extract_entities(chunk, self.ENTITY_LABELS, threshold=threshold)
                entities_dict = result.get('entities', {})
                
                for label, entities in entities_dict.items():
                    for ent in entities:
                        if isinstance(ent, dict):
                            entity_text = ent.get('text', ent.get('entity', ''))
                        else:
                            entity_text = str(ent)
                        
                        if self._is_valid_entity(entity_text):
                            all_entities[label].add(entity_text)
            except Exception as e:
                if self.verbose:
                    console.print(f"[yellow]Chunk extraction warning: {e}[/]")
                continue
        
        # Convert sets to lists
        grouped = {k: list(v) for k, v in all_entities.items() if v}
        
        return {
            "entities": grouped,
            "dimefil_domain": self._classify_dimefil(text),
            "patterns": self._detect_patterns(text)
        }
    
    def extract_file(self, filepath: Path) -> Optional[ExtractionResult]:
        """Extract entities from a single article file."""
        try:
            content = filepath.read_text(encoding='utf-8')
            
            # Skip metadata header
            lines = content.split('\n')
            body_start = 0
            for i, line in enumerate(lines):
                if line.startswith('Content Length:'):
                    body_start = i + 2
                    break
            body = '\n'.join(lines[body_start:])
            
            if len(body) < 100:
                return None
            
            result = self.extract(body)
            
            return ExtractionResult(
                entities=result['entities'],
                dimefil_domain=result['dimefil_domain'],
                patterns=result['patterns'],
                source_file=str(filepath)
            )
        except Exception as e:
            if self.verbose:
                console.print(f"[red]Error extracting {filepath}: {e}[/]")
            return None


class GraphBuilder:
    """Build NetworkX graph from extraction results."""
    
    def __init__(self):
        import networkx as nx
        self.graph = nx.DiGraph()
        self.action_counter = 0
    
    def _normalize_id(self, name: str) -> str:
        """Normalize entity name to ID."""
        if not name:
            return ""
        import re
        name_lower = name.lower()
        
        # Entity resolution
        if name_lower in ["beijing", "prc"]:
            return "china"
        if name_lower == "manila":
            return "philippines"
        
        return re.sub(r'[^a-z0-9_]', '', name_lower.replace(" ", "_"))
    
    def add_extraction(self, result: ExtractionResult) -> None:
        """Add extraction result to graph."""
        entities = result.entities
        
        # Add actor nodes
        actor_types = ["country", "government_body", "spokesperson", "military_unit", "coast_guard"]
        for entity_type in actor_types:
            for entity_name in entities.get(entity_type, []):
                actor_id = self._normalize_id(entity_name)
                if actor_id and actor_id not in self.graph:
                    self.graph.add_node(
                        actor_id,
                        node_type="actor",
                        label=entity_name,
                        actor_type=entity_type
                    )
        
        # Add location nodes
        locations = entities.get("disputed_territory", []) + entities.get("sea_region", [])
        for loc in locations:
            loc_id = self._normalize_id(loc)
            if loc_id and loc_id not in self.graph:
                self.graph.add_node(loc_id, node_type="location", label=loc)
        
        # Add temporal nodes
        for date in entities.get("date", []):
            date_id = self._normalize_id(date)
            if date_id and date_id not in self.graph:
                self.graph.add_node(date_id, node_type="temporal", label=date)
        
        # Create action node if we have countries
        countries = entities.get("country", [])
        valid_countries = [c for c in countries if self._normalize_id(c) in self.graph]
        
        if len(valid_countries) >= 2:
            self.action_counter += 1
            action_id = f"ACT-{self.action_counter:04d}"
            
            self.graph.add_node(
                action_id,
                node_type="action",
                dimefil_domain=result.dimefil_domain,
                patterns=",".join(result.patterns),
                source=result.source_file
            )
            
            # Connect initiator
            init_id = self._normalize_id(valid_countries[0])
            self.graph.add_edge(init_id, action_id, relation="performs")
            
            # Connect targets
            for target in valid_countries[1:]:
                target_id = self._normalize_id(target)
                if target_id in self.graph:
                    self.graph.add_edge(action_id, target_id, relation="targets")
            
            # Connect to location
            if locations:
                loc_id = self._normalize_id(locations[0])
                if loc_id in self.graph:
                    self.graph.add_edge(action_id, loc_id, relation="located_at")
            
            # Connect to dates
            for date in entities.get("date", []):
                date_id = self._normalize_id(date)
                if date_id in self.graph:
                    self.graph.add_edge(action_id, date_id, relation="occurred_at")
    
    def export_json(self) -> str:
        """Export graph as JSON."""
        nodes = [{"id": n, **d} for n, d in self.graph.nodes(data=True)]
        edges = [{"source": s, "target": t, **d} for s, t, d in self.graph.edges(data=True)]
        return json.dumps({"nodes": nodes, "edges": edges}, indent=2)
    
    def get_stats(self) -> Dict[str, int]:
        """Get graph statistics."""
        nodes = list(self.graph.nodes(data=True))
        return {
            "total_nodes": len(nodes),
            "total_edges": self.graph.number_of_edges(),
            "actors": sum(1 for _, d in nodes if d.get("node_type") == "actor"),
            "actions": sum(1 for _, d in nodes if d.get("node_type") == "action"),
            "locations": sum(1 for _, d in nodes if d.get("node_type") == "location"),
            "temporal": sum(1 for _, d in nodes if d.get("node_type") == "temporal"),
        }


def run_extraction(
    input_dir: str,
    output: str,
    model: str = "fastino/gliner2-base-v1",
    verbose: bool = False
) -> None:
    """Extract entities and relationships from articles.
    
    Args:
        input_dir: Directory containing article files
        output: Output path for extracted graph
        model: GLiNER model identifier
        verbose: Enable verbose output
    """
    input_path = Path(input_dir)
    if not input_path.exists():
        console.print(f"[red]Input directory not found: {input_dir}[/]")
        return
    
    article_files = list(input_path.glob("*.txt"))
    if not article_files:
        console.print(f"[yellow]No .txt files found in {input_dir}[/]")
        return
    
    console.print(f"Found [cyan]{len(article_files)}[/] articles")
    
    try:
        extractor = GLiNERExtractor(model_id=model, verbose=verbose)
    except ImportError as e:
        console.print(f"[red]{e}[/]")
        return
    
    builder = GraphBuilder()
    extracted_count = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Extracting...", total=len(article_files))
        
        for filepath in article_files:
            result = extractor.extract_file(filepath)
            if result:
                builder.add_extraction(result)
                extracted_count += 1
            progress.update(task, advance=1)
    
    # Save graph
    output_path = Path(output)
    output_path.write_text(builder.export_json(), encoding='utf-8')
    
    # Show stats
    stats = builder.get_stats()
    
    table = Table(title="Extraction Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", justify="right", style="green")
    
    table.add_row("Articles processed", str(len(article_files)))
    table.add_row("Successful extractions", str(extracted_count))
    table.add_row("", "")
    table.add_row("Total nodes", str(stats["total_nodes"]))
    table.add_row("  Actors", str(stats["actors"]))
    table.add_row("  Actions", str(stats["actions"]))
    table.add_row("  Locations", str(stats["locations"]))
    table.add_row("  Temporal", str(stats["temporal"]))
    table.add_row("Total edges", str(stats["total_edges"]))
    
    console.print(table)
    console.print(f"\n[green]Graph saved to:[/] {output}")
