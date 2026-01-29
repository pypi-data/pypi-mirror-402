"""
Knowledge tracking and indexing system for PDF extractions.
"""

import argparse
import json
import re
import sqlite3
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class KnowledgeTracker:
    """Advanced knowledge tracking and indexing system."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path("knowledge_index.db")
        self.init_database()

    def init_database(self) -> None:
        """Initialize SQLite database for knowledge tracking."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Documents table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                cite_key TEXT PRIMARY KEY,
                title TEXT,
                authors TEXT,  -- JSON array
                year TEXT,
                keywords TEXT,  -- JSON array
                key_concepts TEXT,  -- JSON array
                page_count INTEGER,
                extraction_date TEXT,
                file_path TEXT,
                processing_time REAL
            )
        """
        )

        # Pages table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cite_key TEXT,
                page_num INTEGER,
                content_type TEXT,
                keywords TEXT,  -- JSON array
                word_count INTEGER,
                has_figures BOOLEAN,
                has_tables BOOLEAN,
                has_equations BOOLEAN,
                FOREIGN KEY (cite_key) REFERENCES documents (cite_key)
            )
        """
        )

        # Keywords table for fast searching
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT,
                cite_key TEXT,
                page_num INTEGER,
                frequency INTEGER,
                context TEXT,
                FOREIGN KEY (cite_key) REFERENCES documents (cite_key)
            )
        """
        )

        # Concepts network table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS concept_network (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concept TEXT,
                related_concept TEXT,
                cite_key TEXT,
                co_occurrence_count INTEGER,
                FOREIGN KEY (cite_key) REFERENCES documents (cite_key)
            )
        """
        )

        # Create indexes for fast searching
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON keywords(keyword)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_keywords_cite_key ON keywords(cite_key)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_concepts_concept "
            "ON concept_network(concept)"
        )

        conn.commit()
        conn.close()

    def add_extraction_result(
        self, result_data: Dict[str, Any], file_path: str
    ) -> None:
        """Add extraction result to knowledge database."""
        metadata = result_data.get("metadata", {})
        pages = result_data.get("pages", [])

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Insert/update document
        cursor.execute(
            """
            INSERT OR REPLACE INTO documents
            (cite_key, title, authors, year, keywords, key_concepts, page_count,
             extraction_date, file_path, processing_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                metadata.get("cite_key", ""),
                metadata.get("title", ""),
                json.dumps(metadata.get("authors", [])),
                metadata.get("year", ""),
                json.dumps(metadata.get("keywords", [])),
                json.dumps(result_data.get("key_concepts", [])),
                metadata.get("page_count", 0),
                metadata.get("extraction_date", ""),
                file_path,
                metadata.get("processing_time", 0.0),
            ),
        )

        cite_key = metadata.get("cite_key", "")

        # Clear existing pages and keywords for this document
        cursor.execute("DELETE FROM pages WHERE cite_key = ?", (cite_key,))
        cursor.execute("DELETE FROM keywords WHERE cite_key = ?", (cite_key,))

        # Insert pages
        for page_data in pages:
            cursor.execute(
                """
                INSERT INTO pages
                (cite_key, page_num, content_type, keywords, word_count,
                 has_figures, has_tables, has_equations)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    cite_key,
                    page_data.get("page_num", 0),
                    page_data.get("content_type", "main"),
                    json.dumps(page_data.get("keywords", [])),
                    len(page_data.get("processed_text", "").split()),
                    len(page_data.get("figures", [])) > 0,
                    len(page_data.get("tables", [])) > 0,
                    len(page_data.get("equations", [])) > 0,
                ),
            )

            # Insert keywords for this page
            page_keywords = page_data.get("keywords", [])
            page_text = page_data.get("processed_text", "")

            for keyword in page_keywords:
                # Count frequency of keyword in page
                frequency = len(
                    re.findall(re.escape(keyword.lower()), page_text.lower())
                )

                # Extract context (sentence containing keyword)
                context = self._extract_keyword_context(keyword, page_text)

                cursor.execute(
                    """
                    INSERT INTO keywords
                    (keyword, cite_key, page_num, frequency, context)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        keyword.lower(),
                        cite_key,
                        page_data.get("page_num", 0),
                        frequency,
                        context,
                    ),
                )

        conn.commit()
        conn.close()

        # Build concept network for this document
        self._build_concept_network_for_document(cite_key)

    def _extract_keyword_context(
        self, keyword: str, text: str, context_length: int = 200
    ) -> str:
        """Extract context around a keyword."""
        text_lower = text.lower()
        keyword_lower = keyword.lower()

        pos = text_lower.find(keyword_lower)
        if pos == -1:
            return ""

        start = max(0, pos - context_length // 2)
        end = min(len(text), pos + len(keyword) + context_length // 2)

        context = text[start:end].strip()

        # Clean up context
        if start > 0:
            context = "..." + context
        if end < len(text):
            context = context + "..."

        return context

    def _build_concept_network_for_document(self, cite_key: str) -> None:
        """Build concept co-occurrence network for a specific document."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Clear existing network for this document
        cursor.execute("DELETE FROM concept_network WHERE cite_key = ?", (cite_key,))

        # Get all keywords for this document
        cursor.execute(
            """
            SELECT keyword, COUNT(*) as frequency
            FROM keywords
            WHERE cite_key = ?
            GROUP BY keyword
            ORDER BY frequency DESC
            LIMIT 20
        """,
            (cite_key,),
        )

        keywords = [row[0] for row in cursor.fetchall()]

        # Build co-occurrence matrix
        for i, kw1 in enumerate(keywords):
            for kw2 in keywords[i + 1 :]:
                cursor.execute(
                    """
                    INSERT INTO concept_network
                    (concept, related_concept, cite_key, co_occurrence_count)
                    VALUES (?, ?, ?, ?)
                """,
                    (kw1, kw2, cite_key, 1),
                )

        conn.commit()
        conn.close()

    def search_keywords(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for keywords and return matching documents."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Search keywords
        cursor.execute(
            """
            SELECT DISTINCT k.cite_key, d.title, d.authors, k.keyword,
                   k.context, k.page_num
            FROM keywords k
            JOIN documents d ON k.cite_key = d.cite_key
            WHERE k.keyword LIKE ?
            ORDER BY k.frequency DESC
            LIMIT ?
        """,
            (f"%{query.lower()}%", limit),
        )

        results = []
        for row in cursor.fetchall():
            cite_key, title, authors_json, keyword, context, page_num = row
            authors = json.loads(authors_json) if authors_json else []

            results.append(
                {
                    "cite_key": cite_key,
                    "title": title,
                    "authors": authors,
                    "keyword": keyword,
                    "context": context,
                    "page_num": page_num,
                }
            )

        conn.close()
        return results

    def get_document_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the knowledge base."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Basic counts
        cursor.execute("SELECT COUNT(*) FROM documents")
        doc_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM pages")
        page_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT keyword) FROM keywords")
        unique_keywords = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM keywords")
        total_keyword_instances = cursor.fetchone()[0]

        # Top keywords
        cursor.execute(
            """
            SELECT keyword, COUNT(*) as frequency
            FROM keywords
            GROUP BY keyword
            ORDER BY frequency DESC
            LIMIT 10
        """
        )
        top_keywords = cursor.fetchall()

        # Top authors
        cursor.execute("SELECT authors FROM documents WHERE authors != '[]'")
        all_authors = []
        for (authors_json,) in cursor.fetchall():
            authors = json.loads(authors_json)
            all_authors.extend(authors)

        author_counts = Counter(all_authors)
        top_authors = author_counts.most_common(10)

        # Year distribution
        cursor.execute(
            """
            SELECT year, COUNT(*) as count
            FROM documents
            WHERE year != ''
            GROUP BY year
            ORDER BY year DESC
        """
        )
        year_distribution = cursor.fetchall()

        conn.close()

        return {
            "document_count": doc_count,
            "page_count": page_count,
            "unique_keywords": unique_keywords,
            "total_keyword_instances": total_keyword_instances,
            "top_keywords": top_keywords,
            "top_authors": top_authors,
            "year_distribution": year_distribution,
        }

    def get_related_concepts(
        self, concept: str, limit: int = 10
    ) -> List[Tuple[str, int]]:
        """Get concepts related to the given concept."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT related_concept, SUM(co_occurrence_count) as total_count
            FROM concept_network
            WHERE concept LIKE ?
            GROUP BY related_concept
            ORDER BY total_count DESC
            LIMIT ?
        """,
            (f"%{concept.lower()}%", limit),
        )

        results = cursor.fetchall()
        conn.close()

        return results

    def export_knowledge_graph(self, output_file: Path) -> None:
        """Export knowledge graph for visualization."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get nodes (concepts)
        cursor.execute(
            """
            SELECT keyword, COUNT(*) as frequency
            FROM keywords
            GROUP BY keyword
            HAVING frequency > 2
            ORDER BY frequency DESC
            LIMIT 100
        """
        )
        nodes = [
            {"id": keyword, "frequency": freq} for keyword, freq in cursor.fetchall()
        ]

        # Get edges (co-occurrences)
        cursor.execute(
            """
            SELECT concept, related_concept, SUM(co_occurrence_count) as weight
            FROM concept_network
            GROUP BY concept, related_concept
            HAVING weight > 1
            ORDER BY weight DESC
            LIMIT 200
        """
        )
        edges = [
            {"source": c1, "target": c2, "weight": weight}
            for c1, c2, weight in cursor.fetchall()
        ]

        # Export as JSON
        graph_data = {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "generated": datetime.now().isoformat(),
                "node_count": len(nodes),
                "edge_count": len(edges),
            },
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)

        conn.close()


def main() -> None:
    """Command-line interface for knowledge tracker."""
    parser = argparse.ArgumentParser(
        description="Knowledge tracking system for PDF extractions"
    )
    parser.add_argument("--search", help="Search for keywords in the knowledge base")
    parser.add_argument(
        "--stats", action="store_true", help="Show knowledge base statistics"
    )
    parser.add_argument("--related", help="Find concepts related to given concept")
    parser.add_argument("--export-graph", help="Export knowledge graph to JSON file")
    parser.add_argument("--db-path", help="Path to knowledge database file")

    args = parser.parse_args()

    db_path = Path(args.db_path) if args.db_path else None
    tracker = KnowledgeTracker(db_path)

    if args.search:
        results = tracker.search_keywords(args.search)

        if results:
            print(f"\n🔍 Search results for '{args.search}':")
            for result in results:
                authors_str = ", ".join(result["authors"][:2])
                if len(result["authors"]) > 2:
                    authors_str += " et al."

                print(f"\n📄 {result['cite_key']} - {result['title']}")
                print(f"   👥 {authors_str}")
                print(f"   🔑 Keyword: {result['keyword']} (Page {result['page_num']})")
                print(f"   📝 Context: {result['context'][:200]}...")
        else:
            print(f"❌ No results found for '{args.search}'")

    elif args.related:
        related = tracker.get_related_concepts(args.related)

        if related:
            print(f"\n🔗 Concepts related to '{args.related}':")
            for concept, count in related:
                print(f"   • {concept}: {count} co-occurrences")
        else:
            print(f"❌ No related concepts found for '{args.related}'")

    elif args.export_graph:
        output_file = Path(args.export_graph)
        tracker.export_knowledge_graph(output_file)
        print(f"📊 Knowledge graph exported to: {output_file}")

    elif args.stats:
        stats = tracker.get_document_stats()

        print("\n📊 Knowledge Base Summary:")
        print(f"   📚 Documents: {stats['document_count']}")
        print(f"   📄 Pages: {stats['page_count']}")
        print(f"   🔑 Unique keywords: {stats['unique_keywords']}")
        print(f"   📝 Total keyword instances: {stats['total_keyword_instances']}")

        if stats["top_keywords"]:
            print("\n🔥 Top Keywords:")
            for keyword, freq in stats["top_keywords"][:5]:
                print(f"   • {keyword}: {freq}")

        if stats["top_authors"]:
            print("\n👥 Top Authors:")
            for author, count in stats["top_authors"][:5]:
                print(f"   • {author}: {count} papers")

    else:
        print("Use --help for usage information")


if __name__ == "__main__":
    main()
