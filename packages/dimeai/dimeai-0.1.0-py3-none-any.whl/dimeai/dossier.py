"""
Dossier Management System

A dossier is a persistent investigation/analysis session that:
- Stores collected articles, extracted entities, and analysis results
- Can be revisited and extended over time
- Supports querying for more data and incremental graph updates
"""
import sqlite3
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from contextlib import contextmanager

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

console = Console()

DEFAULT_DB_PATH = Path.home() / ".dimeai" / "dossiers.db"


@dataclass
class Dossier:
    """A dossier (investigation session)."""
    id: int
    name: str
    description: str
    created_at: str
    updated_at: str
    status: str  # active, archived, closed
    tags: List[str]
    
    @property
    def tag_str(self) -> str:
        return ", ".join(self.tags) if self.tags else ""


@dataclass
class DossierArticle:
    """An article in a dossier."""
    id: int
    dossier_id: int
    title: str
    url: str
    content: str
    domain: str
    collected_at: str
    content_hash: str


@dataclass
class DossierEntity:
    """An extracted entity in a dossier."""
    id: int
    dossier_id: int
    entity_id: str
    entity_type: str
    label: str
    metadata: Dict[str, Any]


@dataclass 
class DossierEvent:
    """An extracted event/action in a dossier."""
    id: int
    dossier_id: int
    event_id: str
    domain: str
    actors: List[str]
    targets: List[str]
    location: Optional[str]
    date: Optional[str]
    patterns: List[str]
    source_article_id: int


@dataclass
class AnalysisNote:
    """An analyst's note on a dossier."""
    id: int
    dossier_id: int
    note_type: str  # observation, hypothesis, conclusion, question
    content: str
    created_at: str
    related_entities: List[str]


