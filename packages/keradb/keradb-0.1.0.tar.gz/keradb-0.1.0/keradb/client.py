"""Core client implementation for KeraDB Python SDK."""

import json
from typing import Any, Dict, List, Optional, Iterator

from .ffi import get_ffi
from .results import InsertOneResult, InsertManyResult, UpdateResult, DeleteResult


# Type alias for document
Document = Dict[str, Any]


class KeraDBError(Exception):
    """Base exception for KeraDB errors."""
    pass


class Cursor:
    """
    Cursor for iterating over query results (MongoDB-compatible).
    
    Supports limit(), skip(), and iteration over results.
    """
    
    def __init__(self, documents: List[Document]):
        """
        Initialize the cursor with documents.
        
        Args:
            documents: List of documents to iterate over
        """
        self._documents = documents
        self._index = 0
        self._limit: Optional[int] = None
        self._skip: int = 0
    
    def limit(self, count: int) -> 'Cursor':
        """
        Limit the number of results.
        
        Args:
            count: Maximum number of documents to return
            
        Returns:
            Self for method chaining
        """
        self._limit = count
        return self
    
    def skip(self, count: int) -> 'Cursor':
        """
        Skip a number of results.
        
        Args:
            count: Number of documents to skip
            
        Returns:
            Self for method chaining
        """
        self._skip = count
        return self
    
    def all(self) -> List[Document]:
        """
        Return all documents as a list.
        
        Returns:
            List of documents
        """
        docs = self._documents[self._skip:]
        if self._limit is not None:
            docs = docs[:self._limit]
        return docs
    
    def __iter__(self) -> Iterator[Document]:
        """Iterate over documents."""
        return iter(self.all())
    
    def __next__(self) -> Document:
        """Get next document."""
        docs = self.all()
        if self._index >= len(docs):
            raise StopIteration
        doc = docs[self._index]
        self._index += 1
        return doc


class SingleResult:
    """Represents a single query result."""
    
    def __init__(self, document: Optional[Document], error: Optional[str] = None):
        """
        Initialize the result.
        
        Args:
            document: The document or None if not found
            error: Error message if operation failed
        """
        self._document = document
        self._error = error
    
    def decode(self) -> Optional[Document]:
        """
        Decode and return the document.
        
        Returns:
            The document or None if not found
            
        Raises:
            KeraDBError: If there was an error
        """
        if self._error:
            raise KeraDBError(self._error)
        return self._document


def _matches_filter(doc: Document, filter_dict: Dict[str, Any]) -> bool:
    """
    Check if a document matches a filter (MongoDB query support).
    
    Args:
        doc: Document to check
        filter_dict: Filter criteria
        
    Returns:
        True if document matches filter
    """
    for key, value in filter_dict.items():
        if key.startswith('$'):
            # Logical operators
            if key == '$and':
                if not all(_matches_filter(doc, f) for f in value):
                    return False
            elif key == '$or':
                if not any(_matches_filter(doc, f) for f in value):
                    return False
        else:
            doc_value = doc.get(key)
            if isinstance(value, dict):
                # Comparison operators
                for op, op_value in value.items():
                    if op == '$eq' and doc_value != op_value:
                        return False
                    elif op == '$ne' and doc_value == op_value:
                        return False
                    elif op == '$gt' and not (doc_value is not None and doc_value > op_value):
                        return False
                    elif op == '$gte' and not (doc_value is not None and doc_value >= op_value):
                        return False
                    elif op == '$lt' and not (doc_value is not None and doc_value < op_value):
                        return False
                    elif op == '$lte' and not (doc_value is not None and doc_value <= op_value):
                        return False
                    elif op == '$in' and doc_value not in op_value:
                        return False
                    elif op == '$nin' and doc_value in op_value:
                        return False
            else:
                # Direct equality
                if doc_value != value:
                    return False
    return True


def _apply_update(doc: Document, update: Dict[str, Any]) -> Document:
    """
    Apply MongoDB-style update operators to a document.
    
    Args:
        doc: Original document
        update: Update operations
        
    Returns:
        Updated document
    """
    result = doc.copy()
    
    for op, fields in update.items():
        if op == '$set':
            for key, value in fields.items():
                result[key] = value
        elif op == '$unset':
            for key in fields:
                result.pop(key, None)
        elif op == '$inc':
            for key, value in fields.items():
                result[key] = result.get(key, 0) + value
        elif op == '$push':
            for key, value in fields.items():
                if key not in result:
                    result[key] = []
                result[key].append(value)
        elif not op.startswith('$'):
            # If no operators, treat as replacement
            result = {'_id': doc['_id'], **update}
            break
    
    return result


