# SPDX-License-Identifier: MIT
"""RAG (Retrieval-Augmented Generation) module for YAML pipeline."""

from pipeline.rag.doc_classifier import classify_document_role, DocumentRole
from pipeline.rag.chunk_builder import build_rag_chunks, table_rows_to_sentences
from pipeline.rag.faiss_indexer import FaissIndexer
from pipeline.rag.retriever import RagRetriever
from pipeline.rag.query_classifier import classify_query, QueryType
from pipeline.rag.context_assembler import assemble_context
from pipeline.rag.prompt_templates import (
    SYSTEM_PROMPT,
    build_prompt,
    format_answer_with_sources,
)

__all__ = [
    # 문서 분류
    "classify_document_role",
    "DocumentRole",
    # 청킹
    "build_rag_chunks",
    "table_rows_to_sentences",
    # 인덱싱
    "FaissIndexer",
    # 검색
    "RagRetriever",
    # 질문 분류
    "classify_query",
    "QueryType",
    # 컨텍스트 조합
    "assemble_context",
    # 프롬프트
    "SYSTEM_PROMPT",
    "build_prompt",
    "format_answer_with_sources",
]
