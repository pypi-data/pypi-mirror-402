"""
KnowledgeContext - Lazy access to knowledge base documents.

This is the RLM "RepoContext" adapted for domain knowledge access.
It provides safe, lazy, binary-skipping access to documents that
the LLM can use to explore the knowledge base via Python code.
"""

import logging
import os
import pathlib
import re
from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Optional, Set, Tuple

from watsonx_rlm_knowledge.exceptions import ContextError
from watsonx_rlm_knowledge.preprocessor import DocumentPreprocessor, PreprocessorConfig

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeContextConfig:
    """Configuration for knowledge context access."""
    max_file_bytes: int = 2_000_000          # Hard cap per file read (2MB)
    max_preview_bytes: int = 32_000          # For quick previews (32KB)
    max_grep_matches: int = 100              # Max matches for grep
    follow_symlinks: bool = False
    preprocessor_config: Optional[PreprocessorConfig] = None


@dataclass
class SearchMatch:
    """A single search match result."""
    path: str
    line_number: int
    line_text: str
    context_before: List[str] = field(default_factory=list)
    context_after: List[str] = field(default_factory=list)
    
    def __str__(self) -> str:
        return f"{self.path}:{self.line_number}: {self.line_text}"


@dataclass  
class DocumentSummary:
    """Summary information about a document."""
    path: str
    relative_path: str
    format: str
    size_bytes: int
    text_size_bytes: int
    first_lines: str
    is_binary_converted: bool


