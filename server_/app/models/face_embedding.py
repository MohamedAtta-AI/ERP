"""Face embedding model using SQLModel."""

from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import Text
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from pgvector.sqlalchemy import Vector

if TYPE_CHECKING:
    from .employee import Employee


class FaceEmbeddingBase(SQLModel):
    """Base face embedding model."""

    image_path: Optional[str] = Field(default=None, sa_column=Column(Text))


class FaceEmbedding(FaceEmbeddingBase, table=True):
    """Face embedding database model."""

    __tablename__ = "face_embeddings"

    id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employees.id", ondelete="CASCADE")
    embedding: List[float] = Field(
        sa_column=Column(Vector(512))
    )  # Facenet produces 512-dimensional embeddings
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    employee: Optional["Employee"] = Relationship(back_populates="face_embeddings")
