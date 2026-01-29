"""
NeuroIndex - Production-Ready Hybrid Vector + Semantic Graph Memory System
===========================================================================

🌟 COMMUNITY EDITION (Open Source)
----------------------------------
Free for personal and commercial use under MIT license.

Limitations:
- Max 10,000 documents
- 384-dimension embeddings only
- Vector search only (no semantic graph)
- No batch insert
- No GPU support

⭐ UPGRADE TO PRO
-----------------
For unlimited documents, any dimension, semantic graph, batch ops, and GPU:
→ Contact umeshkumarpal667@gmail.com for Pro

Example:
    >>> from neuroindex import NeuroIndex
    >>> import numpy as np
    >>>
    >>> with NeuroIndex(path="./memory", dim=384) as ni:
    ...     embedding = np.random.rand(384).astype('float32')
    ...     node_id = ni.add_document("Hello world", embedding)
    ...     results = ni.search(embedding, k=5)
    ...     print(results)

Author: Umeshkumar Pal
License: MIT
Repository: https://github.com/Umeshkumar667/NeuroIndex
"""

from .core import NeuroIndex, SearchResult
from .exceptions import (
    ConcurrencyError,
    DimensionMismatchError,
    DocumentNotFoundError,
    IndexCorruptedError,
    InvalidInputError,
    NeuroIndexError,
    StorageError,
)
from .metrics import MetricsCollector

__version__ = "1.0.0"
__author__ = "Umeshkumar Pal"
__license__ = "MIT"
__edition__ = "Community"

__all__ = [
    # Main classes
    "NeuroIndex",
    "SearchResult",
    "MetricsCollector",
    # Exceptions
    "NeuroIndexError",
    "DimensionMismatchError",
    "StorageError",
    "IndexCorruptedError",
    "DocumentNotFoundError",
    "InvalidInputError",
    "ConcurrencyError",
    # Functions
    "get_pro",
    # Metadata
    "__version__",
    "__author__",
    "__license__",
    "__edition__",
]


def get_pro():
    """
    Get NeuroIndex Pro with full features.
    
    Returns instructions to upgrade to Pro version.
    """
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                    NeuroIndex Pro                              ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  Unlock all features:                                         ║
║                                                               ║
║  ✓ Unlimited documents (vs 10,000 limit)                      ║
║  ✓ Any embedding dimension (vs 384 only)                      ║
║  ✓ Semantic graph traversal                                   ║
║  ✓ Batch insert (15x faster)                                  ║
║  ✓ GPU acceleration                                           ║
║  ✓ O(log n) graph building                                    ║
║  ✓ Priority support                                           ║
║                                                               ║
║  Pricing:                                                     ║
║  • Pro: $49/month                                             ║
║  • Enterprise: $149/month (includes cloud API)                ║
║                                                               ║
║  → Email: umeshkumarpal667@gmail.com                          ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    return None
