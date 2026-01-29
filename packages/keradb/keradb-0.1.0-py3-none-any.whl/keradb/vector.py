"""Vector search operations for KeraDB Python SDK."""

import json
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from .ffi import get_ffi


# Type alias for embedding vectors
Embedding = List[float]


class Distance(str, Enum):
    """Distance metric for vector similarity."""
    
    COSINE = "cosine"  # range [0, 2] where 0 = identical
    EUCLIDEAN = "euclidean"  # L2 norm
    DOT_PRODUCT = "dot_product"  # negative dot product for similarity ranking
    MANHATTAN = "manhattan"  # L1 norm


class CompressionMode(str, Enum):
    """Vector compression mode."""
    
    NONE = "none"  # No compression, full vectors
    DELTA = "delta"  # Store sparse differences from neighbors
    QUANTIZED_DELTA = "quantized_delta"  # Aggressive quantized deltas


class CompressionConfig:
    """Configuration for vector compression."""
    
    def __init__(
        self,
        mode: CompressionMode = CompressionMode.NONE,
        sparsity_threshold: Optional[float] = None,
        max_density: Optional[float] = None,
        anchor_frequency: Optional[int] = None,
        quantization_bits: Optional[int] = None,
    ):
        """
        Initialize compression configuration.
        
        Args:
            mode: Compression mode
            sparsity_threshold: Threshold for considering vectors sparse
            max_density: Maximum density for delta compression
            anchor_frequency: Frequency of anchor vectors
            quantization_bits: Number of bits for quantization
        """
        self.mode = mode
        self.sparsity_threshold = sparsity_threshold
        self.max_density = max_density
        self.anchor_frequency = anchor_frequency
        self.quantization_bits = quantization_bits
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {"mode": self.mode.value}
        if self.sparsity_threshold is not None:
            result["sparsity_threshold"] = self.sparsity_threshold
        if self.max_density is not None:
            result["max_density"] = self.max_density
        if self.anchor_frequency is not None:
            result["anchor_frequency"] = self.anchor_frequency
        if self.quantization_bits is not None:
            result["quantization_bits"] = self.quantization_bits
        return result


class VectorConfig:
    """Configuration for a vector collection."""
    
    def __init__(
        self,
        dimensions: int,
        distance: Distance = Distance.COSINE,
        m: Optional[int] = None,
        ef_construction: Optional[int] = None,
        ef_search: Optional[int] = None,
        lazy_embedding: bool = False,
        embedding_model: Optional[str] = None,
        compression: Optional[CompressionConfig] = None,
    ):
        """
        Initialize vector configuration.
        
        Args:
            dimensions: Vector dimensions
            distance: Distance metric (default: cosine)
            m: HNSW M parameter (connections per node, default: 16)
            ef_construction: Build quality parameter (default: 200)
            ef_search: Query quality parameter (default: 50)
            lazy_embedding: Enable lazy embedding mode
            embedding_model: Model name for lazy embedding
            compression: Compression configuration
        """
        self.dimensions = dimensions
        self.distance = distance
        self.m = m
        self.ef_construction = ef_construction
        self.ef_search = ef_search
        self.lazy_embedding = lazy_embedding
        self.embedding_model = embedding_model
        self.compression = compression
    
    def with_distance(self, distance: Distance) -> 'VectorConfig':
        """Set the distance metric."""
        self.distance = distance
        return self
    
    def with_m(self, m: int) -> 'VectorConfig':
        """Set the HNSW M parameter."""
        self.m = m
        return self
    
    def with_ef_construction(self, ef: int) -> 'VectorConfig':
        """Set the ef_construction parameter."""
        self.ef_construction = ef
        return self
    
    def with_ef_search(self, ef: int) -> 'VectorConfig':
        """Set the ef_search parameter."""
        self.ef_search = ef
        return self
    
    def with_lazy_embedding(self, model: str) -> 'VectorConfig':
        """Enable lazy embedding with a model."""
        self.lazy_embedding = True
        self.embedding_model = model
        return self
    
    def with_compression(self, config: CompressionConfig) -> 'VectorConfig':
        """Set compression configuration."""
        self.compression = config
        return self
    
    def with_delta_compression(self) -> 'VectorConfig':
        """Enable delta compression with default settings."""
        self.compression = CompressionConfig(mode=CompressionMode.DELTA)
        return self
    
    def with_quantized_compression(self) -> 'VectorConfig':
        """Enable quantized delta compression."""
        self.compression = CompressionConfig(mode=CompressionMode.QUANTIZED_DELTA)
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "dimensions": self.dimensions,
            "distance": self.distance.value,
        }
        if self.m is not None:
            result["m"] = self.m
        if self.ef_construction is not None:
            result["ef_construction"] = self.ef_construction
        if self.ef_search is not None:
            result["ef_search"] = self.ef_search
        if self.lazy_embedding:
            result["lazy_embedding"] = True
            if self.embedding_model:
                result["embedding_model"] = self.embedding_model
        if self.compression:
            result["compression"] = self.compression.to_dict()
        return result


