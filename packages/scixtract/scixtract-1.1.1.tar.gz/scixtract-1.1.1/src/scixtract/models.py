"""
Data models for AI PDF extraction and knowledge tracking.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class DocumentMetadata:
    """Comprehensive document metadata structure."""

    cite_key: str
    title: str = ""
    authors: List[str] = field(default_factory=list)
    year: str = ""
    journal: str = ""
    doi: str = ""
    url: str = ""
    keywords: List[str] = field(default_factory=list)
    abstract: str = ""
    page_count: int = 0
    extraction_date: str = ""
    processing_time: float = 0.0

    def __post_init__(self) -> None:
        if not self.extraction_date:
            self.extraction_date = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class PageContent:
    """Structure for individual page content."""

    page_num: int
    raw_text: str
    processed_text: str = ""
    content_type: str = "main"  # main, abstract, references, appendix
    keywords: List[str] = field(default_factory=list)
    figures: List[str] = field(default_factory=list)
    tables: List[str] = field(default_factory=list)
    equations: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        pass  # All defaults are now handled by field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class ExtractionResult:
    """Complete extraction result structure."""

    metadata: DocumentMetadata
    pages: List[PageContent]
    sections: Dict[str, Any]
    all_keywords: List[str]
    key_concepts: List[str]
    methodology: str = ""
    main_findings: str = ""
    conclusions: str = ""
    future_work: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "metadata": self.metadata.to_dict(),
            "pages": [page.to_dict() for page in self.pages],
            "sections": self.sections,
            "all_keywords": self.all_keywords,
            "key_concepts": self.key_concepts,
            "methodology": self.methodology,
            "main_findings": self.main_findings,
            "conclusions": self.conclusions,
            "future_work": self.future_work,
        }


@dataclass
class DocumentIndex:
    """Index entry for a processed document."""

    cite_key: str
    title: str
    authors: List[str]
    year: str
    keywords: List[str]
    key_concepts: List[str]
    page_count: int
    extraction_date: str
    file_path: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PageIndex:
    """Index entry for a page within a document."""

    cite_key: str
    page_num: int
    content_type: str
    keywords: List[str]
    word_count: int
    has_figures: bool
    has_tables: bool
    has_equations: bool


@dataclass
class ConceptNetwork:
    """Network of related concepts across documents."""

    concept: str
    related_concepts: List[str]
    documents: List[str]  # cite_keys
    frequency: int
    co_occurrence_score: float
