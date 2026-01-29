"""Document parsers for the pipeline.

PDF, HWP, HWPX 등 다양한 문서 형식을 YAML로 직접 변환.

권장 사용법:
    from pipeline.parsers import UnifiedParser

    parser = UnifiedParser()
    result = parser.parse(file_path)  # Returns YAML dict
"""

from pipeline.parsers.base import (
    BaseParser,
    ParsedDocument,
    DocumentStructure,
    TableData,
)
from pipeline.parsers.factory import ParserFactory  # Deprecated

__all__ = [
    # Base classes
    "BaseParser",
    "ParsedDocument",
    "DocumentStructure",
    "TableData",
    # Factory (deprecated)
    "ParserFactory",
    # YAML adapters (recommended)
    "UnifiedParser",
    "DoclingYAMLAdapter",
    "HWPYAMLAdapter",
    "HWPXYAMLAdapter",
    # Chunk parser
    "ChunkParser",
    "Chunk",
    "ChunkType",
    "ParseResult",
    # Special clause parser
    "SpecialClauseParser",
    "ClauseChunk",
]


def __getattr__(name: str):
    """Lazy loading of parser classes to avoid circular imports."""
    # YAML adapters (recommended)
    if name == "UnifiedParser":
        from pipeline.parsers.unified_parser import UnifiedParser

        return UnifiedParser
    elif name == "DoclingYAMLAdapter":
        from pipeline.parsers.docling_yaml_adapter import DoclingYAMLAdapter

        return DoclingYAMLAdapter
    elif name == "HWPYAMLAdapter":
        from pipeline.parsers.hwp_yaml_adapter import HWPYAMLAdapter

        return HWPYAMLAdapter
    elif name == "HWPXYAMLAdapter":
        from pipeline.parsers.hwpx_yaml_adapter import HWPXYAMLAdapter

        return HWPXYAMLAdapter
    # Chunk parser
    elif name == "ChunkParser":
        from pipeline.parsers.chunk_parser import ChunkParser

        return ChunkParser
    elif name == "Chunk":
        from pipeline.parsers.chunk_parser import Chunk

        return Chunk
    elif name == "ChunkType":
        from pipeline.parsers.chunk_parser import ChunkType

        return ChunkType
    elif name == "ParseResult":
        from pipeline.parsers.chunk_parser import ParseResult

        return ParseResult
    # Special clause parser
    elif name == "SpecialClauseParser":
        from pipeline.parsers.special_clause_parser import SpecialClauseParser

        return SpecialClauseParser
    elif name == "ClauseChunk":
        from pipeline.parsers.special_clause_parser import ClauseChunk

        return ClauseChunk
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
