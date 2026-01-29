"""Result types for KeraDB operations (MongoDB-compatible)."""

from typing import List


class InsertOneResult:
    """Result of an insert_one operation."""
    
    def __init__(self, inserted_id: str):
        """
        Initialize the result.
        
        Args:
            inserted_id: The ID of the inserted document
        """
        self.inserted_id = inserted_id
    
    def __repr__(self) -> str:
        return f"InsertOneResult(inserted_id='{self.inserted_id}')"


class InsertManyResult:
    """Result of an insert_many operation."""
    
    def __init__(self, inserted_ids: List[str]):
        """
        Initialize the result.
        
        Args:
            inserted_ids: List of IDs of the inserted documents
        """
        self.inserted_ids = inserted_ids
    
    def __repr__(self) -> str:
        return f"InsertManyResult(inserted_ids={self.inserted_ids})"


class UpdateResult:
    """Result of an update operation."""
    
    def __init__(self, matched_count: int, modified_count: int):
        """
        Initialize the result.
        
        Args:
            matched_count: Number of documents matched by the filter
            modified_count: Number of documents actually modified
        """
        self.matched_count = matched_count
        self.modified_count = modified_count
    
    def __repr__(self) -> str:
        return f"UpdateResult(matched_count={self.matched_count}, modified_count={self.modified_count})"


class DeleteResult:
    """Result of a delete operation."""
    
    def __init__(self, deleted_count: int):
        """
        Initialize the result.
        
        Args:
            deleted_count: Number of documents deleted
        """
        self.deleted_count = deleted_count
    
    def __repr__(self) -> str:
        return f"DeleteResult(deleted_count={self.deleted_count})"