class KnowledgeContext:
    """Provides lazy, safe access to knowledge base documents.
    
    This class is exposed to the LLM via the RLM loop. The LLM can call
    methods on this object to explore the knowledge base without having
    the entire content in context.
    
    Key features:
    - Lazy file reading (only reads what's requested)
    - Binary document support (PDF, DOCX, etc. via preprocessor)
    - Full-text search across all documents
    - Slice reading for targeted content access
    - Document listing and summaries
    
    Example (as used by LLM in RLM loop):
        # List all documents
        for doc in knowledge.list_documents():
            print(doc.path, doc.format)
        
        # Search for a term
        matches = knowledge.search("authentication")
        for m in matches:
            print(f"{m.path}:{m.line_number}: {m.line_text}")
        
        # Read a specific section
        content = knowledge.read_slice("docs/auth.md", offset=0, nbytes=5000)
        
        # Get document preview
        preview = knowledge.head("manual.pdf", nbytes=10000)
    """
    
    def __init__(
        self,
        root: str,
        config: Optional[KnowledgeContextConfig] = None,
        preprocessor: Optional[DocumentPreprocessor] = None
    ):
        """Initialize knowledge context.
        
        Args:
            root: Root directory of knowledge base
            config: Optional configuration
            preprocessor: Optional preprocessor (created if not provided)
        """
        self.root = pathlib.Path(root).resolve()
        self.config = config or KnowledgeContextConfig()
        
        if not self.root.exists():
            raise ContextError(f"Knowledge root does not exist: {self.root}")
        
        # Initialize preprocessor
        if preprocessor:
            self.preprocessor = preprocessor
        else:
            self.preprocessor = DocumentPreprocessor(
                str(self.root),
                config=self.config.preprocessor_config
            )
        
        # Cache of document metadata
        self._doc_cache: Dict[str, DocumentSummary] = {}
        
        logger.info(f"Initialized KnowledgeContext at {self.root}")
    
    def preprocess(self, force: bool = False) -> int:
        """Run preprocessing on all documents.
        
        Args:
            force: If True, reprocess all documents
        
        Returns:
            Number of documents processed
        """
        manifest = self.preprocessor.preprocess_all(force=force)
        logger.info(f"Preprocessed {len(manifest)} documents")
        return len(manifest)
    
    def list_documents(self, pattern: Optional[str] = None) -> List[DocumentSummary]:
        """List all documents in the knowledge base.
        
        Args:
            pattern: Optional glob pattern to filter (e.g., "*.pdf", "docs/*")
        
        Returns:
            List of document summaries
        """
        documents = []
        
        for path in self.preprocessor.iter_documents():
            rel_path = str(path.relative_to(self.root))
            
            # Apply pattern filter
            if pattern:
                if not pathlib.Path(rel_path).match(pattern):
                    continue
            
            # Get or create summary
            if str(path) in self._doc_cache:
                documents.append(self._doc_cache[str(path)])
            else:
                doc = self._get_document_summary(path)
                self._doc_cache[str(path)] = doc
                documents.append(doc)
        
        return sorted(documents, key=lambda d: d.relative_path)
    
    def list_files(self) -> List[str]:
        """List all document paths (relative to root).
        
        Returns:
            List of relative paths
        """
        return [doc.relative_path for doc in self.list_documents()]
    
    def _get_document_summary(self, path: pathlib.Path) -> DocumentSummary:
        """Create document summary."""
        rel_path = str(path.relative_to(self.root))
        doc_info = self.preprocessor.get_document_info(str(path))
        
        if doc_info:
            # Get first few lines as preview
            try:
                text = self.preprocessor.get_text(str(path))
                lines = text.split("\n")[:5]
                first_lines = "\n".join(lines)
                if len(text) > len(first_lines):
                    first_lines += "\n..."
            except Exception:
                first_lines = "(preview unavailable)"
            
            return DocumentSummary(
                path=str(path),
                relative_path=rel_path,
                format=doc_info.format,
                size_bytes=doc_info.size_bytes,
                text_size_bytes=doc_info.text_size_bytes,
                first_lines=first_lines,
                is_binary_converted=doc_info.original_path != doc_info.text_path,
            )
        else:
            # Document not preprocessed yet
            return DocumentSummary(
                path=str(path),
                relative_path=rel_path,
                format=path.suffix.lower(),
                size_bytes=path.stat().st_size,
                text_size_bytes=0,
                first_lines="(not preprocessed)",
                is_binary_converted=False,
            )
    
    def read_slice(
        self,
        path: str,
        offset: int = 0,
        nbytes: int = 50_000
    ) -> str:
        """Read a slice of a document's text content.
        
        Args:
            path: Path to document (relative or absolute)
            offset: Byte offset to start reading
            nbytes: Number of bytes to read
        
        Returns:
            Text content from the specified slice
        """
        full_path = self._resolve_path(path)
        
        # Cap bytes to prevent excessive reads
        nbytes = min(nbytes, self.config.max_file_bytes)
        
        try:
            # Get text content (preprocessor handles binary conversion)
            text = self.preprocessor.get_text(str(full_path))
            
            # Return slice
            return text[offset:offset + nbytes]
        except Exception as e:
            raise ContextError(f"Failed to read {path}: {e}")
    
    def head(self, path: str, nbytes: Optional[int] = None) -> str:
        """Read the beginning of a document.
        
        Args:
            path: Path to document
            nbytes: Number of bytes to read (default: config.max_preview_bytes)
        
        Returns:
            Beginning of document content
        """
        nbytes = nbytes or self.config.max_preview_bytes
        return self.read_slice(path, 0, nbytes)
    
    def tail(self, path: str, nbytes: Optional[int] = None) -> str:
        """Read the end of a document.
        
        Args:
            path: Path to document
            nbytes: Number of bytes to read
        
        Returns:
            End of document content
        """
        full_path = self._resolve_path(path)
        nbytes = nbytes or self.config.max_preview_bytes
        
        try:
            text = self.preprocessor.get_text(str(full_path))
            if len(text) <= nbytes:
                return text
            return text[-nbytes:]
        except Exception as e:
            raise ContextError(f"Failed to read tail of {path}: {e}")
    
    def read_full(self, path: str) -> str:
        """Read entire document content.
        
        Args:
            path: Path to document
        
        Returns:
            Full document content
        
        Note:
            Subject to max_file_bytes limit in config.
        """
        return self.read_slice(path, 0, self.config.max_file_bytes)
    
    def search(
        self,
        needle: str,
        max_matches: Optional[int] = None,
        case_sensitive: bool = False,
        context_lines: int = 0,
        path_pattern: Optional[str] = None
    ) -> List[SearchMatch]:
        """Search for a string across all documents.
        
        This is the primary discovery mechanism for the LLM to find
        relevant content in the knowledge base.
        
        Args:
            needle: String to search for
            max_matches: Maximum matches to return
            case_sensitive: If True, match case exactly
            context_lines: Number of context lines before/after match
            path_pattern: Optional glob pattern to filter files
        
        Returns:
            List of search matches with file paths and line numbers
        """
        max_matches = max_matches or self.config.max_grep_matches
        matches = []
        
        # Prepare search needle
        if not case_sensitive:
            search_needle = needle.lower()
        else:
            search_needle = needle
        
        for doc in self.list_documents(pattern=path_pattern):
            if len(matches) >= max_matches:
                break
            
            try:
                text = self.preprocessor.get_text(doc.path)
                lines = text.split("\n")
                
                for i, line in enumerate(lines):
                    if len(matches) >= max_matches:
                        break
                    
                    check_line = line if case_sensitive else line.lower()
                    
                    if search_needle in check_line:
                        # Get context lines
                        ctx_before = []
                        ctx_after = []
                        
                        if context_lines > 0:
                            start = max(0, i - context_lines)
                            ctx_before = lines[start:i]
                            
                            end = min(len(lines), i + context_lines + 1)
                            ctx_after = lines[i + 1:end]
                        
                        matches.append(SearchMatch(
                            path=doc.relative_path,
                            line_number=i + 1,
                            line_text=line.rstrip(),
                            context_before=ctx_before,
                            context_after=ctx_after,
                        ))
            except Exception as e:
                logger.warning(f"Error searching {doc.path}: {e}")
                continue
        
        return matches
    
    def grep(
        self,
        needle: str,
        max_matches: int = 50
    ) -> List[Tuple[str, int, str]]:
        """Simple grep interface (for RLM compatibility).
        
        Returns list of (path, line_number, line_text) tuples.
        """
        matches = self.search(needle, max_matches=max_matches)
        return [(m.path, m.line_number, m.line_text) for m in matches]
    
    def search_regex(
        self,
        pattern: str,
        max_matches: Optional[int] = None,
        path_pattern: Optional[str] = None
    ) -> List[SearchMatch]:
        """Search using regular expression.
        
        Args:
            pattern: Regular expression pattern
            max_matches: Maximum matches to return
            path_pattern: Optional glob pattern to filter files
        
        Returns:
            List of search matches
        """
        max_matches = max_matches or self.config.max_grep_matches
        matches = []
        
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            raise ContextError(f"Invalid regex pattern: {e}")
        
        for doc in self.list_documents(pattern=path_pattern):
            if len(matches) >= max_matches:
                break
            
            try:
                text = self.preprocessor.get_text(doc.path)
                lines = text.split("\n")
                
                for i, line in enumerate(lines):
                    if len(matches) >= max_matches:
                        break
                    
                    if regex.search(line):
                        matches.append(SearchMatch(
                            path=doc.relative_path,
                            line_number=i + 1,
                            line_text=line.rstrip(),
                        ))
            except Exception as e:
                logger.warning(f"Error searching {doc.path}: {e}")
                continue
        
        return matches
    
    def find_files(self, pattern: str) -> List[str]:
        """Find files matching a glob pattern.
        
        Args:
            pattern: Glob pattern (e.g., "*.pdf", "docs/**/*.md")
        
        Returns:
            List of matching file paths (relative to root)
        """
        return [doc.relative_path for doc in self.list_documents(pattern=pattern)]
    
    def get_document_info(self, path: str) -> Optional[DocumentSummary]:
        """Get information about a specific document.
        
        Args:
            path: Path to document
        
        Returns:
            Document summary or None if not found
        """
        full_path = self._resolve_path(path)
        
        if str(full_path) in self._doc_cache:
            return self._doc_cache[str(full_path)]
        
        if full_path.exists():
            doc = self._get_document_summary(full_path)
            self._doc_cache[str(full_path)] = doc
            return doc
        
        return None
    
    def get_table_of_contents(self, path: str) -> List[str]:
        """Extract headings/structure from a document.
        
        Args:
            path: Path to document
        
        Returns:
            List of headings/sections found
        """
        full_path = self._resolve_path(path)
        
        try:
            text = self.preprocessor.get_text(str(full_path))
        except Exception as e:
            raise ContextError(f"Failed to read {path}: {e}")
        
        headings = []
        
        # Markdown headings
        md_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
        for match in md_pattern.finditer(text):
            level = len(match.group(1))
            title = match.group(2).strip()
            indent = "  " * (level - 1)
            headings.append(f"{indent}{title}")
        
        # Slide/Page markers
        slide_pattern = re.compile(r"^---\s*(Slide|Page)\s*(\d+)\s*---", re.MULTILINE)
        for match in slide_pattern.finditer(text):
            headings.append(f"[{match.group(1)} {match.group(2)}]")
        
        # Sheet markers (for Excel)
        sheet_pattern = re.compile(r"^===\s*Sheet:\s*(.+)\s*===", re.MULTILINE)
        for match in sheet_pattern.finditer(text):
            headings.append(f"[Sheet: {match.group(1)}]")
        
        return headings
    
    def count_occurrences(self, needle: str, path: Optional[str] = None) -> int:
        """Count occurrences of a string.
        
        Args:
            needle: String to count
            path: Optional specific document (counts in all if None)
        
        Returns:
            Total count of occurrences
        """
        count = 0
        needle_lower = needle.lower()
        
        if path:
            full_path = self._resolve_path(path)
            text = self.preprocessor.get_text(str(full_path)).lower()
            return text.count(needle_lower)
        
        for doc in self.list_documents():
            try:
                text = self.preprocessor.get_text(doc.path).lower()
                count += text.count(needle_lower)
            except Exception:
                continue
        
        return count
    
    def _resolve_path(self, path: str) -> pathlib.Path:
        """Resolve a path to absolute form."""
        p = pathlib.Path(path)
        
        if p.is_absolute():
            return p.resolve()
        
        # Try as relative to root
        full = self.root / p
        if full.exists():
            return full.resolve()
        
        # Try as-is
        if p.exists():
            return p.resolve()
        
        raise ContextError(f"Document not found: {path}")
    
    def __repr__(self) -> str:
        return f"KnowledgeContext(root='{self.root}')"
    
    # Aliases for RLM compatibility
    iter_files = list_files
