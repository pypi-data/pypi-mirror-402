"""
Optimization module for fair embedding model comparison.

Provides the core methodology for comparing embedding models:
- Independent parameter optimization for each model
- Grid search across chunk_size, overlap, top_k
- Reports baseline + optimized + confidence intervals
"""

from embedding_eval.optimization.fair_comparison import (
    OptimizationResult,
    calculate_confidence_interval,
    evaluate_configuration,
    get_embedding_model,
    optimize_model,
    run_fair_comparison,
)

__all__ = [
    "OptimizationResult",
    "calculate_confidence_interval",
    "evaluate_configuration",
    "get_embedding_model",
    "optimize_model",
    "run_fair_comparison",
]
