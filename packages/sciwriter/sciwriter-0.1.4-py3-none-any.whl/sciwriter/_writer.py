"""Writer class - Object-oriented interface for sciwriter.

Provides a clean OOP API for managing scientific manuscripts.

Example:
    writer = Writer("./my-paper")
    writer.section.list()
    writer.section.read("abstract")
    writer.compile.manuscript()
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from sciwriter._analysis import OutlineItem, ValidationResult, WordCountResult
    from sciwriter._compiler import CompileResult
    from sciwriter._content import Section
    from sciwriter._media import CitationInfo, FigureInfo, Reference, TableInfo


class _JobManager:
    """Job management submodule."""

    def __init__(self, writer: "Writer"):
        self._writer = writer

    def list(self, status: Optional[str] = None, limit: int = 20) -> list[dict]:
        """List background jobs."""
        from sciwriter._jobs import JobStatus, job_manager

        status_enum = JobStatus(status) if status else None
        jobs = job_manager.list_jobs(status_enum, limit)
        return [j.to_dict() for j in jobs]

    def read(self, job_id: str) -> Optional[dict]:
        """Read job details by ID."""
        from sciwriter._jobs import job_manager

        job = job_manager.get_job(job_id)
        return job.to_dict() if job else None

    def cancel(self, job_id: str) -> bool:
        """Cancel a running job."""
        from sciwriter._jobs import job_manager

        return job_manager.cancel_job(job_id)

    def clear(self, statuses: Optional[list[str]] = None) -> int:
        """Clear completed/failed jobs."""
        from sciwriter._jobs import JobStatus, job_manager

        status_enums = [JobStatus(s) for s in statuses] if statuses else None
        return job_manager.clear_jobs(status_enums)


class _SectionManager:
    """Section management submodule."""

    def __init__(self, writer: "Writer"):
        self._writer = writer

    def list(self, doc_type: str = "manuscript") -> list[dict]:
        """List available sections with paths."""
        from sciwriter._content import list_sections

        return list_sections(self._writer._path, doc_type)

    def read(self, section: str, doc_type: str = "manuscript") -> Optional["Section"]:
        """Read a section's content."""
        from sciwriter._content import read_section

        return read_section(self._writer._path, section, doc_type)

    def create(
        self, section: str, content: str = "", doc_type: str = "manuscript"
    ) -> bool:
        """Create a new section."""
        from sciwriter._content import create_section

        return create_section(self._writer._path, section, content, doc_type)

    def update(self, section: str, content: str, doc_type: str = "manuscript") -> bool:
        """Update a section's content."""
        from sciwriter._content import update_section

        return update_section(self._writer._path, section, content, doc_type)

    def delete(self, section: str, doc_type: str = "manuscript") -> bool:
        """Delete a section."""
        from sciwriter._content import delete_section

        return delete_section(self._writer._path, section, doc_type)

    def init(
        self,
        sections: Optional[list[str]] = None,
        doc_type: str = "manuscript",
    ) -> dict[str, bool]:
        """Initialize sections to default templates."""
        from sciwriter._content import init_sections

        return init_sections(self._writer._path, sections, doc_type)


class _FigureManager:
    """Figure management submodule."""

    def __init__(self, writer: "Writer"):
        self._writer = writer

    def list(self, doc_type: str = "manuscript") -> list[dict]:
        """List all figures."""
        from sciwriter._media import list_figures

        return list_figures(self._writer._path, doc_type)

    def read(
        self, figure_id: str, doc_type: str = "manuscript"
    ) -> Optional["FigureInfo"]:
        """Read figure details."""
        from sciwriter._media import get_figure

        return get_figure(self._writer._path, figure_id, doc_type)

    def create(
        self,
        figure_id: str,
        caption: str,
        doc_type: str = "manuscript",
        image_path: Optional[str] = None,
    ) -> bool:
        """Create a new figure with caption and optional image.

        Args:
            figure_id: Figure identifier (e.g., '01', '02_overview'). Creates
                      contents/figures/caption_and_media/{figure_id}.tex
            caption: Figure caption text
            doc_type: Document type (manuscript, supplementary, revision)
            image_path: Optional path to image file (PNG, PDF, TIF, etc.)

        Returns:
            True if created successfully, False if already exists

        Example:
            writer.figures.create('01_overview', 'System overview',
                                 image_path='./plots/overview.png')
        """
        from sciwriter._media import create_figure

        result = create_figure(
            self._writer._path, figure_id, caption, doc_type, image_path
        )
        return result is not None

    def update(
        self, figure_id: str, caption: str, doc_type: str = "manuscript"
    ) -> bool:
        """Update figure caption."""
        from sciwriter._media import update_figure

        return update_figure(self._writer._path, figure_id, caption, doc_type)

    def delete(self, figure_id: str, doc_type: str = "manuscript") -> bool:
        """Delete a figure."""
        from sciwriter._media import delete_figure

        return delete_figure(self._writer._path, figure_id, doc_type)


