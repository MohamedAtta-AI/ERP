"""Vector similarity search service."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from pgvector.sqlalchemy import Vector
import numpy as np
from typing import Optional, Dict

from ..models.face_embedding import FaceEmbedding


class VectorSearchService:
    """Service for vector similarity search."""
    
    async def find_similar_face(
        self,
        db: AsyncSession,
        query_embedding: np.ndarray,
        threshold: float = 0.65,
        limit: int = 1
    ) -> Optional[Dict]:
        """Find similar face using cosine similarity."""
        # Convert numpy array to list for pgvector
        embedding_list = query_embedding.tolist()
        
        # Use cosine similarity operator (<=>)
        # Note: pgvector uses 1 - cosine_distance, so higher is better
        # We want similarity >= threshold, which means distance <= (1 - threshold)
        
        query = select(
            FaceEmbedding.employee_id,
            FaceEmbedding.id,
            (1 - (FaceEmbedding.embedding.cosine_distance(embedding_list))).label("similarity")
        ).where(
            FaceEmbedding.embedding.cosine_distance(embedding_list) <= (1 - threshold)
        ).order_by(
            FaceEmbedding.embedding.cosine_distance(embedding_list)
        ).limit(limit)
        
        result = await db.execute(query)
        row = result.first()
        
        if row:
            return {
                "employee_id": row.employee_id,
                "embedding_id": row.id,
                "similarity": float(row.similarity)
            }
        
        return None