class DossierManager:
    """Manage dossiers with SQLite backend."""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    @contextmanager
    def _get_conn(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    def _init_db(self):
        """Initialize database schema."""
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS dossiers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    tags TEXT DEFAULT '[]'
                );
                
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dossier_id INTEGER NOT NULL,
                    title TEXT,
                    url TEXT,
                    content TEXT,
                    domain TEXT,
                    collected_at TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    FOREIGN KEY (dossier_id) REFERENCES dossiers(id),
                    UNIQUE(dossier_id, content_hash)
                );
                
                CREATE TABLE IF NOT EXISTS entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dossier_id INTEGER NOT NULL,
                    entity_id TEXT NOT NULL,
                    entity_type TEXT,
                    label TEXT,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (dossier_id) REFERENCES dossiers(id),
                    UNIQUE(dossier_id, entity_id)
                );
                
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dossier_id INTEGER NOT NULL,
                    event_id TEXT NOT NULL,
                    domain TEXT,
                    actors TEXT DEFAULT '[]',
                    targets TEXT DEFAULT '[]',
                    location TEXT,
                    date TEXT,
                    patterns TEXT DEFAULT '[]',
                    source_article_id INTEGER,
                    FOREIGN KEY (dossier_id) REFERENCES dossiers(id),
                    FOREIGN KEY (source_article_id) REFERENCES articles(id)
                );
                
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dossier_id INTEGER NOT NULL,
                    note_type TEXT DEFAULT 'observation',
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    related_entities TEXT DEFAULT '[]',
                    FOREIGN KEY (dossier_id) REFERENCES dossiers(id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_articles_dossier ON articles(dossier_id);
                CREATE INDEX IF NOT EXISTS idx_entities_dossier ON entities(dossier_id);
                CREATE INDEX IF NOT EXISTS idx_events_dossier ON events(dossier_id);
                CREATE INDEX IF NOT EXISTS idx_notes_dossier ON notes(dossier_id);
            """)
    
    # Dossier CRUD
    def create_dossier(self, name: str, description: str = "", tags: List[str] = None) -> Dossier:
        """Create a new dossier."""
        now = datetime.now().isoformat()
        tags = tags or []
        
        with self._get_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO dossiers (name, description, created_at, updated_at, tags) VALUES (?, ?, ?, ?, ?)",
                (name, description, now, now, json.dumps(tags))
            )
            dossier_id = cursor.lastrowid
        
        return Dossier(
            id=dossier_id, name=name, description=description,
            created_at=now, updated_at=now, status="active", tags=tags
        )
    
    def get_dossier(self, dossier_id: int) -> Optional[Dossier]:
        """Get a dossier by ID."""
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM dossiers WHERE id = ?", (dossier_id,)).fetchone()
            if row:
                return Dossier(
                    id=row["id"], name=row["name"], description=row["description"],
                    created_at=row["created_at"], updated_at=row["updated_at"],
                    status=row["status"], tags=json.loads(row["tags"])
                )
        return None
    
    def get_dossier_by_name(self, name: str) -> Optional[Dossier]:
        """Get a dossier by name."""
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM dossiers WHERE name = ?", (name,)).fetchone()
            if row:
                return Dossier(
                    id=row["id"], name=row["name"], description=row["description"],
                    created_at=row["created_at"], updated_at=row["updated_at"],
                    status=row["status"], tags=json.loads(row["tags"])
                )
        return None
    
    def list_dossiers(self, status: str = None) -> List[Dossier]:
        """List all dossiers."""
        with self._get_conn() as conn:
            if status:
                rows = conn.execute("SELECT * FROM dossiers WHERE status = ? ORDER BY updated_at DESC", (status,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM dossiers ORDER BY updated_at DESC").fetchall()
            
            return [
                Dossier(
                    id=row["id"], name=row["name"], description=row["description"],
                    created_at=row["created_at"], updated_at=row["updated_at"],
                    status=row["status"], tags=json.loads(row["tags"])
                )
                for row in rows
            ]
    
    def update_dossier(self, dossier_id: int, **kwargs) -> None:
        """Update dossier fields."""
        allowed = {"name", "description", "status", "tags"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        
        if not updates:
            return
        
        if "tags" in updates:
            updates["tags"] = json.dumps(updates["tags"])
        
        updates["updated_at"] = datetime.now().isoformat()
        
        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [dossier_id]
        
        with self._get_conn() as conn:
            conn.execute(f"UPDATE dossiers SET {set_clause} WHERE id = ?", values)
    
    def delete_dossier(self, dossier_id: int) -> None:
        """Delete a dossier and all its data."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM notes WHERE dossier_id = ?", (dossier_id,))
            conn.execute("DELETE FROM events WHERE dossier_id = ?", (dossier_id,))
            conn.execute("DELETE FROM entities WHERE dossier_id = ?", (dossier_id,))
            conn.execute("DELETE FROM articles WHERE dossier_id = ?", (dossier_id,))
            conn.execute("DELETE FROM dossiers WHERE id = ?", (dossier_id,))
    
    # Article management
    def add_article(self, dossier_id: int, title: str, url: str, content: str, domain: str) -> Optional[int]:
        """Add an article to a dossier. Returns None if duplicate."""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        now = datetime.now().isoformat()
        
        with self._get_conn() as conn:
            try:
                cursor = conn.execute(
                    "INSERT INTO articles (dossier_id, title, url, content, domain, collected_at, content_hash) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (dossier_id, title, url, content, domain, now, content_hash)
                )
                self._touch_dossier(conn, dossier_id)
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return None  # Duplicate
    
    def get_articles(self, dossier_id: int) -> List[DossierArticle]:
        """Get all articles in a dossier."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM articles WHERE dossier_id = ? ORDER BY collected_at DESC",
                (dossier_id,)
            ).fetchall()
            
            return [
                DossierArticle(
                    id=row["id"], dossier_id=row["dossier_id"], title=row["title"],
                    url=row["url"], content=row["content"], domain=row["domain"],
                    collected_at=row["collected_at"], content_hash=row["content_hash"]
                )
                for row in rows
            ]
    
    def count_articles(self, dossier_id: int) -> int:
        """Count articles in a dossier."""
        with self._get_conn() as conn:
            row = conn.execute("SELECT COUNT(*) as cnt FROM articles WHERE dossier_id = ?", (dossier_id,)).fetchone()
            return row["cnt"]
    
    # Entity management
    def add_entity(self, dossier_id: int, entity_id: str, entity_type: str, label: str, metadata: Dict = None) -> Optional[int]:
        """Add an entity to a dossier."""
        metadata = metadata or {}
        
        with self._get_conn() as conn:
            try:
                cursor = conn.execute(
                    "INSERT INTO entities (dossier_id, entity_id, entity_type, label, metadata) VALUES (?, ?, ?, ?, ?)",
                    (dossier_id, entity_id, entity_type, label, json.dumps(metadata))
                )
                self._touch_dossier(conn, dossier_id)
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                # Update existing
                conn.execute(
                    "UPDATE entities SET label = ?, metadata = ? WHERE dossier_id = ? AND entity_id = ?",
                    (label, json.dumps(metadata), dossier_id, entity_id)
                )
                return None
    
    def get_entities(self, dossier_id: int, entity_type: str = None) -> List[DossierEntity]:
        """Get entities in a dossier."""
        with self._get_conn() as conn:
            if entity_type:
                rows = conn.execute(
                    "SELECT * FROM entities WHERE dossier_id = ? AND entity_type = ?",
                    (dossier_id, entity_type)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM entities WHERE dossier_id = ?",
                    (dossier_id,)
                ).fetchall()
            
            return [
                DossierEntity(
                    id=row["id"], dossier_id=row["dossier_id"], entity_id=row["entity_id"],
                    entity_type=row["entity_type"], label=row["label"],
                    metadata=json.loads(row["metadata"])
                )
                for row in rows
            ]
    
    # Event management
    def add_event(self, dossier_id: int, event_id: str, domain: str, actors: List[str],
                  targets: List[str], location: str = None, date: str = None,
                  patterns: List[str] = None, source_article_id: int = None) -> int:
        """Add an event to a dossier."""
        patterns = patterns or []
        
        with self._get_conn() as conn:
            cursor = conn.execute(
                """INSERT INTO events (dossier_id, event_id, domain, actors, targets, location, date, patterns, source_article_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (dossier_id, event_id, domain, json.dumps(actors), json.dumps(targets),
                 location, date, json.dumps(patterns), source_article_id)
            )
            self._touch_dossier(conn, dossier_id)
            return cursor.lastrowid
    
    def get_events(self, dossier_id: int, domain: str = None) -> List[DossierEvent]:
        """Get events in a dossier."""
        with self._get_conn() as conn:
            if domain:
                rows = conn.execute(
                    "SELECT * FROM events WHERE dossier_id = ? AND domain = ?",
                    (dossier_id, domain)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM events WHERE dossier_id = ?",
                    (dossier_id,)
                ).fetchall()
            
            return [
                DossierEvent(
                    id=row["id"], dossier_id=row["dossier_id"], event_id=row["event_id"],
                    domain=row["domain"], actors=json.loads(row["actors"]),
                    targets=json.loads(row["targets"]), location=row["location"],
                    date=row["date"], patterns=json.loads(row["patterns"]),
                    source_article_id=row["source_article_id"]
                )
                for row in rows
            ]
    
    # Notes management
    def add_note(self, dossier_id: int, content: str, note_type: str = "observation",
                 related_entities: List[str] = None) -> int:
        """Add an analyst note to a dossier."""
        related_entities = related_entities or []
        now = datetime.now().isoformat()
        
        with self._get_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO notes (dossier_id, note_type, content, created_at, related_entities) VALUES (?, ?, ?, ?, ?)",
                (dossier_id, note_type, content, now, json.dumps(related_entities))
            )
            self._touch_dossier(conn, dossier_id)
            return cursor.lastrowid
    
    def get_notes(self, dossier_id: int) -> List[AnalysisNote]:
        """Get notes in a dossier."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM notes WHERE dossier_id = ? ORDER BY created_at DESC",
                (dossier_id,)
            ).fetchall()
            
            return [
                AnalysisNote(
                    id=row["id"], dossier_id=row["dossier_id"], note_type=row["note_type"],
                    content=row["content"], created_at=row["created_at"],
                    related_entities=json.loads(row["related_entities"])
                )
                for row in rows
            ]
    
    # Graph export
    def export_graph(self, dossier_id: int) -> Dict[str, Any]:
        """Export dossier as a graph JSON."""
        entities = self.get_entities(dossier_id)
        events = self.get_events(dossier_id)
        
        nodes = []
        edges = []
        
        # Add entity nodes
        for entity in entities:
            nodes.append({
                "id": entity.entity_id,
                "node_type": "actor" if entity.entity_type in ["country", "government_body", "military_unit"] else entity.entity_type,
                "label": entity.label,
                "entity_type": entity.entity_type,
                **entity.metadata
            })
        
        # Add event nodes and edges
        for event in events:
            event_node_id = event.event_id
            nodes.append({
                "id": event_node_id,
                "node_type": "action",
                "dimefil_domain": event.domain,
                "patterns": ",".join(event.patterns),
                "date": event.date,
                "location": event.location
            })
            
            # Actor -> event edges
            for actor in event.actors:
                edges.append({"source": actor, "target": event_node_id, "relation": "performs"})
            
            # Event -> target edges
            for target in event.targets:
                edges.append({"source": event_node_id, "target": target, "relation": "targets"})
        
        return {"nodes": nodes, "edges": edges}
    
    def _touch_dossier(self, conn, dossier_id: int):
        """Update dossier's updated_at timestamp."""
        now = datetime.now().isoformat()
        conn.execute("UPDATE dossiers SET updated_at = ? WHERE id = ?", (now, dossier_id))
    
    # Statistics
    def get_dossier_stats(self, dossier_id: int) -> Dict[str, int]:
        """Get statistics for a dossier."""
        with self._get_conn() as conn:
            articles = conn.execute("SELECT COUNT(*) as cnt FROM articles WHERE dossier_id = ?", (dossier_id,)).fetchone()["cnt"]
            entities = conn.execute("SELECT COUNT(*) as cnt FROM entities WHERE dossier_id = ?", (dossier_id,)).fetchone()["cnt"]
            events = conn.execute("SELECT COUNT(*) as cnt FROM events WHERE dossier_id = ?", (dossier_id,)).fetchone()["cnt"]
            notes = conn.execute("SELECT COUNT(*) as cnt FROM notes WHERE dossier_id = ?", (dossier_id,)).fetchone()["cnt"]
            
            return {
                "articles": articles,
                "entities": entities,
                "events": events,
                "notes": notes
            }