class _TableManager:
    """Table management submodule."""

    def __init__(self, writer: "Writer"):
        self._writer = writer

    def list(self, doc_type: str = "manuscript") -> list[dict]:
        """List all tables."""
        from sciwriter._media import list_tables

        return list_tables(self._writer._path, doc_type)

    def read(
        self, table_id: str, doc_type: str = "manuscript"
    ) -> Optional["TableInfo"]:
        """Read table details."""
        from sciwriter._media import get_table

        return get_table(self._writer._path, table_id, doc_type)

    def create(
        self,
        table_id: str,
        caption: str,
        doc_type: str = "manuscript",
        csv_path: Optional[str] = None,
    ) -> bool:
        """Create a new table with caption and CSV data.

        Args:
            table_id: Table identifier (e.g., '01', '02_results'). Creates
                     contents/tables/caption_and_media/{table_id}.tex
            caption: Table caption text
            doc_type: Document type (manuscript, supplementary, revision)
            csv_path: Optional path to CSV file with table data

        Returns:
            True if created successfully, False if already exists

        Example:
            writer.tables.create('01_results', 'Experimental results',
                                csv_path='./data/results.csv')
        """
        from sciwriter._media import create_table

        result = create_table(self._writer._path, table_id, caption, doc_type, csv_path)
        return result is not None

    def update(self, table_id: str, caption: str, doc_type: str = "manuscript") -> bool:
        """Update table caption."""
        from sciwriter._media import update_table

        return update_table(self._writer._path, table_id, caption, doc_type)

    def delete(self, table_id: str, doc_type: str = "manuscript") -> bool:
        """Delete a table."""
        from sciwriter._media import delete_table

        return delete_table(self._writer._path, table_id, doc_type)


class _CitationManager:
    """Citation management submodule."""

    def __init__(self, writer: "Writer"):
        self._writer = writer

    def list(self) -> list[dict]:
        """List all citations."""
        from sciwriter._media import list_citations

        return list_citations(self._writer._path)

    def read(self, key: str) -> Optional["CitationInfo"]:
        """Read citation details."""
        from sciwriter._media import get_citation

        return get_citation(self._writer._path, key)

    def create(self, key: str, entry_type: str, fields: dict) -> bool:
        """Create a new BibTeX citation entry.

        Args:
            key: Citation key (e.g., 'smith2024', 'jones2023nature')
            entry_type: BibTeX type (article, book, inproceedings, misc, etc.)
            fields: BibTeX fields dict, e.g.:
                    {'author': 'Smith, John', 'title': 'My Paper',
                     'journal': 'Nature', 'year': '2024', 'doi': '10.1234/...'}

        Returns:
            True if created, False if key already exists

        Example:
            writer.citations.create('smith2024', 'article', {
                'author': 'Smith, John and Doe, Jane',
                'title': 'A Great Paper',
                'journal': 'Nature',
                'year': '2024',
                'volume': '123',
                'pages': '1--10',
            })
        """
        from sciwriter._media import create_citation

        return create_citation(self._writer._path, key, entry_type, fields)

    def update(self, key: str, fields: dict) -> bool:
        """Update citation fields."""
        from sciwriter._media import update_citation

        return update_citation(self._writer._path, key, fields)

    def delete(self, key: str) -> bool:
        """Delete a citation."""
        from sciwriter._media import delete_citation

        return delete_citation(self._writer._path, key)


class _VersionManager:
    """Version/history management submodule."""

    def __init__(self, writer: "Writer"):
        self._writer = writer

    def list(self, doc_type: str = "manuscript", limit: int = 10) -> list[dict]:
        """List document versions."""
        from sciwriter._analysis import list_versions

        return list_versions(self._writer._path, doc_type, limit)

    def diff(
        self,
        doc_type: str = "manuscript",
        commit1: str = "HEAD~1",
        commit2: str = "HEAD",
    ) -> str:
        """View diff between versions."""
        from sciwriter._analysis import view_diff

        return view_diff(self._writer._path, doc_type, commit1, commit2)


