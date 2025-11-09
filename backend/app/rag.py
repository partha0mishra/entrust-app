"""
RAG (Retrieval-Augmented Generation) Module for Data Governance Analysis
Uses ChromaDB for vector storage and sentence-transformers for embeddings.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import required libraries
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    logger.warning("ChromaDB not installed. Install with: pip install chromadb")
    CHROMADB_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    logger.warning("sentence-transformers not installed. Install with: pip install sentence-transformers")
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class RAGService:
    """Service for RAG operations: ingestion, retrieval, and context generation"""

    def __init__(
        self,
        knowledge_base_dir: Optional[str] = None,
        chroma_persist_dir: Optional[str] = None,
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize RAG service

        Args:
            knowledge_base_dir: Path to knowledge base directory
            chroma_persist_dir: Path to ChromaDB persistence directory
            embedding_model: Name of sentence-transformer model to use
        """
        self.knowledge_base_dir = Path(knowledge_base_dir or Path(__file__).parent.parent / "Knowledge")
        self.chroma_persist_dir = chroma_persist_dir or str(Path(__file__).parent.parent / "chroma_db")
        self.embedding_model_name = embedding_model

        # Check dependencies
        if not CHROMADB_AVAILABLE or not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.error("RAG dependencies not available. Install chromadb and sentence-transformers.")
            self.enabled = False
            return

        self.enabled = True

        # Initialize embedding model
        try:
            logger.info(f"Loading embedding model: {self.embedding_model_name}")
            self.embedder = SentenceTransformer(self.embedding_model_name)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.enabled = False
            return

        # Initialize ChromaDB client
        try:
            logger.info(f"Initializing ChromaDB at: {self.chroma_persist_dir}")
            # Disable telemetry to prevent PostHog errors
            self.client = chromadb.PersistentClient(
                path=self.chroma_persist_dir,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name="data_governance_knowledge",
                metadata={"description": "Knowledge base for data governance dimensions"}
            )
            logger.info(f"ChromaDB collection initialized. Document count: {self.collection.count()}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self.enabled = False

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
        """
        Split text into overlapping chunks

        Args:
            text: Text to chunk
            chunk_size: Target size of each chunk in characters
            overlap: Overlap between chunks in characters

        Returns:
            List of text chunks
        """
        # Simple character-based chunking
        # For production, consider using more sophisticated chunking (sentence-based, etc.)
        chunks = []
        words = text.split()

        current_chunk = []
        current_size = 0

        for word in words:
            current_chunk.append(word)
            current_size += len(word) + 1  # +1 for space

            if current_size >= chunk_size:
                chunk_text = ' '.join(current_chunk)
                chunks.append(chunk_text)

                # Keep overlap words for next chunk
                overlap_words = []
                overlap_size = 0
                for w in reversed(current_chunk):
                    if overlap_size >= overlap:
                        break
                    overlap_words.insert(0, w)
                    overlap_size += len(w) + 1

                current_chunk = overlap_words
                current_size = overlap_size

        # Add remaining words
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def _generate_chunk_id(self, dimension: str, filename: str, chunk_index: int) -> str:
        """Generate unique ID for a chunk"""
        raw_id = f"{dimension}_{filename}_{chunk_index}"
        return hashlib.md5(raw_id.encode()).hexdigest()

    def ingest_knowledge(self, force_reingest: bool = False) -> Dict:
        """
        Ingest knowledge base documents into ChromaDB

        Args:
            force_reingest: If True, clear existing collection and reingest all

        Returns:
            Dictionary with ingestion statistics
        """
        if not self.enabled:
            return {
                "success": False,
                "error": "RAG service not enabled. Check dependencies."
            }

        logger.info("Starting knowledge base ingestion...")

        # Check if already ingested
        existing_count = self.collection.count()
        if existing_count > 0 and not force_reingest:
            logger.info(f"Knowledge base already ingested ({existing_count} documents). Use force_reingest=True to re-ingest.")
            return {
                "success": True,
                "message": f"Knowledge base already ingested with {existing_count} documents",
                "documents_ingested": existing_count,
                "skipped": True
            }

        # Clear collection if force reingest
        if force_reingest and existing_count > 0:
            logger.info("Force reingest: Clearing existing collection...")
            try:
                self.client.delete_collection("data_governance_knowledge")
                self.collection = self.client.get_or_create_collection(
                    name="data_governance_knowledge",
                    metadata={"description": "Knowledge base for data governance dimensions"}
                )
                logger.info("Collection cleared")
            except Exception as e:
                logger.error(f"Failed to clear collection: {e}")
                return {"success": False, "error": str(e)}

        stats = {
            "files_processed": 0,
            "chunks_created": 0,
            "dimensions": {},
            "errors": []
        }

        # Map folder names to dimension names
        dimension_mapping = {
            "privacy_compliance": "Data Privacy & Compliance",
            "ethics_bias": "Data Ethics & Bias",
            "lineage_traceability": "Data Lineage & Traceability",
            "value_lifecycle": "Data Value & Lifecycle Management",
            "governance_management": "Data Governance & Management",
            "security_access": "Data Security & Access",
            "metadata_documentation": "Metadata & Documentation",
            "quality": "Data Quality",
            "maturity": "Organizational Maturity"  # Cross-cutting
        }

        # Process each dimension folder
        if not self.knowledge_base_dir.exists():
            error_msg = f"Knowledge base directory not found: {self.knowledge_base_dir}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

        for dimension_folder in self.knowledge_base_dir.iterdir():
            if not dimension_folder.is_dir():
                continue

            dimension_key = dimension_folder.name
            dimension_name = dimension_mapping.get(dimension_key, dimension_key)

            logger.info(f"Processing dimension: {dimension_name}")
            stats["dimensions"][dimension_name] = {"files": 0, "chunks": 0}

            # Process each file in dimension folder
            for file_path in dimension_folder.glob("*.txt"):
                try:
                    logger.info(f"  Reading file: {file_path.name}")

                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    if len(content) < 50:  # Skip very small files
                        logger.warning(f"  Skipping small file: {file_path.name}")
                        continue

                    # Chunk the content
                    chunks = self._chunk_text(content, chunk_size=500, overlap=100)
                    logger.info(f"  Created {len(chunks)} chunks")

                    # Prepare batch data
                    chunk_ids = []
                    chunk_texts = []
                    chunk_metadatas = []

                    for i, chunk in enumerate(chunks):
                        chunk_id = self._generate_chunk_id(dimension_key, file_path.name, i)
                        chunk_ids.append(chunk_id)
                        chunk_texts.append(chunk)
                        chunk_metadatas.append({
                            "dimension": dimension_name,
                            "dimension_key": dimension_key,
                            "source_file": file_path.name,
                            "chunk_index": i,
                            "total_chunks": len(chunks)
                        })

                    # Generate embeddings
                    logger.info(f"  Generating embeddings...")
                    embeddings = self.embedder.encode(chunk_texts, show_progress_bar=False)

                    # Add to collection
                    self.collection.add(
                        ids=chunk_ids,
                        documents=chunk_texts,
                        embeddings=embeddings.tolist(),
                        metadatas=chunk_metadatas
                    )

                    stats["files_processed"] += 1
                    stats["chunks_created"] += len(chunks)
                    stats["dimensions"][dimension_name]["files"] += 1
                    stats["dimensions"][dimension_name]["chunks"] += len(chunks)

                    logger.info(f"  ✓ Ingested {len(chunks)} chunks from {file_path.name}")

                except Exception as e:
                    error_msg = f"Error processing {file_path}: {e}"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)

        logger.info(f"\n{'='*60}")
        logger.info("Ingestion Complete!")
        logger.info(f"{'='*60}")
        logger.info(f"Files processed: {stats['files_processed']}")
        logger.info(f"Total chunks created: {stats['chunks_created']}")
        logger.info(f"Total documents in collection: {self.collection.count()}")

        return {
            "success": True,
            "stats": stats,
            "total_documents": self.collection.count()
        }

    def retrieve_context(
        self,
        query: str,
        dimension: Optional[str] = None,
        top_k: int = 3,
        include_maturity: bool = False
    ) -> str:
        """
        Retrieve relevant context for a query

        Args:
            query: Query text
            dimension: Optional dimension filter (e.g., "Data Privacy & Compliance")
            top_k: Number of top results to return
            include_maturity: If True, also retrieve from maturity dimension

        Returns:
            Formatted context string
        """
        if not self.enabled:
            logger.warning("RAG service not enabled")
            return ""

        try:
            # Generate query embedding
            query_embedding = self.embedder.encode([query])[0]

            # Build where clause for filtering
            where_clause = None
            if dimension:
                where_clause = {"dimension": dimension}

            # Query collection
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k,
                where=where_clause
            )

            # Also retrieve maturity context if requested
            maturity_results = None
            if include_maturity:
                maturity_results = self.collection.query(
                    query_embeddings=[query_embedding.tolist()],
                    n_results=2,  # Fewer maturity docs
                    where={"dimension": "Organizational Maturity"}
                )

            # Format context
            context_parts = []

            if results and results['documents'] and len(results['documents'][0]) > 0:
                context_parts.append("**Relevant Standards and Best Practices:**\n")

                for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                    source = metadata.get('source_file', 'Unknown')
                    context_parts.append(f"\n{i+1}. [{source}]\n{doc}\n")

            if maturity_results and maturity_results['documents'] and len(maturity_results['documents'][0]) > 0:
                context_parts.append("\n**Maturity Model Context:**\n")

                for i, doc in enumerate(maturity_results['documents'][0]):
                    context_parts.append(f"\n{doc}\n")

            if not context_parts:
                return ""

            return '\n'.join(context_parts)

        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return ""

    def get_dimension_context(
        self,
        dimension: str,
        survey_summary: Optional[str] = None,
        top_k: int = 5
    ) -> str:
        """
        Get comprehensive context for a specific dimension

        Args:
            dimension: Dimension name
            survey_summary: Optional summary of survey data for context-aware retrieval
            top_k: Number of chunks to retrieve

        Returns:
            Formatted context string
        """
        if not self.enabled:
            return ""

        # Build query
        if survey_summary:
            query = f"{dimension}: {survey_summary}"
        else:
            query = f"Best practices and standards for {dimension}"

        # Retrieve context (always include maturity)
        context = self.retrieve_context(
            query=query,
            dimension=dimension,
            top_k=top_k,
            include_maturity=True
        )

        return context

    def get_stats(self) -> Dict:
        """Get statistics about the knowledge base"""
        if not self.enabled:
            return {"enabled": False}

        try:
            total_docs = self.collection.count()

            # Get counts by dimension
            dimensions = {}

            # Query for each dimension
            dimension_names = [
                "Data Privacy & Compliance",
                "Data Ethics & Bias",
                "Data Lineage & Traceability",
                "Data Value & Lifecycle Management",
                "Data Governance & Management",
                "Data Security & Access",
                "Metadata & Documentation",
                "Data Quality",
                "Organizational Maturity"
            ]

            for dim in dimension_names:
                try:
                    results = self.collection.get(where={"dimension": dim})
                    dimensions[dim] = len(results['ids']) if results else 0
                except:
                    dimensions[dim] = 0

            return {
                "enabled": True,
                "total_documents": total_docs,
                "by_dimension": dimensions,
                "embedding_model": self.embedding_model_name,
                "knowledge_base_dir": str(self.knowledge_base_dir),
                "chroma_persist_dir": self.chroma_persist_dir
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"enabled": True, "error": str(e)}


