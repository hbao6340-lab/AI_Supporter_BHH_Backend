"""
Knowledge Retriever - Semantic search through documents
Uses TF-IDF + cosine similarity if scikit-learn is available,
otherwise falls back to simple keyword matching
"""

import os
import logging
import pickle
import hashlib
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import re

logger = logging.getLogger(__name__)

# Try to import sklearn for TF-IDF
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not installed. Using simple keyword search instead.")


class KnowledgeRetriever:
    """Retrieves relevant documents using TF-IDF similarity search."""
    
    def __init__(self, knowledge_dir: str = None):
        # Default to knowledge folder - use absolute path from project root
        if knowledge_dir is None:
            # Go up from backend/knowledge/retriever.py to project root
            retriever_path = Path(__file__).parent
            knowledge_parent = retriever_path.parent  # backend/knowledge
            project_root = knowledge_parent.parent  # project root
            
            # Debug: Log the paths being calculated
            logger.info(f"retriever_path: {retriever_path}")
            logger.info(f"knowledge_parent: {knowledge_parent}")
            logger.info(f"project_root: {project_root}")
            
            # Try multiple possible locations for knowledge files
            # Order matters! Check root knowledge folder first (more likely to be deployed)
            possible_paths = [
                # Option 1: knowledge/data (Render deployment - docs are in data subfolder)
                project_root / "knowledge" / "data",
                # Option 2: knowledge (root folder - documents directly in folder)
                project_root / "knowledge",
                # Option 3: Current working directory with knowledge/data
                Path(".") / "knowledge" / "data",
                # Option 4: Current working directory with knowledge
                Path(".") / "knowledge",
                # Option 5: /var/task (Render/Vercel typical deployment)
                Path("/var/task"),
                Path("/var/task/knowledge"),
                Path("/var/task/knowledge/data"),
                Path("/var/task/backend/knowledge/data"),
                # Option 6: backend/knowledge/data (local development)
                project_root / "backend" / "knowledge" / "data",
                # Option 7: backend/knowledge/data directly
                knowledge_parent / "data",
            ]
            
            # Use the first path that exists
            knowledge_dir = None
            for path in possible_paths:
                logger.info(f"Checking knowledge path: {path} (exists: {path.exists()})")
                if path.exists():
                    knowledge_dir = path
                    logger.info(f"Using knowledge directory: {knowledge_dir}")
                    break
            
            # Fallback to first option if none exist (will log warning later)
            if knowledge_dir is None:
                knowledge_dir = possible_paths[0]
                logger.warning(f"No knowledge directory found, using default: {knowledge_dir}")
        
        # Convert to absolute path if relative
        if not Path(knowledge_dir).is_absolute():
            knowledge_dir = Path(__file__).parent.parent.parent / knowledge_dir
            
        self.knowledge_dir = Path(knowledge_dir)
        self.documents = []
        self.vectorizer = None
        self.tfidf_matrix = None
        self.document_sources = []
        
        logger.info(f"Knowledge directory: {self.knowledge_dir}")
        
        # Cache file for processed documents
        cache_path = Path(__file__).parent / ".cache"
        cache_path.mkdir(exist_ok=True)
        self.cache_dir = cache_path
    
    def load_knowledge(self, force_reload: bool = False) -> bool:
        """Load and index all documents from the knowledge directory."""
        # Check if knowledge directory exists
        logger.info(f"load_knowledge called with dir: {self.knowledge_dir}")
        logger.info(f"Directory exists: {self.knowledge_dir.exists()}")
        logger.info(f"Is directory: {self.knowledge_dir.is_dir() if self.knowledge_dir.exists() else 'N/A'}")
        
        if not self.knowledge_dir.exists():
            logger.warning(f"Knowledge directory does not exist: {self.knowledge_dir}")
            return False
        
        # Try to import parser - try different paths for local vs deployment
        try:
            from backend.knowledge.document_parser import parser
        except (ImportError, ModuleNotFoundError):
            try:
                from knowledge.document_parser import parser
            except (ImportError, ModuleNotFoundError):
                try:
                    from document_parser import parser
                except ImportError:
                    logger.error("Could not import document parser")
                    return False
        
        # Parse all documents
        parsed_docs = parser.parse_directory(str(self.knowledge_dir))
        
        if not parsed_docs:
            logger.info("No documents found in knowledge directory")
            return True  # Not an error, just empty
        
        # Prepare documents for indexing
        self.documents = []
        self.document_sources = []
        
        for doc in parsed_docs:
            # Split long documents into chunks
            chunks = self._chunk_text(doc['content'], chunk_size=500, overlap=50)
            
            for i, chunk in enumerate(chunks):
                if chunk.strip():
                    self.documents.append(chunk)
                    self.document_sources.append({
                        'filename': doc['filename'],
                        'chunk_id': i,
                        'filepath': doc['filepath']
                    })
        
        if not self.documents:
            logger.info("No text content extracted from documents")
            return True
        
        # If scikit-learn is available, build TF-IDF index
        if SKLEARN_AVAILABLE:
            try:
                self.vectorizer = TfidfVectorizer(
                    lowercase=True,
                    stop_words=None,  # Don't use English stop words for Vietnamese
                    ngram_range=(1, 2),
                    max_features=10000,
                    min_df=1
                )
                
                self.tfidf_matrix = self.vectorizer.fit_transform(self.documents)
                
                # Save to cache
                try:
                    cache_file = self.cache_dir / "knowledge_cache.pkl"
                    with open(cache_file, 'wb') as f:
                        pickle.dump({
                            'documents': self.documents,
                            'sources': self.document_sources,
                            'vectorizer': self.vectorizer,
                            'tfidf_matrix': self.tfidf_matrix
                        }, f)
                    logger.info(f"Cached knowledge base to {cache_file}")
                except Exception as e:
                    logger.warning(f"Failed to save cache: {e}")
                    
            except Exception as e:
                logger.warning(f"TF-IDF indexing failed: {e}, using simple search")
        
        logger.info(f"Loaded {len(self.documents)} document chunks from {len(parsed_docs)} files")
        return True
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks."""
        # Clean text
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings near chunk boundary
                for sep in ['. ', '! ', '? ', '\n', '। ']:
                    last_sep = text.rfind(sep, start, end)
                    if last_sep > start + chunk_size // 2:
                        end = last_sep + 1
                        break
            
            chunks.append(text[start:end])
            start = end - overlap
        
        return chunks
    
    def search(self, query: str, top_k: int = 3, min_similarity: float = 0.1) -> List[Dict]:
        """Search for relevant documents given a query."""
        if not self.documents:
            return []
        
        # Use TF-IDF if available
        if SKLEARN_AVAILABLE and self.tfidf_matrix is not None:
            try:
                # Transform query
                query_vector = self.vectorizer.transform([query])
                
                # Calculate similarities
                similarities = cosine_similarity(query_vector, self.tfidf_matrix)[0]
                
                # Get top results
                top_indices = similarities.argsort()[::-1][:top_k]
                
                results = []
                for idx in top_indices:
                    sim_score = similarities[idx]
                    if sim_score >= min_similarity:
                        results.append({
                            'content': self.documents[idx],
                            'source': self.document_sources[idx],
                            'similarity': float(sim_score)
                        })
                
                return results
            except Exception as e:
                logger.error(f"TF-IDF Search error: {e}")
        
        # Fallback: Simple keyword matching
        return self._simple_search(query, top_k, min_similarity)
    
    def _simple_search(self, query: str, top_k: int = 3, min_similarity: float = 0.1) -> List[Dict]:
        """Simple keyword-based search fallback when scikit-learn is not available."""
        if not self.documents:
            return []
        
        # Normalize query
        query_lower = query.lower()
        query_words = set(re.findall(r'\w+', query_lower))
        
        if not query_words:
            return []
        
        results = []
        
        for idx, doc in enumerate(self.documents):
            doc_lower = doc.lower()
            doc_words = set(re.findall(r'\w+', doc_lower))
            
            # Calculate keyword overlap score
            matches = query_words & doc_words
            if matches:
                score = len(matches) / max(len(query_words), len(doc_words))
                
                if score >= min_similarity:
                    results.append({
                        'content': self.documents[idx],
                        'source': self.document_sources[idx],
                        'similarity': float(score)
                    })
        
        # Sort by score and return top k
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]
    
    def get_answer_context(self, query: str, max_chars: int = 2000) -> Tuple[str, bool]:
        """
        Get context from knowledge base for a query.
        Returns (context, found_flag) - found_flag is True if relevant content found.
        """
        if not self.documents:
            return "", False
        
        # Use lower similarity threshold to find more relevant documents
        results = self.search(query, top_k=10, min_similarity=0.01)
        
        if not results:
            return "", False
        
        logger.info(f"Search results for '{query[:30]}...': {len(results)} documents found")
        for r in results:
            logger.info(f"  - {r['source']['filename']}: similarity={r['similarity']:.3f}")
        
        # Build context from results
        context_parts = []
        total_chars = 0
        
        for result in results:
            if total_chars + len(result['content']) > max_chars:
                break
            
            source_info = f"[Nguồn: {result['source']['filename']}]"
            context_parts.append(f"{source_info}\n{result['content']}")
            total_chars += len(result['content'])
        
        context = "\n\n".join(context_parts)
        
        # Check if we have meaningful results - be more lenient
        if results:
            return context, True
        
        return context, False
    
    def has_knowledge(self) -> bool:
        """Check if knowledge base is loaded."""
        return len(self.documents) > 0


# Singleton instance
retriever = KnowledgeRetriever()
