"""
Advanced AI-powered PDF text extraction and processing.
"""

import json
import time
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

try:
    # Suppress PyMuPDF/SWIG deprecation warnings during import
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore", category=DeprecationWarning, module="importlib._bootstrap"
        )
        warnings.filterwarnings(
            "ignore", message="builtin type.*has no __module__ attribute"
        )
        import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    import bibtexparser

    HAS_BIBTEXPARSER = True
except ImportError:
    HAS_BIBTEXPARSER = False

from .models import DocumentMetadata, ExtractionResult, PageContent


class OllamaAIProcessor:
    """Advanced AI processor using Ollama with sophisticated prompting."""

    def __init__(
        self, model: str = "qwen3:8b", base_url: str = "http://localhost:11434"
    ):
        self.model = model
        self.base_url = base_url
        self.available = self._check_availability()
        self.conversation_history: List[Dict[str, str]] = []

    def _check_availability(self) -> bool:
        """Check if Ollama is available and model exists."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                available_models = [m["name"] for m in models]

                # Check for exact match or partial match
                model_available = any(
                    self.model in name or name.startswith(self.model)
                    for name in available_models
                )

                return model_available
        except Exception:
            pass
        return False

    def _call_ollama(
        self, prompt: str, system_prompt: str = "", temperature: float = 0.1
    ) -> str:
        """Call Ollama API with error handling."""
        if not self.available:
            raise RuntimeError("Ollama not available")

        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "top_p": 0.9,
                    "num_ctx": 8192,
                },
            }

            response = requests.post(
                f"{self.base_url}/api/generate", json=payload, timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")
                return str(response_text).strip() if response_text else ""

            detail = response.text.strip() if getattr(response, "text", None) else ""
            raise RuntimeError(
                "Ollama request failed "
                f"(status={response.status_code}, model={self.model}): {detail}"
            )

        except requests.exceptions.RequestException as e:
            raise RuntimeError(
                f"Ollama request failed (model={self.model}): {e}"
            ) from e

    def extract_keywords_and_concepts(self, text: str) -> Dict[str, List[str]]:
        """First pass: Extract keywords and key concepts."""
        system_prompt = (
            "You are an expert academic researcher specializing in analyzing "
            "scientific papers. Your task is to extract keywords and key "
            "concepts from academic text with high precision."
        )

        prompt = f"""Analyze this academic text and extract:

1. TECHNICAL KEYWORDS: Specific technical terms, methods, materials, equipment
2. RESEARCH CONCEPTS: Broader research concepts and themes
3. CHEMICAL COMPOUNDS: All chemical formulas and compound names
4. METHODOLOGIES: Research methods and analytical techniques
5. EQUIPMENT: Instruments and analytical equipment mentioned

Text to analyze:
{text[:4000]}

Return ONLY a JSON object with this exact structure:
{{
    "technical_keywords": ["keyword1", "keyword2"],
    "research_concepts": ["concept1", "concept2"],
    "chemical_compounds": ["compound1", "compound2"],
    "methodologies": ["method1", "method2"],
    "equipment": ["instrument1", "instrument2"]
}}

Be precise and avoid duplicates. Focus on the most important and specific terms."""

        response = self._call_ollama(prompt, system_prompt, temperature=0.1)

        try:
            result = json.loads(response)
            if isinstance(result, dict):
                return result
            return {"keywords": [], "concepts": []}
        except json.JSONDecodeError:
            return {
                "technical_keywords": [],
                "research_concepts": [],
                "chemical_compounds": [],
                "methodologies": [],
                "equipment": [],
            }

    def classify_content_type(self, text: str, page_num: int, total_pages: int) -> str:
        """Classify the type of content on a page."""
        system_prompt = (
            "You are an expert at analyzing academic paper structure. "
            "Classify the content type of each page section."
        )

        prompt = f"""Classify this text from page {page_num} of {total_pages} pages.

Text:
{text[:2000]}

Classify as ONE of these types:
- abstract: Abstract or summary section
- introduction: Introduction or background
- methods: Methodology, experimental procedures, materials
- results: Results, data, findings, analysis
- discussion: Discussion, interpretation, comparison
- conclusion: Conclusions, summary, future work
- references: Reference list, bibliography
- appendix: Supplementary material, appendices
- main: General main content that doesn't fit other categories

