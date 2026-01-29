"""
KeraDB Python SDK

A MongoDB-compatible Python client for KeraDB - a lightweight, embedded NoSQL 
document database with advanced vector search capabilities.

Usage:
    >>> import keradb
    >>> 
    >>> client = keradb.connect("mydb.ndb")
    >>> db = client.database()
    >>> users = db.collection("users")
    >>> 
    >>> # Insert
    >>> result = users.insert_one({"name": "Alice", "age": 30})
    >>> print(f"Inserted: {result.inserted_id}")
    >>> 
    >>> # Find
    >>> user = users.find_one({"_id": result.inserted_id})
    >>> 
    >>> # Update
    >>> users.update_one({"_id": result.inserted_id}, {"$set": {"age": 31}})
    >>> 
    >>> # Delete
    >>> users.delete_one({"_id": result.inserted_id})
"""

from .client import (
    connect,
    Client,
    Database,
    Collection,
    Cursor,
    SingleResult,
    Document,
)
from .results import (
    InsertOneResult,
    InsertManyResult,
    UpdateResult,
    DeleteResult,
)
from .vector import (
    VectorConfig,
    VectorDocument,
    VectorSearchResult,
    VectorCollectionStats,
    MetadataFilter,
    Embedding,
    Distance,
    CompressionMode,
    CompressionConfig,
)

__version__ = "0.1.0"
__all__ = [
    # Connection
    "connect",
    "Client",
    "Database",
    "Collection",
    # Query
    "Cursor",
    "SingleResult",
    "Document",
    # Results
    "InsertOneResult",
    "InsertManyResult",
    "UpdateResult",
    "DeleteResult",
    # Vector
    "VectorConfig",
    "VectorDocument",
    "VectorSearchResult",
    "VectorCollectionStats",
    "MetadataFilter",
    "Embedding",
    "Distance",
    "CompressionMode",
    "CompressionConfig",
]
