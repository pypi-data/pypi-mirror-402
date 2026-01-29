"""
Tests for Dossier System
"""
import pytest
import tempfile
from pathlib import Path

from dimeai.dossier import DossierManager, Dossier


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_dossiers.db"
        yield db_path


@pytest.fixture
def manager(temp_db):
    """Create a DossierManager with temp database."""
    return DossierManager(db_path=temp_db)


class TestDossierCRUD:
    """Test dossier create/read/update/delete."""
    
    def test_create_dossier(self, manager):
        """Test creating a dossier."""
        dossier = manager.create_dossier("Test Dossier", "A test description", ["tag1", "tag2"])
        
        assert dossier.id == 1
        assert dossier.name == "Test Dossier"
        assert dossier.description == "A test description"
        assert dossier.status == "active"
        assert dossier.tags == ["tag1", "tag2"]
    
    def test_get_dossier(self, manager):
        """Test retrieving a dossier."""
        created = manager.create_dossier("Get Test")
        retrieved = manager.get_dossier(created.id)
        
        assert retrieved is not None
        assert retrieved.name == "Get Test"
    
    def test_get_nonexistent_dossier(self, manager):
        """Test retrieving a nonexistent dossier."""
        result = manager.get_dossier(999)
        assert result is None
    
    def test_list_dossiers(self, manager):
        """Test listing dossiers."""
        manager.create_dossier("Dossier 1")
        manager.create_dossier("Dossier 2")
        manager.create_dossier("Dossier 3")
        
        dossiers = manager.list_dossiers()
        assert len(dossiers) == 3
    
    def test_list_dossiers_by_status(self, manager):
        """Test filtering dossiers by status."""
        d1 = manager.create_dossier("Active 1")
        d2 = manager.create_dossier("Active 2")
        manager.update_dossier(d2.id, status="archived")
        
        active = manager.list_dossiers(status="active")
        archived = manager.list_dossiers(status="archived")
        
        assert len(active) == 1
        assert len(archived) == 1
    
    def test_update_dossier(self, manager):
        """Test updating a dossier."""
        dossier = manager.create_dossier("Original Name")
        manager.update_dossier(dossier.id, name="Updated Name", status="closed")
        
        updated = manager.get_dossier(dossier.id)
        assert updated.name == "Updated Name"
        assert updated.status == "closed"
    
    def test_delete_dossier(self, manager):
        """Test deleting a dossier."""
        dossier = manager.create_dossier("To Delete")
        manager.delete_dossier(dossier.id)
        
        result = manager.get_dossier(dossier.id)
        assert result is None


class TestArticles:
    """Test article management."""
    
    def test_add_article(self, manager):
        """Test adding an article."""
        dossier = manager.create_dossier("Article Test")
        article_id = manager.add_article(
            dossier.id,
            title="Test Article",
            url="https://example.com/article",
            content="This is test content for the article.",
            domain="diplomatic"
        )
        
        assert article_id is not None
        assert article_id > 0
    
    def test_duplicate_article_rejected(self, manager):
        """Test that duplicate articles are rejected."""
        dossier = manager.create_dossier("Dedup Test")
        content = "Unique content for deduplication test"
        
        id1 = manager.add_article(dossier.id, "Title 1", "url1", content, "diplomatic")
        id2 = manager.add_article(dossier.id, "Title 2", "url2", content, "military")
        
        assert id1 is not None
        assert id2 is None  # Duplicate rejected
    
    def test_get_articles(self, manager):
        """Test retrieving articles."""
        dossier = manager.create_dossier("Get Articles Test")
        manager.add_article(dossier.id, "Article 1", "url1", "Content 1", "diplomatic")
        manager.add_article(dossier.id, "Article 2", "url2", "Content 2", "military")
        
        articles = manager.get_articles(dossier.id)
        assert len(articles) == 2
    
    def test_count_articles(self, manager):
        """Test counting articles."""
        dossier = manager.create_dossier("Count Test")
        manager.add_article(dossier.id, "A1", "u1", "C1", "d")
        manager.add_article(dossier.id, "A2", "u2", "C2", "d")
        manager.add_article(dossier.id, "A3", "u3", "C3", "d")
        
        count = manager.count_articles(dossier.id)
        assert count == 3