Return only the classification word, nothing else."""

        response = self._call_ollama(prompt, system_prompt, temperature=0.1)
        return response.lower().strip() if response else "main"

    def extract_structured_content(
        self, text: str, content_type: str, keywords: List[str]
    ) -> Dict[str, Any]:
        """Extract structured content based on content type."""
        system_prompt = (
            f"You are an expert academic researcher. Extract structured "
            f"information from {content_type} sections of scientific papers."
        )

        keyword_context = (
            f"Key terms to focus on: {', '.join(keywords[:10])}" if keywords else ""
        )

        if content_type == "abstract":
            prompt = f"""Extract structured information from this abstract:

{text}

{keyword_context}

Return JSON with:
{{
    "objective": "main research objective",
    "methods": "key methods used",
    "findings": "main findings",
    "significance": "research significance"
}}"""

        elif content_type == "methods":
            prompt = f"""Extract methodology information:

{text}

{keyword_context}

Return JSON with:
{{
    "materials": ["material1", "material2"],
    "equipment": ["instrument1", "instrument2"],
    "procedures": ["step1", "step2"],
    "conditions": "experimental conditions"
}}"""

        elif content_type == "results":
            prompt = f"""Extract results information:

{text}

{keyword_context}

Return JSON with:
{{
    "key_findings": ["finding1", "finding2"],
    "data_types": ["data_type1", "data_type2"],
    "measurements": ["measurement1", "measurement2"],
    "performance": "performance metrics if any"
}}"""

        else:
            prompt = f"""Extract key information from this {content_type} section:

{text}

{keyword_context}

Return JSON with:
{{
    "main_points": ["point1", "point2"],
    "key_terms": ["term1", "term2"],
    "important_info": "most important information"
}}"""

        response = self._call_ollama(prompt, system_prompt, temperature=0.1)

        try:
            result = json.loads(response)
            if isinstance(result, dict):
                return result
            return {"extraction_error": "Invalid response format"}
        except json.JSONDecodeError:
            return {"extraction_error": "Could not parse structured content"}

    def fix_text_spacing(self, text: str) -> str:
        """Fix spacing and formatting issues in extracted text."""
        system_prompt = (
            "You are a text processing expert. Fix spacing, formatting, and "
            "readability issues in academic text extracted from PDFs."
        )

        prompt = f"""Fix spacing and formatting issues in this academic text:

RULES:
1. Add spaces between words incorrectly joined together
2. Fix broken words across lines (remove hyphens, join parts)
3. Preserve chemical formulas (NOx, NH3, etc.) exactly
4. Preserve citations and references exactly
5. Fix punctuation spacing
6. Maintain paragraph structure
7. Do NOT change technical terms or add new content

Text to fix:
{text}

Return only the corrected text with no explanations."""

        response = self._call_ollama(prompt, system_prompt, temperature=0.1)
        return response if response else text

    def generate_summary(self, extraction_result: ExtractionResult) -> str:
        """Generate a comprehensive summary of the document."""
        system_prompt = (
            "You are an expert academic researcher. Create comprehensive "
            "summaries of scientific papers."
        )

        # Prepare context
        metadata = extraction_result.metadata
        all_text = " ".join(
            [page.processed_text for page in extraction_result.pages[:5]]
        )  # First 5 pages

        prompt = f"""Create a comprehensive summary of this research paper:

PAPER METADATA:
- Title: {metadata.title}
- Authors: {', '.join(metadata.authors)}
- Year: {metadata.year}
- Keywords: {', '.join(metadata.keywords)}

CONTENT SAMPLE:
{all_text[:3000]}

Create a structured summary with:

## Research Overview
[Brief overview of the research topic and objectives]

## Methodology
[Key methods and approaches used]

## Main Findings
[Primary results and discoveries]

## Significance
[Research significance and implications]

## Key Technical Details
[Important technical information, equipment, conditions]

## Relevance to NOx/Ammonia Research
[How this relates to NOx to ammonia conversion research, if applicable]

