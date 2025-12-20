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
        threshold: float = 0.60,  # Lowered threshold for better matching
        limit: int = 10  # Get top 10 matches
    ) -> Optional[Dict]:
        """
        Find similar face using cosine similarity.
        Returns best match across all embeddings (supports multiple embeddings per employee).
        """
        # Convert numpy array to list for pgvector
        embedding_list = query_embedding.tolist()
        
        # Get top N matches
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
        rows = result.all()
        
        if not rows:
            return None
        
        # Group by employee_id and find best match per employee
        best_by_employee = {}
        for row in rows:
            emp_id = row.employee_id
            similarity = float(row.similarity)
            
            if emp_id not in best_by_employee or similarity > best_by_employee[emp_id]["similarity"]:
                best_by_employee[emp_id] = {
                    "employee_id": emp_id,
                    "embedding_id": row.id,
                    "similarity": similarity
                }
        
        # Return the best match overall
        if best_by_employee:
            best_match = max(best_by_employee.values(), key=lambda x: x["similarity"])
            return best_match
        
        return None