class TestEntities:
    """Test entity management."""
    
    def test_add_entity(self, manager):
        """Test adding an entity."""
        dossier = manager.create_dossier("Entity Test")
        entity_id = manager.add_entity(
            dossier.id,
            entity_id="china",
            entity_type="country",
            label="China",
            metadata={"capital": "Beijing"}
        )
        
        assert entity_id is not None
    
    def test_update_existing_entity(self, manager):
        """Test that adding duplicate entity updates it."""
        dossier = manager.create_dossier("Entity Update Test")
        
        manager.add_entity(dossier.id, "china", "country", "China")
        manager.add_entity(dossier.id, "china", "country", "People's Republic of China")
        
        entities = manager.get_entities(dossier.id)
        assert len(entities) == 1
        assert entities[0].label == "People's Republic of China"
    
    def test_get_entities_by_type(self, manager):
        """Test filtering entities by type."""
        dossier = manager.create_dossier("Entity Type Test")
        manager.add_entity(dossier.id, "china", "country", "China")
        manager.add_entity(dossier.id, "philippines", "country", "Philippines")
        manager.add_entity(dossier.id, "scs", "sea_region", "South China Sea")
        
        countries = manager.get_entities(dossier.id, entity_type="country")
        regions = manager.get_entities(dossier.id, entity_type="sea_region")
        
        assert len(countries) == 2
        assert len(regions) == 1


class TestEvents:
    """Test event management."""
    
    def test_add_event(self, manager):
        """Test adding an event."""
        dossier = manager.create_dossier("Event Test")
        event_id = manager.add_event(
            dossier.id,
            event_id="EVT-0001",
            domain="law_enforcement",
            actors=["china"],
            targets=["philippines"],
            location="Scarborough Shoal",
            date="2024-01-15",
            patterns=["water_cannon", "blocking"]
        )
        
        assert event_id is not None
    
    def test_get_events(self, manager):
        """Test retrieving events."""
        dossier = manager.create_dossier("Get Events Test")
        manager.add_event(dossier.id, "E1", "diplomatic", ["a"], ["b"])
        manager.add_event(dossier.id, "E2", "military", ["c"], ["d"])
        
        events = manager.get_events(dossier.id)
        assert len(events) == 2
    
    def test_get_events_by_domain(self, manager):
        """Test filtering events by domain."""
        dossier = manager.create_dossier("Event Domain Test")
        manager.add_event(dossier.id, "E1", "diplomatic", ["a"], ["b"])
        manager.add_event(dossier.id, "E2", "diplomatic", ["c"], ["d"])
        manager.add_event(dossier.id, "E3", "military", ["e"], ["f"])
        
        diplomatic = manager.get_events(dossier.id, domain="diplomatic")
        military = manager.get_events(dossier.id, domain="military")
        
        assert len(diplomatic) == 2
        assert len(military) == 1


class TestNotes:
    """Test analyst notes."""
    
    def test_add_note(self, manager):
        """Test adding a note."""
        dossier = manager.create_dossier("Note Test")
        note_id = manager.add_note(
            dossier.id,
            content="This is an observation",
            note_type="observation"
        )
        
        assert note_id is not None
    
    def test_get_notes(self, manager):
        """Test retrieving notes."""
        dossier = manager.create_dossier("Get Notes Test")
        manager.add_note(dossier.id, "Observation 1", "observation")
        manager.add_note(dossier.id, "Hypothesis 1", "hypothesis")
        manager.add_note(dossier.id, "Question 1", "question")
        
        notes = manager.get_notes(dossier.id)
        assert len(notes) == 3