def display_dossier_list(dossiers: List[Dossier], manager: DossierManager):
    """Display list of dossiers."""
    if not dossiers:
        console.print("[yellow]No dossiers found[/]")
        return
    
    table = Table(title="Dossiers")
    table.add_column("ID", style="cyan", justify="right")
    table.add_column("Name", style="green")
    table.add_column("Status")
    table.add_column("Articles", justify="right")
    table.add_column("Events", justify="right")
    table.add_column("Updated", style="dim")
    table.add_column("Tags", style="yellow")
    
    for d in dossiers:
        stats = manager.get_dossier_stats(d.id)
        status_color = {"active": "green", "archived": "yellow", "closed": "red"}.get(d.status, "white")
        
        table.add_row(
            str(d.id),
            d.name,
            f"[{status_color}]{d.status}[/]",
            str(stats["articles"]),
            str(stats["events"]),
            d.updated_at[:10],
            d.tag_str
        )
    
    console.print(table)


def display_dossier_detail(dossier: Dossier, manager: DossierManager):
    """Display detailed dossier view."""
    stats = manager.get_dossier_stats(dossier.id)
    
    console.print(Panel(f"[bold]{dossier.name}[/]\n{dossier.description or 'No description'}", 
                       title=f"Dossier #{dossier.id}"))
    
    table = Table(title="Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", justify="right", style="green")
    
    table.add_row("Articles", str(stats["articles"]))
    table.add_row("Entities", str(stats["entities"]))
    table.add_row("Events", str(stats["events"]))
    table.add_row("Notes", str(stats["notes"]))
    
    console.print(table)
    
    console.print(f"\n[dim]Created: {dossier.created_at}[/]")
    console.print(f"[dim]Updated: {dossier.updated_at}[/]")
    console.print(f"[dim]Status: {dossier.status}[/]")
    if dossier.tags:
        console.print(f"[dim]Tags: {dossier.tag_str}[/]")