Keep the summary concise but comprehensive (300-500 words)."""

        response = self._call_ollama(prompt, system_prompt, temperature=0.2)
        return response if response else "Summary generation failed"


class AdvancedPDFProcessor:
    """Advanced PDF processor with AI enhancement and tracking."""

    def __init__(self, model: str = "qwen3:8b", bib_file: Optional[Path] = None):
        self.ai = OllamaAIProcessor(model)
        self.bib_data = self._load_bibliography(bib_file) if bib_file else {}

    def _load_bibliography(self, bib_file: Path) -> Dict[str, Dict[str, Any]]:
        """Load bibliography data from BibTeX file."""
        if not HAS_BIBTEXPARSER:
            print(
                "Warning: bibtexparser not available. "
                "Install with: pip install bibtexparser"
            )
            return {}

        if not bib_file.exists():
            print(f"Warning: Bibliography file not found: {bib_file}")
            return {}

        try:
            with open(bib_file, "r", encoding="utf-8") as f:
                bib_database = bibtexparser.load(f)

            return {entry["ID"]: entry for entry in bib_database.entries}
        except Exception as e:
            print(f"Warning: Could not load bibliography: {e}")
            return {}

    def _get_metadata_from_bib(self, cite_key: str) -> DocumentMetadata:
        """Extract metadata from bibliography entry."""
        metadata = DocumentMetadata(cite_key=cite_key)

        if cite_key in self.bib_data:
            entry = self.bib_data[cite_key]
            metadata.title = entry.get("title", "").replace("{", "").replace("}", "")
            metadata.year = entry.get("year", "")
            metadata.journal = entry.get("journal", "")
            metadata.doi = entry.get("doi", "")
            metadata.url = entry.get("url", "")

            # Parse authors
            authors_str = entry.get("author", "")
            if authors_str:
                # Simple author parsing (could be improved)
                authors = [author.strip() for author in authors_str.split(" and ")]
                metadata.authors = authors

        return metadata

    def extract_pdf_content(self, pdf_path: Path) -> List[PageContent]:
        """Extract content from PDF with layout analysis."""
        if not HAS_PYMUPDF:
            raise RuntimeError(
                "PyMuPDF not available. Install with: pip install PyMuPDF"
            )

        try:
            doc = fitz.open(pdf_path)
            pages = []

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)

                # Extract text with better formatting
                text = page.get_text("text")

                # Create page content
                page_content = PageContent(page_num=page_num + 1, raw_text=text)

                pages.append(page_content)

            doc.close()
            return pages

        except Exception as e:
            raise RuntimeError(f"PDF extraction failed: {e}")

    def process_with_ai(
        self, pages: List[PageContent], metadata: DocumentMetadata
    ) -> ExtractionResult:
        """Process pages with AI enhancement."""
        if not self.ai.available:
            raise RuntimeError(
                "AI processing not available. Please install and configure Ollama."
            )

        # Step 1: Extract keywords from first few pages
        combined_text = " ".join([page.raw_text for page in pages[:3]])
        keyword_data = self.ai.extract_keywords_and_concepts(combined_text)

        # Combine all keywords
        all_keywords = []
        for keyword_list in keyword_data.values():
            all_keywords.extend(keyword_list)

        metadata.keywords = all_keywords[:20]  # Keep top 20 keywords

        # Step 2: Process each page
        sections: Dict[str, Any] = {}

        for page in pages:
            # Fix text spacing
            page.processed_text = self.ai.fix_text_spacing(page.raw_text)

            # Classify content type
            page.content_type = self.ai.classify_content_type(
                page.processed_text, page.page_num, len(pages)
            )

            # Extract structured content
            structured = self.ai.extract_structured_content(
                page.processed_text, page.content_type, all_keywords
            )

            # Store in sections
            if page.content_type not in sections:
                sections[page.content_type] = []
            sections[page.content_type].append(
                {
                    "page": page.page_num,
                    "content": page.processed_text,
                    "structured": structured,
                }
            )

        # Step 3: Create extraction result
        result = ExtractionResult(
            metadata=metadata,
            pages=pages,
            sections=sections,
            all_keywords=all_keywords,
            key_concepts=keyword_data.get("research_concepts", []),
        )

        return result

    def process_pdf(
        self, pdf_path: Path, bib_file: Optional[Path] = None
    ) -> ExtractionResult:
        """Main processing function."""
        start_time = time.time()

        # Load bibliography if provided
        if bib_file and not self.bib_data:
            self.bib_data = self._load_bibliography(bib_file)

        # Get cite key from filename
        cite_key = pdf_path.stem

        # Get metadata from bibliography
        metadata = self._get_metadata_from_bib(cite_key)

        # Extract PDF content
        pages = self.extract_pdf_content(pdf_path)
        metadata.page_count = len(pages)

        # Process with AI
        result = self.process_with_ai(pages, metadata)

        # Calculate processing time
        processing_time = time.time() - start_time
        result.metadata.processing_time = processing_time

        return result