# Global RAG service instance (lazy initialization)
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create global RAG service instance"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service


def initialize_rag(force_reingest: bool = False) -> Dict:
    """
    Initialize RAG service and ingest knowledge base

    Args:
        force_reingest: If True, clear and re-ingest all documents

    Returns:
        Ingestion result dictionary
    """
    service = get_rag_service()
    if not service.enabled:
        return {
            "success": False,
            "error": "RAG service not enabled. Install dependencies: pip install chromadb sentence-transformers"
        }

    return service.ingest_knowledge(force_reingest=force_reingest)


# Convenience functions for easy import
def retrieve_context(query: str, dimension: Optional[str] = None, top_k: int = 3) -> str:
    """Retrieve relevant context for a query"""
    service = get_rag_service()
    return service.retrieve_context(query, dimension, top_k)


def get_dimension_context(dimension: str, survey_summary: Optional[str] = None) -> str:
    """Get comprehensive context for a dimension"""
    service = get_rag_service()
    return service.get_dimension_context(dimension, survey_summary)


def get_rag_stats() -> Dict:
    """Get RAG service statistics"""
    service = get_rag_service()
    return service.get_stats()


# Command-line interface
if __name__ == "__main__":
    import sys

    logger.info("="*60)
    logger.info("RAG Service - Knowledge Base Ingestion")
    logger.info("="*60)

    # Parse arguments
    force_reingest = "--force" in sys.argv

    # Initialize and ingest
    result = initialize_rag(force_reingest=force_reingest)

    if result.get("success"):
        logger.info("\n✓ RAG service initialized successfully!")
        if result.get("stats"):
            logger.info(f"\nStatistics:")
            logger.info(f"  Files processed: {result['stats']['files_processed']}")
            logger.info(f"  Total chunks: {result['stats']['chunks_created']}")
            logger.info(f"  Total documents: {result.get('total_documents', 0)}")
    else:
        logger.error(f"\n✗ RAG initialization failed: {result.get('error')}")
        sys.exit(1)

    # Print stats
    stats = get_rag_stats()
    if stats.get("enabled"):
        logger.info(f"\n{'='*60}")
        logger.info("Knowledge Base Statistics")
        logger.info(f"{'='*60}")
        logger.info(f"Total documents: {stats.get('total_documents', 0)}")
        logger.info(f"Embedding model: {stats.get('embedding_model')}")
        logger.info(f"\nDocuments by dimension:")
        for dim, count in stats.get('by_dimension', {}).items():
            logger.info(f"  {dim}: {count}")
