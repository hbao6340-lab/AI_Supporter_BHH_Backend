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
except ImportError as e:
    SKLEARN_AVAILABLE = False
    logger.warning(f"scikit-learn not installed: {e}. Using simple keyword search instead.")


class KnowledgeRetriever:
    """Retrieves relevant documents using TF-IDF similarity search."""

    # This file lives at:  <project_root>/backend/knowledge/retriever.py
    # Dir hierarchy:      backend/  ←  knowledge/  ←  retriever.py
    # knowledge_parent = retriever_path.parent  →  .../backend/knowledge/   (= the "knowledge" dir)
    # project_root     = knowledge_parent.parent → .../backend/            (one above)

    def __init__(self, knowledge_dir: str = None):
        if knowledge_dir is None:
            retriever_path   = Path(__file__).parent       # .../backend/knowledge/
            knowledge_parent = retriever_path              # .../backend/knowledge/
            project_root     = knowledge_parent.parent      # .../backend/

            logger.info(f"retriever_path: {retriever_path}")
            logger.info(f"knowledge_parent: {knowledge_parent}")
            logger.info(f"project_root: {project_root}")

            possible_paths = [
                # [0] local-dev: data/ subfolder of the knowledge dir
                knowledge_parent / "data",
                # [1] fallback: docs directly in the knowledge/ folder
                knowledge_parent,
                # [2] project-root-aware: vn_testing/knowledge/data
                project_root.parent / "knowledge" / "data",
                # [3] project-root-aware: vn_testing/knowledge
                project_root.parent / "knowledge",
                # [4] Render / Vercel
                Path("/var/task"),
                Path("/var/task/knowledge"),
                Path("/var/task/knowledge/data"),
                Path("/var/task/backend/knowledge/data"),
                # [8] via project root chain
                project_root / "knowledge" / "data",
            ]

            knowledge_dir = None
            for path in possible_paths:
                logger.info(f"Checking knowledge path: {path} (exists: {path.exists()})")
                if path.exists():
                    knowledge_dir = path
                    logger.info(f"Using knowledge directory: {knowledge_dir}")
                    break

            if knowledge_dir is None:
                knowledge_dir = possible_paths[0]
                logger.warning(f"No knowledge directory found, using default: {knowledge_dir}")

        # Convert relative paths to absolute using CWD
        if not Path(knowledge_dir).is_absolute():
            import os
            knowledge_dir = Path(os.getcwd()) / knowledge_dir

        self.knowledge_dir  = Path(knowledge_dir)
        self.documents      = []
        self.vectorizer     = None
        self.tfidf_matrix   = None
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

    def _chunk_text(self, text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks, trying to keep names and entities intact."""
        # Clean text
        text = re.sub(r'\s+', ' ', text)
        # Collapse Excel pipe-delimited cell markers:  "A | B | C" → "A B C"
        text = re.sub(r'\s*\|\s*', ' ', text)
        text = text.strip()

        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            # Try to break at sentence boundary or at whitespace to avoid splitting words
            if end < len(text):
                # Look for sentence endings near chunk boundary
                for sep in ['. ', '! ', '? ', '\n', '। ']:
                    last_sep = text.rfind(sep, start, end)
                    if last_sep > start + chunk_size // 2:
                        end = last_sep + 1
                        break
                # If no sentence break found, try to break at whitespace
                if end == start + chunk_size:  # No sentence break found
                    # Look for whitespace to break at
                    last_space = text.rfind(' ', start, end)
                    if last_space > start + chunk_size // 2:
                        end = last_space

            chunks.append(text[start:end])
            start = end - overlap

            # Ensure we make progress
            if start >= len(text) - overlap:
                break

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

                # If TF-IDF search returned no results, fall back to keyword search
                if not results:
                    logger.info(f"TF-IDF search returned no results for '{query[:30]}...', falling back to keyword search")
                    return self._simple_search(query, top_k, min_similarity)

                return results
            except Exception as e:
                logger.error(f"TF-IDF Search error: {e}")
                # Fall back to keyword search on exception
                return self._simple_search(query, top_k, min_similarity)

        # Fallback: Simple keyword matching
        return self._simple_search(query, top_k, min_similarity)

    def _simple_search(self, query: str, top_k: int = 3, min_similarity: float = 0.1) -> List[Dict]:
        """Simple keyword-based search fallback when scikit-learn is not available."""
        if not self.documents:
            return []

        # Normalize query — Vietnamese chars are kept as-is (re.UNICODE is default in Py3)
        query_lower = query.lower()
        # Tokenize: run of word chars including Vietnamese accented letters
        query_words = set(re.findall(r'[\w\u00C0-\u024F\u1E00-\u1EFF]+', query_lower))

        if not query_words:
            return []

        results = []

        for idx, doc in enumerate(self.documents):
            doc_lower = doc.lower()
            doc_words = set(re.findall(r'[\w\u00C0-\u024F\u1E00-\u1EFF]+', doc_lower))

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

    def get_answer_context(self, query: str, max_chars: int = 5000) -> Tuple[str, bool]:
        """
        Get context from knowledge base for a query.
        Returns (context, found_flag) - found_flag is True if relevant content found.
        """
        if not self.documents:
            return "", False

        # Use lower similarity threshold to find more relevant documents
        results = self.search(query, top_k=15, min_similarity=0.005)

        if not results:
            return "", False

        logger.info(f"Search results for '{query[:30]}...': {len(results)} documents found")
        for r in results:
            logger.info(f"  - {r['source']['filename']}: similarity={r['similarity']:.3f}")

        # Boost score for exact matches of key terms
        query_lower = query.lower()
        for result in results:
            # Check if query terms appear exactly in content
            content_lower = result['content'].lower()
            if query_lower in content_lower:
                # Boost similarity score for exact query match (highest priority)
                result['similarity'] = min(1.0, result['similarity'] + 0.5)
            # Check for individual important words (like names)
            query_words = set(re.findall(r'\b[a-zA-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠàáâãèéêìíòóôõùúăđĩũơƯĂÂÊÔƠƯ]+\b', query_lower))
            content_words = set(re.findall(r'\b[a-zA-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠàáâãèéêìíòóôõùúăđĩũơƯĂÂÊÔƠƯ]+\b', content_lower))
            exact_word_matches = query_words & content_words
            if exact_word_matches:
                # Penalize if query has more unique words than content chunk AND not all query words matched
                # This prevents shorter exact name variants from scoring higher than longer variants
                query_unique_count = len(query_words)
                content_match_count = len(exact_word_matches)
                if query_unique_count > content_match_count:
                    # Not all query words found in content - this is likely a partial match
                    # Reduce the score if it has fewer matches than query words
                    coverage_ratio = content_match_count / query_unique_count
                    # If coverage is low (< 0.7), reduce the score
                    if coverage_ratio < 0.7:
                        word_boost = min(0.1, len(exact_word_matches) * 0.02)
                        result['similarity'] = min(1.0, result['similarity'] + word_boost) - (1 - coverage_ratio) * 0.2
                    else:
                        word_boost = min(0.2, len(exact_word_matches) * 0.05)
                        result['similarity'] = min(1.0, result['similarity'] + word_boost)
                else:
                    # All query words are in content - good match
                    word_boost = min(0.2, len(exact_word_matches) * 0.05)
                    result['similarity'] = min(1.0, result['similarity'] + word_boost)

        # Re-sort by boosted similarity
        results.sort(key=lambda x: x['similarity'], reverse=True)

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
        if results and results[0]['similarity'] >= 0.005:
            return context, True

        return context, False

    def has_knowledge(self) -> bool:
        """Check if knowledge base is loaded."""
        return len(self.documents) > 0


# Singleton instance
retriever = KnowledgeRetriever()
