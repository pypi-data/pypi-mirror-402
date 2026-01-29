"""
embedding-eval: Fair Embedding Model Evaluation

A minimal package for fair comparison of embedding models with
independent parameter optimization.

Key Features:
- Each model gets its own optimized parameters (chunk_size, overlap, top_k)
- Binary evaluation with substring matching (no LLM cost)
- Reports baseline + optimized + 95% confidence intervals
- No external dependencies for core functionality

Quick Start:
    ```python
    from embedding_eval import run_fair_comparison

    # Compare models with independent optimization
    results = run_fair_comparison(
        models=["st:bge-base", "st:minilm"],
        doc_content=document_text,
        qa_pairs=[{"question": "...", "answer": "..."}],
    )

    for r in results:
        print(f"{r.model_name}: {r.best_accuracy:.1f}% (baseline: {r.baseline_accuracy:.1f}%)")
    ```

Components:
- `optimization`: Fair comparison with grid search
- `evaluation`: Binary substring evaluator
- `chunking`: Fixed-size chunker with token counting
- `adapters.embedding`: SentenceTransformers and OpenAI
- `adapters.vector`: InMemoryVectorStore (no external deps)
"""

__version__ = "0.2.0"

# Core exports
from embedding_eval.core.models import (
    Chunk,
    Document,
    EvaluationScore,
    QAPair,
)
from embedding_eval.evaluation import BinaryEvaluator
from embedding_eval.evaluation.validation import (
    ValidationResult,
    validate_fixture,
)
from embedding_eval.optimization import (
    OptimizationResult,
    optimize_model,
    run_fair_comparison,
)

__all__ = [
    # Version
    "__version__",
    # Core models
    "Chunk",
    "Document",
    "EvaluationScore",
    "QAPair",
    # Evaluation
    "BinaryEvaluator",
    # Validation
    "ValidationResult",
    "validate_fixture",
    # Optimization
    "OptimizationResult",
    "optimize_model",
    "run_fair_comparison",
]
