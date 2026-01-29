"""
Core functionality for Elasticsearch operations.

This package contains the core components for interacting with Elasticsearch.
"""

from elastro.core.client import ElasticsearchClient
from elastro.core.index import IndexManager
from elastro.core.document import DocumentManager
from elastro.core.datastream import DatastreamManager
from elastro.core.validation import Validator
from elastro.core.document_bulk import BulkDocumentManager

__all__ = [
    "ElasticsearchClient",
    "IndexManager",
    "DocumentManager",
    "DatastreamManager",
    "Validator",
    "BulkDocumentManager",
]
