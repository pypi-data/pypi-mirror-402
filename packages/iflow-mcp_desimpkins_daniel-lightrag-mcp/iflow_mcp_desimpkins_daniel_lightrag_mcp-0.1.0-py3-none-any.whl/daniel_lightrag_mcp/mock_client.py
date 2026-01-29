"""
Mock LightRAG client for testing without a real LightRAG server.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, AsyncGenerator
from .models import (
    # Request models
    InsertTextRequest, InsertTextsRequest, QueryRequest, EntityUpdateRequest,
    RelationUpdateRequest, DeleteDocRequest, DeleteEntityRequest, DeleteRelationRequest,
    DocumentsRequest, ClearCacheRequest, EntityExistsRequest,
    # Response models
    InsertResponse, ScanResponse, UploadResponse, DocumentsResponse, PaginatedDocsResponse,
    DeleteDocByIdResponse, ClearDocumentsResponse, PipelineStatusResponse, TrackStatusResponse,
    StatusCountsResponse, ClearCacheResponse, DeletionResult, QueryResponse, GraphResponse,
    LabelsResponse, EntityExistsResponse, EntityUpdateResponse, RelationUpdateResponse,
    HealthResponse, TextDocument
)
from .client import LightRAGError, LightRAGValidationError

logger = logging.getLogger(__name__)


class MockLightRAGClient:
    """Mock client for LightRAG API for testing purposes."""
    
    def __init__(self, base_url: str = "http://localhost:9621", api_key: Optional[str] = None, timeout: float = 30.0):
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        
        # Mock data storage
        self._documents = []
        self._entities = []
        self._relations = []
        self._track_counter = 0
        
        logger.info(f"Initialized MockLightRAG client with base_url: {base_url}")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    # Document Management Methods
    
    async def insert_text(self, text: str) -> InsertResponse:
        """Mock insert text into LightRAG."""
        self._track_counter += 1
        track_id = f"track_{self._track_counter}"
        
        doc = TextDocument(
            doc_id=f"doc_{self._track_counter}",
            title=f"Document {self._track_counter}",
            content=text[:100],
            status="PROCESSED",
            metadata={"source": "text_insert"}
        )
        self._documents.append(doc)
        
        return InsertResponse(
            status="success",
            message=f"Text inserted successfully",
            track_id=track_id
        )
    
    async def insert_texts(self, texts: List[Dict[str, Any]]) -> InsertResponse:
        """Mock insert multiple texts into LightRAG."""
        self._track_counter += 1
        track_id = f"track_{self._track_counter}"
        
        for text_data in texts:
            self._track_counter += 1
            doc = TextDocument(
                doc_id=f"doc_{self._track_counter}",
                title=text_data.get("title", f"Document {self._track_counter}"),
                content=text_data.get("content", "")[:100],
                status="PROCESSED",
                metadata=text_data.get("metadata", {})
            )
            self._documents.append(doc)
        
        return InsertResponse(
            status="success",
            message=f"{len(texts)} texts inserted successfully",
            track_id=track_id
        )
    
    async def upload_document(self, file_path: str) -> UploadResponse:
        """Mock upload document to LightRAG."""
        import os
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File does not exist: {file_path}")
        
        self._track_counter += 1
        track_id = f"track_{self._track_counter}"
        
        doc = TextDocument(
            doc_id=f"doc_{self._track_counter}",
            title=os.path.basename(file_path),
            content=f"Uploaded file: {file_path}",
            status="PROCESSED",
            metadata={"source": "file_upload", "file_path": file_path}
        )
        self._documents.append(doc)
        
        return UploadResponse(
            status="success",
            message=f"Document uploaded successfully",
            track_id=track_id
        )
    
    async def scan_documents(self) -> ScanResponse:
        """Mock scan for new documents."""
        return ScanResponse(
            status="success",
            message="Scan completed",
            scanned_count=len(self._documents)
        )
    
    async def get_documents(self) -> DocumentsResponse:
        """Mock retrieve all documents."""
        return DocumentsResponse(
            documents=self._documents,
            total=len(self._documents)
        )
    
    async def get_documents_paginated(self, page: int = 1, page_size: int = 10, status_filter: Optional[str] = None) -> PaginatedDocsResponse:
        """Mock retrieve documents with pagination."""
        start = (page - 1) * page_size
        end = start + page_size
        docs = self._documents[start:end]
        
        return PaginatedDocsResponse(
            documents=docs,
            total=len(self._documents),
            page=page,
            page_size=page_size
        )
    
    async def delete_document(self, document_id: str) -> DeleteDocByIdResponse:
        """Mock delete document by ID."""
        self._documents = [doc for doc in self._documents if doc.doc_id != document_id]
        return DeleteDocByIdResponse(
            status="success",
            message=f"Document {document_id} deleted successfully"
        )
    
    async def clear_documents(self) -> ClearDocumentsResponse:
        """Mock clear all documents."""
        count = len(self._documents)
        self._documents.clear()
        return ClearDocumentsResponse(
            status="success",
            message=f"Cleared {count} documents"
        )
    
    # Query Methods
    
    async def query_text(self, query: str, mode: str = "hybrid", only_need_context: bool = False) -> QueryResponse:
        """Mock query LightRAG with text."""
        if not query or not query.strip():
            raise LightRAGValidationError("Query cannot be empty")
        
        return QueryResponse(
            query=query,
            mode=mode,
            results=[
                {
                    "content": f"Mock response for query: {query[:50]}...",
                    "confidence": 0.9,
                    "sources": ["doc_1"]
                }
            ]
        )
    
    async def query_text_stream(self, query: str, mode: str = "hybrid", only_need_context: bool = False) -> AsyncGenerator[str, None]:
        """Mock stream query results."""
        if not query or not query.strip():
            raise LightRAGValidationError("Query cannot be empty")
        
        chunks = [f"Mock streaming response for: {query[:30]}...", " Chunk 2", " Chunk 3"]
        for chunk in chunks:
            yield chunk
            await asyncio.sleep(0.1)
    
    # Knowledge Graph Methods
    
    async def get_knowledge_graph(self, label: str = "*") -> GraphResponse:
        """Mock retrieve knowledge graph."""
        return GraphResponse(
            entities=self._entities,
            relations=self._relations,
            total_entities=len(self._entities),
            total_relations=len(self._relations)
        )
    
    async def get_graph_labels(self) -> LabelsResponse:
        """Mock get graph labels."""
        return LabelsResponse(
            labels=["Person", "Organization", "Concept"]
        )
    
    async def check_entity_exists(self, entity_name: str) -> EntityExistsResponse:
        """Mock check if entity exists."""
        exists = any(e.get("entity_name") == entity_name for e in self._entities)
        return EntityExistsResponse(
            exists=exists,
            entity_name=entity_name
        )
    
    async def update_entity(self, entity_id: str, properties: Dict[str, Any], entity_name: Optional[str] = None) -> EntityUpdateResponse:
        """Mock update entity."""
        return EntityUpdateResponse(
            status="success",
            message=f"Entity {entity_id} updated successfully"
        )
    
    async def update_relation(self, source_id: str, target_id: str, updated_data: Dict[str, Any]) -> RelationUpdateResponse:
        """Mock update relation."""
        return RelationUpdateResponse(
            status="success",
            message=f"Relation updated successfully"
        )
    
    async def delete_entity(self, entity_id: str, entity_name: Optional[str] = None) -> DeletionResult:
        """Mock delete entity."""
        self._entities = [e for e in self._entities if e.get("entity_id") != entity_id]
        return DeletionResult(
            status="success",
            message=f"Entity {entity_id} deleted successfully"
        )
    
    async def delete_relation(self, relation_id: str, source_entity: str = "unknown", target_entity: str = "unknown") -> DeletionResult:
        """Mock delete relation."""
        self._relations = [r for r in self._relations if r.get("relation_id") != relation_id]
        return DeletionResult(
            status="success",
            message=f"Relation {relation_id} deleted successfully"
        )
    
    # System Management Methods
    
    async def get_pipeline_status(self) -> PipelineStatusResponse:
        """Mock get pipeline status."""
        return PipelineStatusResponse(
            status="running",
            message="Pipeline is running"
        )
    
    async def get_track_status(self, track_id: str) -> TrackStatusResponse:
        """Mock get track status."""
        return TrackStatusResponse(
            track_id=track_id,
            status="completed",
            message=f"Track {track_id} completed successfully"
        )
    
    async def get_document_status_counts(self) -> StatusCountsResponse:
        """Mock get document status counts."""
        return StatusCountsResponse(
            processed=len(self._documents),
            pending=0,
            failed=0
        )
    
    async def clear_cache(self, cache_type: Optional[str] = None) -> ClearCacheResponse:
        """Mock clear cache."""
        return ClearCacheResponse(
            status="success",
            message="Cache cleared successfully"
        )
    
    async def get_health(self) -> HealthResponse:
        """Mock get health status."""
        return HealthResponse(
            status="healthy",
            message="Mock LightRAG server is healthy"
        )