class Collection:
    """
    A MongoDB-compatible collection interface.
    
    Provides methods like insert_one, find_one, update_one, delete_one, etc.
    """
    
    def __init__(self, db_handle, name: str):
        """
        Initialize the collection.
        
        Args:
            db_handle: Native database handle
            name: Collection name
        """
        self._db = db_handle
        self._name = name
        self._ffi = get_ffi()
    
    @property
    def name(self) -> str:
        """Get collection name."""
        return self._name
    
    def insert_one(self, document: Document) -> InsertOneResult:
        """
        Insert a single document.
        
        Args:
            document: The document to insert
            
        Returns:
            InsertOneResult with inserted_id
            
        Raises:
            KeraDBError: If insert fails
        """
        json_data = json.dumps(document).encode('utf-8')
        collection = self._name.encode('utf-8')
        
        id_ptr = self._ffi.lib.keradb_insert(self._db, collection, json_data)
        if not id_ptr:
            raise KeraDBError(f"Insert failed: {self._ffi.get_last_error()}")
        
        doc_id = id_ptr.decode('utf-8')
        
        return InsertOneResult(doc_id)
    
    def insert_many(self, documents: List[Document]) -> InsertManyResult:
        """
        Insert multiple documents.
        
        Args:
            documents: List of documents to insert
            
        Returns:
            InsertManyResult with inserted_ids
            
        Raises:
            KeraDBError: If any insert fails
        """
        inserted_ids = []
        for doc in documents:
            result = self.insert_one(doc)
            inserted_ids.append(result.inserted_id)
        return InsertManyResult(inserted_ids)
    
    def find_one(self, filter_dict: Optional[Dict[str, Any]] = None) -> Optional[Document]:
        """
        Find a single document matching the filter.
        
        Args:
            filter_dict: Query filter (supports {'_id': '...'} and MongoDB operators)
            
        Returns:
            The document or None if not found
            
        Raises:
            KeraDBError: If query fails
        """
        if filter_dict is None:
            # Return first document
            cursor = self.find().limit(1)
            docs = cursor.all()
            return docs[0] if docs else None
        
        # Check for _id filter
        if '_id' in filter_dict:
            doc_id = str(filter_dict['_id']).encode('utf-8')
            collection = self._name.encode('utf-8')
            
            doc_ptr = self._ffi.lib.keradb_find_by_id(self._db, collection, doc_id)
            if not doc_ptr:
                return None
            
            doc_json = doc_ptr.decode('utf-8')
            
            return json.loads(doc_json)
        
        # For other filters, scan all documents
        for doc in self.find():
            if _matches_filter(doc, filter_dict):
                return doc
        return None
    
    def find(self, filter_dict: Optional[Dict[str, Any]] = None) -> Cursor:
        """
        Find documents matching the filter.
        
        Args:
            filter_dict: Query filter (optional)
            
        Returns:
            Cursor for iterating results
            
        Raises:
            KeraDBError: If query fails
        """
        collection = self._name.encode('utf-8')
        
        docs_ptr = self._ffi.lib.keradb_find_all(self._db, collection, -1, -1)
        if not docs_ptr:
            return Cursor([])
        
        docs_json = docs_ptr.decode('utf-8')
        
        documents = json.loads(docs_json)
        
        # Apply filter if provided
        if filter_dict:
            documents = [doc for doc in documents if _matches_filter(doc, filter_dict)]
        
        return Cursor(documents)
    
    def update_one(self, filter_dict: Dict[str, Any], update: Dict[str, Any]) -> UpdateResult:
        """
        Update a single document.
        
        Args:
            filter_dict: Query filter to find the document
            update: Update operations (supports $set, $unset, $inc, $push)
            
        Returns:
            UpdateResult with matched_count and modified_count
            
        Raises:
            KeraDBError: If update fails
        """
        doc = self.find_one(filter_dict)
        if not doc:
            return UpdateResult(0, 0)
        
        # Apply update operators
        updated_doc = _apply_update(doc, update)
        
        # Remove _id from update data
        doc_id = updated_doc.pop('_id')
        
        json_data = json.dumps(updated_doc).encode('utf-8')
        collection = self._name.encode('utf-8')
        id_bytes = doc_id.encode('utf-8')
        
        result_ptr = self._ffi.lib.keradb_update(self._db, collection, id_bytes, json_data)
        if not result_ptr:
            raise KeraDBError(f"Update failed: {self._ffi.get_last_error()}")
        
        return UpdateResult(1, 1)
    
    def update_many(self, filter_dict: Dict[str, Any], update: Dict[str, Any]) -> UpdateResult:
        """
        Update multiple documents.
        
        Args:
            filter_dict: Query filter to find documents
            update: Update operations
            
        Returns:
            UpdateResult with matched_count and modified_count
            
        Raises:
            KeraDBError: If any update fails
        """
        docs = self.find(filter_dict).all()
        modified = 0
        
        for doc in docs:
            self.update_one({'_id': doc['_id']}, update)
            modified += 1
        
        return UpdateResult(len(docs), modified)
    
    def delete_one(self, filter_dict: Dict[str, Any]) -> DeleteResult:
        """
        Delete a single document.
        
        Args:
            filter_dict: Query filter to find the document
            
        Returns:
            DeleteResult with deleted_count
            
        Raises:
            KeraDBError: If delete fails
        """
        doc = self.find_one(filter_dict)
        if not doc:
            return DeleteResult(0)
        
        collection = self._name.encode('utf-8')
        doc_id = str(doc['_id']).encode('utf-8')
        
        result = self._ffi.lib.keradb_delete(self._db, collection, doc_id)
        return DeleteResult(1 if result else 0)
    
    def delete_many(self, filter_dict: Dict[str, Any]) -> DeleteResult:
        """
        Delete multiple documents.
        
        Args:
            filter_dict: Query filter to find documents
            
        Returns:
            DeleteResult with deleted_count
            
        Raises:
            KeraDBError: If any delete fails
        """
        docs = self.find(filter_dict).all()
        deleted = 0
        
        for doc in docs:
            result = self.delete_one({'_id': doc['_id']})
            deleted += result.deleted_count
        
        return DeleteResult(deleted)
    
    def count_documents(self, filter_dict: Optional[Dict[str, Any]] = None) -> int:
        """
        Count documents matching the filter.
        
        Args:
            filter_dict: Query filter (optional)
            
        Returns:
            Number of matching documents
        """
        if filter_dict:
            return len(self.find(filter_dict).all())
        
        collection = self._name.encode('utf-8')
        return self._ffi.lib.keradb_count(self._db, collection)