class TestGraphExport:
    """Test graph export functionality."""
    
    def test_export_empty_dossier(self, manager):
        """Test exporting an empty dossier."""
        dossier = manager.create_dossier("Empty Export Test")
        graph = manager.export_graph(dossier.id)
        
        assert "nodes" in graph
        assert "edges" in graph
        assert len(graph["nodes"]) == 0
        assert len(graph["edges"]) == 0
    
    def test_export_with_entities_and_events(self, manager):
        """Test exporting dossier with data."""
        dossier = manager.create_dossier("Full Export Test")
        
        # Add entities
        manager.add_entity(dossier.id, "china", "country", "China")
        manager.add_entity(dossier.id, "philippines", "country", "Philippines")
        
        # Add event
        manager.add_event(
            dossier.id, "EVT-0001", "law_enforcement",
            actors=["china"], targets=["philippines"]
        )
        
        graph = manager.export_graph(dossier.id)
        
        # 2 entities + 1 event = 3 nodes
        assert len(graph["nodes"]) == 3
        # 1 actor->event + 1 event->target = 2 edges
        assert len(graph["edges"]) == 2


class TestStatistics:
    """Test dossier statistics."""
    
    def test_get_dossier_stats(self, manager):
        """Test getting dossier statistics."""
        dossier = manager.create_dossier("Stats Test")
        
        manager.add_article(dossier.id, "A1", "u1", "C1", "d")
        manager.add_article(dossier.id, "A2", "u2", "C2", "d")
        manager.add_entity(dossier.id, "e1", "country", "E1")
        manager.add_event(dossier.id, "EV1", "diplomatic", ["a"], ["b"])
        manager.add_note(dossier.id, "Note", "observation")
        
        stats = manager.get_dossier_stats(dossier.id)
        
        assert stats["articles"] == 2
        assert stats["entities"] == 1
        assert stats["events"] == 1
        assert stats["notes"] == 1


class TestCascadeDelete:
    """Test that deleting dossier removes all related data."""
    
    def test_cascade_delete(self, manager):
        """Test that all related data is deleted with dossier."""
        dossier = manager.create_dossier("Cascade Test")
        
        manager.add_article(dossier.id, "A1", "u1", "C1", "d")
        manager.add_entity(dossier.id, "e1", "country", "E1")
        manager.add_event(dossier.id, "EV1", "diplomatic", ["a"], ["b"])
        manager.add_note(dossier.id, "Note", "observation")
        
        # Delete dossier
        manager.delete_dossier(dossier.id)
        
        # Verify all data is gone
        assert manager.get_dossier(dossier.id) is None
        assert len(manager.get_articles(dossier.id)) == 0
        assert len(manager.get_entities(dossier.id)) == 0
        assert len(manager.get_events(dossier.id)) == 0
        assert len(manager.get_notes(dossier.id)) == 0


class TestSourceFiltering:
    """Test reputable source filtering."""
    
    def test_reputable_sources_accepted(self):
        """Test that reputable sources are accepted."""
        from dimeai.dossier_session import _is_reputable_source
        
        reputable = [
            "https://www.reuters.com/article/123",
            "https://bbc.com/news/world",
            "https://www.aljazeera.com/news/2024",
            "https://amti.csis.org/analysis",
            "https://www.scmp.com/news/china",
            "https://www.theguardian.com/world",
            "https://navalnews.com/naval-news",
        ]
        
        for url in reputable:
            assert _is_reputable_source(url), f"Should accept: {url}"
    
    def test_non_reputable_sources_rejected(self):
        """Test that non-reputable sources are rejected."""
        from dimeai.dossier_session import _is_reputable_source
        
        non_reputable = [
            "https://randomsite.com/article",
            "https://blog.example.org/post",
            "https://medium.com/@user/story",
            "https://wordpress.com/news",
        ]
        
        for url in non_reputable:
            assert not _is_reputable_source(url), f"Should reject: {url}"
    
    def test_query_expansion(self):
        """Test grey zone query expansion."""
        from dimeai.dossier_session import expand_grey_zone_queries
        
        queries = expand_grey_zone_queries("China Philippines")
        
        assert len(queries) >= 1
        assert len(queries) <= 5
        assert "China Philippines" in queries