class VectorDocument:
    """Document in a vector collection."""
    
    def __init__(
        self,
        id: int,
        embedding: Optional[Embedding] = None,
        text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize vector document.
        
        Args:
            id: Document ID
            embedding: Vector embedding
            text: Text content
            metadata: Additional metadata
        """
        self.id = id
        self.embedding = embedding
        self.text = text
        self.metadata = metadata or {}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VectorDocument':
        """Create from dictionary."""
        return cls(
            id=data["id"],
            embedding=data.get("embedding"),
            text=data.get("text"),
            metadata=data.get("metadata", {}),
        )
    
    def __repr__(self) -> str:
        return f"VectorDocument(id={self.id}, metadata={self.metadata})"


class VectorSearchResult:
    """Result from a vector search query."""
    
    def __init__(self, document: VectorDocument, score: float, rank: int):
        """
        Initialize search result.
        
        Args:
            document: The vector document
            score: Similarity score
            rank: Result rank
        """
        self.document = document
        self.score = score
        self.rank = rank
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VectorSearchResult':
        """Create from dictionary."""
        return cls(
            document=VectorDocument.from_dict(data["document"]),
            score=data["score"],
            rank=data["rank"],
        )
    
    def __repr__(self) -> str:
        return f"VectorSearchResult(rank={self.rank}, score={self.score:.4f}, id={self.document.id})"


class VectorCollectionStats:
    """Statistics for a vector collection."""
    
    def __init__(
        self,
        vector_count: int,
        dimensions: int,
        distance: Distance,
        memory_usage: int,
        layer_count: int,
        lazy_embedding: bool,
        compression: Optional[CompressionMode] = None,
        anchor_count: Optional[int] = None,
        delta_count: Optional[int] = None,
    ):
        """
        Initialize collection statistics.
        
        Args:
            vector_count: Number of vectors
            dimensions: Vector dimensions
            distance: Distance metric
            memory_usage: Memory usage in bytes
            layer_count: Number of HNSW layers
            lazy_embedding: Whether lazy embedding is enabled
            compression: Compression mode
            anchor_count: Number of anchor vectors
            delta_count: Number of delta vectors
        """
        self.vector_count = vector_count
        self.dimensions = dimensions
        self.distance = distance
        self.memory_usage = memory_usage
        self.layer_count = layer_count
        self.lazy_embedding = lazy_embedding
        self.compression = compression
        self.anchor_count = anchor_count
        self.delta_count = delta_count
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VectorCollectionStats':
        """Create from dictionary."""
        return cls(
            vector_count=data["vector_count"],
            dimensions=data["dimensions"],
            distance=Distance(data["distance"]),
            memory_usage=data["memory_usage"],
            layer_count=data["layer_count"],
            lazy_embedding=data["lazy_embedding"],
            compression=CompressionMode(data["compression"]) if "compression" in data else None,
            anchor_count=data.get("anchor_count"),
            delta_count=data.get("delta_count"),
        )
    
    def __repr__(self) -> str:
        return (
            f"VectorCollectionStats(vectors={self.vector_count}, "
            f"dimensions={self.dimensions}, distance={self.distance.value}, "
            f"memory={self.memory_usage} bytes)"
        )


class MetadataFilter:
    """Filter for metadata fields in vector search."""
    
    def __init__(self, field: str, condition: str, value: Any):
        """
        Initialize metadata filter.
        
        Args:
            field: Metadata field name
            condition: Condition type (eq, ne, gt, gte, lt, lte, in, not_in, contains, starts_with, ends_with)
            value: Filter value
        """
        self.field = field
        self.condition = condition
        self.value = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "field": self.field,
            "condition": self.condition,
            "value": self.value,
        }


class VectorOperations:
    """Vector operations mixin for Client class."""
    
    def create_vector_collection(self, name: str, config: VectorConfig) -> None:
        """
        Create a new vector collection.
        
        Args:
            name: Collection name
            config: Vector configuration
            
        Raises:
            Exception: If creation fails
        """
        ffi = get_ffi()
        config_json = json.dumps(config.to_dict()).encode('utf-8')
        name_bytes = name.encode('utf-8')
        
        result_ptr = ffi.lib.keradb_create_vector_collection(self._db, name_bytes, config_json)
        if not result_ptr:
            raise Exception(f"Failed to create vector collection: {ffi.get_last_error()}")
        ffi.free_string(result_ptr)
    
    def list_vector_collections(self) -> List[Dict[str, Any]]:
        """
        List all vector collections.
        
        Returns:
            List of collections with name and count
        """
        ffi = get_ffi()
        result_ptr = ffi.lib.keradb_list_vector_collections(self._db)
        if not result_ptr:
            return []
        
        result_json = result_ptr.decode('utf-8')
        ffi.free_string(result_ptr)
        
        collections = json.loads(result_json)
        return [{"name": c["Name"], "count": c["Count"]} for c in collections]
    
    def drop_vector_collection(self, name: str) -> bool:
        """
        Drop a vector collection.
        
        Args:
            name: Collection name
            
        Returns:
            True if dropped successfully
        """
        ffi = get_ffi()
        name_bytes = name.encode('utf-8')
        result = ffi.lib.keradb_drop_vector_collection(self._db, name_bytes)
        return result != 0
    
    def insert_vector(
        self,
        collection: str,
        embedding: Embedding,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Insert a vector with optional metadata.
        
        Args:
            collection: Collection name
            embedding: Vector embedding
            metadata: Optional metadata
            
        Returns:
            Vector ID
        """
        ffi = get_ffi()
        vector_json = json.dumps(embedding).encode('utf-8')
        metadata_json = json.dumps(metadata or {}).encode('utf-8')
        collection_bytes = collection.encode('utf-8')
        
        result_ptr = ffi.lib.keradb_insert_vector(
            self._db, collection_bytes, vector_json, metadata_json
        )
        if not result_ptr:
            raise Exception(f"Failed to insert vector: {ffi.get_last_error()}")
        
        id_str = result_ptr.decode('utf-8')
        ffi.free_string(result_ptr)
        return int(id_str)
    
    def insert_text(
        self,
        collection: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Insert text with optional metadata (requires embedding provider).
        
        Args:
            collection: Collection name
            text: Text content
            metadata: Optional metadata
            
        Returns:
            Vector ID
        """
        ffi = get_ffi()
        text_bytes = text.encode('utf-8')
        metadata_json = json.dumps(metadata or {}).encode('utf-8')
        collection_bytes = collection.encode('utf-8')
        
        result_ptr = ffi.lib.keradb_insert_text(
            self._db, collection_bytes, text_bytes, metadata_json
        )
        if not result_ptr:
            raise Exception(f"Failed to insert text: {ffi.get_last_error()}")
        
        id_str = result_ptr.decode('utf-8')
        ffi.free_string(result_ptr)
        return int(id_str)
    
    def vector_search(
        self,
        collection: str,
        query_vector: Embedding,
        k: int = 10,
    ) -> List[VectorSearchResult]:
        """
        Perform vector similarity search.
        
        Args:
            collection: Collection name
            query_vector: Query vector
            k: Number of results
            
        Returns:
            List of search results
        """
        ffi = get_ffi()
        vector_json = json.dumps(query_vector).encode('utf-8')
        collection_bytes = collection.encode('utf-8')
        
        result_ptr = ffi.lib.keradb_vector_search(
            self._db, collection_bytes, vector_json, k
        )
        if not result_ptr:
            raise Exception(f"Vector search failed: {ffi.get_last_error()}")
        
        result_json = result_ptr.decode('utf-8')
        ffi.free_string(result_ptr)
        
        results_data = json.loads(result_json)
        return [VectorSearchResult.from_dict(r) for r in results_data]
    
    def vector_search_text(
        self,
        collection: str,
        query_text: str,
        k: int = 10,
    ) -> List[VectorSearchResult]:
        """
        Perform text-based similarity search (requires embedding provider).
        
        Args:
            collection: Collection name
            query_text: Query text
            k: Number of results
            
        Returns:
            List of search results
        """
        ffi = get_ffi()
        text_bytes = query_text.encode('utf-8')
        collection_bytes = collection.encode('utf-8')
        
        result_ptr = ffi.lib.keradb_vector_search_text(
            self._db, collection_bytes, text_bytes, k
        )
        if not result_ptr:
            raise Exception(f"Vector search text failed: {ffi.get_last_error()}")
        
        result_json = result_ptr.decode('utf-8')
        ffi.free_string(result_ptr)
        
        results_data = json.loads(result_json)
        return [VectorSearchResult.from_dict(r) for r in results_data]
    
    def vector_search_filtered(
        self,
        collection: str,
        query_vector: Embedding,
        k: int,
        filter: MetadataFilter,
    ) -> List[VectorSearchResult]:
        """
        Perform filtered vector similarity search.
        
        Args:
            collection: Collection name
            query_vector: Query vector
            k: Number of results
            filter: Metadata filter
            
        Returns:
            List of search results
        """
        ffi = get_ffi()
        vector_json = json.dumps(query_vector).encode('utf-8')
        filter_json = json.dumps(filter.to_dict()).encode('utf-8')
        collection_bytes = collection.encode('utf-8')
        
        result_ptr = ffi.lib.keradb_vector_search_filtered(
            self._db, collection_bytes, vector_json, k, filter_json
        )
        if not result_ptr:
            raise Exception(f"Vector search filtered failed: {ffi.get_last_error()}")
        
        result_json = result_ptr.decode('utf-8')
        ffi.free_string(result_ptr)
        
        results_data = json.loads(result_json)
        return [VectorSearchResult.from_dict(r) for r in results_data]
    
    def get_vector(self, collection: str, id: int) -> Optional[VectorDocument]:
        """
        Get a vector document by ID.
        
        Args:
            collection: Collection name
            id: Vector ID
            
        Returns:
            Vector document or None if not found
        """
        ffi = get_ffi()
        collection_bytes = collection.encode('utf-8')
        
        result_ptr = ffi.lib.keradb_get_vector(self._db, collection_bytes, id)
        if not result_ptr:
            return None
        
        result_json = result_ptr.decode('utf-8')
        ffi.free_string(result_ptr)
        
        return VectorDocument.from_dict(json.loads(result_json))
    
    def delete_vector(self, collection: str, id: int) -> bool:
        """
        Delete a vector document by ID.
        
        Args:
            collection: Collection name
            id: Vector ID
            
        Returns:
            True if deleted successfully
        """
        ffi = get_ffi()
        collection_bytes = collection.encode('utf-8')
        result = ffi.lib.keradb_delete_vector(self._db, collection_bytes, id)
        return result != 0
    
    def vector_stats(self, collection: str) -> VectorCollectionStats:
        """
        Get statistics for a vector collection.
        
        Args:
            collection: Collection name
            
        Returns:
            Collection statistics
        """
        ffi = get_ffi()
        collection_bytes = collection.encode('utf-8')
        
        result_ptr = ffi.lib.keradb_vector_stats(self._db, collection_bytes)
        if not result_ptr:
            raise Exception(f"Vector stats failed: {ffi.get_last_error()}")
        
        result_json = result_ptr.decode('utf-8')
        ffi.free_string(result_ptr)
        
        return VectorCollectionStats.from_dict(json.loads(result_json))


# Inject vector operations into Client class
from .client import Client
for attr_name in dir(VectorOperations):
    if not attr_name.startswith('_'):
        setattr(Client, attr_name, getattr(VectorOperations, attr_name))
