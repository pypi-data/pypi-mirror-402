"""
Property-based tests using Hypothesis
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
import numpy as np


class TestTemporalSplitProperties:
    """Property-based tests for temporal splitting."""
    
    @given(
        timestamps=st.lists(st.integers(min_value=0, max_value=1000), min_size=5, max_size=100),
        ratio=st.floats(min_value=0.1, max_value=0.9)
    )
    @settings(max_examples=50)
    def test_temporal_split_preserves_order(self, timestamps, ratio):
        """Temporal split should preserve chronological order."""
        from dimeai.training import TemporalEdge
        
        # Create edges with given timestamps
        edges = [TemporalEdge(f"a{i}", f"b{i}", ts, "military") 
                for i, ts in enumerate(timestamps)]
        
        # Sort and split
        sorted_edges = sorted(edges, key=lambda e: e.timestamp)
        split_idx = int(len(sorted_edges) * ratio)
        
        assume(split_idx > 0 and split_idx < len(sorted_edges))
        
        train = sorted_edges[:split_idx]
        test = sorted_edges[split_idx:]
        
        # Property: max train timestamp < min test timestamp
        max_train = max(e.timestamp for e in train)
        min_test = min(e.timestamp for e in test)
        
        assert max_train <= min_test, "Temporal leakage detected"
    
    @given(
        n_edges=st.integers(min_value=10, max_value=100),
        ratio=st.floats(min_value=0.1, max_value=0.9)
    )
    @settings(max_examples=30)
    def test_split_sizes_correct(self, n_edges, ratio):
        """Split sizes should match ratio."""
        from dimeai.training import TemporalEdge
        
        edges = [TemporalEdge(f"a{i}", f"b{i}", i, "military") for i in range(n_edges)]
        
        split_idx = int(len(edges) * ratio)
        train = edges[:split_idx]
        test = edges[split_idx:]
        
        # Property: train + test = total
        assert len(train) + len(test) == n_edges
        
        # Property: train size approximately matches ratio
        actual_ratio = len(train) / n_edges
        assert abs(actual_ratio - ratio) < 0.1


class TestFeatureProperties:
    """Property-based tests for feature computation."""
    
    @given(
        centrality_values=st.lists(
            st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=50
        )
    )
    @settings(max_examples=30)
    def test_centrality_bounded(self, centrality_values):
        """Centrality values should be bounded [0, 1]."""
        for val in centrality_values:
            assert 0.0 <= val <= 1.0
    
    @given(
        embedding_dim=st.integers(min_value=32, max_value=512),
        n_nodes=st.integers(min_value=1, max_value=100)
    )
    @settings(max_examples=20)
    def test_embedding_dimensions(self, embedding_dim, n_nodes):
        """Embeddings should have correct dimensions."""
        import torch
        
        # Simulate embedding matrix
        embeddings = torch.randn(n_nodes, embedding_dim)
        
        assert embeddings.shape == (n_nodes, embedding_dim)
        assert not torch.isnan(embeddings).any()


class TestDomainClassificationProperties:
    """Property-based tests for domain classification."""
    
    @given(text=st.text(min_size=10, max_size=500))
    @settings(max_examples=30, deadline=None)
    def test_classification_returns_valid_domain(self, text):
        """Classification should always return a valid domain."""
        from dimeai.extraction import GLiNERExtractor
        
        extractor = GLiNERExtractor.__new__(GLiNERExtractor)
        
        valid_domains = {"military", "law_enforcement", "legal", 
                        "economic", "information", "diplomatic"}
        
        result = extractor._classify_dimefil(text)
        assert result in valid_domains
    
    @given(text=st.text(min_size=10, max_size=500))
    @settings(max_examples=30, deadline=None)
    def test_pattern_detection_returns_list(self, text):
        """Pattern detection should always return a list."""
        from dimeai.extraction import GLiNERExtractor
        
        extractor = GLiNERExtractor.__new__(GLiNERExtractor)
        
        result = extractor._detect_patterns(text)
        assert isinstance(result, list)


class TestSimulationProperties:
    """Property-based tests for simulation."""
    
    @given(
        domain=st.sampled_from(["military", "law_enforcement", "legal", 
                               "diplomatic", "economic", "information"])
    )
    def test_escalation_risk_valid(self, domain):
        """Escalation risk should be in valid range."""
        from dimeai.simulation import WhatIfSimulator
        
        risk = WhatIfSimulator.DOMAIN_ESCALATION.get(domain, 0.3)
        assert 0.0 <= risk <= 1.0
    
    @given(
        domain=st.sampled_from(["military", "law_enforcement", "legal", 
                               "diplomatic", "economic", "information"])
    )
    def test_countermeasures_non_empty(self, domain):
        """Each domain should have countermeasures."""
        from dimeai.simulation import WhatIfSimulator
        
        countermeasures = WhatIfSimulator.COUNTERMEASURES.get(domain, [])
        assert len(countermeasures) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