class Database:
    """
    A MongoDB-compatible database interface.
    
    Access collections using the collection() method.
    """
    
    def __init__(self, db_handle):
        """
        Initialize the database.
        
        Args:
            db_handle: Native database handle
        """
        self._db = db_handle
        self._ffi = get_ffi()
        self._collections: Dict[str, Collection] = {}
    
    def collection(self, name: str) -> Collection:
        """
        Get a collection by name.
        
        Args:
            name: Collection name
            
        Returns:
            Collection object
        """
        if name not in self._collections:
            self._collections[name] = Collection(self._db, name)
        return self._collections[name]
    
    def list_collection_names(self) -> List[str]:
        """
        Get list of collection names.
        
        Returns:
            List of collection names
        """
        collections_ptr = self._ffi.lib.keradb_list_collections(self._db)
        if not collections_ptr:
            return []
        
        collections_json = collections_ptr.decode('utf-8')
        
        collections = json.loads(collections_json)
        return [c[0] for c in collections]


class Client:
    """
    MongoDB-compatible client for KeraDB.
    
    Usage:
        client = Client("mydb.ndb")
        db = client.database()
        users = db.collection("users")
        client.close()
    
    Or as context manager:
        with Client("mydb.ndb") as client:
            db = client.database()
            db.collection("users").insert_one({"name": "Alice"})
    """
    
    def __init__(self, path: str):
        """
        Create or open a KeraDB database.
        
        Args:
            path: Path to the database file
            
        Raises:
            KeraDBError: If database cannot be opened
        """
        self._ffi = get_ffi()
        self._path = path
        
        path_bytes = path.encode('utf-8')
        self._db = self._ffi.lib.keradb_open(path_bytes)
        
        if not self._db:
            # Try creating if opening failed
            self._db = self._ffi.lib.keradb_create(path_bytes)
            if not self._db:
                raise KeraDBError(f"Failed to open database: {self._ffi.get_last_error()}")
        
        self._database = Database(self._db)
    
    def database(self, name: Optional[str] = None) -> Database:
        """
        Get the database object.
        
        Args:
            name: Database name (ignored, kept for MongoDB compatibility)
            
        Returns:
            Database object
        """
        return self._database
    
    def close(self) -> None:
        """Close the database connection."""
        if self._db:
            self._ffi.lib.keradb_close(self._db)
            self._db = None
    
    def sync(self) -> None:
        """Sync all changes to disk."""
        if self._db:
            self._ffi.lib.keradb_sync(self._db)
    
    def __enter__(self) -> 'Client':
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


def connect(path: str) -> Client:
    """
    Create or open a KeraDB database.
    
    Args:
        path: Path to the database file
        
    Returns:
        Client object
        
    Raises:
        KeraDBError: If database cannot be opened
    """
    return Client(path)
