from typing import Dict, List, Optional, Union
from datetime import datetime
import os
import json

class DocumentStore:
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize the document store with an optional storage path."""
        self.storage_path = storage_path or os.path.join(os.getcwd(), "data", "documents")
        self.documents: Dict[str, Dict] = {}
        self.collections: Dict[str, List[str]] = {}
        
        # Create storage directory if it doesn't exist
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path, exist_ok=True)
    
    async def add_document(
        self,
        content: str,
        doc_type: str,
        metadata: Optional[Dict] = None,
        collection: Optional[str] = None
    ) -> str:
        """Add a document to the store and return its ID."""
        # Generate a unique document ID
        doc_id = f"{doc_type}_{datetime.now().timestamp()}"
        
        # Create document record
        document = {
            "id": doc_id,
            "type": doc_type,
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Store in memory
        self.documents[doc_id] = document
        
        # Add to collection if specified
        if collection:
            if collection not in self.collections:
                self.collections[collection] = []
            self.collections[collection].append(doc_id)
        
        # Persist to disk
        self._save_document(doc_id, document)
        
        return doc_id
    
    async def get_document(self, doc_id: str) -> Optional[Dict]:
        """Retrieve a document by its ID."""
        # Try to get from memory first
        if doc_id in self.documents:
            return self.documents[doc_id]
        
        # Try to load from disk if not in memory
        document = self._load_document(doc_id)
        if document:
            # Cache in memory
            self.documents[doc_id] = document
            return document
        
        return None
    
    async def update_document(
        self,
        doc_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Update an existing document's content and/or metadata."""
        document = await self.get_document(doc_id)
        if not document:
            return None
        
        # Update fields if provided
        if content is not None:
            document["content"] = content
        
        if metadata is not None:
            document["metadata"].update(metadata)
        
        document["updated_at"] = datetime.now().isoformat()
        
        # Update in memory
        self.documents[doc_id] = document
        
        # Persist to disk
        self._save_document(doc_id, document)
        
        return document
    
    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the store."""
        if doc_id not in self.documents and not self._document_exists(doc_id):
            return False
        
        # Remove from memory
        if doc_id in self.documents:
            del self.documents[doc_id]
        
        # Remove from collections
        for collection, docs in self.collections.items():
            if doc_id in docs:
                self.collections[collection].remove(doc_id)
        
        # Remove from disk
        self._delete_document_file(doc_id)
        
        return True
    
    async def search_documents(
        self,
        query: str,
        doc_type: Optional[str] = None,
        collection: Optional[str] = None,
        metadata_filters: Optional[Dict] = None
    ) -> List[Dict]:
        """Search for documents matching the query and filters."""
        results = []
        
        # Determine which documents to search
        doc_ids_to_search = []
        
        if collection and collection in self.collections:
            # Search only within the specified collection
            doc_ids_to_search = self.collections[collection]
        else:
            # Search all documents
            doc_ids_to_search = list(self.documents.keys())
            
            # If documents aren't loaded in memory, scan the storage directory
            if not doc_ids_to_search:
                doc_ids_to_search = self._scan_document_ids()
        
        # Process each document
        for doc_id in doc_ids_to_search:
            document = await self.get_document(doc_id)
            if not document:
                continue
            
            # Apply type filter
            if doc_type and document["type"] != doc_type:
                continue
            
            # Apply metadata filters
            if metadata_filters:
                skip = False
                for key, value in metadata_filters.items():
                    if key not in document["metadata"] or document["metadata"][key] != value:
                        skip = True
                        break
                if skip:
                    continue
            
            # Apply text search
            if query.lower() in document["content"].lower():
                results.append(document)
        
        return results
    
    async def get_collection(self, collection: str) -> List[Dict]:
        """Get all documents in a collection."""
        if collection not in self.collections:
            return []
        
        documents = []
        for doc_id in self.collections[collection]:
            document = await self.get_document(doc_id)
            if document:
                documents.append(document)
        
        return documents
    
    def _save_document(self, doc_id: str, document: Dict) -> None:
        """Save a document to disk."""
        file_path = os.path.join(self.storage_path, f"{doc_id}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(document, f, ensure_ascii=False, indent=2)
    
    def _load_document(self, doc_id: str) -> Optional[Dict]:
        """Load a document from disk."""
        file_path = os.path.join(self.storage_path, f"{doc_id}.json")
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    
    def _document_exists(self, doc_id: str) -> bool:
        """Check if a document exists on disk."""
        file_path = os.path.join(self.storage_path, f"{doc_id}.json")
        return os.path.exists(file_path)
    
    def _delete_document_file(self, doc_id: str) -> None:
        """Delete a document file from disk."""
        file_path = os.path.join(self.storage_path, f"{doc_id}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
    
    def _scan_document_ids(self) -> List[str]:
        """Scan the storage directory for document IDs."""
        doc_ids = []
        if os.path.exists(self.storage_path):
            for filename in os.listdir(self.storage_path):
                if filename.endswith('.json'):
                    doc_ids.append(filename[:-5])  # Remove .json extension
        return doc_ids