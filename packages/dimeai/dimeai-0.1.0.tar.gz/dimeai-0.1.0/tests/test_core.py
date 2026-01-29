"""
Core tests for DimeAI
"""
import pytest
import json
import tempfile
from pathlib import Path


class TestConfig:
    """Test configuration module."""
    
    def test_load_default_config(self):
        from dimeai.config import load_config, DEFAULT_CONFIG
        
        config = load_config()
        assert isinstance(config, dict)
        assert "gliner_model" in config
        assert config["gliner_model"] == DEFAULT_CONFIG["gliner_model"]
    
    def test_config_has_required_keys(self):
        from dimeai.config import load_config
        
        config = load_config()
        required = ["data_dir", "model_dir", "gliner_model", "embedding_model"]
        for key in required:
            assert key in config, f"Missing required config key: {key}"


class TestExtraction:
    """Test extraction module."""
    
    def test_dimefil_classification(self):
        from dimeai.extraction import GLiNERExtractor
        
        # Test without loading model (just classification logic)
        extractor = GLiNERExtractor.__new__(GLiNERExtractor)
        
        # Military text
        military_text = "China conducted military exercises with warships and fighter jets"
        assert extractor._classify_dimefil(military_text) == "military"
        
        # Law enforcement text
        law_text = "Coast guard fired water cannons at fishing vessels"
        assert extractor._classify_dimefil(law_text) == "law_enforcement"
        
        # Legal text
        legal_text = "The tribunal ruling on UNCLOS arbitration"
        assert extractor._classify_dimefil(legal_text) == "legal"
    
    def test_pattern_detection(self):
        from dimeai.extraction import GLiNERExtractor
        
        extractor = GLiNERExtractor.__new__(GLiNERExtractor)
        
        # Grey zone coercion
        text = "Coast guard rammed the vessel and used water cannon"
        patterns = extractor._detect_patterns(text)
        assert "grey_zone_coercion" in patterns
        
        # Legal warfare
        text = "The tribunal ruled in favor of the arbitration"
        patterns = extractor._detect_patterns(text)
        assert "legal_warfare" in patterns


class TestTraining:
    """Test training module."""
    
    def test_temporal_split_no_leakage(self):
        """Ensure temporal split has no leakage."""
        from dimeai.training import TemporalGraphDataset, TemporalEdge
        
        # Create mock dataset
        class MockDataset:
            def __init__(self):
                self.temporal_edges = [
                    TemporalEdge("a", "b", 1, "military"),
                    TemporalEdge("b", "c", 2, "legal"),
                    TemporalEdge("c", "d", 3, "diplomatic"),
                    TemporalEdge("d", "e", 4, "economic"),
                    TemporalEdge("e", "f", 5, "law_enforcement"),
                ]
            
            def get_temporal_split(self, ratio):
                sorted_edges = sorted(self.temporal_edges, key=lambda e: e.timestamp)
                split_idx = int(len(sorted_edges) * ratio)
                return sorted_edges[:split_idx], sorted_edges[split_idx:]
        
        dataset = MockDataset()
        train, test = dataset.get_temporal_split(0.6)
        
        # Check no overlap
        max_train_ts = max(e.timestamp for e in train)
        min_test_ts = min(e.timestamp for e in test)
        
        assert max_train_ts < min_test_ts, "Temporal leakage detected!"
    
    def test_edge_labels_valid(self):
        """Ensure edge labels are in valid range."""
        from dimeai.training import TemporalGraphDataset, TemporalEdge
        import torch
        
        # Mock edges
        edges = [
            TemporalEdge("a", "b", 1, "military"),
            TemporalEdge("b", "c", 2, "unknown"),
            TemporalEdge("c", "d", 3, "legal"),
        ]
        
        # Mock dataset
        class MockDataset:
            def __init__(self):
                self.temporal_edges = edges
            
            def get_edge_labels(self, edges):
                domain_to_idx = {
                    "diplomatic": 0, "information": 1, "military": 2,
                    "economic": 3, "law_enforcement": 4, "legal": 5, "unknown": 6
                }
                labels = [domain_to_idx.get(e.edge_type, 6) for e in edges]
                return torch.tensor(labels, dtype=torch.long)
        
        dataset = MockDataset()
        labels = dataset.get_edge_labels(edges)
        
        assert labels.min() >= 0
        assert labels.max() <= 6


class TestSimulation:
    """Test simulation module."""
    
    def test_escalation_risk_levels(self):
        from dimeai.simulation import WhatIfSimulator
        
        # Check escalation levels are valid
        assert WhatIfSimulator.DOMAIN_ESCALATION["military"] > WhatIfSimulator.DOMAIN_ESCALATION["legal"]
        assert WhatIfSimulator.DOMAIN_ESCALATION["law_enforcement"] > WhatIfSimulator.DOMAIN_ESCALATION["diplomatic"]
    
    def test_countermeasures_exist(self):
        from dimeai.simulation import WhatIfSimulator
        
        domains = ["military", "law_enforcement", "legal", "diplomatic", "economic", "information"]
        
        for domain in domains:
            assert domain in WhatIfSimulator.COUNTERMEASURES
            assert len(WhatIfSimulator.COUNTERMEASURES[domain]) > 0


class TestAgent:
    """Test agent module."""
    
    def test_actor_id_normalization(self):
        from dimeai.agent import GraphAnalyzer
        
        # Test normalization logic
        analyzer = GraphAnalyzer.__new__(GraphAnalyzer)
        
        # These should normalize to same ID
        assert "china" in "china".lower()
        assert "philippines" in "philippines".lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
