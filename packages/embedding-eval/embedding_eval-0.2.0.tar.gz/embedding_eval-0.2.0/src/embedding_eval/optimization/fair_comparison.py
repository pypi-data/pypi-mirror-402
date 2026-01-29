"""
Fair Embedding Model Comparison with Independent Optimization.

This module performs a fair comparison of embedding models by:
1. Optimizing parameters independently for each model
2. Using grid search across chunk sizes, overlap, and top-k
3. Reporting both optimized and baseline results

Key Methodology:
- Each model gets its own best parameters
- Not: "Use parameters optimized for model A on all models"
- Reports baseline + optimized + confidence intervals
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from embedding_eval.adapters.vector import InMemoryVectorStore
from embedding_eval.chunking import FixedSizeChunker
from embedding_eval.core.models import Document
from embedding_eval.evaluation import BinaryEvaluator


@dataclass
class OptimizationResult:
    """Result of parameter optimization for a single model."""

    model_spec: str
    model_name: str
    dimensions: int

    # Optimized results
    best_accuracy: float
    best_params: dict[str, Any]
    best_passed: int
    total_questions: int

    # Baseline results (512 chunk, 50 overlap, top-k 10)
    baseline_accuracy: float
    baseline_passed: int

    # Improvement
    improvement_pct: float = 0.0

    # Confidence interval (95%)
    ci_lower: float = 0.0
    ci_upper: float = 0.0

    # Timing
    optimization_time_seconds: float = 0.0
    configurations_tested: int = 0

    # Full grid results
    all_results: list[dict[str, Any]] = field(default_factory=list)


def calculate_confidence_interval(
    accuracy: float, n: int, confidence: float = 0.95
) -> tuple[float, float]:
    """
    Calculate confidence interval for proportion using Wilson score.

    Args:
        accuracy: Observed accuracy (0-100)
        n: Number of questions
        confidence: Confidence level (default 0.95)

    Returns:
        (lower, upper) bounds as percentages
    """
    if n == 0:
        return 0.0, 0.0

    p = accuracy / 100
    z = 1.96 if confidence == 0.95 else 2.576  # z-score for 95% or 99%

    # Wilson score interval
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denominator

    lower = max(0, (center - margin) * 100)
    upper = min(100, (center + margin) * 100)

    return lower, upper


def get_embedding_model(model_spec: str):
    """
    Get an embedding model from specification string.

    Formats:
    - "st:bge-base" or "st:BAAI/bge-base-en-v1.5" - SentenceTransformers
    - "openai:text-embedding-3-small" - OpenAI (requires API key)

    Args:
        model_spec: Model specification string

    Returns:
        Embedding model instance
    """
    parts = model_spec.split(":")
    provider = parts[0].lower()
    model_name = parts[1] if len(parts) > 1 else None

    if provider in ("st", "sentence-transformers", "local"):
        from embedding_eval.adapters.embedding import SentenceTransformerEmbedding

        return SentenceTransformerEmbedding(model=model_name or "bge-base")

    elif provider == "openai":
        from embedding_eval.adapters.embedding.openai_embedding import OpenAIEmbedding

        return OpenAIEmbedding(model=model_name or "text-embedding-3-small")

    else:
        raise ValueError(f"Unknown provider: {provider}. Use 'st:' or 'openai:'")


def evaluate_configuration(
    embedding_model,
    doc_content: str,
    qa_pairs: list[dict[str, Any]],
    chunk_size: int,
    overlap: int,
    top_k: int,
    evaluator: BinaryEvaluator,
) -> tuple[int, int, float]:
    """
    Evaluate a single configuration.

    Args:
        embedding_model: Embedding model instance
        doc_content: Document text content
        qa_pairs: List of Q&A pairs
        chunk_size: Chunk size in tokens
        overlap: Overlap in tokens
        top_k: Number of results to retrieve
        evaluator: BinaryEvaluator instance

    Returns:
        (passed, total, accuracy)
    """
    # Create chunks
    chunker = FixedSizeChunker(chunk_size=chunk_size, overlap=overlap)
    doc = Document(content=doc_content)
    chunks = chunker.chunk(doc)
    chunk_texts = [c.content for c in chunks]

    if not chunks:
        return 0, len(qa_pairs), 0.0

    # Embed chunks
    if hasattr(embedding_model, "embed_documents"):
        chunk_embeddings = embedding_model.embed_documents(chunk_texts)
    else:
        chunk_embeddings = embedding_model.embed_texts(chunk_texts)

    # Create vector store
    store = InMemoryVectorStore()
    store.connect()
    ids = [str(uuid4()) for _ in chunks]
    dims = len(chunk_embeddings[0])
    store.create_collection("test", dimensions=dims)
    store.upsert("test", ids, chunk_embeddings, texts=chunk_texts)

    # Evaluate
    passed = 0
    for qa in qa_pairs:
        query = qa["question"]
        expected = qa["answer"]

        query_embedding = embedding_model.embed_query(query)
        search_results = store.search("test", query_embedding, top_k=top_k)
        retrieved_texts = [r.get("text", "") for r in search_results]

        score = evaluator.evaluate(query, expected, retrieved_texts)
        if score.score >= 0.5:
            passed += 1

    accuracy = passed / len(qa_pairs) * 100
    return passed, len(qa_pairs), accuracy


def optimize_model(
    model_spec: str,
    doc_content: str,
    qa_pairs: list[dict[str, Any]],
    chunk_sizes: list[int] | None = None,
    overlaps: list[int] | None = None,
    top_ks: list[int] | None = None,
    baseline_params: dict[str, int] | None = None,
    verbose: bool = True,
) -> OptimizationResult:
    """
    Optimize parameters for a single embedding model.

    Performs grid search over chunk_size, overlap, and top_k.

    Args:
        model_spec: Model specification (e.g., "st:bge-base")
        doc_content: Document text content
        qa_pairs: List of Q&A pairs with 'question' and 'answer' keys
        chunk_sizes: List of chunk sizes to try (default: [256, 384, 512])
        overlaps: List of overlaps to try (default: [25, 50, 100])
        top_ks: List of top-k values to try (default: [5, 10, 15])
        baseline_params: Baseline parameters (default: chunk=512, overlap=50, top_k=10)
        verbose: Print progress

    Returns:
        OptimizationResult with best and baseline accuracy
    """
    # Default parameter grids
    if chunk_sizes is None:
        chunk_sizes = [256, 384, 512]
    if overlaps is None:
        overlaps = [25, 50, 100]
    if top_ks is None:
        top_ks = [5, 10, 15]
    if baseline_params is None:
        baseline_params = {"chunk_size": 512, "overlap": 50, "top_k": 10}

    start_time = time.time()

    # Load model
    if verbose:
        print(f"\nOptimizing: {model_spec}")

    embedding_model = get_embedding_model(model_spec)
    model_name = embedding_model.model_name
    dimensions = embedding_model.dimensions

    if verbose:
        print(f"  Model: {model_name} ({dimensions} dims)")

    evaluator = BinaryEvaluator()
    all_results = []
    best_result = None
    baseline_result = None

    total_configs = len(chunk_sizes) * len(overlaps) * len(top_ks)
    config_num = 0

    for chunk_size in chunk_sizes:
        for overlap in overlaps:
            # Skip invalid configurations
            if overlap >= chunk_size:
                continue

            for top_k in top_ks:
                config_num += 1

                if verbose:
                    print(
                        f"  [{config_num}/{total_configs}] "
                        f"chunk={chunk_size}, overlap={overlap}, top_k={top_k}",
                        end=" ",
                    )

                passed, total, accuracy = evaluate_configuration(
                    embedding_model=embedding_model,
                    doc_content=doc_content,
                    qa_pairs=qa_pairs,
                    chunk_size=chunk_size,
                    overlap=overlap,
                    top_k=top_k,
                    evaluator=evaluator,
                )

                result = {
                    "chunk_size": chunk_size,
                    "overlap": overlap,
                    "top_k": top_k,
                    "passed": passed,
                    "total": total,
                    "accuracy": accuracy,
                }
                all_results.append(result)

                if verbose:
                    print(f"-> {passed}/{total} ({accuracy:.1f}%)")

                # Track best
                if best_result is None or accuracy > best_result["accuracy"]:
                    best_result = result

                # Track baseline
                if (
                    chunk_size == baseline_params["chunk_size"]
                    and overlap == baseline_params["overlap"]
                    and top_k == baseline_params["top_k"]
                ):
                    baseline_result = result

    # If baseline wasn't in grid, compute it
    if baseline_result is None:
        if verbose:
            print(f"  Computing baseline ({baseline_params})...")
        passed, total, accuracy = evaluate_configuration(
            embedding_model=embedding_model,
            doc_content=doc_content,
            qa_pairs=qa_pairs,
            chunk_size=baseline_params["chunk_size"],
            overlap=baseline_params["overlap"],
            top_k=baseline_params["top_k"],
            evaluator=evaluator,
        )
        baseline_result = {
            **baseline_params,
            "passed": passed,
            "total": total,
            "accuracy": accuracy,
        }

    elapsed = time.time() - start_time

    # Calculate confidence interval for best result
    ci_lower, ci_upper = calculate_confidence_interval(
        best_result["accuracy"], best_result["total"]
    )

    # Calculate improvement
    improvement = best_result["accuracy"] - baseline_result["accuracy"]

    if verbose:
        print(
            f"  Best: {best_result['accuracy']:.1f}% "
            f"(chunk={best_result['chunk_size']}, overlap={best_result['overlap']}, "
            f"top_k={best_result['top_k']})"
        )
        print(f"  95% CI: [{ci_lower:.1f}%, {ci_upper:.1f}%]")
        print(f"  Baseline: {baseline_result['accuracy']:.1f}%")
        print(f"  Improvement: {improvement:+.1f}pp")
        print(f"  Time: {elapsed:.1f}s")

    return OptimizationResult(
        model_spec=model_spec,
        model_name=model_name,
        dimensions=dimensions,
        best_accuracy=best_result["accuracy"],
        best_params={
            "chunk_size": best_result["chunk_size"],
            "overlap": best_result["overlap"],
            "top_k": best_result["top_k"],
        },
        best_passed=best_result["passed"],
        total_questions=best_result["total"],
        baseline_accuracy=baseline_result["accuracy"],
        baseline_passed=baseline_result["passed"],
        improvement_pct=improvement,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        optimization_time_seconds=elapsed,
        configurations_tested=len(all_results),
        all_results=all_results,
    )


def run_fair_comparison(
    models: list[str],
    doc_content: str,
    qa_pairs: list[dict[str, Any]],
    chunk_sizes: list[int] | None = None,
    overlaps: list[int] | None = None,
    top_ks: list[int] | None = None,
    verbose: bool = True,
) -> list[OptimizationResult]:
    """
    Run fair comparison by optimizing each model independently.

    This is the recommended way to compare embedding models:
    - Each model gets its own optimized parameters
    - Reports both baseline and optimized accuracy
    - Includes confidence intervals

    Args:
        models: List of model specifications (e.g., ["st:bge-base", "st:minilm"])
        doc_content: Document text content
        qa_pairs: List of Q&A pairs
        chunk_sizes: Parameter grid for chunk sizes
        overlaps: Parameter grid for overlaps
        top_ks: Parameter grid for top-k
        verbose: Print progress

    Returns:
        List of OptimizationResult, one per model
    """
    if verbose:
        print("=" * 70)
        print("FAIR EMBEDDING MODEL COMPARISON")
        print("=" * 70)
        print(f"Models: {len(models)}")
        print(f"Questions: {len(qa_pairs)}")
        print(f"Document length: {len(doc_content):,} chars")
        print("=" * 70)

    results = []
    for model_spec in models:
        result = optimize_model(
            model_spec=model_spec,
            doc_content=doc_content,
            qa_pairs=qa_pairs,
            chunk_sizes=chunk_sizes,
            overlaps=overlaps,
            top_ks=top_ks,
            verbose=verbose,
        )
        results.append(result)

    if verbose:
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"{'Model':<40} {'Baseline':>10} {'Optimized':>10} {'Δ':>8}")
        print("-" * 70)
        for r in sorted(results, key=lambda x: x.best_accuracy, reverse=True):
            print(
                f"{r.model_name:<40} "
                f"{r.baseline_accuracy:>9.1f}% "
                f"{r.best_accuracy:>9.1f}% "
                f"{r.improvement_pct:>+7.1f}pp"
            )
        print("=" * 70)

    return results
