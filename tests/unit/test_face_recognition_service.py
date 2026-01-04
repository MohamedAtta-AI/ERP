"""
Unit tests for the Face Recognition Service.

Tests cover:
- Embedding similarity computation
- Match detection with configurable threshold
- Best match finding from candidates
"""

import pytest
import numpy as np

from server.services.face_recognition import FaceRecognitionService


@pytest.fixture
def face_service():
    """Create a FaceRecognitionService instance for testing."""
    return FaceRecognitionService()


class TestComputeSimilarity:
    """Tests for the compute_similarity method."""

    def test_identical_embeddings_return_1(self, face_service, sample_embedding):
        """Identical embeddings should have similarity of 1.0."""
        similarity = face_service.compute_similarity(sample_embedding, sample_embedding)
        assert similarity == pytest.approx(1.0, abs=1e-6)

    def test_orthogonal_embeddings_return_0(self, face_service):
        """Orthogonal embeddings should have similarity of 0.0."""
        emb1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        emb2 = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        similarity = face_service.compute_similarity(emb1, emb2)
        assert similarity == pytest.approx(0.0, abs=1e-6)

    def test_opposite_embeddings_return_negative(self, face_service):
        """Opposite embeddings should have similarity of -1.0."""
        emb1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        emb2 = np.array([-1.0, 0.0, 0.0], dtype=np.float32)
        similarity = face_service.compute_similarity(emb1, emb2)
        assert similarity == pytest.approx(-1.0, abs=1e-6)

    def test_similar_embeddings_have_high_similarity(
        self, face_service, sample_embedding, similar_embedding
    ):
        """Similar embeddings should have high similarity (> 0.8)."""
        similarity = face_service.compute_similarity(sample_embedding, similar_embedding)
        assert similarity > 0.8

    def test_different_embeddings_have_low_similarity(
        self, face_service, sample_embedding, different_embedding
    ):
        """Different embeddings should have lower similarity."""
        similarity = face_service.compute_similarity(sample_embedding, different_embedding)
        # Different random embeddings typically have low similarity
        assert similarity < 0.5

    def test_zero_embedding_returns_0(self, face_service, sample_embedding):
        """Zero vector should return 0 similarity."""
        zero_emb = np.zeros(128, dtype=np.float32)
        similarity = face_service.compute_similarity(sample_embedding, zero_emb)
        assert similarity == 0.0


class TestIsMatch:
    """Tests for the is_match method."""

    def test_identical_embeddings_match(self, face_service, sample_embedding):
        """Identical embeddings should always match."""
        assert face_service.is_match(sample_embedding, sample_embedding) is True

    def test_similar_embeddings_match(
        self, face_service, sample_embedding, similar_embedding
    ):
        """Similar embeddings should match when above threshold."""
        # Similar embeddings should have high similarity
        assert face_service.is_match(sample_embedding, similar_embedding) is True

    def test_different_embeddings_do_not_match(
        self, face_service, sample_embedding, different_embedding
    ):
        """Different embeddings should not match."""
        assert face_service.is_match(sample_embedding, different_embedding) is False

    def test_uses_configured_threshold(self, sample_embedding, similar_embedding):
        """Matching should respect the configured threshold."""
        # Create service with high threshold
        service = FaceRecognitionService()
        service.similarity_threshold = 0.99
        
        # Similar but not identical should not match with very high threshold
        assert service.is_match(sample_embedding, similar_embedding) is False
        
        # Create service with low threshold
        service.similarity_threshold = 0.1
        assert service.is_match(sample_embedding, similar_embedding) is True


class TestFindBestMatch:
    """Tests for the find_best_match method."""

    def test_empty_candidates_returns_none(self, face_service, sample_embedding):
        """Empty candidate list should return (None, 0.0)."""
        idx, score = face_service.find_best_match(sample_embedding, [])
        assert idx is None
        assert score == 0.0

    def test_finds_exact_match(self, face_service, sample_embedding, different_embedding):
        """Should find exact match in candidate list."""
        candidates = [different_embedding, sample_embedding]
        idx, score = face_service.find_best_match(sample_embedding, candidates)
        assert idx == 1
        assert score == pytest.approx(1.0, abs=1e-6)

    def test_finds_best_among_similar(
        self, face_service, sample_embedding, similar_embedding, different_embedding
    ):
        """Should find the best match among multiple candidates."""
        candidates = [different_embedding, similar_embedding]
        idx, score = face_service.find_best_match(sample_embedding, candidates)
        assert idx == 1  # similar_embedding should be best match
        assert score > 0.8

    def test_returns_none_when_below_threshold(self, face_service, different_embedding):
        """Should return None when best match is below threshold."""
        query = np.random.randn(128).astype(np.float32)
        query = query / np.linalg.norm(query)
        
        candidates = [different_embedding]
        idx, score = face_service.find_best_match(query, candidates)
        # Should still return the best score even if no match
        assert idx is None or score < face_service.similarity_threshold


class TestServiceConfiguration:
    """Tests for service configuration from config."""

    def test_loads_config_values(self):
        """Service should load values from config."""
        from server.config import config
        
        service = FaceRecognitionService()
        
        assert service.model_name == config.RECOGNITION_MODEL_NAME
        assert service.embedding_size == config.EMBEDDING_SIZE
        assert service.similarity_threshold == config.SIMILARITY_THRESHOLD

    def test_model_name_in_available_models(self):
        """Configured model should be in available models list."""
        from server.services.face_recognition import AVAILABLE_MODELS
        
        service = FaceRecognitionService()
        assert service.model_name in AVAILABLE_MODELS