class _RefManager:
    """Reference/label management submodule."""

    def __init__(self, writer: "Writer"):
        self._writer = writer

    def list(
        self, doc_type: str = "manuscript", ref_type: Optional[str] = None
    ) -> list["Reference"]:
        """Find all references in the document."""
        from sciwriter._media import find_references

        return find_references(self._writer._path, doc_type, ref_type)

    def labels(self, doc_type: str = "manuscript") -> list[str]:
        """Find all labels in the document."""
        from sciwriter._media import find_labels

        return find_labels(self._writer._path, doc_type)


class _CompileManager:
    """Compilation submodule."""

    def __init__(self, writer: "Writer"):
        self._writer = writer

    def manuscript(self, **kwargs) -> "CompileResult":
        """Compile the manuscript document."""
        from sciwriter._compiler import compile_manuscript

        return compile_manuscript(self._writer._path, **kwargs)

    def supplementary(self, **kwargs) -> "CompileResult":
        """Compile the supplementary materials."""
        from sciwriter._compiler import compile_supplementary

        return compile_supplementary(self._writer._path, **kwargs)

    def revision(self, **kwargs) -> "CompileResult":
        """Compile the revision response document."""
        from sciwriter._compiler import compile_revision

        return compile_revision(self._writer._path, **kwargs)

    def __call__(self, doc_type: str = "manuscript", **kwargs) -> "CompileResult":
        """Compile a document by type."""
        from sciwriter._compiler import compile_document

        return compile_document(doc_type, self._writer._path, **kwargs)


class _DocManager:
    """Document and project analysis submodule."""

    def __init__(self, writer: "Writer"):
        self._writer = writer

    @property
    def path(self) -> Path:
        """Project directory path."""
        return self._writer._path

    @property
    def status(self) -> dict:
        """Get combined project and compilation status."""
        from sciwriter._compiler import get_project_info, get_status

        info = get_project_info(self._writer._path)
        compilation = get_status(self._writer._path)
        return {**info, "compilation": compilation}

    def clean(self) -> int:
        """Clean compilation artifacts."""
        from sciwriter._compiler import clean_project

        return clean_project(self._writer._path)

    def get_outline(self, doc_type: str = "manuscript") -> list["OutlineItem"]:
        """Get document outline with word counts."""
        from sciwriter._analysis import get_outline

        return get_outline(self._writer._path, doc_type)

    def count_words(
        self, doc_type: str = "manuscript", section: Optional[str] = None
    ) -> "WordCountResult":
        """Get word count."""
        from sciwriter._analysis import get_word_count

        return get_word_count(self._writer._path, doc_type, section)

    def validate(self, doc_type: str = "manuscript") -> "ValidationResult":
        """Validate document for issues."""
        from sciwriter._analysis import check_document

        return check_document(self._writer._path, doc_type)


class Writer:
    """Object-oriented interface for managing a sciwriter project.

    Submodules:
        citations: Manage citations (list, get, create, update, delete)
        compile:   Compile documents (manuscript, supplementary, revision)
        doc:       Project/document (path, status, clean, get_outline, count_words, validate)
        figures:   Manage figures (list, get, create, update, delete)
        jobs:      Background jobs (list, get, cancel, clear)
        refs:      References (list, labels)
        sections:  Manage sections (list, read, create, update, delete, init)
        tables:    Manage tables (list, get, create, update, delete)
        versions:  Version history (list, diff)

    Example:
        >>> writer = Writer("./my-paper")
        >>> writer.doc.path
        PosixPath('/path/to/my-paper')
        >>> writer.doc.status
        {'has_manuscript': True, ...}
        >>> writer.sections.list()
        [{'name': 'abstract', 'path': '...'}, ...]
        >>> writer.compile.manuscript()
        CompileResult(success=True, output_path=...)
    """

    def __init__(self, project: str | Path):
        """Initialize Writer with a project path or name.

        Args:
            project: Path to project directory or registered project name
        """
        from sciwriter._project import resolve_project

        resolved = resolve_project(str(project))
        if resolved is None:
            self._path = Path(project).resolve()
        else:
            self._path = resolved

        # Initialize submodules (plural names)
        self.citations = _CitationManager(self)
        self.compile = _CompileManager(self)
        self.doc = _DocManager(self)
        self.figures = _FigureManager(self)
        self.jobs = _JobManager(self)
        self.refs = _RefManager(self)
        self.sections = _SectionManager(self)
        self.tables = _TableManager(self)
        self.versions = _VersionManager(self)

    def __repr__(self) -> str:
        return f"Writer('{self._path}')"

    def __str__(self) -> str:
        return str(self._path)


__all__ = ["Writer"]
